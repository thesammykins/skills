---
name: creating-pull-requests
description: Pushes a branch and opens or updates a GitHub pull request whose description reads like a person wrote it. Use only when the user asks for a PR; routine work goes straight to main.
---

# Creating Pull Requests

Default workflow is trunk-based: commit to `main`, pass local CI, push. Open a PR
only when the user asks, or when a repository you don't own requires one. A PR
here is for a reader, not a gate, so write it for the person who will merge it
or find it in history a year from now.

## Before opening

1. Read repository instructions and any PR template.
2. Resolve the base from the user, an existing PR, or `origin/HEAD`
   (`git remote set-head origin --auto` if unset). Never assume `main`.
3. `git status --short --branch`. Stop on uncommitted tracked changes or
   conflicts; commit with `creating-conventional-commits` first. Warn about
   untracked files that won't be included.
4. Read the whole base-to-head diff and every commit, not just the last one.
5. Run the repository's local CI gate. Fix failures; never open a PR that is
   red locally. Because the gate is mandatory, don't report that it ran.
6. Confirm the branch holds only this work: no secrets, scratch files, generated
   reports or unrelated edits.

## Linking the reason

- If an issue exists, link it: `Closes #N` when fully resolved, `Refs #N`
  otherwise. Search open issues (`gh issue list --search`) before saying none
  exists.
- If there's no issue, say what you saw in a sentence: "Checking out of the first
  of two shifts marked the second as checked out." Don't create an issue just
  to have something to link.

## Writing the description

Open with the problem and the outcome in plain sentences: what was wrong or
missing, and what is true now. Then add only what a reviewer needs and can't
get from the diff:

- a decision that isn't obvious, and why you chose it over the alternative;
- compatibility, migration, rollout or data consequences;
- what to look at closely, if one part carries the risk;
- for any visible UI change, before/after screenshots or a short recording.
  Capture them with the repo's tooling and synthetic data. A UI PR without
  them isn't ready.

Scale to risk, not line count. A narrow fix can be two sentences. A change to
stored data, signing or a trust boundary needs its invariants spelled out.
[writing-pull-requests.md](references/writing-pull-requests.md) has worked
examples by size.

The title states the outcome in the repo's commit style, e.g.
`fix(shifts): keep check-ins per shift on split days`. Avoid "Fix bug",
"Updates" or a branch name.

### Don't write like an agent

These patterns mark a description as machine-written and make reviewers trust
it less:

- **Claims the diff doesn't support.** The most common defect in agent PRs is
  describing work that isn't there. Re-read the final diff and delete any
  sentence it doesn't back up, including plans that were later dropped.
- **Code tours.** Lists of files, functions and identifiers the reader can see
  in the diff, with no framing of what the change does overall. Lead with
  behaviour; name a symbol only when the reader needs it to follow the argument.
- **Ceremony.** Fixed `## Summary` / `## Changes` / `## Testing` headings on
  every PR, `N/A` sections, a "Changes" list that restates the summary.
- **Test theatre.** "All tests pass", "Ran lint", command lists, checkmark
  emoji. Passing local CI is implied. Mention a test only when it proves
  something specific a reviewer would ask about, e.g. "the new regression fails
  before the fix".
- **Activity narration.** "I investigated…", "After analysing the codebase…",
  "This PR aims to…". Describe the change, not the session.
- **Inflated language.** "Comprehensive", "robust", "seamless", "enhances",
  "ensures", "significant improvement". Say what changed.
- **Leftovers.** `[WIP]` prefixes, template placeholders, unchecked boxes copied
  from the template, a body that's longer than the change warrants.

Write in short paragraphs. Use a list only for truly separate items. Keep
each paragraph or bullet on one line, since GitHub turns hard wraps inside a
paragraph into line breaks.

## Push and open

Write the body to a file so backticks and `$` survive:

```bash
git push -u origin HEAD
gh pr view --json number,url 2>/dev/null   # update instead if one exists
gh pr create --base <base> --title "<title>" --body-file <file>
```

Use `gh pr edit --title/--body-file` for an existing PR, and refresh the body
after material review changes so it matches the final code. Open as ready unless
the user asks for a draft. Don't add reviewers or labels, or merge, unless asked.
Report the URL.

## Boundaries

- Never weaken tests, suppress errors or exclude files to get a PR green.
- Keep one logical outcome per PR. Split unrelated work instead of hiding it in
  a long description.
- Add attribution trailers only as the harness or user instructs.
