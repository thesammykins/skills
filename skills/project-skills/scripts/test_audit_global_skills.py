from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import audit_global_skills as audit


def write_skill(root: Path, name: str, body: str = "body") -> Path:
    path = root / name
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill.\n---\n{body}\n")
    return path


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class AuditGlobalSkillsTests(unittest.TestCase):
    def test_provenance_precedence_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills = root / ".agents" / "skills"
            write_skill(skills / ".system", "system-skill")
            write_skill(skills, "locked-skill")
            write_skill(skills, "historical-skill")
            write_skill(skills, "local-skill")
            write_skill(skills, "unresolved-skill")

            local_source = root / "source"
            write_skill(local_source, "local-skill")
            catalog = {
                "localSources": [
                    {
                        "path": str(local_source),
                        "skillsPath": ".",
                        "root": "https://example.com/local",
                        "defaultScope": "global",
                    }
                ],
                "globalCandidates": ["unresolved-skill"],
            }
            profiles = {
                "profiles": [
                    {
                        "id": "language",
                        "sources": [
                            {
                                "root": "https://example.com/locked",
                                "skill": "locked-skill",
                            }
                        ],
                    }
                ]
            }
            current_lock = root / ".agents" / ".skill-lock.json"
            historical_lock = root / "backup" / ".skill-lock.json"
            write_json(
                current_lock,
                {"skills": {"locked-skill": {"sourceUrl": "https://example.com/locked"}}},
            )
            write_json(
                historical_lock,
                {"skills": {"historical-skill": {"source": "example/historical"}}},
            )

            records = audit.build_inventory(
                skills,
                catalog,
                profiles,
                current_lock,
                [historical_lock],
            )
            by_name = {record["name"]: record for record in records}

            self.assertEqual(by_name["system-skill"]["provenance"], "system-provided")
            self.assertEqual(by_name["system-skill"]["root"], "client-managed:.system")
            self.assertEqual(by_name["locked-skill"]["provenance"], "current-lock")
            self.assertEqual(by_name["locked-skill"]["recommendedScope"], "project")
            self.assertFalse(by_name["locked-skill"]["needsReview"])
            self.assertEqual(by_name["historical-skill"]["provenance"], "historical-lock-candidate")
            self.assertTrue(by_name["historical-skill"]["needsReview"])
            self.assertEqual(by_name["local-skill"]["provenance"], "local-exact-match")
            self.assertEqual(by_name["unresolved-skill"]["provenance"], "unresolved")
            self.assertEqual(by_name["unresolved-skill"]["recommendedScope"], "global")

    def test_source_roots_match_across_git_url_forms(self) -> None:
        profiles = {
            "profiles": [
                {
                    "id": "language",
                    "sources": [{"root": "https://github.com/example/skills"}],
                }
            ]
        }

        roots, _ = audit.project_sources(profiles)

        self.assertEqual(roots[audit.canonical_root("git@github.com:example/skills.git")], ["language"])

    def test_exact_tree_match_precedes_historical_name_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills = root / ".agents" / "skills"
            write_skill(skills, "same-name", "current content")
            source = root / "source"
            write_skill(source, "same-name", "current content")
            historical_lock = root / "backup" / ".skill-lock.json"
            write_json(
                historical_lock,
                {"skills": {"same-name": {"source": "obsolete/source"}}},
            )
            catalog = {
                "localSources": [
                    {
                        "path": str(source),
                        "skillsPath": ".",
                        "root": "https://example.com/current",
                        "defaultScope": "global",
                    }
                ]
            }

            records = audit.build_inventory(
                skills,
                catalog,
                {"profiles": []},
                root / ".agents" / ".skill-lock.json",
                [historical_lock],
            )

            self.assertEqual(records[0]["provenance"], "local-exact-match")
            self.assertEqual(records[0]["root"], "https://example.com/current")

    def test_duplicate_system_and_global_names_fail_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = Path(directory) / "skills"
            write_skill(skills / ".system", "duplicate")
            write_skill(skills, "duplicate")

            with self.assertRaisesRegex(ValueError, "Duplicate skill name 'duplicate'.*skills/.system/duplicate.*skills/duplicate"):
                audit.installed_skills(skills)


if __name__ == "__main__":
    unittest.main()
