#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "skills.toml"


def load_manifest() -> dict[str, Any]:
    with MANIFEST.open("rb") as handle:
        return tomllib.load(handle)


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def split_csv(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        result.extend(item.strip() for item in value.split(",") if item.strip())
    return result


def selected_skills(manifest: dict[str, Any], profiles: list[str], only: list[str]) -> list[str]:
    skills = manifest.get("skills", {})
    if only:
        names = only
    else:
        names = []
        profile_map = manifest.get("profiles", {})
        for profile in profiles:
            if profile not in profile_map:
                valid = ", ".join(sorted(profile_map))
                raise SystemExit(f"Unknown profile '{profile}'. Expected one of: {valid}")
            names.extend(profile_map[profile])

    ordered: list[str] = []
    for name in names:
        if name not in skills:
            raise SystemExit(f"Profile references unknown skill '{name}'")
        if name not in ordered:
            ordered.append(name)
    return ordered


def local_destination(name: str, spec: dict[str, Any], install_root: Path) -> Path:
    return install_root / str(spec.get("install_as", name))


def github_destinations(spec: dict[str, Any], install_root: Path) -> list[Path]:
    return [install_root / Path(path).name for path in spec.get("paths", [])]


def install_local(name: str, spec: dict[str, Any], install_root: Path, dry_run: bool) -> list[Path]:
    source = REPO_ROOT / str(spec["path"])
    destination = local_destination(name, spec, install_root)
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Local skill is missing SKILL.md: {source}")

    if dry_run:
        print(f"[dry-run] copy {source} -> {destination}")
        return [destination]

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print(f"installed local skill {name} -> {destination}")
    return [destination]


def install_github(spec: dict[str, Any], install_root: Path, installer: Path, dry_run: bool) -> list[Path]:
    if not spec.get("paths"):
        raise SystemExit(f"GitHub skill entry has no paths: {spec}")
    command = [sys.executable, str(installer), "--repo", str(spec["repo"]), "--path", *spec["paths"]]

    if dry_run:
        print("[dry-run] " + " ".join(command))
        return github_destinations(spec, install_root)

    if not installer.exists():
        raise SystemExit(f"Codex skill installer not found: {installer}")
    subprocess.run(command, check=True)
    return github_destinations(spec, install_root)


def verify_destinations(destinations: list[Path], dry_run: bool) -> None:
    if dry_run:
        return
    missing = [path for path in destinations if not (path / "SKILL.md").exists()]
    if missing:
        for path in missing:
            print(f"missing SKILL.md: {path}", file=sys.stderr)
        raise SystemExit(1)


def check_manifest(manifest: dict[str, Any]) -> None:
    problems: list[str] = []
    skills = manifest.get("skills", {})
    for name, spec in skills.items():
        source = spec.get("source")
        if source not in {"local", "github"}:
            problems.append(f"{name}: unsupported source {source!r}")
        if source == "local" and not (REPO_ROOT / str(spec.get("path", "")) / "SKILL.md").exists():
            problems.append(f"{name}: local path missing SKILL.md")
        if source == "github" and (not spec.get("repo") or not spec.get("paths")):
            problems.append(f"{name}: github entries require repo and paths")

    for profile, entries in manifest.get("profiles", {}).items():
        for entry in entries:
            if entry not in skills:
                problems.append(f"profile {profile}: unknown skill {entry}")

    if problems:
        print("skills manifest check failed:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("skills manifest checks passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install curated skills into ~/.agents/skills.")
    parser.add_argument("--profile", action="append", default=[], help="Profile name or comma-separated profile names.")
    parser.add_argument("--only", action="append", default=[], help="Install only the named skill entry.")
    parser.add_argument("--install-root", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = load_manifest()

    if args.check:
        check_manifest(manifest)
        return

    profiles = split_csv(args.profile) or ["core"]
    only = split_csv(args.only)
    install_root = expand_path(args.install_root or manifest["defaults"]["install_root"])
    installer = expand_path(manifest["defaults"]["system_installer"])

    destinations: list[Path] = []
    for name in selected_skills(manifest, profiles, only):
        spec = manifest["skills"][name]
        if spec["source"] == "local":
            destinations.extend(install_local(name, spec, install_root, args.dry_run))
        elif spec["source"] == "github":
            destinations.extend(install_github(spec, install_root, installer, args.dry_run))
        else:
            raise SystemExit(f"Unsupported source for {name}: {spec['source']}")

    verify_destinations(destinations, args.dry_run)
    if not args.dry_run:
        print(f"verified {len(destinations)} installed skill directories")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error

