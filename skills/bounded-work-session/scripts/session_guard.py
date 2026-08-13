#!/usr/bin/env python3
"""Validate optional bounded-session state and inspect Git scope.

The guard reports facts and warnings. It does not decide that a session must end.
Use --strict only where a project or harness has explicitly made declared write
paths an enforcement boundary.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "task_id",
    "status",
    "objective",
    "current_checkpoint",
    "repository",
    "scope",
    "progress",
    "evidence",
    "boundary",
    "handoff_path",
}
VALID_STATUSES = {"active", "paused", "blocked", "ready_to_resume", "complete"}


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(state, dict):
        raise ValueError("state root must be a JSON object")
    return state


def validate(state: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - state.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    if state.get("schema_version") != 2:
        errors.append("schema_version must be 2")

    status = state.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    for field in ("task_id", "objective", "current_checkpoint"):
        value = state.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    repository = state.get("repository")
    if not isinstance(repository, dict):
        errors.append("repository must be an object")
    else:
        for field in ("root", "worktree", "branch", "head_observed"):
            value = repository.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"repository.{field} must be a non-empty string")

    scope = state.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        write_paths = scope.get("write_paths")
        if not isinstance(write_paths, list) or not all(isinstance(item, str) for item in write_paths):
            errors.append("scope.write_paths must be an array of strings")
        elif not write_paths:
            warnings.append("scope.write_paths is empty; scope checks will be informational only")

        non_goals = scope.get("non_goals")
        if not isinstance(non_goals, list) or not all(isinstance(item, str) for item in non_goals):
            errors.append("scope.non_goals must be an array of strings")

    evidence = state.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be an array")

    boundary = state.get("boundary")
    if not isinstance(boundary, dict) or not isinstance(boundary.get("new_session_required"), bool):
        errors.append("boundary.new_session_required must be boolean")

    if status in {"paused", "blocked", "ready_to_resume"} and not state.get("progress", {}).get("next_action"):
        warnings.append("paused or resumable state should record progress.next_action")

    if boundary and boundary.get("new_session_required") and not state.get("handoff_path"):
        warnings.append("new_session_required is true but handoff_path is empty")

    placeholder_paths = find_placeholders(state)
    if placeholder_paths:
        warnings.append("template placeholders remain at: " + ", ".join(placeholder_paths[:12]))

    return errors, warnings


def find_placeholders(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(find_placeholders(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_placeholders(item, f"{path}[{index}]"))
    elif isinstance(value, str) and "<" in value and ">" in value:
        found.append(path)
    return found


def run_git(worktree: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(worktree), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise ValueError(process.stderr.strip() or "git command failed")
    return process.stdout


def changed_paths(worktree: Path) -> list[str]:
    output = run_git(worktree, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = output.split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(entries):
        entry = entries[index]
        if not entry:
            index += 1
            continue
        if len(entry) < 4:
            index += 1
            continue
        status = entry[:2]
        path = entry[3:]
        paths.add(path)
        if "R" in status or "C" in status:
            index += 1
            if index < len(entries) and entries[index]:
                paths.add(entries[index])
        index += 1
    return sorted(paths)


def normalise_pattern(pattern: str) -> str:
    value = pattern.strip().replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    return value.rstrip("/") or "."


def path_matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    pattern = normalise_pattern(pattern)
    if pattern in {".", "**", "*"}:
        return True
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return path == pattern or path.startswith(pattern + "/")


def command_check(args: argparse.Namespace) -> int:
    state = load_state(args.state)
    errors, warnings = validate(state)
    output = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "new_session_required": state.get("boundary", {}).get("new_session_required"),
    }
    print(json.dumps(output, indent=2))
    return 1 if errors else 0


def command_scope(args: argparse.Namespace) -> int:
    state = load_state(args.state)
    errors, warnings = validate(state)
    if errors:
        print(json.dumps({"valid": False, "errors": errors, "warnings": warnings}, indent=2))
        return 1

    repository = state["repository"]
    worktree = Path(repository.get("worktree") or repository["root"]).expanduser()
    patterns = [normalise_pattern(item) for item in state["scope"].get("write_paths", [])]
    changed = changed_paths(worktree)
    outside = [path for path in changed if patterns and not any(path_matches(path, pattern) for pattern in patterns)]

    result = {
        "worktree": str(worktree),
        "changed_paths": changed,
        "declared_write_paths": patterns,
        "outside_declared_scope": outside,
        "mode": "strict" if args.strict else "advisory",
        "note": (
            "Outside paths are evidence to reconcile, not an automatic session boundary."
            if not args.strict
            else "Strict mode treats outside paths as an enforcement failure."
        ),
    }
    print(json.dumps(result, indent=2))
    return 1 if args.strict and outside else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="validate an optional session-state file")
    check_parser.add_argument("state", type=Path)
    check_parser.set_defaults(func=command_check)

    scope_parser = subparsers.add_parser("scope", help="compare Git changes with advisory write paths")
    scope_parser.add_argument("state", type=Path)
    scope_parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero for outside paths; use only when project policy makes scope mechanical",
    )
    scope_parser.set_defaults(func=command_scope)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
