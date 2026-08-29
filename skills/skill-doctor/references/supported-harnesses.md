# Supported harnesses

This file is the single source of truth for harness support in `skill-doctor`. Reference it instead of repeating harness lists in `SKILL.md`.

## Startup gate

| Harness | Collector ID | Conversation source |
| --- | --- | --- |
| Amp | `amp` | Authenticated Amp thread API through `amp threads` |
| Warp | `warp` | Read-only Warp conversation databases |
| Claude Code | `claude` | Project-history JSONL |
| Codex | `codex` | Rollout JSONL |

At startup, identify the harness executing the skill from the runtime context. Do not infer it from conversation files found on disk.

Amp is identified only when `AMP_THREAD_ID` contains a valid `T-…` thread ID and either `AMP_EXECUTOR` or `AMP_ORB` is present. Confirm that `amp threads list --json --limit 1` succeeds before collecting. The presence of an `amp` binary, an Amp skill directory, or Amp transcript search results is not sufficient runtime identification.

If the executing harness is not listed above, or cannot be identified confidently, stop before creating a report directory or reading conversation history. Tell the user:

> skill-doctor currently supports Amp, Warp, Claude Code, and Codex. This run appears to be using an unsupported harness, so no conversations were read.

## Collector source selection

- `--harness auto` scans every locally available supported source and is the default.
- `--harness all` also requests every supported source.
- `--harness <collector-id>` restricts collection to one source from the table.
- A report containing one source uses its collector ID in `inventory.json`; a report containing multiple sources uses `mixed`.

Harness-specific source overrides:

- `--amp-thread ID_OR_URL` — collect an explicit Amp thread; repeatable. Explicit threads are not dropped only because they are older than `--days`.
- `--amp-query QUERY` — discover Amp threads with the thread-search DSL; repeatable. Use structured filters when possible, for example `project:not_paper author:me`, `repo:https://ampcode.com/git/@sammykins/jamf-sandbox`, or a focused topic query.
- `--amp-cli PATH` — nonstandard Amp CLI executable.
- `--claude-home PATH` — nonstandard Claude Code configuration directory.
- `--codex-home PATH` — nonstandard Codex home.
- `--warp-db PATH` — explicit Warp database; repeatable.
- `--warp-data-dir PATH` — nonstandard Warp channel-data directory.

## Skill locations

Project skills are discovered from:

- `.agents/skills`
- `.claude/skills`
- `.codex/skills`

Amp project skills use `.agents/skills`. Amp-compatible local global locations are `~/.config/agents/skills`, `~/.agents/skills`, and `~/.config/amp/skills`. When `--include-global-skills` is set, the collector also reads personal and workspace skills reported by `amp skill list --json`; it excludes Amp built-ins from the evaluated installed-skill inventory.

## Amp collection contract

Amp has no required filesystem transcript location. The collector uses:

- `amp threads list --include-archived --json` to index active and archived threads and annotate archive state.
- `amp threads search QUERY --json` for explicit project, repository, topic, file, parent, or other DSL discovery.
- `amp threads export ID` for full messages, tool calls/results, activated skills, per-message token/model usage, repository/tree context, and thread metadata.
- `parent:ID` searches to represent direct child-thread activity. Add `--include-subagents` to evaluate child threads as separate sessions as well.

Every Amp candidate has one outcome in `inventory.json`: a scoreable session in `sessions`, or an entry in `amp_exclusions`. Exclusion reasons include `deleted`, `deleted_or_missing`, `inaccessible`, `irrelevant`, `tiny`, and `outside_window`. Archived threads are supported and are not excluded merely for being archived. Never describe an exclusion as sampled, analyzed, or evaluated.

For a known corpus, prefer explicit IDs/URLs or a structured `project:`/`repo:` query over broad keywords. The previously supplied `not_paper` corpus is discoverable with `--amp-query 'project:not_paper author:me'`; `jamf_sandbox` work should use its canonical `jamf-sandbox` project/repository identity or explicit thread IDs so incidental Jamf mentions are excluded.

Add `--sample-all` when the user asks to evaluate the entire bounded corpus. Without it, the normal per-skill and no-skill sampling caps still apply, even if discovery found every requested thread.

## Amp report delivery

Amp reports must be served by an orb-managed static server and exposed with `amp orb portal`. Run `scripts/publish_amp_report.py` after rendering `report.html` without `--open`. The publisher passes the report's internal loopback URL to `amp orb portal`, writes `.amp/portals/skill-doctor-report.json`, verifies that it contains the exact public URL returned by the command, and prints only that public HTTPS URL.

Return that exact URL in the requesting thread. When another source thread explicitly requested the run or notification, send the same URL to that source thread with Amp's authenticated thread-messaging tool. Never expose the internal `localhost`, `127.0.0.1`, or `[::1]` target. This delivery contract is Amp-specific; Warp, Claude Code, and Codex continue to open the local `file://` report.

## Skill remediation

Apply only edits that satisfy `references/skill-improvements.md`. Resolve each installed skill to its authoritative project, user, or workspace source; never edit an installation copy or Amp's materialized global-skill cache. Preserve licenses and attribution, show the proposed and final diffs, and run relevant tests, validation, and syntax checks. Respect source scope, write permissions, and the approval requirement for pushing global repositories. If no proposal clears the evidence bar, make no edits and say so explicitly.
