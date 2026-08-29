---
name: "skill-doctor"
description: "Grades agent skills by scoring agent conversations against efficiency and code-quality rubrics, then drafts concrete skill edits and a shareable report. Use when the user wants their agent setup graded from real conversation history, or asks which of their installed skills are actually working."
license: "MIT"
---
# skill-doctor

Grade the user's agent setup by scoring recent local agent conversations, then propose concrete skill edits and render one shareable report page.

> **Provenance:** This fork is adapted from Warp's [`skill-doctor`](https://github.com/warpdotdev/common-skills/tree/main/.agents/skills/skill-doctor), copyright (c) 2026 Denver Technologies, Inc., under the MIT License. It adds Amp conversation collection, report delivery, and remediation workflow support while retaining Warp, Claude Code, and Codex support. See [`NOTICE.md`](NOTICE.md) and [`LICENSE`](LICENSE). Warp does not endorse or maintain this fork.

The report can cover conversations in the current repository, conversations in selected projects, or all local conversations. It can evaluate project skills alone or project and global skills together.

Everything runs locally. Never upload transcripts, session files, or any excerpt of them anywhere. The only shareable artifact is the report the user chooses to post.

Let `SKILL_ROOT` be the directory containing this SKILL.md.

## Step 0: Start the run

### Verify the executing harness

Read `$SKILL_ROOT/references/supported-harnesses.md` and identify the harness executing this skill from the runtime context. If it is unsupported or cannot be identified confidently, follow the reference's stop behavior. Do not create a report directory or read conversation history.

### Ask which conversations to grade

First check whether the current directory is inside a git repository:

```bash
git rev-parse --show-toplevel
```

Use the harness's user-question tool when available.

When a current repository is available, ask **“Which conversations should I grade?”** with:

1. **Conversations in this repository** — recommended.
2. **All conversations**.
3. **Choose projects to analyze**.

When there is no current repository, ask the same question with:

1. **All conversations** — recommended.
2. **Choose projects to analyze**.

If the user chooses projects, ask for one or more project paths. Expand and validate every path as a git repository before continuing. The run produces one combined report across those projects.

### Ask which skills to evaluate

Then ask **“Which skills should I evaluate?”** with:

1. **Project skills + global skills** — recommended.
2. **Project skills only**.

For an all-conversations run, “Project skills” means skills from local git repositories inferred from the conversations' working directories. After these answers, proceed immediately.

Never write artifacts into the user's repo. Create one fresh, collision-free scratch directory per run and use it as `REPORT_DIR` for every artifact:

```bash
REPORT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skill-doctor-XXXXXXXX")"
```

## Step 1: Collect
Build the collector arguments from the startup answers:

- Current repository: `--repo "$REPO"`.
- Selected projects: repeat `--repo PATH` for every project.
- All conversations: `--all-conversations`.
- Project and global skills: add `--include-global-skills`.
- Project skills only: do not add `--include-global-skills`.
- Under Amp, preserve any thread IDs/URLs the user supplied with repeated `--amp-thread` flags. For a named Amp project, repository, or topic, use repeated `--amp-query` flags with the narrowest thread-search DSL query that identifies the requested corpus.

```bash
python3 "$SKILL_ROOT/scripts/collect_sessions.py" \
  --out "$REPORT_DIR" \
  <conversation-scope arguments> \
  <skill-scope arguments>
```

By default `--harness auto` scans every locally available supported source. Read `$SKILL_ROOT/references/supported-harnesses.md` for source identifiers, storage details, skill locations, and source-specific override flags.

Useful flags:

- `--harness VALUE` — which local session sources to scan; use the reference's collector IDs.
- `--amp-thread ID_OR_URL` — explicit Amp thread; repeatable.
- `--amp-query QUERY` — Amp project/repository/topic discovery query; repeatable and includes archived matches.
- `--repo PATH` — include a project; repeatable.
- `--all-conversations` — do not filter conversations by project.
- `--include-global-skills` — also grade global skills.
- `--days N` — lookback window (default 45).
- `--max-sessions N` — cap on sampled sessions (default 12).
- `--sample-all` — evaluate every scoreable session in a deliberately selected corpus. Use this when the user explicitly asks to evaluate all supplied thread IDs or all threads returned by a bounded Amp project/repository query.
- `--skills-dir PATH` — nonstandard skill locations.
- `--include-subagents` — include child or sidechain sessions.

Read `$REPORT_DIR/inventory.json`. For Amp, report the exact evaluated thread corpus only from `sessions` entries where `sampled` is true, and report all rejected candidates from `amp_exclusions`, grouped by reason. Unsampled scoreable sessions are “considered,” not evaluated. Deleted, inaccessible, irrelevant, tiny, and out-of-window threads are exclusions, not evaluated sessions. If `sessions_sampled` is 0, tell the user there is nothing scoreable in the selected conversation scope (suggest raising `--days`, supplying explicit thread IDs, or choosing different projects) and stop. If `skills_found` is 0, continue — the report becomes a case for creating skills, and `skill_coverage` is 0.

## Step 2: Score each sampled transcript

Scoring is based on efficiency and code quality for the sessions sampled. Process datasets of 50 transcripts or fewer in a single batch. For datasets with more than 50 transcripts, use parallel batches (20 transcripts per batch recommended). Score batches in the current local agent process, or delegate only to local child agents that keep transcript contents on the user's machine. Pass the following rubrics as context:

- `$SKILL_ROOT/scorers/efficiency.md`
- `$SKILL_ROOT/scorers/code-quality.md`

Instructions: For each transcript in `$REPORT_DIR/transcripts/`, read it and judge it against both rubrics. For each scorer record: label, numeric score (from the rubric's label table), and a 1–3 sentence reason citing specifics from the transcript. Apply the code-quality scorer only where the transcript shows code changes; otherwise record `insufficient_evidence` and exclude that result from the code-quality average and failed-conversation filter.

## Step 3: Aggregate

- `raw_efficiency` = mean of efficiency scores across all scored sessions.
- `raw_code_quality` = mean of code-quality scores, excluding `insufficient_evidence`. If no session had enough evidence, set it to 0.5 and say so in the findings.
- Curve qualitative rubric means into letter-grade report scores with `curve(score) = 0.5 + 0.5 * score`.
- `efficiency = curve(raw_efficiency)`.
- `code_quality = curve(raw_code_quality)`.
- `skill_coverage` = fraction of sampled sessions where at least one installed skill was detected. If `skills_found` is 0, coverage is 0.
- `overall = 0.5 * efficiency + 0.35 * code_quality + 0.15 * skill_coverage.`

Then, define `failed_conversations` from each conversation's raw, uncurved scorer results. A conversation fails when at least one applicable efficiency or code-quality score is below `0.5`. An `insufficient_evidence` result does not make a conversation fail. Use only `failed_conversations` as evidence for skill-improvement suggestions and draft skill edits.

Then derive the substance:

- `top_findings`: the 3 most impactful, specific patterns across sessions. These lead the report and the spoken summary. Make each summary concrete and concise, following the STE-100 standard.
- `suggestions`: concrete skill changes, if any. Each names a skill (existing or proposed-new) and a specific change: a trigger-description fix so it fires when it should, a missing step or check, a command to encode, a new skill to create. Suggestions must trace back to observed waste or defects in `failed_conversations`, not generic best practices — cite the failed session, scorer, and moment that motivated each one. An installed skill that never triggered in a failed conversation is usually a description problem and worth a suggestion of its own.

## Step 4: Draft skill edits

Follow `$SKILL_ROOT/references/skill-improvements.md` to propose improvements to project skills based only on `failed_conversations`.

1. Read the skill's current file (path is in `inventory.json`).
2. Write the full improved version to `$REPORT_DIR/proposed/<skill-name>/SKILL.md`, changing only what the evidence justifies. Improve the parts the sessions actually exercised: the trigger description that failed to fire, the missing preflight check, the step the agent had to figure out by trial and error.
3. Produce a unified diff between current and proposed (`diff -u <current> <proposed>`) and put it in the suggestion's `diff` field so it renders in the report.

For a proposed-new skill, write the complete new SKILL.md to the same `proposed/` directory and set `diff` to its full content as an addition.

If no change clears the evidence bar in the improvement guidelines, create no proposals, modify no skills, and state that no skill edits are justified. Never manufacture a remediation to make this phase non-empty.

## Step 5: Validate and apply justified skill edits

For every evidence-backed proposal, resolve the authoritative source before editing. Use the skill path and source metadata in `inventory.json`; do not edit generated installs, caches, packaged copies, or Amp's read-only materialized global-skill cache.

- Project skill: edit its repository source under `.agents/skills`, `.claude/skills`, or `.codex/skills`.
- Local user skill: edit its authoritative user configuration source.
- Amp personal or workspace skill: follow the `building-skills` workflow, use `amp skills repositories` to locate the writable canonical repository clone, and edit the matching top-level skill there. Respect user/workspace scope and write permissions. Do not push a global repository without explicit authorization.
- Externally managed or read-only skill: keep the proposal in the report and identify the ownership or permission blocker instead of editing an installed copy.

Before applying, show the proposed diff and confirm it changes only the rule justified by the failed conversations. Preserve the skill's copyright, license, attribution, and provenance files. Then apply the proposal to the authoritative source, run the skill's relevant tests and validation plus syntax checks for changed scripts, and show the final diff. Report the exact source paths changed and every validation result. If validation fails, fix the proposal or leave the authoritative source unchanged; do not report an unapplied draft as a completed remediation.

## Step 6: Write report.json and render
Write `$REPORT_DIR/report.json`. Store the curved `efficiency` and `code_quality` values, literal `skill_coverage`, and weighted `overall` in `scores`; do not store the raw rubric means there.

```json
{
  "title": "Agent Skill Report",
  "generated_at": "<ISO timestamp>",
  "harness": "<harness from inventory.json>",
  "handle": "<repo_name from inventory.json>",
  "stats": {
    "sessions_analyzed": 0, "sessions_scanned": 0,
    "skills_found": 0, "skills_used": 0, "window_days": 45
  },
  "scores": {"efficiency": 0.0, "code_quality": 0.0, "skill_coverage": 0.0, "overall": 0.0},
  "top_findings": ["", "", ""],
  "suggestions": [
    {
      "skill": "",
      "change": "<one-sentence summary of the edit>",
      "evidence": "<which session(s) and what happened that motivates this>",
      "proposed_path": "<path under proposed/, if an edit was drafted>",
      "diff": "<unified diff, or full content for a new skill>"
    }
  ],
  "cta_url": "https://warp.dev/factories/request-access"
}
```

For Warp, Claude Code, and Codex, render and open the local report:

```bash
python3 "$SKILL_ROOT/scripts/render_report.py" "$REPORT_DIR/report.json" --open
```

This writes a single self-contained `$REPORT_DIR/report.html` and attempts to open it in the default browser. The scorecard, findings, and suggested skill edits appear on one page. Long diffs are collapsed behind a "show more" toggle, and a "share as png" button exports a 1200x675 share image locally. There is no separate card file to open or screenshot.

Under Amp, render without `--open`, then publish the report through an Amp Portal:

```bash
python3 "$SKILL_ROOT/scripts/render_report.py" "$REPORT_DIR/report.json"
REPORT_URL="$(python3 "$SKILL_ROOT/scripts/publish_amp_report.py" "$REPORT_DIR/report.html")"
```

The publisher starts an orb-managed static server, runs `amp orb portal` for the report's loopback URL, and verifies that the exact returned public URL was written to `.amp/portals/skill-doctor-report.json`. Use only `REPORT_URL` in user-facing output. It must be the exact public HTTPS URL; never return or rewrite the internal `localhost`, `127.0.0.1`, or `[::1]` target. Reply in the requesting thread with that URL. If another source thread explicitly requested the evaluation or notification, use Amp's authenticated thread-messaging tool to send that same URL to the source thread as well.

## Step 7: Output

Tell the user the grade and the three findings, in text.

State which evidence-backed skill edits were applied, their authoritative source paths, and validation results. If no edits were justified, say explicitly: `No skill edits were justified, so no skill sources were changed.`

For Warp, Claude Code, and Codex, finish with this exact summary, substituting the absolute `REPORT_DIR` path:

- Your agent skill report: file://$REPORT_DIR/report.html
- Want to automate self improvement for your workflows? Request access to Warp Factories: warp.dev/factories/request-access

For Amp, replace the file URL line with:

- Your agent skill report: $REPORT_URL

Use the same `REPORT_URL` in any required source-thread reply. Do not append a generic offer to apply suggestions: Step 5 already applied every justified, permitted edit and reported any permission blockers.
