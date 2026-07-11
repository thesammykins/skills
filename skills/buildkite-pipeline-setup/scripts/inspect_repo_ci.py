#!/usr/bin/env python3
"""Inspect a repository for CI/CD signals relevant to Buildkite setup."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "DerivedData",
}

MANIFEST_NAMES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "bun.lockb",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "Gemfile.lock",
    "composer.json",
    "Package.swift",
    "Makefile",
}

EXISTING_CI_EXACT = {
    ".buildkite/pipeline.yml",
    ".buildkite/pipeline.yaml",
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    ".circleci/config.yml",
    ".circleci/config.yaml",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    "Jenkinsfile",
    "buildkite.yml",
    "buildkite.yaml",
}

DEPLOY_HINT_RE = re.compile(
    r"(^|/|[-_.])(deploy|deployment|release|publish|helm|charts?|k8s|kubernetes|terraform|pulumi|serverless)(/|[-_.]|$)",
    re.IGNORECASE,
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_repo(root: Path) -> list[Path]:
    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".xcodeproj")
        )
        for filename in sorted(filenames):
            paths.append(Path(dirpath) / filename)
    return paths


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def parse_makefile_targets(path: Path) -> list[str]:
    targets: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?:\s|$)", line)
            if match and not match.group(1).startswith("."):
                targets.add(match.group(1))
    except OSError:
        return []
    return sorted(targets)


def file_contains(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def detect_package_manager(root: Path) -> str | None:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists():
        return "bun"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "package.json").exists():
        return "npm"
    return None


def node_command(manager: str, script: str) -> str:
    if manager == "pnpm":
        return f"pnpm run {script}"
    if manager == "yarn":
        return f"yarn {script}"
    if manager == "bun":
        return f"bun run {script}"
    return f"npm run {script}"


def add_candidate(
    candidates: list[dict[str, str]], phase: str, key: str, label: str, command: str, reason: str
) -> None:
    item = {
        "phase": phase,
        "key": key,
        "label": label,
        "command": command,
        "reason": reason,
    }
    if item not in candidates:
        candidates.append(item)


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = walk_repo(root)
    rel_files = [rel(path, root) for path in files]
    rel_set = set(rel_files)

    manifests = sorted(
        path for path in rel_files if Path(path).name in MANIFEST_NAMES or path.endswith(".xcodeproj/project.pbxproj")
    )
    existing_ci = sorted(
        path
        for path in rel_files
        if path in EXISTING_CI_EXACT
        or path.startswith(".github/workflows/")
        and path.endswith((".yml", ".yaml"))
    )
    docker_files = sorted(
        path
        for path in rel_files
        if Path(path).name == "Dockerfile"
        or Path(path).name.startswith("Dockerfile.")
        or Path(path).name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}
    )
    deploy_hints = sorted(
        path
        for path in rel_files
        if DEPLOY_HINT_RE.search(path)
        or Path(path).name in {"fly.toml", "vercel.json", "netlify.toml", "Procfile", "app.yaml"}
    )

    package_manager = detect_package_manager(root)
    package_scripts: dict[str, str] = {}
    package_json = root / "package.json"
    package_data = read_json(package_json) if package_json.exists() else None
    if package_data:
        scripts = package_data.get("scripts", {})
        if isinstance(scripts, dict):
            package_scripts = {str(key): str(value) for key, value in sorted(scripts.items())}

    make_targets = parse_makefile_targets(root / "Makefile") if (root / "Makefile").exists() else []

    candidates: list[dict[str, str]] = []
    if ".buildkite/pipeline.yml" in rel_set or ".buildkite/pipeline.yaml" in rel_set:
        add_candidate(
            candidates,
            "review",
            "review-existing-buildkite",
            ":buildkite: Review existing Buildkite pipeline",
            "python3 <skill>/scripts/check_buildkite_pipeline.py .buildkite/pipeline.yml",
            "Existing Buildkite pipeline detected",
        )

    if package_manager:
        install = {
            "pnpm": "corepack enable && pnpm install --frozen-lockfile",
            "yarn": "corepack enable && yarn install --frozen-lockfile",
            "bun": "bun install --frozen-lockfile",
            "npm": "npm ci",
        }[package_manager]
        add_candidate(candidates, "setup", "install", ":package: Install dependencies", install, f"{package_manager} project detected")
        for script, phase, label, key in [
            ("lint", "verify", ":mag: Lint", "lint"),
            ("typecheck", "verify", ":label: Typecheck", "typecheck"),
            ("test", "test", ":test_tube: Test", "test"),
            ("build", "build", ":hammer: Build", "build"),
            ("e2e", "test", ":computer: End-to-end tests", "e2e"),
        ]:
            if script in package_scripts:
                add_candidate(candidates, phase, key, label, node_command(package_manager, script), f"package.json script '{script}' detected")
        for script in sorted(package_scripts):
            if script in {"deploy", "release", "publish"}:
                add_candidate(candidates, "deploy", script, f":rocket: {script.title()}", node_command(package_manager, script), f"package.json script '{script}' detected")

    if "pyproject.toml" in rel_set or any(path.startswith("requirements") for path in rel_set):
        install = "python -m pip install -U pip && python -m pip install -e '.[dev]'"
        if "requirements.txt" in rel_set:
            install = "python -m pip install -U pip && python -m pip install -r requirements.txt"
        add_candidate(candidates, "setup", "python-install", ":package: Install Python dependencies", install, "Python project detected")
        pyproject = root / "pyproject.toml"
        if "ruff.toml" in rel_set or ".ruff.toml" in rel_set or file_contains(pyproject, "[tool.ruff"):
            add_candidate(candidates, "verify", "python-lint", ":mag: Python lint", "python -m ruff check .", "Python lint configuration detected")
        if "tests" in {Path(path).parts[0] for path in rel_files} or "pytest.ini" in rel_set:
            add_candidate(candidates, "test", "python-test", ":test_tube: Python tests", "python -m pytest", "Python tests detected")

    if "Makefile" in rel_set:
        for target, phase, label in [
            ("lint", "verify", ":mag: Make lint"),
            ("test", "test", ":test_tube: Make test"),
            ("build", "build", ":hammer: Make build"),
            ("package", "build", ":package: Make package"),
            ("release", "deploy", ":rocket: Make release"),
            ("deploy", "deploy", ":rocket: Make deploy"),
        ]:
            if target in make_targets:
                add_candidate(candidates, phase, f"make-{target}", label, f"make {target}", f"Makefile target '{target}' detected")

    if docker_files:
        add_candidate(candidates, "build", "docker-build", ":whale: Docker build", "docker build -t \"$BUILDKITE_PIPELINE_SLUG:$BUILDKITE_COMMIT\" .", "Dockerfile detected")

    if "go.mod" in rel_set:
        add_candidate(candidates, "test", "go-test", ":test_tube: Go tests", "go test ./...", "Go module detected")
    if "Cargo.toml" in rel_set:
        add_candidate(candidates, "test", "cargo-test", ":test_tube: Rust tests", "cargo test --workspace", "Cargo manifest detected")
    if "Package.swift" in rel_set:
        add_candidate(candidates, "test", "swift-test", ":test_tube: Swift tests", "swift test", "Swift package detected")

    return {
        "root": root.as_posix(),
        "existing_ci": existing_ci,
        "manifests": manifests,
        "package_manager": package_manager,
        "package_scripts": package_scripts,
        "make_targets": make_targets,
        "docker_files": docker_files,
        "deploy_hints": deploy_hints,
        "candidate_steps": candidates,
    }


def print_text(data: dict[str, Any]) -> None:
    print(f"Repository: {data['root']}")
    for key, title in [
        ("existing_ci", "Existing CI"),
        ("manifests", "Manifests"),
        ("docker_files", "Docker files"),
        ("deploy_hints", "Deploy hints"),
    ]:
        values = data[key]
        print(f"\n{title}:")
        if values:
            for value in values:
                print(f"  - {value}")
        else:
            print("  - none detected")

    print(f"\nPackage manager: {data['package_manager'] or 'none detected'}")
    print("\nPackage scripts:")
    if data["package_scripts"]:
        for name, command in data["package_scripts"].items():
            print(f"  - {name}: {command}")
    else:
        print("  - none detected")

    print("\nMake targets:")
    if data["make_targets"]:
        for target in data["make_targets"]:
            print(f"  - {target}")
    else:
        print("  - none detected")

    print("\nLikely Buildkite step candidates:")
    if data["candidate_steps"]:
        for step in data["candidate_steps"]:
            print(f"  - [{step['phase']}] {step['key']}: {step['command']}")
            print(f"    reason: {step['reason']}")
    else:
        print("  - none detected; inspect repo docs and scripts manually")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to inspect")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format")
    args = parser.parse_args()

    root = Path(args.repo)
    if not root.exists() or not root.is_dir():
        print(f"error: repository path is not a directory: {root}", file=sys.stderr)
        return 2

    data = inspect(root)
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
