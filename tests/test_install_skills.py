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
    def test_manifest_is_valid(self) -> None:
        MODULE.check_manifest(MODULE.load_toml(ROOT / "skills.toml"))

    def test_npx_command_is_pinned_and_global(self) -> None:
        command = MODULE.npx_command(
            "skills@1.5.16",
            {"repo": "owner/repo", "ref": "abc123", "paths": ["skills/example"]},
        )
        self.assertEqual(command[:5], ["npx", "--yes", "skills@1.5.16", "add", "owner/repo@abc123"])
        self.assertIn("--global", command)
        self.assertIn("*", command)

    def test_local_install_supports_isolated_root(self) -> None:
        manifest = MODULE.load_toml(ROOT / "skills.toml")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / ".agents/skills"
            paths = MODULE.install_local("convert-prompt", manifest["skills"]["convert-prompt"], root, False)
            self.assertTrue((paths[0] / "SKILL.md").is_file())
            self.assertEqual([], MODULE.verify_one("convert-prompt", manifest["skills"]["convert-prompt"], paths))


if __name__ == "__main__":
    unittest.main()
