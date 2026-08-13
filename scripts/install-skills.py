#!/usr/bin/env python3
"""Verify and install the local skill snapshot, excluding Codex-managed .system."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "skills.toml"
LOCAL_SKILLS = Path.home() / ".agents" / "skills"


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode() + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def catalog(manifest: dict) -> list[dict]:
    inventory = REPO_ROOT / manifest.get("defaults", {}).get("catalog", "inventory.toml")
    import tomllib
    return tomllib.loads(inventory.read_text(encoding="utf-8")).get("skill", [])


def npx_command(package: str, source: str, skill_names: list[str], *, full_depth: bool = False) -> list[str]:
    command = ["npx", "--yes", package, "add", source, "--global", "--agent", "*", "--skill", *skill_names, "--yes", "--copy"]
    if full_depth:
        command.append("--full-depth")
    return command


def grouped_upstream(manifest: dict):
    return []


def copy_from_npx_home(home: Path, install_root: Path, mappings):
    for source_name, destination_name in mappings:
        source = home / ".agents" / "skills" / source_name
        if not source.is_dir():
            raise SystemExit(f"npx did not produce expected skill: {source}")
        destination = install_root / destination_name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)


def expected_names() -> set[str]:
    return {path.name for path in LOCAL_SKILLS.iterdir() if path.is_dir() and path.name != ".system"}


def verify(manifest: dict, install_root: Path) -> None:
    expected = expected_names()
    actual = {path.name for path in install_root.iterdir() if path.is_dir()} if install_root.is_dir() else set()
    problems = []
    if actual != expected:
        problems.append(f"skill directories differ: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    if (install_root / ".system").exists():
        problems.append(".system must be excluded")
    for name in sorted(expected & actual):
        if tree_digest(install_root / name) != tree_digest(LOCAL_SKILLS / name):
            problems.append(f"{name}: content differs from local snapshot")
    if problems:
        print("skills verification failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        raise SystemExit(1)


def check(manifest: dict) -> None:
    entries = catalog(manifest)
    expected = expected_names()
    problems = []
    if {entry.get("directory") for entry in entries} != expected:
        problems.append("inventory does not match local non-system skill directories")
    if any(entry.get("directory") == ".system" for entry in entries):
        problems.append(".system must not be inventoried")
    if problems:
        print("skills checks failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        raise SystemExit(1)
    print(f"skills checks passed: {len(entries)} local skills; .system excluded")


def install(manifest: dict, install_root: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"would mirror {LOCAL_SKILLS} to {install_root}, excluding .system")
        return
    if install_root.exists():
        shutil.rmtree(install_root)
    install_root.mkdir(parents=True)
    for name in sorted(expected_names()):
        shutil.copytree(LOCAL_SKILLS / name, install_root / name)
    verify(manifest, install_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-root", type=Path, default=LOCAL_SKILLS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    import tomllib
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.check:
        check(manifest)
    elif args.verify:
        verify(manifest, args.install_root)
    else:
        install(manifest, args.install_root, args.dry_run)


if __name__ == "__main__":
    main()
