#!/usr/bin/env python3
"""Read-only structural audit for an Agent Skills catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")
RISK_PATTERNS = {
    "remote shell pipeline": re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:ba)?sh\b"),
    "privileged command": re.compile(r"(?m)(?:^|\s)sudo\s+"),
    "destructive filesystem command": re.compile(r"\brm\s+-[^\n]*r[^\n]*f|\brm\s+-[^\n]*f[^\n]*r"),
    "destructive git command": re.compile(r"\bgit\s+(?:reset\s+--hard|clean\s+-[^\n]*f)"),
}
ARTIFACT_DIRS = {".git", "node_modules", "__pycache__"}
ARTIFACT_FILES = {".DS_Store"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class SkillRecord:
    name: str
    path: str
    lines: int
    provenance: str


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}

    values: dict[str, str] = {}
    lines = text[4:end].splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if value in {">", "|", ">-", "|-"}:
            folded: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
                folded.append(lines[index].strip())
                index += 1
            values[key] = " ".join(part for part in folded if part)
            continue
        values[key] = value.strip().strip("\"'")
        index += 1
    return values


def load_locked_sources(catalog: Path) -> dict[str, str]:
    lock_path = catalog.parent / ".skill-lock.json"
    if not lock_path.exists():
        return {}
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {
        name: entry.get("source", "installer-managed")
        for name, entry in data.get("skills", {}).items()
    }


def provenance_for(skill_path: Path, catalog: Path, locked: dict[str, str]) -> str:
    relative = skill_path.relative_to(catalog)
    direct_name = relative.parts[0]
    if direct_name == ".system":
        return "system-managed"
    if direct_name in locked:
        return f"installer:{locked[direct_name]}"
    if len(relative.parts) > 2:
        return "nested"
    return "local"


def local_link_findings(skill_file: Path, catalog: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for target in MARKDOWN_LINK_PATTERN.findall(prose):
        target = target.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue
        decoded = target.replace("%20", " ")
        if "/" not in decoded and not Path(decoded).suffix:
            continue
        resolved = (skill_file.parent / decoded).resolve()
        try:
            resolved.relative_to(catalog.resolve())
        except ValueError:
            continue
        if not resolved.exists():
            findings.append(
                Finding(
                    "warning",
                    "missing-local-link",
                    str(skill_file.relative_to(catalog)),
                    f"Missing target: {target}",
                )
            )
    return findings


def audit(catalog: Path, line_budget: int) -> tuple[list[SkillRecord], list[Finding]]:
    locked = load_locked_sources(catalog)
    findings: list[Finding] = []
    skills: list[SkillRecord] = []
    names: list[tuple[str, Path]] = []

    for skill_file in sorted(catalog.rglob("SKILL.md")):
        metadata = parse_frontmatter(skill_file)
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        lines = len(skill_file.read_text(encoding="utf-8", errors="replace").splitlines())
        relative = str(skill_file.relative_to(catalog))
        provenance = provenance_for(skill_file, catalog, locked)
        skills.append(SkillRecord(name or "<missing>", relative, lines, provenance))

        if not name:
            findings.append(Finding("error", "missing-name", relative, "Frontmatter has no name"))
        elif not NAME_PATTERN.fullmatch(name):
            findings.append(Finding("error", "invalid-name", relative, f"Invalid name: {name}"))
        else:
            names.append((name, skill_file))
            if skill_file.parent.name != name:
                findings.append(
                    Finding(
                        "error",
                        "name-directory-mismatch",
                        relative,
                        f"Directory '{skill_file.parent.name}' does not match '{name}'",
                    )
                )

        if not description or description.lower() in {"(no description)", "todo", "tbd"}:
            findings.append(Finding("error", "missing-description", relative, "Description is missing or placeholder"))
        if lines > line_budget:
            findings.append(
                Finding("warning", "line-budget", relative, f"{lines} lines exceeds budget of {line_budget}")
            )
        findings.extend(local_link_findings(skill_file, catalog))

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        for label, pattern in RISK_PATTERNS.items():
            if pattern.search(text):
                findings.append(Finding("warning", "risky-command", relative, label))
        if ("mcpServers:" in text or (skill_file.parent / "mcp.json").exists()) and "includeTools" not in text:
            mcp_file = skill_file.parent / "mcp.json"
            if not mcp_file.exists() or "includeTools" not in mcp_file.read_text(errors="replace"):
                findings.append(Finding("warning", "unfiltered-mcp", relative, "MCP server lacks includeTools"))

    counts = Counter(name for name, _ in names)
    for name, count in sorted(counts.items()):
        if count > 1:
            paths = ", ".join(str(path.relative_to(catalog)) for candidate, path in names if candidate == name)
            findings.append(Finding("error", "duplicate-name", paths, f"'{name}' appears {count} times"))

    for path in sorted(catalog.rglob("*")):
        relative = str(path.relative_to(catalog))
        if path.is_dir() and path.name in ARTIFACT_DIRS:
            findings.append(Finding("warning", "generated-artifact", relative, f"Unexpected directory: {path.name}"))
        elif path.is_file() and (
            path.name in ARTIFACT_FILES
            or path.suffix == ".pyc"
            or path.suffix.lower() in ARCHIVE_SUFFIXES
        ):
            findings.append(Finding("warning", "generated-artifact", relative, f"Unexpected file: {path.name}"))

    return skills, findings


def print_markdown(catalog: Path, skills: list[SkillRecord], findings: list[Finding]) -> None:
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    print(f"# Agent Skills catalog audit\n\nCatalog: `{catalog}`")
    print(f"\n- Skills: **{len(skills)}**\n- Errors: **{errors}**\n- Warnings: **{warnings}**")
    if not findings:
        print("\nNo findings.")
        return
    print("\n| Severity | Code | Path | Finding |\n|---|---|---|---|")
    for finding in findings:
        message = finding.message.replace("|", "\\|")
        print(f"| {finding.severity} | {finding.code} | `{finding.path}` | {message} |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path, help="Path containing skill directories")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--line-budget", type=int, default=500)
    args = parser.parse_args()

    catalog = args.catalog.expanduser().resolve()
    if not catalog.is_dir():
        parser.error(f"catalog is not a directory: {catalog}")

    skills, findings = audit(catalog, args.line_budget)
    if args.format == "json":
        json.dump(
            {
                "catalog": str(catalog),
                "summary": {
                    "skills": len(skills),
                    "errors": sum(finding.severity == "error" for finding in findings),
                    "warnings": sum(finding.severity == "warning" for finding in findings),
                },
                "skills": [asdict(skill) for skill in skills],
                "findings": [asdict(finding) for finding in findings],
            },
            sys.stdout,
            indent=2,
        )
        print()
    else:
        print_markdown(catalog, skills, findings)
    return 1 if any(finding.severity == "error" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
