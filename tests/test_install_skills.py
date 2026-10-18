from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
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
        self.assertEqual(len(commands), len(MODULE.load_external_manifest()["source"]))
        self.assertEqual(
            commands[0][:7],
            ["npx", "--yes", "-p", "node@22", "-p", "skills@1.5.16", "skills"],
        )
        self.assertIn("warpdotdev/common-skills", commands[0])
        self.assertIn("council", commands[0])
        self.assertEqual(commands[0][-1], "--global")
        self.assertIn("*", commands[0])

    def fake_checkouts(self, root: Path, edited: set[str] = frozenset()):
        """Stand-in for checkout_reviewed_revision that writes each pinned skill."""
        def checkout(repository: str, revision: str, destination: Path) -> None:
            source = next(s for s in MODULE.load_external_manifest()["source"] if s["repository"] == repository)
            for name in source["skills"]:
                (destination / "skills" / name).mkdir(parents=True)
                (destination / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n---\npinned\n")
        return checkout

    def test_external_install_only_runs_with_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(MODULE.subprocess, "run") as run:
            MODULE.install_external(apply=False, project=True, agents=["codex"])
            run.assert_not_called()

            with (
                mock.patch.object(MODULE, "checkout_reviewed_revision", side_effect=self.fake_checkouts(Path(temporary))) as checkout,
                mock.patch.object(MODULE.shutil, "which", return_value="/usr/bin/npx"),
                mock.patch.object(MODULE.Path, "cwd", return_value=Path(temporary)),
            ):
                with redirect_stdout(io.StringIO()):
                    MODULE.install_external(apply=True, project=True, agents=["codex"])
            # Each source is fetched at its reviewed commit and installed from
            # that local checkout, not from the repository's current tip.
            revisions = {source["reviewed_revision"] for source in MODULE.load_external_manifest()["source"]}
            self.assertEqual({call.args[1] for call in checkout.call_args_list}, revisions)
            command = run.call_args_list[0].args[0]
            self.assertEqual(command[0], "npx")
            self.assertTrue(command[command.index("add") + 1].startswith("/"))
            self.assertNotIn("--global", command)
            self.assertEqual(command[command.index("--agent") + 1], "codex")
            self.assertEqual(run.call_args_list[0].kwargs["env"]["DISABLE_TELEMETRY"], "1")

    def run_external(self, project: Path, **kwargs):
        """Apply with a fake checkout and an npx stand-in that copies pinned skills."""
        target = project / ".agents/skills"
        checkout = self.fake_checkouts(project)

        def fake_npx(command, check, env):
            source = Path(command[command.index("add") + 1])
            for name in command[command.index("--skill") + 1:command.index("--agent")]:
                destination = target / name
                if destination.exists():
                    MODULE.shutil.rmtree(destination)
                MODULE.shutil.copytree(source / "skills" / name, destination)

        with (
            mock.patch.object(MODULE.subprocess, "run", side_effect=fake_npx) as run,
            mock.patch.object(MODULE, "checkout_reviewed_revision", side_effect=checkout),
            mock.patch.object(MODULE.shutil, "which", return_value="/usr/bin/npx"),
            mock.patch.object(MODULE.Path, "cwd", return_value=project),
            redirect_stdout(io.StringIO()) as output,
        ):
            MODULE.install_external(apply=True, project=True, **kwargs)
        installed = {name for call in run.call_args_list
                     for name in call.args[0][call.args[0].index("--skill") + 1:call.args[0].index("--agent")]}
        return installed, output.getvalue(), target

    def test_external_edits_are_kept_and_reported_until_forced_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed, _, target = self.run_external(project)
            self.assertIn("council", installed)
            (target / "council/SKILL.md").write_text("---\nname: council\n---\nmy edits\n")

            installed, output, _ = self.run_external(project)
            self.assertNotIn("council", installed)
            self.assertIn("--force-skill council", output)
            self.assertIn("my edits", (target / "council/SKILL.md").read_text())

            installed, _, _ = self.run_external(project, force={"council"})
            self.assertEqual(installed, {"council"})
            self.assertNotIn("my edits", (target / "council/SKILL.md").read_text())

    def test_unedited_external_skill_updates_when_the_pin_moves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            _, _, target = self.run_external(project)
            # Simulate an older revision we installed: content and record agree.
            (target / "review-pr/SKILL.md").write_text("---\nname: review-pr\n---\nolder\n")
            MODULE.write_record(target, ["review-pr"])
            installed, _, _ = self.run_external(project)
            self.assertIn("review-pr", installed)

    def test_older_copy_installed_another_way_is_held_for_a_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            target = project / ".agents/skills"
            (target / "review-pr").mkdir(parents=True)
            (target / "review-pr/SKILL.md").write_text("---\nname: review-pr\n---\nolder upstream\n")
            installed, output, _ = self.run_external(project)
            self.assertNotIn("review-pr", installed)
            self.assertIn("--force-skill review-pr", output)

    def test_unknown_force_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(MODULE.SkillsError):
            self.run_external(Path(temporary), force={"no-such-skill"})

    def test_verify_checks_external_skills_against_the_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            _, _, target = self.run_external(project)
            manifest = MODULE.load_manifest()
            names = MODULE.catalog_names(manifest)
            MODULE.install(manifest, names, target, force=False, dry_run=False)
            MODULE.verify(names, target, include_external=True)
            (target / "council/SKILL.md").write_text("edited\n")
            with self.assertRaises(MODULE.SkillsError) as failure:
                MODULE.verify(names, target, include_external=True)
            self.assertIn("council (external): changed since it was installed", str(failure.exception))

    def test_verify_reports_a_symlink_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            name = MODULE.catalog_names(MODULE.load_manifest())[0]
            MODULE.shutil.copytree(MODULE.SKILLS_ROOT / name, target / name)
            (target / name / "link").symlink_to("/etc/hosts")
            with self.assertRaises(MODULE.SkillsError) as failure:
                MODULE.verify([name], target)
            self.assertIn("symbolic link", str(failure.exception))

    def test_finder_files_do_not_change_a_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            name = MODULE.catalog_names(MODULE.load_manifest())[0]
            MODULE.shutil.copytree(MODULE.SKILLS_ROOT / name, target / name)
            (target / name / ".DS_Store").write_bytes(b"finder")
            MODULE.verify([name], target)

    def test_external_install_uses_mise_node_when_npx_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            which = lambda tool: "/opt/homebrew/bin/mise" if tool == "mise" else None  # noqa: E731
            with (
                mock.patch.object(MODULE.subprocess, "run") as run,
                mock.patch.object(MODULE, "checkout_reviewed_revision", side_effect=self.fake_checkouts(Path(temporary))),
                mock.patch.object(MODULE.shutil, "which", side_effect=which),
                mock.patch.object(MODULE.Path, "cwd", return_value=Path(temporary)),
            ):
                with redirect_stdout(io.StringIO()):
                    MODULE.install_external(apply=True, project=True)
            self.assertEqual(run.call_args_list[0].args[0][:4], ["mise", "exec", "node@22", "--"])

    def test_external_install_without_node_or_mise_explains_what_to_install(self) -> None:
        with mock.patch.object(MODULE.shutil, "which", return_value=None), self.assertRaises(MODULE.SkillsError) as error:
            MODULE.install_external(apply=True, project=True)
        self.assertIn("Node.js", str(error.exception))

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
