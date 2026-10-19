"""Runs the real skills CLI in a throwaway HOME and checks where it writes.

Needs the network on first run (npx fetches the pinned skills CLI), so it is
its own task: `mise run check-cli`. It proves the default external install
only creates ~/.agents/skills, not a folder per known agent.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("install_skills", ROOT / "scripts/install-skills.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        home, source = root / "home", root / "source"
        skill = source / "skills" / "demo-skill"
        skill.mkdir(parents=True)
        home.mkdir()
        (skill / "SKILL.md").write_text("---\nname: demo-skill\ndescription: Demo for the CLI write check.\n---\nbody\n")
        command = module.external_commands(project=False, sources={
            module.load_external_manifest()["source"][0]["repository"]: source})[0]
        start, end = command.index("--skill") + 1, command.index("--agent")
        command = [*module.node_runner(module.load_external_manifest()["tool"]), *command[:start], "demo-skill", *command[end:]]
        env = {**os.environ, "HOME": str(home), "DISABLE_TELEMETRY": "1"}
        subprocess.run(command, check=True, env=env, cwd=root, capture_output=True)
        created = sorted(str(p.relative_to(home)) for p in home.iterdir() if p.name not in {".npm", ".cache"})
        if created != [".agents"] or not (home / ".agents/skills/demo-skill/SKILL.md").is_file():
            print(f"FAIL: the external install created {created} in HOME; expected only .agents", file=sys.stderr)
            return 1
    print("ok: the default external install writes only ~/.agents/skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
