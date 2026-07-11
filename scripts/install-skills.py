#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "skills.toml"
VALID_CATEGORIES = {
    "apple-platform",
    "ci-release",
    "quality-security",
    "agent-development",
    "web-api-design",
    "general-tooling",
}
VALID_PROVENANCE = {"unresolved", "verified-upstream", "verified-local", "customized-upstream"}
VALID_LICENSE_STATUS = {"unresolved", "upstream", "included"}
VALID_CUSTOMIZATION_STATUS = {"unknown", "none", "local", "customized"}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        if path.is_symlink():
            digest.update(b"L" + os.readlink(path).encode() + b"\0")
        elif path.is_file():
            digest.update(b"F" + path.read_bytes())
        elif path.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def catalog(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    path = REPO_ROOT / str(manifest["defaults"].get("catalog", "inventory.toml"))
    return load_toml(path).get("skill", [])


def npx_command(package: str, source: str, skill_names: list[str], *, full_depth: bool = False) -> list[str]:
    command = ["npx", "--yes", package, "add", source, "--global", "--agent", "*", "--skill", *skill_names, "--yes", "--copy"]
    if full_depth:
        command.append("--full-depth")
    return command


def grouped_upstream(manifest: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for spec in manifest.get("upstream", {}).values():
        groups[(spec["repo"], spec["ref"])].extend(Path(path).name for path in spec["paths"])
    return [(repo, ref, list(dict.fromkeys(names))) for (repo, ref), names in groups.items()]


def copy_from_npx_home(home: Path, install_root: Path, mappings: list[tuple[str, str]]) -> None:
    source_root = home / ".agents/skills"
    install_root.mkdir(parents=True, exist_ok=True)
    for installed_name, directory in mappings:
        source = source_root / installed_name
        if not (source / "SKILL.md").exists():
            raise SystemExit(f"npx did not produce expected skill: {source}")
        shutil.copytree(source, install_root / directory, dirs_exist_ok=True)


def run_install(command: list[str], install_root: Path, mappings: list[tuple[str, str]], dry_run: bool) -> None:
    if dry_run:
        print("[dry-run] " + " ".join(command))
        return
    with tempfile.TemporaryDirectory(prefix="skills-install-home-") as temporary:
        home = Path(temporary)
        env = os.environ.copy()
        env["HOME"] = str(home)
        subprocess.run(command, check=True, env=env)
        copy_from_npx_home(home, install_root, mappings)


def install(manifest: dict[str, Any], install_root: Path, dry_run: bool) -> None:
    entries = catalog(manifest)
    package = str(manifest["defaults"]["npx_package"])
    vendored = [entry for entry in entries if entry["source_type"] == "vendored"]
    vendored_names = [entry["install_name"] for entry in vendored]
    vendored_mappings = [(entry["install_name"], entry["directory"]) for entry in vendored]
    run_install(npx_command(package, str(REPO_ROOT), vendored_names, full_depth=True), install_root, vendored_mappings, dry_run)
    for repo, ref, names in grouped_upstream(manifest):
        run_install(npx_command(package, f"{repo}@{ref}", names), install_root, [(name, name) for name in names], dry_run)
    if not dry_run:
        verify(manifest, install_root)


def verify(manifest: dict[str, Any], install_root: Path) -> None:
    problems: list[str] = []
    for entry in catalog(manifest):
        path = install_root / entry["directory"]
        if not (path / "SKILL.md").exists():
            problems.append(f"{entry['directory']}: missing SKILL.md")
        elif tree_digest(path) != entry["sha256"]:
            problems.append(f"{entry['directory']}: content hash differs from inventory")
    if problems:
        print("skills verification failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        raise SystemExit(1)
    print(f"verified {len(catalog(manifest))} canonical skill directories")


def check(manifest: dict[str, Any]) -> None:
    entries = catalog(manifest)
    problems: list[str] = []
    directories = [entry.get("directory") for entry in entries]
    install_names = [entry.get("install_name") for entry in entries]
    vendored = [entry for entry in entries if entry.get("source_type") == "vendored"]
    upstream = [entry for entry in entries if entry.get("source_type") == "github"]
    expected_upstream = {
        Path(path).name: (name, spec["repo"], spec["ref"], path)
        for name, spec in manifest.get("upstream", {}).items()
        for path in spec.get("paths", [])
    }
    if len(entries) != 113 or len(vendored) != 86 or len(upstream) != 27:
        problems.append(f"expected 113 desired skills (86 vendored, 27 upstream), got {len(entries)} ({len(vendored)}, {len(upstream)})")
    if len(directories) != len(set(directories)):
        problems.append("catalog contains duplicate directories")
    if len(install_names) != len(set(install_names)):
        problems.append("catalog contains duplicate install names")
    vendored_on_disk = {
        path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if vendored_on_disk != {entry["directory"] for entry in vendored}:
        problems.append("skills/ directories differ from the vendored catalog")
    for entry in entries:
        required = (
            "directory",
            "install_name",
            "category",
            "sha256",
            "source_type",
            "provenance",
            "customization_status",
            "license_status",
        )
        if not all(entry.get(key) for key in required):
            problems.append(f"{entry.get('directory', '<unknown>')}: incomplete catalog entry")
            continue
        if entry["category"] not in VALID_CATEGORIES:
            problems.append(f"{entry['directory']}: unknown category {entry['category']!r}")
        if entry["provenance"] not in VALID_PROVENANCE:
            problems.append(f"{entry['directory']}: unknown provenance {entry['provenance']!r}")
        if entry["license_status"] not in VALID_LICENSE_STATUS:
            problems.append(f"{entry['directory']}: unknown license status {entry['license_status']!r}")
        if entry["customization_status"] not in VALID_CUSTOMIZATION_STATUS:
            problems.append(f"{entry['directory']}: unknown customization status {entry['customization_status']!r}")
        if entry["source_type"] == "vendored":
            path = REPO_ROOT / entry["path"]
            if not (path / "SKILL.md").exists():
                problems.append(f"{entry['directory']}: vendored SKILL.md missing")
            elif tree_digest(path) != entry["sha256"]:
                problems.append(f"{entry['directory']}: vendored content hash differs")
        elif entry["source_type"] == "github":
            expected = expected_upstream.get(entry["directory"])
            actual = (entry.get("upstream_entry"), entry.get("upstream_repo"), entry.get("upstream_ref"), entry.get("upstream_path"))
            if expected != actual:
                problems.append(f"{entry['directory']}: upstream catalog and manifest differ")
        else:
            problems.append(f"{entry['directory']}: unsupported source_type {entry['source_type']!r}")
    if any(entry.get("provenance") == "unresolved" for entry in entries) and not (REPO_ROOT / "PROVENANCE.md").is_file():
        problems.append("PROVENANCE.md is required while unresolved skills are vendored")
    if problems:
        print("skills checks failed:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("skills checks passed: 113 desired, 86 vendored, 27 pinned upstream")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Install or verify the complete global skill inventory.")
    result.add_argument("--install-root")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--check", action="store_true")
    result.add_argument("--verify", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    manifest = load_toml(MANIFEST)
    root = expand_path(args.install_root or "~/.agents/skills")
    if args.check:
        check(manifest)
    elif args.verify:
        verify(manifest, root)
    else:
        install(manifest, root, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
