#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = SKILL_ROOT / "references" / "known-sources.json"
DEFAULT_PROFILES = SKILL_ROOT / "references" / "project-profiles.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_lock(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    skills = load_json(path).get("skills", {})
    return skills if isinstance(skills, dict) else {}


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if not file.is_file() or file.name == ".DS_Store" or ".git" in file.parts:
            continue
        digest.update(str(file.relative_to(path)).encode())
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def installed_skills(skills_root: Path) -> dict[str, tuple[Path, bool]]:
    result: dict[str, tuple[Path, bool]] = {}
    if not skills_root.is_dir():
        return result

    def add(name: str, path: Path, is_system: bool) -> None:
        if name in result:
            other_path, _ = result[name]
            raise ValueError(f"Duplicate skill name '{name}': {other_path} and {path}")
        result[name] = (path, is_system)

    for path in sorted(skills_root.iterdir()):
        if path.name == ".system" and path.is_dir():
            for system_path in sorted(path.iterdir()):
                if (system_path / "SKILL.md").is_file():
                    add(system_path.name, system_path, True)
        elif path.is_dir() and (path / "SKILL.md").is_file():
            add(path.name, path, False)
    return result


def source_root(entry: dict[str, Any]) -> str:
    return str(entry.get("sourceUrl") or entry.get("source") or "unknown")


def canonical_root(value: str) -> str:
    root = value.strip()
    if root.startswith("git@github.com:"):
        root = "github.com/" + root.removeprefix("git@github.com:")
    elif "://" in root:
        parsed = urlparse(root)
        root = f"{parsed.netloc}{parsed.path}"
    return root.lower().removesuffix("/").removesuffix(".git")


def project_sources(profiles: dict[str, Any]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    roots: dict[str, list[str]] = {}
    entry_skills: dict[str, list[str]] = {}
    for profile in profiles.get("profiles", []):
        profile_id = str(profile.get("id", "unknown"))
        for source in profile.get("sources", []):
            root = canonical_root(str(source.get("root", "")))
            if root:
                roots.setdefault(root, []).append(profile_id)
            skill = source.get("skill")
            if skill:
                entry_skills.setdefault(str(skill), []).append(profile_id)
    return roots, entry_skills


def local_source_matches(catalog: dict[str, Any], installed: dict[str, tuple[Path, bool]]) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    installed_digests: dict[str, str] = {}

    for source in catalog.get("localSources", []):
        checkout = Path(str(source["path"])).expanduser()
        skills_path = checkout / str(source.get("skillsPath", "."))
        if not skills_path.is_dir():
            continue

        for name, (installed_path, is_system) in installed.items():
            if is_system or name in matches:
                continue
            candidate = skills_path / name
            if not (candidate / "SKILL.md").is_file():
                continue
            installed_digest = installed_digests.setdefault(name, tree_digest(installed_path))
            if tree_digest(candidate) == installed_digest:
                matches[name] = source
    return matches


def discover_historical_locks(home: Path, current_lock: Path) -> list[Path]:
    locks = set(home.glob(".agents*.bak*/.skill-lock.json"))
    locks.update(home.glob(".agents*/.skill-lock.json"))
    locks.discard(current_lock)
    return sorted(path for path in locks if path.is_file())


def build_inventory(
    skills_root: Path,
    catalog: dict[str, Any],
    profiles: dict[str, Any],
    current_lock_path: Path,
    historical_lock_paths: list[Path],
) -> list[dict[str, Any]]:
    installed = installed_skills(skills_root)
    current = load_lock(current_lock_path)
    historical: dict[str, tuple[dict[str, Any], Path]] = {}
    for lock_path in historical_lock_paths:
        for name, entry in load_lock(lock_path).items():
            historical.setdefault(name, (entry, lock_path))

    local_matches = local_source_matches(catalog, installed)
    profiles_by_root, profiles_by_entry_skill = project_sources(profiles)
    global_candidates = set(catalog.get("globalCandidates", []))

    records: list[dict[str, Any]] = []
    for name, (path, is_system) in sorted(installed.items()):
        related_profiles = set(profiles_by_entry_skill.get(name, []))
        if is_system:
            provenance = "system-provided"
            root = "client-managed:.system"
            evidence = ".system placement"
            scope = "system"
            confidence = "high"
            needs_review = False
        elif name in current:
            provenance = "current-lock"
            root = source_root(current[name])
            related_profiles.update(profiles_by_root.get(canonical_root(root), []))
            evidence = str(current_lock_path)
            scope = "project" if related_profiles else "global" if name in global_candidates else "review"
            confidence = "high"
            needs_review = False
        elif name in local_matches:
            source = local_matches[name]
            provenance = "local-exact-match"
            root = str(source["root"])
            evidence = str(Path(str(source["path"])).expanduser())
            scope = str(source.get("defaultScope", "review"))
            confidence = "high"
            needs_review = False
        elif name in historical:
            entry, lock_path = historical[name]
            provenance = "historical-lock-candidate"
            root = source_root(entry)
            related_profiles.update(profiles_by_root.get(canonical_root(root), []))
            evidence = str(lock_path)
            scope = "project" if related_profiles else "global" if name in global_candidates else "review"
            confidence = "candidate"
            needs_review = True
        else:
            provenance = "unresolved"
            root = "unknown"
            evidence = "none"
            scope = "project" if related_profiles else "global" if name in global_candidates else "review"
            confidence = "unknown"
            needs_review = True

        records.append(
            {
                "name": name,
                "path": str(path),
                "provenance": provenance,
                "root": root,
                "evidence": evidence,
                "sourceConfidence": confidence,
                "needsReview": needs_review,
                "recommendedScope": scope,
                "profiles": sorted(related_profiles),
            }
        )
    return records


def markdown_report(records: list[dict[str, Any]], skills_root: Path, details: bool) -> str:
    provenance_counts = Counter(record["provenance"] for record in records)
    scope_counts = Counter(record["recommendedScope"] for record in records)
    review_queue = [record for record in records if record["needsReview"]]

    lines = [
        "# Global skill provenance audit",
        "",
        f"Skills root: `{skills_root}`",
        "",
        f"Total discovered skills: **{len(records)}**",
        "",
        "## Provenance",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in sorted(provenance_counts.items()))
    lines.extend(["", "## Recommended scope", "", "| Scope | Count |", "|---|---:|"])
    lines.extend(f"| {name} | {count} |" for name, count in sorted(scope_counts.items()))
    lines.extend(["", f"## Provenance review queue ({len(review_queue)})", ""])
    if review_queue:
        lines.extend(
            f"- `{record['name']}` — {record['provenance']}; candidate root: {record['root']}; "
            f"scope: {record['recommendedScope']}"
            for record in review_queue
        )
    else:
        lines.append("None.")

    if details:
        lines.extend(
            [
                "",
                "## Complete inventory",
                "",
                "| Skill | Provenance | Confidence | Root | Scope | Profiles |",
                "|---|---|---|---|---|---|",
            ]
        )
        for record in records:
            profiles = ", ".join(record["profiles"])
            lines.append(
                f"| {record['name']} | {record['provenance']} | {record['sourceConfidence']} | "
                f"{record['root']} | {record['recommendedScope']} | {profiles} |"
            )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit global Agent Skills without modifying them.")
    parser.add_argument("--skills-root", type=Path, default=Path("~/.agents/skills").expanduser())
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--current-lock", type=Path, default=None)
    parser.add_argument("--historical-lock", action="append", type=Path, default=[])
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--details", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    skills_root = args.skills_root.expanduser().resolve()
    current_lock = (args.current_lock or skills_root.parent / ".skill-lock.json").expanduser().resolve()
    historical_locks = [path.expanduser().resolve() for path in args.historical_lock]
    if not historical_locks:
        historical_locks = discover_historical_locks(Path.home(), current_lock)

    records = build_inventory(
        skills_root,
        load_json(args.catalog.expanduser().resolve()),
        load_json(args.profiles.expanduser().resolve()),
        current_lock,
        historical_locks,
    )
    if args.format == "json":
        print(json.dumps({"skillsRoot": str(skills_root), "skills": records}, indent=2))
    else:
        print(markdown_report(records, skills_root, args.details), end="")


if __name__ == "__main__":
    main()
