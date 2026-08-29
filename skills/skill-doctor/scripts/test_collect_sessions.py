#!/usr/bin/env python3
"""Tests for skill-doctor session collection."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from collect_sessions import (
    collect_amp_sessions,
    detect_skills_from_entries,
    discover_amp_managed_skills,
    discover_skills,
    find_amp_candidates,
    find_claude_session_files,
    is_amp_runtime,
    parse_amp_thread,
    parse_claude_session,
    session_matches_repos,
)


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")


class ClaudeSessionTests(unittest.TestCase):
    def test_discovers_skills_and_matches_sessions_across_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first"
            second = root / "second"
            first_skill = first / ".agents" / "skills" / "alpha" / "SKILL.md"
            second_skill = second / ".claude" / "skills" / "beta" / "SKILL.md"
            first_skill.parent.mkdir(parents=True)
            second_skill.parent.mkdir(parents=True)
            first_skill.write_text("---\ndescription: Alpha\n---\n")
            second_skill.write_text("---\ndescription: Beta\n---\n")

            skills = discover_skills(
                [first, second],
                root / "codex-home",
                [],
                False,
            )

            self.assertEqual(set(skills), {"alpha", "beta"})
            self.assertTrue(
                session_matches_repos(second / "src", [first, second])
            )
            self.assertFalse(
                session_matches_repos(root / "elsewhere", [first, second])
            )

    def test_detects_skills_from_deferred_tool_entries(self):
        entries = [
            ("tool:Skill", '{"skill": "alpha"}'),
            ("tool:read", '{"path": "/repo/.agents/skills/beta/SKILL.md"}'),
            ("assistant", "Mentioning gamma here does not count."),
        ]

        self.assertEqual(
            detect_skills_from_entries(entries, {"alpha", "beta", "gamma"}),
            {"alpha", "beta"},
        )

    def test_discovers_parent_sessions_and_optional_subagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            parent = claude_home / "projects" / "-repo" / "parent.jsonl"
            subagent = (
                claude_home
                / "projects"
                / "-repo"
                / "parent"
                / "subagents"
                / "agent-child.jsonl"
            )
            old = claude_home / "projects" / "-repo" / "old.jsonl"
            for path in (parent, subagent, old):
                write_jsonl(path, [{"type": "user"}])
            old_time = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
            os.utime(old, (old_time, old_time))
            cutoff = datetime.now(timezone.utc) - timedelta(days=1)

            parents = find_claude_session_files(claude_home, cutoff, False)
            with_subagents = find_claude_session_files(claude_home, cutoff, True)

            self.assertEqual([path for _, path in parents], [parent])
            self.assertEqual(
                {path for _, path in with_subagents},
                {parent, subagent},
            )

    def test_parses_messages_tools_skills_and_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            common = {
                "sessionId": "session-1",
                "cwd": "/tmp/repo",
                "timestamp": "2026-08-20T10:00:00Z",
                "version": "1.0.0",
            }
            write_jsonl(path, [
                {
                    **common,
                    "type": "user",
                    "uuid": "user-1",
                    "message": {"role": "user", "content": "Improve my skill"},
                },
                {
                    **common,
                    "type": "assistant",
                    "uuid": "assistant-1",
                    "message": {
                        "id": "message-1",
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I will inspect it."},
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "input": {"skill": "update-skill"},
                            },
                        ],
                    },
                },
                {
                    **common,
                    "type": "assistant",
                    "uuid": "assistant-2",
                    "message": {
                        "id": "message-1",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Edit",
                                "input": {"file_path": "/tmp/repo/SKILL.md"},
                            }
                        ],
                    },
                },
                {
                    **common,
                    "type": "user",
                    "uuid": "result-1",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "is_error": True,
                                "content": "permission denied",
                            }
                        ],
                    },
                },
            ])

            meta, stats, entries, skills = parse_claude_session(
                path,
                {"update-skill"},
                False,
            )

            self.assertEqual(meta["id"], "session-1")
            self.assertEqual(meta["cwd"], "/tmp/repo")
            self.assertEqual(stats["user_turns"], 1)
            self.assertEqual(stats["assistant_turns"], 1)
            self.assertEqual(stats["tool_calls"], 2)
            self.assertEqual(stats["error_outputs"], 1)
            self.assertTrue(stats["has_code_edits"])
            self.assertEqual(skills, ["update-skill"])
            self.assertIn(("user", "Improve my skill"), entries)
            self.assertIn(("assistant", "I will inspect it."), entries)

    def test_excludes_sidechains_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent-child.jsonl"
            write_jsonl(path, [{
                "type": "user",
                "sessionId": "session-1",
                "agentId": "child-1",
                "isSidechain": True,
                "cwd": "/tmp/repo",
                "timestamp": "2026-08-20T10:00:00Z",
                "message": {"role": "user", "content": "Investigate"},
            }])

            self.assertIsNone(parse_claude_session(path, set(), False))
            parsed = parse_claude_session(path, set(), True)
            self.assertEqual(parsed[0]["id"], "session-1-child-1")
            self.assertEqual(parsed[0]["thread_source"], "subagent")


class AmpSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures = Path(__file__).parent / "fixtures"
        cls.payload = json.loads((fixtures / "amp-thread.json").read_text())
        cls.collection_cases = json.loads(
            (fixtures / "amp-collection-cases.json").read_text()
        )

    def test_identifies_amp_only_from_runtime_context(self):
        thread_id = "T-019f0000-0000-7000-8000-000000000001"
        self.assertTrue(is_amp_runtime({"AMP_THREAD_ID": thread_id, "AMP_EXECUTOR": "orb"}))
        self.assertTrue(is_amp_runtime({"AMP_THREAD_ID": thread_id, "AMP_ORB": "1"}))
        self.assertFalse(is_amp_runtime({"AMP_THREAD_ID": thread_id}))
        self.assertFalse(is_amp_runtime({"AMP_EXECUTOR": "orb"}))

    @patch("collect_sessions.run_json_command")
    def test_discovers_amp_personal_skills_and_excludes_builtins(self, run_json):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "personal-skill"
            base.mkdir()
            skill_md = base / "SKILL.md"
            skill_md.write_text("---\nname: personal-skill\ndescription: Personal skill\n---\n")
            run_json.return_value = {
                "skills": [
                    {
                        "name": "personal-skill",
                        "description": "Personal skill",
                        "baseDir": base.as_uri(),
                        "source": "global-user",
                    },
                    {
                        "name": "builtin-skill",
                        "description": "Built in",
                        "baseDir": "builtin:///skills",
                        "source": "builtin",
                    },
                ]
            }

            skills = discover_amp_managed_skills("amp")

        self.assertEqual([skill["name"] for skill in skills], ["personal-skill"])
        self.assertEqual(skills[0]["path"], str(skill_md))

    def test_normalizes_messages_tools_usage_metadata_and_children(self):
        children = [{
            "id": "T-019f0000-0000-7000-8000-000000000002",
            "title": "Review parser patch",
            "updatedAt": "2026-08-20T10:04:00Z",
        }]
        meta, stats, entries, skills = parse_amp_thread(
            self.payload,
            {"agent-change-verification"},
            archived=True,
            children=children,
        )

        self.assertEqual(meta["cwd"], "/workspace/example")
        self.assertTrue(meta["archived"])
        self.assertEqual(meta["repository_urls"], ["https://github.com/example/project"])
        self.assertEqual(meta["child_threads"][0]["id"], children[0]["id"])
        self.assertEqual(stats["user_turns"], 1)
        self.assertEqual(stats["assistant_turns"], 2)
        self.assertEqual(stats["tool_calls"], 2)
        self.assertTrue(stats["has_code_edits"])
        self.assertEqual(stats["usage"]["requests"], 2)
        self.assertEqual(stats["usage"]["input_tokens"], 280)
        self.assertEqual(stats["usage"]["output_tokens"], 45)
        self.assertEqual(skills, ["agent-change-verification"])
        self.assertIn(("child-thread", f"{children[0]['id']}: Review parser patch"), entries)
        self.assertFalse(any("internal routing metadata" in text for _, text in entries))

    @patch("collect_sessions.search_amp_threads")
    @patch("collect_sessions.list_amp_threads")
    def test_discovers_archived_explicit_and_query_threads(self, list_threads, search_threads):
        active = self.collection_cases["active"]
        archived = self.collection_cases["includingArchived"][1]
        list_threads.side_effect = [active, self.collection_cases["includingArchived"]]
        search_threads.return_value = [archived]

        candidates = find_amp_candidates(
            "amp",
            [f"https://ampcode.com/threads/{self.payload['id']}"],
            ["project:not_paper author:me"],
            [],
            False,
        )

        by_id = {candidate["id"]: candidate for candidate in candidates}
        self.assertTrue(by_id[self.payload["id"]]["explicit"])
        self.assertTrue(by_id[archived["id"]]["archived"])

    @patch("collect_sessions.search_amp_threads", return_value=[])
    @patch("collect_sessions.run_json_command")
    def test_records_inaccessible_deleted_irrelevant_and_tiny_exclusions(self, run_json, _search):
        inaccessible_case = self.collection_cases["inaccessible"]
        inaccessible = inaccessible_case["id"]
        deleted = "T-019f0000-0000-7000-8000-000000000011"
        irrelevant = "T-019f0000-0000-7000-8000-000000000012"
        tiny = "T-019f0000-0000-7000-8000-000000000013"
        good = self.payload["id"]

        def export(command, timeout=60):
            thread_id = command[-1]
            if thread_id == inaccessible:
                raise RuntimeError(inaccessible_case["error"])
            if thread_id == deleted:
                return {"id": deleted, "meta": {"deleted": True}, "messages": []}
            if thread_id == irrelevant:
                return {**self.payload, "id": irrelevant, "title": "Unrelated work"}
            if thread_id == tiny:
                return {"id": tiny, "title": "Tiny", "meta": {}, "messages": []}
            return self.payload

        run_json.side_effect = export
        candidates = [
            {"id": inaccessible, "reasons": ["explicit"], "explicit": True, "archived": False},
            {"id": deleted, "reasons": ["explicit"], "explicit": True, "archived": False},
            {"id": irrelevant, "reasons": ["query:jamf_sandbox"], "explicit": False, "archived": False},
            {"id": tiny, "reasons": ["explicit"], "explicit": True, "archived": False},
            {"id": good, "reasons": ["explicit"], "explicit": True, "archived": False},
        ]

        sessions, exclusions = collect_amp_sessions(
            "amp", candidates, {"agent-change-verification"}, datetime(2026, 1, 1, tzinfo=timezone.utc), False
        )

        self.assertEqual([session["meta"]["id"] for session in sessions], [good])
        self.assertEqual(
            {item["reason"] for item in exclusions},
            {"inaccessible", "deleted", "irrelevant", "tiny"},
        )

    def test_amp_and_claude_sessions_share_the_internal_shape(self):
        amp = parse_amp_thread(self.payload, set())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.jsonl"
            write_jsonl(path, [
                {
                    "type": "user",
                    "sessionId": "claude-1",
                    "cwd": "/workspace/example",
                    "timestamp": "2026-08-20T10:00:00Z",
                    "message": {"role": "user", "content": "Fix it"},
                },
                {
                    "type": "assistant",
                    "sessionId": "claude-1",
                    "cwd": "/workspace/example",
                    "timestamp": "2026-08-20T10:01:00Z",
                    "message": {"role": "assistant", "content": [
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "parser.py"}}
                    ]},
                },
            ])
            claude = parse_claude_session(path, set(), False)

        for parsed in (amp, claude):
            meta, stats, entries, skills = parsed
            self.assertIn("id", meta)
            self.assertIn("cwd", meta)
            self.assertIn("tool_calls", stats)
            self.assertIsInstance(entries, list)
            self.assertIsInstance(skills, list)


if __name__ == "__main__":
    unittest.main()
