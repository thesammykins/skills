#!/usr/bin/env python3
"""Validate, package, install, and verify the checked-in skills catalog."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
MANIFEST_PATH = REPO_ROOT / "skills.toml"
EXTERNAL_MANIFEST_PATH = REPO_ROOT / "external-skills.toml"
DEFAULT_INSTALL_ROOT = Path.home() / ".agents" / "skills"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class SkillsError(Exception):
    """A user-facing catalog or installation error."""


def load_manifest() -> dict:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_external_manifest() -> dict:
    return tomllib.loads(EXTERNAL_MANIFEST_PATH.read_text(encoding="utf-8"))


def load_catalog(manifest: dict) -> list[dict]:
    catalog_path = REPO_ROOT / manifest.get("defaults", {}).get("catalog", "inventory.toml")
    return tomllib.loads(catalog_path.read_text(encoding="utf-8")).get("skill", [])


def catalog_names(manifest: dict) -> list[str]:
    return [entry["directory"] for entry in load_catalog(manifest)]


def source_skill_names() -> list[str]:
    return sorted(path.name for path in SKILLS_ROOT.iterdir() if path.is_dir())


def frontmatter_value(skill_file: Path, key: str) -> str | None:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text[4:end], re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def skill_files(skill_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_root.rglob("*")):
        if path.is_symlink():
            raise SkillsError(f"{path.relative_to(REPO_ROOT)}: symbolic links are not packageable")
        if path.is_file():
            files.append(path)
    return files


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in skill_files(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def check(manifest: dict, *, quiet: bool = False) -> None:
    entries = load_catalog(manifest)
    external_manifest = load_external_manifest()
    source_names = source_skill_names()
    inventory_names = [entry.get("directory") for entry in entries]
    problems: list[str] = []

    if len(inventory_names) != len(set(inventory_names)):
        problems.append("inventory contains duplicate skill directories")
    if sorted(inventory_names) != source_names:
        problems.append(
            "inventory does not match skills/: "
            f"missing={sorted(set(source_names) - set(inventory_names))}, "
            f"extra={sorted(set(inventory_names) - set(source_names))}"
        )

    for entry in entries:
        name = entry.get("directory")
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or len(name) > 64:
            problems.append(f"{name!r}: invalid skill directory name")
            continue
        if entry.get("install_name") != name:
            problems.append(f"{name}: install_name must match directory")
        if entry.get("path") != f"skills/{name}":
            problems.append(f"{name}: inventory path must be skills/{name}")

        skill_root = SKILLS_ROOT / name
        skill_file = skill_root / "SKILL.md"
        if not skill_file.is_file():
            problems.append(f"{name}: missing SKILL.md")
            continue
        if frontmatter_value(skill_file, "name") != name:
            problems.append(f"{name}: frontmatter name must match its directory")
        if not frontmatter_value(skill_file, "description"):
            problems.append(f"{name}: frontmatter description is missing")
        try:
            skill_files(skill_root)
        except (OSError, SkillsError) as error:
            problems.append(str(error))

    ignored = {entry.get("directory") for entry in manifest.get("ignored", [])}
    if ".system" in source_names or ".system" not in ignored:
        problems.append(".system must be excluded from skills/ and recorded as ignored")

    external_names: list[str] = []
    tool = external_manifest.get("tool", {})
    if not tool.get("node_package") or not tool.get("skills_package"):
        problems.append("external skill tool packages must be pinned")
    for source in external_manifest.get("source", []):
        repository = source.get("repository")
        revision = source.get("reviewed_revision")
        names = source.get("skills")
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository):
            problems.append(f"{repository!r}: invalid external repository")
        if not isinstance(revision, str) or not REVISION_PATTERN.fullmatch(revision):
            problems.append(f"{repository!r}: reviewed_revision must be a full commit SHA")
        if not isinstance(names, list) or not names:
            problems.append(f"{repository!r}: external skills must be a non-empty list")
            continue
        for name in names:
            if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
                problems.append(f"{repository!r}: invalid external skill name {name!r}")
            else:
                external_names.append(name)
    if len(external_names) != len(set(external_names)):
        problems.append("external skill manifest contains duplicate skill names")
    overlap = sorted(set(external_names) & set(source_names))
    if overlap:
        problems.append("skills cannot be both checked in and external: " + ", ".join(overlap))

    if problems:
        raise SkillsError("skills checks failed:\n  - " + "\n  - ".join(problems))
    if not quiet:
        unresolved = sum(entry.get("license_status") == "unresolved" for entry in entries)
        suffix = f"; {unresolved} provenance/license records still need resolution" if unresolved else ""
        print(
            f"skills checks passed: {len(entries)} checked-in and "
            f"{len(external_names)} external skills{suffix}"
        )


def external_commands(*, project: bool, agents: list[str] | None = None) -> list[list[str]]:
    external_manifest = load_external_manifest()
    tool = external_manifest["tool"]
    selected_agents = agents or ["*"]
    commands: list[list[str]] = []
    for source in external_manifest["source"]:
        command = [
            "npx",
            "--yes",
            "-p",
            tool["node_package"],
            "-p",
            tool["skills_package"],
            "skills",
            "add",
            source["repository"],
            "--skill",
            *source["skills"],
            "--agent",
            *selected_agents,
            "--yes",
        ]
        if not project:
            command.append("--global")
        commands.append(command)
    return commands


def install_external(*, apply: bool, project: bool, agents: list[str] | None = None) -> None:
    commands = external_commands(project=project, agents=agents)
    if not apply:
        print("External skill install preview (no commands were run):")
        for command in commands:
            print(shlex.join(command))
        print("Run again with --apply to download and install these reviewed sources.")
        return

    environment = os.environ.copy()
    environment["DISABLE_TELEMETRY"] = "1"
    for command in commands:
        subprocess.run(command, check=True, env=environment)


def select_skills(manifest: dict, requested: list[str] | None) -> list[str]:
    available = catalog_names(manifest)
    if not requested:
        return available
    unknown = sorted(set(requested) - set(available))
    if unknown:
        raise SkillsError(f"unknown skills: {', '.join(unknown)}")
    return list(dict.fromkeys(requested))


def zip_info(archive_name: str, source: Path) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
    info.create_system = 3
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def write_zip(destination: Path, entries: list[tuple[Path, str]]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, archive_name in sorted(entries, key=lambda item: item[1]):
            archive.writestr(zip_info(archive_name, source), source.read_bytes())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(manifest: dict, output: Path) -> None:
    check(manifest, quiet=True)
    output.mkdir(parents=True, exist_ok=True)
    generated_files = [
        *output.glob("*.skill"),
        output / "skills-bundle.zip",
        output / "SHA256SUMS",
        output / "SKILL-SHA256SUMS",
    ]
    for stale in generated_files:
        if stale.exists():
            stale.unlink()

    skill_artifacts: list[Path] = []
    for name in catalog_names(manifest):
        root = SKILLS_ROOT / name
        artifact = output / f"{name}.skill"
        write_zip(artifact, [(path, path.relative_to(root).as_posix()) for path in skill_files(root)])
        skill_artifacts.append(artifact)

    skill_checksums = output / "SKILL-SHA256SUMS"
    skill_checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(skill_artifacts)),
        encoding="utf-8",
    )

    bundle_entries: list[tuple[Path, str]] = [
        (REPO_ROOT / "README.md", "README.md"),
        (EXTERNAL_MANIFEST_PATH, "external-skills.toml"),
        (REPO_ROOT / "inventory.toml", "inventory.toml"),
        (REPO_ROOT / "skills.toml", "skills.toml"),
        (Path(__file__), "scripts/install-skills.py"),
        (skill_checksums, "SKILL-SHA256SUMS"),
    ]
    for name in catalog_names(manifest):
        root = SKILLS_ROOT / name
        bundle_entries.extend(
            (path, f"skills/{name}/{path.relative_to(root).as_posix()}") for path in skill_files(root)
        )
    bundle = output / "skills-bundle.zip"
    write_zip(bundle, bundle_entries)

    all_artifacts = sorted([*skill_artifacts, bundle], key=lambda path: path.name)
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in all_artifacts),
        encoding="utf-8",
    )
    print(f"packaged {len(skill_artifacts)} skills and one bundle in {output}")


def resolve_target(args: argparse.Namespace) -> Path:
    if args.project:
        return Path.cwd() / ".agents" / "skills"
    return args.target.expanduser()


def differing_destinations(names: list[str], target: Path) -> list[str]:
    return [
        name
        for name in names
        if (target / name).exists() and tree_digest(SKILLS_ROOT / name) != tree_digest(target / name)
    ]


def install(manifest: dict, names: list[str], target: Path, *, force: bool, dry_run: bool) -> None:
    check(manifest, quiet=True)
    conflicts = differing_destinations(names, target) if target.exists() else []
    if conflicts and not force:
        raise SkillsError(
            "refusing to overwrite changed installed skills without --force: " + ", ".join(conflicts)
        )
    if dry_run:
        print(f"would install {len(names)} skills into {target}")
        return

    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = SKILLS_ROOT / name
        destination = target / name
        if destination.is_dir() and tree_digest(source) == tree_digest(destination):
            continue
        with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=target) as temporary:
            staged = Path(temporary) / name
            shutil.copytree(source, staged)
            if destination.exists():
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            staged.rename(destination)
    print(f"installed {len(names)} skills into {target}")


def verify(names: list[str], target: Path) -> None:
    problems: list[str] = []
    for name in names:
        destination = target / name
        if not destination.is_dir():
            problems.append(f"{name}: not installed")
        elif tree_digest(SKILLS_ROOT / name) != tree_digest(destination):
            problems.append(f"{name}: installed content differs")
    if problems:
        raise SkillsError("skills verification failed:\n  - " + "\n  - ".join(problems))
    print(f"verified {len(names)} skills in {target}")


def add_target_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--target", type=Path, default=DEFAULT_INSTALL_ROOT)
    target.add_argument("--project", action="store_true", help="install into ./.agents/skills")
    parser.add_argument("--skill", action="append", dest="skills", metavar="NAME")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate the catalog and skill metadata")

    package_parser = commands.add_parser("package", help="build deterministic release archives")
    package_parser.add_argument("--output", type=Path, default=REPO_ROOT / "dist")

    install_parser = commands.add_parser("install", help="install all or selected checked-in skills")
    add_target_arguments(install_parser)
    install_parser.add_argument("--force", action="store_true", help="replace changed named skills")
    install_parser.add_argument("--dry-run", action="store_true")

    verify_parser = commands.add_parser("verify", help="verify all or selected installed skills")
    add_target_arguments(verify_parser)

    external_parser = commands.add_parser(
        "external", help="preview or install skills managed by the npx skills CLI"
    )
    external_parser.add_argument(
        "--apply", action="store_true", help="run the displayed network install commands"
    )
    external_parser.add_argument(
        "--project", action="store_true", help="install for the current project instead of globally"
    )
    external_parser.add_argument(
        "--agent", action="append", dest="agents", metavar="NAME", help="target agent (default: all)"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest()
        if args.command == "check":
            check(manifest)
        elif args.command == "package":
            package(manifest, args.output)
        elif args.command == "external":
            check(manifest, quiet=True)
            install_external(apply=args.apply, project=args.project, agents=args.agents)
        else:
            names = select_skills(manifest, args.skills)
            target = resolve_target(args)
            if args.command == "install":
                install(manifest, names, target, force=args.force, dry_run=args.dry_run)
            else:
                verify(names, target)
    except (OSError, SkillsError, subprocess.CalledProcessError, tomllib.TOMLDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
