from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install_skills", ROOT / "scripts/install-skills.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillsToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = MODULE.load_manifest()

    def test_catalog_matches_checked_in_skills(self) -> None:
        MODULE.check(self.manifest)
        self.assertEqual(sorted(MODULE.catalog_names(self.manifest)), MODULE.source_skill_names())

    def test_install_and_verify_selected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "skills"
            MODULE.install(
                self.manifest,
                ["agent-change-verification"],
                target,
                force=False,
                dry_run=False,
            )
            MODULE.verify(["agent-change-verification"], target)
            self.assertTrue((target / "agent-change-verification/references/verification-methods.md").is_file())

    def test_install_requires_force_to_replace_changed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "skills"
            destination = target / "agent-browser"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("changed", encoding="utf-8")
            with self.assertRaises(MODULE.SkillsError):
                MODULE.install(self.manifest, ["agent-browser"], target, force=False, dry_run=False)
            MODULE.install(self.manifest, ["agent-browser"], target, force=True, dry_run=False)
            MODULE.verify(["agent-browser"], target)

    def test_package_is_reproducible_and_has_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_output = Path(first)
            second_output = Path(second)
            MODULE.package(self.manifest, first_output)
            MODULE.package(self.manifest, second_output)

            first_files = sorted(path.name for path in first_output.iterdir())
            second_files = sorted(path.name for path in second_output.iterdir())
            self.assertEqual(first_files, second_files)
            for name in first_files:
                self.assertEqual((first_output / name).read_bytes(), (second_output / name).read_bytes())

            with zipfile.ZipFile(first_output / "agent-change-verification.skill") as archive:
                self.assertIn("SKILL.md", archive.namelist())
                self.assertIn("references/verification-methods.md", archive.namelist())
                self.assertNotIn("agent-change-verification/SKILL.md", archive.namelist())
            with zipfile.ZipFile(first_output / "skills-bundle.zip") as archive:
                self.assertIn("scripts/install-skills.py", archive.namelist())
                self.assertIn("external-skills.toml", archive.namelist())
                self.assertIn("skills/agent-change-verification/SKILL.md", archive.namelist())
                self.assertIn("SKILL-SHA256SUMS", archive.namelist())

    def test_external_commands_are_pinned_and_global_by_default(self) -> None:
        commands = MODULE.external_commands(project=False)
        self.assertEqual(len(commands), 2)
        self.assertEqual(
            commands[0][:7],
            ["npx", "--yes", "-p", "node@22", "-p", "skills@1.5.16", "skills"],
        )
        self.assertIn("warpdotdev/common-skills", commands[0])
        self.assertIn("council", commands[0])
        self.assertEqual(commands[0][-1], "--global")
        self.assertIn("*", commands[0])

    def test_external_install_only_runs_with_apply(self) -> None:
        with mock.patch.object(MODULE.subprocess, "run") as run:
            MODULE.install_external(apply=False, project=True, agents=["codex"])
            run.assert_not_called()

            MODULE.install_external(apply=True, project=True, agents=["codex"])
            self.assertEqual(run.call_count, 2)
            command = run.call_args_list[0].args[0]
            self.assertNotIn("--global", command)
            self.assertEqual(command[command.index("--agent") + 1], "codex")
            self.assertEqual(run.call_args_list[0].kwargs["env"]["DISABLE_TELEMETRY"], "1")

    def test_verify_ignores_unmanaged_skills_and_system_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "skills"
            (target / "unmanaged").mkdir(parents=True)
            (target / ".system").mkdir()
            (target / ".system/marker").write_text("preserve", encoding="utf-8")
            MODULE.install(self.manifest, ["agent-browser"], target, force=False, dry_run=False)
            MODULE.verify(["agent-browser"], target)
            self.assertTrue((target / "unmanaged").is_dir())
            self.assertEqual((target / ".system/marker").read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
