from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install_skills", ROOT / "scripts/install-skills.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = MODULE.load_toml(ROOT / "skills.toml")

    def test_catalog_contract(self) -> None:
        MODULE.check(self.manifest)
        entries = MODULE.catalog(self.manifest)
        self.assertEqual(113, len(entries))
        self.assertEqual(86, sum(entry["source_type"] == "vendored" for entry in entries))
        self.assertEqual(27, sum(entry["source_type"] == "github" for entry in entries))
        self.assertTrue(all(entry["customization_status"] for entry in entries))

    def test_vendored_npx_command_is_local_global_and_full_depth(self) -> None:
        command = MODULE.npx_command("skills@1.5.16", str(ROOT), ["example"], full_depth=True)
        self.assertEqual(["npx", "--yes", "skills@1.5.16", "add", str(ROOT)], command[:5])
        self.assertIn("--global", command)
        self.assertIn("--copy", command)
        self.assertIn("--full-depth", command)

    def test_upstream_commands_are_grouped_by_repo_and_ref(self) -> None:
        groups = MODULE.grouped_upstream(self.manifest)
        common = next(group for group in groups if group[0] == "warpdotdev/common-skills")
        self.assertEqual("f2882b9458370cbc23d1b8cb0e458d23b1591205", common[1])
        self.assertEqual(17, len(common[2]))

    def test_verifier_rejects_an_empty_install_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                MODULE.verify(self.manifest, Path(temporary))

    def test_npx_install_name_can_map_to_a_different_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            install_root = Path(temporary) / "target"
            source = home / ".agents/skills/anti-ai-slop"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: anti-ai-slop\n---\n", encoding="utf-8")
            MODULE.copy_from_npx_home(home, install_root, [("anti-ai-slop", "anti-slop")])
            self.assertTrue((install_root / "anti-slop/SKILL.md").is_file())
            self.assertFalse((install_root / "anti-ai-slop").exists())


if __name__ == "__main__":
    unittest.main()
