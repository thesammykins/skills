#!/usr/bin/env python3
"""Validate Buildkite pipeline YAML against local quality guardrails."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SECRET_KEY_RE = re.compile(r"(secret|token|password|passwd|private[_-]?key|credential|api[_-]?key|access[_-]?key)", re.IGNORECASE)
RAW_SECRET_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY|ACCESS_KEY)[A-Z0-9_]*)\b\s*[:=]\s*['\"]?([^'\"\s#]{10,})"
)
DEPLOY_RE = re.compile(r"\b(deploy|release|publish|promote|production|prod)\b", re.IGNORECASE)
BRANCH_OR_TAG_RE = re.compile(r"build\.(branch|tag)\b")
MAKE_COMMAND_RE = re.compile(r"(?:^|[;&|]\s*)make\s+([A-Za-z0-9_.-]+)")
NPM_RUN_RE = re.compile(r"(?:^|[;&|]\s*)npm\s+run\s+([A-Za-z0-9:_.-]+)")


class CheckResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def load_yaml(path: Path) -> tuple[Any | None, str | None]:
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        yaml = None

    if yaml is not None:
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")), None
        except Exception as exc:  # pragma: no cover - depends on optional dependency
            return None, str(exc)

    ruby = shutil.which("ruby")
    if ruby:
        code = (
            "require 'yaml'; require 'json'; "
            "obj = YAML.safe_load(File.read(ARGV[0]), aliases: true); "
            "puts JSON.generate(obj)"
        )
        proc = subprocess.run(
            [ruby, "-e", code, str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            return None, proc.stderr.strip() or proc.stdout.strip() or "ruby YAML parser failed"
        try:
            return json.loads(proc.stdout), None
        except json.JSONDecodeError as exc:
            return None, f"ruby YAML parser returned invalid JSON: {exc}"

    return None, "no YAML parser found; install PyYAML or make ruby available"


def infer_repo_root(pipeline_path: Path) -> Path:
    parent = pipeline_path.resolve().parent
    if parent.name == ".buildkite":
        return parent.parent
    return parent


def parse_makefile_targets(repo_root: Path) -> set[str]:
    makefile = repo_root / "Makefile"
    if not makefile.exists():
        return set()
    targets: set[str] = set()
    try:
        for line in makefile.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?:\s|$)", line)
            if match and not match.group(1).startswith("."):
                targets.add(match.group(1))
    except OSError:
        return set()
    return targets


def parse_package_scripts(repo_root: Path) -> set[str]:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return set()
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return set()
    return {str(key) for key in scripts}


def step_type(step: Any) -> str:
    if isinstance(step, str):
        return step
    if not isinstance(step, dict):
        return "unknown"
    if "command" in step or "commands" in step:
        return "command"
    if "trigger" in step:
        return "trigger"
    if "block" in step:
        return "block"
    if "input" in step:
        return "input"
    if "wait" in step:
        return "wait"
    if "group" in step:
        return "group"
    return "unknown"


def command_text(step: dict[str, Any]) -> str:
    value = step.get("command", step.get("commands", ""))
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value)


def step_label(step: Any, index: int) -> str:
    if isinstance(step, dict):
        for key in ("label", "key", "group", "trigger", "block", "input"):
            if key in step:
                return str(step[key])
    if isinstance(step, str):
        return step
    return f"step {index + 1}"


def has_stable_key(step: dict[str, Any]) -> bool:
    value = step.get("key")
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", value))


def is_bootstrap_upload(step: Any) -> bool:
    if not isinstance(step, dict) or step_type(step) != "command":
        return False
    return "buildkite-agent pipeline upload" in command_text(step)


def env_looks_literal_secret(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    lower = text.lower()
    if text.startswith(("$", "${", "$$")):
        return False
    if "buildkite-agent secret" in lower:
        return False
    if lower in {"redacted", "masked", "changeme", "todo", "<secret>", "***"}:
        return False
    return True


def scan_env(env: Any, context: str, result: CheckResult) -> None:
    if not isinstance(env, dict):
        return
    for key, value in sorted(env.items()):
        if SECRET_KEY_RE.search(str(key)) and env_looks_literal_secret(value):
            result.error(f"{context} has inline secret-like env value for {key!s}")


def scan_raw_secrets(text: str, result: CheckResult) -> None:
    if "BEGIN PRIVATE KEY" in text or "BEGIN RSA PRIVATE KEY" in text:
        result.error("pipeline appears to contain a private key block")
    for match in RAW_SECRET_RE.finditer(text):
        key, value = match.group(1), match.group(2)
        if env_looks_literal_secret(value):
            result.error(f"pipeline appears to contain inline secret-like value for {key}")


def flatten_steps(steps: list[Any]) -> list[tuple[str, Any]]:
    flattened: list[tuple[str, Any]] = []

    def visit(items: list[Any], prefix: str) -> None:
        for index, step in enumerate(items):
            path = f"{prefix}{index}"
            flattened.append((path, step))
            if isinstance(step, dict) and isinstance(step.get("steps"), list):
                visit(step["steps"], f"{path}.")

    visit(steps, "")
    return flattened


def has_branch_tag_gate(step: dict[str, Any]) -> bool:
    condition = step.get("if")
    if isinstance(condition, str) and BRANCH_OR_TAG_RE.search(condition):
        return True
    branches = step.get("branches")
    if isinstance(branches, str) and branches.strip():
        return True
    return False


def validate(path: Path) -> CheckResult:
    result = CheckResult()
    repo_root = infer_repo_root(path)
    make_targets = parse_makefile_targets(repo_root)
    package_scripts = parse_package_scripts(repo_root)
    text = path.read_text(encoding="utf-8", errors="replace")
    scan_raw_secrets(text, result)

    data, error = load_yaml(path)
    if error:
        result.error(f"YAML parse failed: {error}")
        return result

    if not isinstance(data, dict):
        result.error("pipeline YAML must be a mapping with a top-level steps key")
        return result

    scan_env(data.get("env"), "top-level env", result)
    steps = data.get("steps")
    if not isinstance(steps, list):
        result.error("pipeline must define top-level steps as a list")
        return result
    if not steps:
        result.error("pipeline steps must not be empty")
        return result

    flat = flatten_steps(steps)
    meaningful_types = {"command", "trigger", "block", "input"}
    meaningful = [(path_id, step) for path_id, step in flat if step_type(step) in meaningful_types]
    bootstrap_only = len(steps) == 1 and is_bootstrap_upload(steps[0])

    if len(meaningful) < 2 and not bootstrap_only:
        result.error("pipeline must expose multiple meaningful steps; single-node pipelines are rejected")
    if bootstrap_only:
        result.warn("bootstrap upload pipeline detected; validate the uploaded pipeline YAML separately")

    prior_block_seen = False
    for order, (path_id, step) in enumerate(flat):
        kind = step_type(step)
        label = step_label(step, order)
        if kind in {"command", "trigger", "block", "input", "group"}:
            if not isinstance(step, dict) or not has_stable_key(step):
                result.error(f"{path_id} ({label}) must define a stable lowercase key")
        if isinstance(step, dict):
            scan_env(step.get("env"), f"{path_id} ({label}) env", result)
        if kind == "block":
            prior_block_seen = True
        if kind in {"command", "trigger"} and isinstance(step, dict):
            haystack = " ".join(
                str(step.get(field, "")) for field in ("label", "key", "command", "commands", "trigger")
            )
            is_deploy = bool(DEPLOY_RE.search(haystack))
            gated = has_branch_tag_gate(step) or prior_block_seen or "buildkite-agent block" in command_text(step)
            if is_deploy and not gated:
                result.error(f"{path_id} ({label}) looks like a deploy/release step without branch/tag/block gating")
        if kind == "command" and isinstance(step, dict):
            command = command_text(step)
            for target in sorted(set(MAKE_COMMAND_RE.findall(command))):
                if make_targets and target not in make_targets:
                    result.error(f"{path_id} ({label}) calls missing Makefile target '{target}'")
            for script in sorted(set(NPM_RUN_RE.findall(command))):
                if package_scripts and script not in package_scripts:
                    result.error(f"{path_id} ({label}) calls missing package.json script '{script}'")
            shell_link_count = command.count("&&") + command.count(";")
            line_count = len([line for line in command.splitlines() if line.strip()])
            if shell_link_count >= 4 or line_count >= 8:
                result.warn(f"{path_id} ({label}) has a long command block; prefer visible separate steps")

    if "agents" not in data:
        result.note("no top-level agents/queue selector found; add step-level agents if runners matter")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline", help="Path to .buildkite/pipeline.yml or another Buildkite YAML file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    path = Path(args.pipeline)
    if not path.exists() or not path.is_file():
        print(f"error: pipeline path is not a file: {path}", file=sys.stderr)
        return 2

    result = validate(path)
    if args.json:
        print(json.dumps({"errors": result.errors, "warnings": result.warnings, "notes": result.notes}, indent=2, sort_keys=True))
    else:
        print(f"Checked: {path}")
        for title, values in [("Errors", result.errors), ("Warnings", result.warnings), ("Notes", result.notes)]:
            print(f"\n{title}:")
            if values:
                for value in values:
                    print(f"  - {value}")
            else:
                print("  - none")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
