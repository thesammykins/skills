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
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "skills.toml"


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def split_csv(values: list[str]) -> list[str]:
    return [item.strip() for value in values for item in value.split(",") if item.strip()]


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


def selected_skills(manifest: dict[str, Any], profiles: list[str], only: list[str]) -> list[str]:
    skills = manifest.get("skills", {})
    names = only[:]
    if not names:
        for profile in profiles:
            if profile not in manifest.get("profiles", {}):
                valid = ", ".join(sorted(manifest.get("profiles", {})))
                raise SystemExit(f"Unknown profile '{profile}'. Expected one of: {valid}")
            names.extend(manifest["profiles"][profile])
    ordered = list(dict.fromkeys(names))
    missing = [name for name in ordered if name not in skills]
    if missing:
        raise SystemExit(f"Unknown skills: {', '.join(missing)}")
    return ordered


def destinations(name: str, spec: dict[str, Any], root: Path) -> list[Path]:
    if spec["source"] == "local":
        return [root / str(spec.get("install_as", name))]
    return [root / Path(path).name for path in spec["paths"]]


def install_local(name: str, spec: dict[str, Any], root: Path, dry_run: bool) -> list[Path]:
    source = REPO_ROOT / str(spec["path"])
    destination = destinations(name, spec, root)[0]
    if dry_run:
        print(f"[dry-run] copy {source} -> {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, dirs_exist_ok=True)
        print(f"installed local skill {name} -> {destination}")
    return [destination]


def npx_command(package: str, spec: dict[str, Any]) -> list[str]:
    source = f"{spec['repo']}@{spec['ref']}"
    skill_names = [Path(path).name for path in spec["paths"]]
    return ["npx", "--yes", package, "add", source, "--global", "--agent", "*", "--skill", *skill_names, "--yes"]


def install_github(name: str, spec: dict[str, Any], root: Path, package: str, dry_run: bool) -> list[Path]:
    command = npx_command(package, spec)
    expected = destinations(name, spec, root)
    if dry_run:
        print("[dry-run] " + " ".join(command))
        return expected

    default_root = expand_path("~/.agents/skills")
    if root == default_root:
        subprocess.run(command, check=True)
        return expected

    with tempfile.TemporaryDirectory(prefix="skills-install-home-") as temp:
        env = os.environ.copy()
        env["HOME"] = temp
        subprocess.run(command, check=True, env=env)
        staged = Path(temp) / ".agents/skills"
        root.mkdir(parents=True, exist_ok=True)
        for destination in expected:
            source = staged / destination.name
            if not source.exists():
                raise SystemExit(f"npx did not produce expected skill: {source}")
            shutil.copytree(source, destination, dirs_exist_ok=True)
    return expected


def verify_one(name: str, spec: dict[str, Any], paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        if not (path / "SKILL.md").exists():
            problems.append(f"{name}: missing {path}/SKILL.md")
    expected = spec.get("expected_sha256")
    if expected and len(paths) == 1 and paths[0].exists():
        actual = tree_digest(paths[0])
        if actual != expected:
            problems.append(f"{name}: hash mismatch, expected {expected}, got {actual}")
    return problems


def check_manifest(manifest: dict[str, Any]) -> None:
    problems: list[str] = []
    seen_destinations: dict[str, str] = {}
    skills = manifest.get("skills", {})
    for name, spec in skills.items():
        source = spec.get("source")
        if source not in {"local", "github"}:
            problems.append(f"{name}: unsupported source {source!r}")
            continue
        if source == "local":
            path = REPO_ROOT / str(spec.get("path", ""))
            if not (path / "SKILL.md").exists():
                problems.append(f"{name}: local path missing SKILL.md")
            if spec.get("expected_sha256") and path.exists() and tree_digest(path) != spec["expected_sha256"]:
                problems.append(f"{name}: vendored content hash differs from manifest")
            names = [str(spec.get("install_as", name))]
        else:
            if not spec.get("repo") or not spec.get("ref") or not spec.get("paths"):
                problems.append(f"{name}: github entries require repo, ref, and paths")
            names = [Path(path).name for path in spec.get("paths", [])]
        for destination in names:
            owner = seen_destinations.setdefault(destination, name)
            if owner != name:
                problems.append(f"duplicate install name {destination}: {owner}, {name}")

    for profile, entries in manifest.get("profiles", {}).items():
        for entry in entries:
            if entry not in skills:
                problems.append(f"profile {profile}: unknown skill {entry}")

    catalog_path = REPO_ROOT / str(manifest["defaults"].get("catalog", "inventory.toml"))
    if not catalog_path.exists():
        problems.append(f"missing catalog: {catalog_path}")
    else:
        catalog = load_toml(catalog_path)
        directories = [entry.get("directory") for entry in catalog.get("skill", [])]
        if len(directories) != len(set(directories)):
            problems.append("catalog contains duplicate directories")

    if problems:
        print("skills manifest check failed:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("skills manifest checks passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install curated skills into ~/.agents/skills.")
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--install-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = load_toml(MANIFEST)
    if args.check:
        check_manifest(manifest)
        return

    profiles = split_csv(args.profile) or ["core"]
    names = selected_skills(manifest, profiles, split_csv(args.only))
    root = expand_path(args.install_root or manifest["defaults"]["install_root"])
    package = str(manifest["defaults"]["npx_package"])
    problems: list[str] = []
    if not args.verify:
        for name in names:
            spec = manifest["skills"][name]
            if spec["source"] == "local":
                install_local(name, spec, root, args.dry_run)

        groups: dict[tuple[str, str], list[str]] = {}
        for name in names:
            spec = manifest["skills"][name]
            if spec["source"] == "github":
                groups.setdefault((spec["repo"], spec["ref"]), []).extend(spec["paths"])
        for (repo, ref), paths in groups.items():
            install_github(repo, {"source": "github", "repo": repo, "ref": ref, "paths": list(dict.fromkeys(paths))}, root, package, args.dry_run)

    if not args.dry_run:
        for name in names:
            spec = manifest["skills"][name]
            problems.extend(verify_one(name, spec, destinations(name, spec, root)))
    if problems:
        print("skills verification failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        raise SystemExit(1)
    if not args.dry_run:
        print(f"verified {sum(len(destinations(name, manifest['skills'][name], root)) for name in names)} installed skill directories")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
