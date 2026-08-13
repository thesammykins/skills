from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install_skills", ROOT / "scripts/install-skills.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstallerTests(unittest.TestCase):
    def test_catalog_matches_local_non_system_skills(self) -> None:
        import tomllib
        manifest = tomllib.loads((ROOT / "skills.toml").read_text())
        MODULE.check(manifest)

    def test_npx_command(self) -> None:
        command = MODULE.npx_command("skills@1.5.16", "source", ["example"], full_depth=True)
        self.assertIn("--global", command)
        self.assertIn("--copy", command)
        self.assertIn("--full-depth", command)

    def test_verify_rejects_empty_install_root(self) -> None:
        import tomllib
        manifest = tomllib.loads((ROOT / "skills.toml").read_text())
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(SystemExit):
            MODULE.verify(manifest, Path(temporary))

    def test_npx_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            target = Path(temporary) / "target"
            source = home / ".agents/skills/example"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: example\n---\n")
            MODULE.copy_from_npx_home(home, target, [("example", "renamed")])
            self.assertTrue((target / "renamed/SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
