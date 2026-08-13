#!/usr/bin/env python3
"""Validate the portable bounded-work-session skill package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/context-and-scope.md",
    "references/session-lifecycle.md",
    "references/handoff-and-resume.md",
    "references/enforcement.md",
    "assets/session-state.template.json",
    "assets/session-handoff.template.md",
    "assets/continuation-prompt.template.md",
    "scripts/capture_git_state.py",
    "scripts/session_guard.py",
    "scripts/validate_skill.py",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must begin with YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text(encoding="utf-8")
        try:
            metadata = parse_frontmatter(text)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if metadata.get("name") != "bounded-work-session":
                errors.append("SKILL.md frontmatter name must be bounded-work-session")
            description = metadata.get("description", "")
            if not description:
                errors.append("SKILL.md frontmatter requires a description")
            if len(description) > 1024:
                errors.append("SKILL.md description exceeds 1024 characters")

        if "A milestone is a checkpoint, not an automatic reason to stop." not in text:
            warnings.append("SKILL.md is missing the productivity-preserving milestone statement")
        if "Do not automatically spawn a new thread" not in text:
            warnings.append("SKILL.md is missing the no-automatic-thread rule")

    state_path = root / "assets/session-state.template.json"
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"session-state.template.json is invalid: {exc}")
        else:
            if state.get("schema_version") != 2:
                errors.append("session-state.template.json schema_version must be 2")

    for path in root.rglob("*"):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "\t" in content:
            warnings.append(f"tab character found: {path.relative_to(root)}")
        for line_number, line in enumerate(content.splitlines(), start=1):
            if line.rstrip() != line:
                errors.append(f"trailing whitespace: {path.relative_to(root)}:{line_number}")

    return errors, sorted(set(warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors, warnings = validate(root)
    print(json.dumps({"root": str(root), "valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
