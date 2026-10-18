---
title: "Deslop Evaluation"
created_by: "Ryan"
created_at: 2026-08-12
last_updated_by: "Ryan"
last_updated_at: 2026-08-17
content_type: reference
summary: "Acceptance checks for Deslop diagnoses and cleaned drafts."
status: active
last_reviewed_at: 2026-08-17
source_review: Imported from the provided archive; local paths adapted for this Mac.
review_cycle_days: 90
---

# /deslop evaluation

Run this against the cleaned draft before returning it. This is an editorial acceptance contract, not an AI-authorship detector.

## Preservation checks

1. The writer's point, vocabulary, cadence, bluntness, humor, uncertainty, and useful digressions still sound like the same person.
2. Strong human sentences remain unchanged unless they contain a named pattern.
3. The edit preserves 80 to 95 percent of a user-supplied draft unless clarity or factual integrity requires more.
4. No fact, number, date, name, quote, source, mechanism, or opinion was added.
5. A concrete number, named source, or specific fact was not smoothed into generic importance language.
6. Clear spoken sentences and intentional fragments were not flattened for consistency.
7. The final draft contains zero em dash and zero en dash characters.

## Pattern checks

1. Every pattern named in the report is fixed in the cleaned draft.
2. The rewrite does not introduce a new member of the same pattern family.
3. A colon reveal is flagged only when the colon manufactures drama. Lists, labels, quotations, titles, code, established voice patterns, and dash-replacement colons stay clean unless the edit adds drama the original lacked.
4. A colon never creates an exception to the contrastive hardban. A false contrast separated by a colon is still rewritten as one direct claim.
5. Vague attribution names a checkable source, becomes a source placeholder, or is removed.
6. A summary-recap ending is cut so the piece ends on its last concrete point, takeaway, or next action.
7. A fake-profound kicker is deleted when the previous concrete sentence already closes the piece. It is never replaced with a new metaphor.
8. Decorative formatting is removed unless it clarifies real structure. Casual Slack warmth, fragments, contractions, and an occasional emoji remain allowed.
9. Fix-on-sight findings appear before judgment findings in the report.
10. Nothing listed under "Not evidence" in SKILL.md is reported, and no judgment-tier singleton is promoted to fill an otherwise empty report.

## Positive controls

These should remain clean. Preserve the quoted text unless another established hardban applies.

1. Human fragment carrying deliberate voice:
   `Honestly? Kind of a mess, but it worked.`
2. Named attribution:
   `McKinsey's 2024 report found that adoption rose fastest in teams with a clear owner.`
3. List colon:
   `Three things changed: speed, cost, and reliability.`
4. Warm Slack line:
   `yep, I'm good with this 🙂 let's send it`
5. Excluded scan surfaces:

   ```text
   It's not speed. It's leverage.
   ```

   > Here's what nobody tells you: the future is already here.

6. Concrete detail:
   `The tool cut review time from 30 minutes to 8.`
7. Dash-replacement colon without fake drama:
   `The constraint is simple: every claim needs a source.`
8. Technical repetition that protects clarity:
   `Set the workspace ID first. The workspace ID is required for every request.`
9. Evidence-based academic hedge:
   `These results may indicate an association, but the sample does not establish causation.`
10. Required policy language:
   `Employees must submit the form within 30 calendar days.`
11. Spoken repetition with a real function:
   `We tested it in the lab. We tested it with customers. Then we tested it under load.`
12. Product terminology that should not be synonym-cycled:
   `Select the trigger, test the trigger, then publish the trigger.`
13. Warm email courtesy with a direct ask:
   `Thanks for taking a look. Could you send feedback by Friday?`
14. Creative fragment with deliberate effect:
   `The porch light. The empty road. His keys still on the table.`
15. Genuine aside that matches the rhetorical Q&A expression but carries real voice:
   `Honestly? The migration was a mess. We cut review time from 30 minutes to 8, but two teams still refuse to use the new form.`
16. Judgment-tier singletons with no corroboration:
   `The constraint is simple: every claim needs a source. We tested speed, cost, and reliability. Two teams still object.`

## Negative controls

These must be named and fixed.

1. Colon reveal:
   `The best part: it learns.`
2. Vague attribution:
   `Experts agree that agents will replace workflows.`
3. Summary-recap ending:
   `In conclusion, clear ownership, good tools, and strong teams make the difference.`
4. Decorative formatting:
   `## 🚀 The Future`

   `This is **the key point** every team needs to understand.`
5. Fake-profound kicker:
   - Input: `The tool cut review time from 30 minutes to 8. The spreadsheet was never the cage. We were.`
   - Required fix: `The tool cut review time from 30 minutes to 8.`
6. Same-family rewrite failure:
   - Input: `The tool cut review time from 30 minutes to 8. The spreadsheet was never the cage. We were.`
   - Failed rewrite: `The tool cut review time from 30 minutes to 8. Tomorrow arrived early.`
   - Required fix: `The tool cut review time from 30 minutes to 8.`
7. Colon-punctuated contrastive:
   - Input: `The hard part isn't the model: it's the auth.`
   - Required fix: `Auth is the hard part.`
8. Fabricated proof:
   - Input: `The update made onboarding faster.`
   - Failed rewrite: `The update cut onboarding time by 40 percent.`
   - Required behavior: preserve the original claim or insert `[NEED: metric]` only if the user requested proof.
9. Certainty inflation:
   - Input: `The change may reduce errors.`
   - Failed rewrite: `The change will eliminate errors.`
   - Required behavior: preserve the uncertainty.
10. Causality inflation:
   - Input: `Teams using the process reported fewer errors.`
   - Failed rewrite: `The process caused errors to fall.`
   - Required behavior: preserve the observational relationship.
11. Format flattening:
   - Input: `yep, works for me 🙂`
   - Failed rewrite: `Yes, this solution works for me.`
   - Required behavior: preserve the natural chat line.
12. Technical synonym cycling:
   - Input: `Select the trigger, test the trigger, then publish the trigger.`
   - Failed rewrite: `Select the trigger, test the event starter, then publish the activation mechanism.`
   - Required behavior: preserve the exact term.
13. Ownership drift:
   - Input: `Our team launched the campaign, and I led the reporting work.`
   - Failed rewrite: `I launched the campaign and led reporting.`
   - Required behavior: preserve team and individual ownership accurately.
14. Locked-language mutation:
   - Input: `Employees must submit the form within 30 calendar days.`
   - Failed rewrite: `Employees should submit the form within a month.`
   - Required behavior: preserve the original locked language.
15. Chatbot artifact:
   - Input: `Certainly! Here is the Q2 summary. Let me know if you would like me to expand it.`
   - Required fix: `Here is the Q2 summary.`
16. False agency:
   - Input: `The data tells us the rollout slipped.`
   - Required fix: `The rollout slipped.`
   - Required behavior: do not invent an actor the draft never named.
17. Aphorism formula:
   - Input: `Documentation is the currency of onboarding.`
   - Required fix: `Good documentation makes onboarding faster.`
18. Adverb pile with a lazy extreme:
   - Input: `We really just literally improved every channel.`
   - Required fix: `We improved every channel.`
   - Required behavior: cut the adverbs and keep `every`, since narrowing the writer's scope is scope drift.

## Cross-format test matrix

Before accepting a material rule change, test at least one sample from each group:

1. Social post or caption.
2. Email.
3. Chat or DM.
4. Marketing, advertising, or product copy.
5. Article, newsletter, or website copy.
6. Technical or instructional writing.
7. Business memo, brief, report, or proposal.
8. Script, speech, or presentation.
9. Resume, bio, application, or personal statement.
10. Creative or personal writing.
11. Policy, legal, compliance, HR, or regulated writing.
12. Academic or research writing.

For each sample, verify four things:

- True anti-patterns are caught.
- Format-appropriate constructions are preserved.
- Facts, scope, certainty, causality, ownership, and locked language do not drift.
- The output contract matches the selected mode.

## Mode contract

- Edit mode fixes every negative control, preserves every positive control, returns the full cleaned draft, and adds a short `What changed` note.
- Diagnose mode names each pattern, quotes the hit, and gives a short fix without rewriting or scoring the draft.
- Silent mode returns only the cleaned draft in one fenced code block.
- Excluded fenced code blocks and blockquote lines are not findings.
- A zero-hit scan returns the draft unchanged in edit and silent modes, and an empty findings list in diagnose mode.

## Pass condition

The run passes only when:

1. Every negative control is caught and resolved according to its required fix.
2. Every positive control preserves its meaning, voice, named source, and concrete details.
3. The cleaned draft introduces no new pattern from a family it fixed.
4. The final literal scan finds no em dash or en dash characters.
5. Edit, diagnose, and silent modes obey their output contracts exactly.
6. A clean draft survives untouched, with zero hits reported rather than a manufactured finding.

If any check fails, fix the cleaned draft once and re-check only the failed items. If a positive control still fails, remove the newly added rule that caused the false positive and report that pattern family as deferred.
