#!/usr/bin/env python3
"""Capture concise Git and worktree state as JSON for a real handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository or worktree path")
    args = parser.parse_args()
    repo = args.repo.expanduser().resolve()

    try:
        root = Path(run(repo, "rev-parse", "--show-toplevel")).resolve()
        data = {
            "repository_root": str(root),
            "git_dir": run(root, "rev-parse", "--git-dir"),
            "branch": run(root, "branch", "--show-current"),
            "head": run(root, "rev-parse", "HEAD"),
            "status_porcelain_v2": run(root, "status", "--porcelain=v2", "--branch"),
            "changed_paths": sorted(
                set(
                    filter(
                        None,
                        (
                            run(root, "diff", "--name-only").splitlines()
                            + run(root, "diff", "--cached", "--name-only").splitlines()
                            + run(root, "ls-files", "--others", "--exclude-standard").splitlines()
                        ),
                    )
                )
            ),
            "recent_commits": run(root, "log", "-n", "8", "--format=%H %s").splitlines(),
            "worktrees": run(root, "worktree", "list", "--porcelain").splitlines(),
        }
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
