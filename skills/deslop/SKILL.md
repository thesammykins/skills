---
name: deslop
description: "Diagnose and remove AI writing tells from social posts, email, chat, marketing copy, articles, documentation, business writing, scripts, speeches, and other prose while preserving facts, intent, voice, and format. Use when a user says deslop this, clean this up, make this sound human, does this sound like AI, diagnose the writing, or asks for an anti-pattern review."
title: "Deslop"
created_by: "Ryan"
created_at: 2026-08-12
last_updated_by: "Ryan"
last_updated_at: 2026-08-17
content_type: reference
summary: "Diagnoses and removes AI writing tells across social, conversational, marketing, editorial, technical, business, creative, academic, and regulated prose while preserving facts, intent, voice, and format."
status: active
last_reviewed_at: 2026-08-17
source_review: Imported from the provided archive; local paths adapted for this Mac.
review_cycle_days: 90
---

# Deslop

Remove AI writing tells from prose without sanding away the writer. This skill works across social posts, email, chat, ads, landing pages, product copy, articles, newsletters, documentation, reports, briefs, proposals, memos, scripts, speeches, resumes, applications, and other user-authored writing.

This is an editorial cleanup skill. It does not fact-check, perform legal review, build a full voice profile, or clean code. Use a specialized skill when the user asks for one of those jobs.

Slop makes writing less specific and more exaggerated at the same time. A concrete detail gets smoothed into a generic important-sounding claim. Every fix has two halves: remove the construction, then restore the specific detail it displaced. A cleaned draft that is only shorter and blander has done half the job.

## Required references

On every invocation, read `/Users/sammykins/.agents/skills/deslop/references/patterns.md` before diagnosing or editing. For edit and silent modes, also read `/Users/sammykins/.agents/skills/deslop/references/eval.md` and apply it to the cleaned draft before responding. These bundled files are authoritative for this skill. Do not search other spaces for alternate rule files.

## Modes

- **Default:** receipts then rewrite. Report every distinct hit, then return the full cleaned version.
- **Diagnose:** when the user says "just flag it," "diagnose," or equivalent, report findings without rewriting.
- **Silent:** when the user says "just clean it," "rewrite only," or equivalent, return only the cleaned version in one fenced code block.

If the user asks for a narrower action, such as "remove only AI tells" or "change only the opener," obey that scope exactly.

## Build the scan surface

Scan only prose the user wants evaluated.

Exclude these surfaces unless the user explicitly asks to rewrite them:

1. Fenced code blocks, inline code, commands, configuration, formulas, and URLs.
2. Blockquotes, quotations, testimonials, cited excerpts, transcripts attributed to another speaker, and legally required language.
3. Product names, trademarks, approved terminology, placeholders, merge fields, and text the user marks as locked.
4. Data tables and reference lists, except surrounding explanatory prose.

If excluded text contains a hardban, do not silently alter the source. Flag it outside the cleaned draft when the user needs to know.

## Preserve before editing

Create an internal preservation map with:

- The core claim or requested outcome.
- Every fact, number, date, name, quote, source, mechanism, link, and opinion.
- Three to five voice signals, such as vocabulary, cadence, bluntness, warmth, humor, uncertainty, formality, or deliberate roughness.
- Required structure, length, channel limits, calls to action, headings, and locked text.

Preserve 80 to 95 percent of a user-supplied draft unless clarity, factual integrity, or the user's requested scope requires more change. Prefer deletion and sentence-level repair over a full ghostwrite.

If the user supplies a sample of their own writing, read it before editing. Match its sentence lengths, vocabulary, paragraph openings, punctuation habits, and recurring phrases instead of applying default polish. A sample outranks this skill's stylistic defaults. It does not override hardbans, factual integrity, locked language, or the no-fabrication rule.

## Infer the writing type

Use the user's label first. Otherwise infer from structure and purpose. Default to **general prose**, not LinkedIn.

| Writing type | Common cues | Editing posture |
|---|---|---|
| Social post or caption | Platform named, short paragraphs, hook, engagement prompt | Protect platform length, voice, and intentional line breaks. Apply hook and engagement-bait checks. |
| Short message or chat | Slack, Teams, text, DM, conversational fragments, emoji | Preserve warmth, contractions, shorthand, fragments, and occasional emoji. Do not impose article polish. |
| Email | Subject, greeting, signoff, recipient-specific request | Preserve relationship cues and the requested action. Remove throat-clearing and passive asks. |
| Marketing or product copy | Headline, CTA, landing page, ad, lifecycle message, UI string | Protect product facts, approved claims, character limits, hierarchy, and conversion intent. Do not invent proof. |
| Article or newsletter | Title, sections, sustained argument, byline | Preserve narrative logic, evidence, and useful transitions. Remove formulaic framing and recap padding. |
| Technical or instructional writing | Procedures, requirements, API or product terminology, numbered steps | Prioritize precision and scannability. Do not replace exact terms for variety or remove necessary repetition. |
| Business writing | Brief, memo, report, proposal, strategy, update, meeting notes | Preserve decisions, owners, dates, risks, and evidence. Remove corporate fog without making the tone casual. |
| Script or speech | Spoken cadence, stage directions, beats, audience cues | Read for breath and delivery. Preserve deliberate repetition, callbacks, and fragments when they work aloud. |
| Resume, application, or bio | Roles, dates, achievements, first-person narrative | Protect verifiable claims and required format. Replace inflated adjectives with evidence. |
| Creative or personal writing | Scene, dialogue, memoir, humor, fiction, poetry | Treat repetition, fragments, metaphor, and unusual syntax as intentional unless they match a clear stock AI construction. |
| Regulated, legal, policy, or compliance text | Required clauses, policy terms, disclosures, formal approvals | Default to diagnose-only for locked language. Never change legal meaning, obligations, defined terms, or approved claims. |
| Academic or research writing | Citations, methods, results, limitations, evidence-based hedging | Preserve disciplinary terminology, uncertainty, and the distinction between correlation and causation. Remove ornament without overstating findings. |

Read the format-specific section in the pattern library before rewriting. Format rules change sensitivity, but they never permit fabricated facts or unapproved claims.

## Mandatory scan order

1. **Hardban scan:** Find Unicode code points `\u2014` and `\u2013`, plus the smart typography listed in the pattern library. Rewrite authored prose to remove them. Represent a banned character in a findings quote by its code point name so the report does not reintroduce it.
2. **Deterministic pattern scan:** Apply every expression and explicit count rule in the pattern library to the scan surface. Treat expressions as guidance if no regex engine is available.
3. **Manual pattern scan:** Read for every named family in the mandatory checklist below. Do not rely on keyword matching alone.
4. **Format scan:** Apply the inferred writing type's rules and constraints.
5. **Rewrite:** Fix every reported construction in the full draft. Fold fragments and stacks into finished prose instead of merely suggesting alternatives.
6. **Evaluation:** Apply the evaluation contract to the cleaned draft. Fix failures once, then re-check the failed items.
7. **Final gates:** Apply the final acceptance gates to the full response.

## Mandatory anti-pattern checklist

Do not skip a family because another family already produced a hit. Count one distinct construction once, then assign the most useful primary label.

Two tiers apply. Fix-on-sight patterns include hardbans, chatbot artifacts, fabricated detail and other factual-integrity failures, contrastive negation, detached narration and payoff announcers, filler transitions, applause-sign closers, and inline-header lists. Judgment patterns include colon reveals, isolated three-item lists, repetition, fragments, formal register, false agency, adverb piles, lazy extremes, aphorism formulas, and rhythm. Unsupported claims are fix-on-sight only when they are presented as precise, causal, superlative, or proof-framed facts without support. Put fix-on-sight findings first in the report.

### Hardbans

- Em dash and en dash characters.
- Curly single quotes, curly double quotes, and the single-character ellipsis.

### AI writing tells

- Repetitive short structures, short-sentence stacks, fragment triplets, pronoun tricolons, and adjective-noun stacks.
- One-sentence-per-line formatting used as the default rhythm.
- Fake-casual lowercase runs.
- Filler transitions, narration openers, bridge sentences, announce-then-show framing, payoff announcers, reader-directed self-reference, and meta commentary about what comes next.
- Noun-heavy prose, copula avoidance, passive corporate phrasing, formal-register inflation, buzzword clusters, cringe verbs, and synonym cycling.
- Emotional escalation, significance inflation, evaluative qualifiers, applause-sign closers, and unsupported superlatives.
- Present-participle label analysis, false ranges, vague attribution, fabricated numbers, false precision, unsupported causal claims, and claims without checkable proof.
- Inline-header lists, decorative formatting, excessive headings, and formatting that manufactures importance.
- Stacked negation reveals, contrastive negation, colon-punctuated contrasts, and performative contrarian framing.
- Rhetorical question-and-answer pairs, generic engagement questions, and answer fragments.
- "10x" bait, insider framing, faux-insight setups, "let that sink in," and self-grading claims.
- Colon reveals that manufacture drama.
- Summary-recap endings, repeated conclusions, fake-profound kickers, and bookend negation.
- Specific-fact smoothing that replaces evidence with generic importance language.
- Hedge stacks and contradictory certainty.
- Chatbot and reasoning artifacts: "I hope this helps," "Certainly," "Would you like me to," "Let me know if," "Let me think," "Step 1," and "Breaking this down" left in the deliverable as correspondence or hidden-reasoning scaffolding. Delete the scaffolding; keep only the answer and evidence. Preserve "Step 1" when the requested format is genuinely procedural.
- False agency: inanimate subjects given human verbs, such as "the decision emerges," "the culture shifts," "the data tells us," or "the market rewards." When the construction obscures responsibility or mechanism, name the known actor or state the observable change without inventing one.
- Metronomic rhythm: most sentences landing at nearly the same length, with uniformly sized paragraphs. This is distinct from a short-sentence stack. Vary rhythm only where it preserves the writer's actual voice.
- Speculative gap-filling: a paragraph about missing information followed by plausible invented detail, plus knowledge-cutoff disclaimers left in a draft. Cut the speculation, preserve uncertainty, or use `[NEED: source]`.
- Lazy extremes: every, always, never, everyone, and nobody used to fake authority instead of stating the real scope.
- Adverb piles: really, just, literally, genuinely, actually, simply, and truly when they add no meaning. Cut them, then reread the claim.
- Aphorism formulas: "X is the Y of Z," "the currency of," and "the architecture of." Replace a pull-quote-shaped abstraction with the concrete claim.
- Forced rule of three: a third item added for rhythm rather than accuracy.

Do not calculate burstiness, type-token ratio, trigram repetition, or a numeric slop score. Those require a deterministic scanner and calibrated baselines. Estimating them here creates fake precision.

### Formulaic hooks and promotion patterns

- "Here's what I learned" hooks with no tension or evidence.
- Numbered listicle promises that overclaim transformation.
- "Most people think" contrarian templates.
- "I used to think" journey bait without a real turn.
- "Unpopular opinion," "Stop doing X," and "The secret is" formulas.
- Time-jump hooks that fail to deliver a specific payoff.
- Repeated headlines, serial promotions with the same lead, generic comment bait, and fake scarcity.

### Voice and integrity failures

- Flattening humor, edge, uncertainty, warmth, swearing, dialect, or deliberate roughness.
- Replacing exact terminology merely to vary wording.
- Turning connected clauses into staccato statements for punch.
- Taste-only punctuation changes that do not fix a named problem.
- Adding facts, examples, names, numbers, quotes, sources, opinions, certainty, or claims.
- Changing the strength, scope, causality, or legal meaning of a statement.
- Making every format sound like polished LinkedIn copy.

## Not evidence

These do not indicate AI writing on their own. Except for the separate hardban and factual-integrity rules, do not report them, and do not edit around them.

- Perfect grammar, consistent style, or clean structure. Polish is not a tell.
- Formal or unusual vocabulary that is not in a named pattern. Do not flatten a word only because it sounds brainy.
- One transition word, short emphatic sentence, colon, three-item list, curly quote, or em dash. Hardbanned typography must still be replaced, but its presence alone is not evidence of AI writing.
- Mixed casual and formal register. This is common in technical writers and ordinary human drafts.
- Unsourced claims in informal writing, unless they independently meet a named factual-integrity pattern.
- A watched phrase that is quoted, named, or discussed rather than used.
- Dry or plain prose with no named pattern present.

Judgment-tier patterns need corroboration. Report one when it carries no content on its own, or when it clusters with related tells.

## Preserve these

Leave these alone. Aggressive edits remove them first, and they often make writing recognizably human.

- Specific, odd, hard-to-fabricate detail: a real number, name, mechanism, or quote.
- Mixed feelings, unresolved tension, and admitted uncertainty.
- Dated references, in-jokes, slang, and deliberate roughness.
- First-person editorial choices the writer can defend.
- Genuine asides, parentheticals, self-corrections, and uneven rhythm.

## Rewrite rules

- Fix means fold, cut, or state directly. Do not annotate a problem while leaving it in the cleaned version.
- Preserve strong human sentences unless they contain a named pattern.
- Protect every concrete detail. If proof is missing, delete the unsupported claim, keep the user's uncertainty, or insert a clear placeholder such as `[NEED: source]`.
- Do not swap commas for periods, or periods for commas, only to make prose punchier.
- Preserve intentional repetition in speeches, creative work, instructional steps, and short messages when it serves function rather than formula.
- Delete a fake-profound ending when the preceding concrete sentence already closes the piece. Do not replace it with another metaphor.
- A rewrite fails if it introduces another member of the same family it removed.
- Do not broaden the task into fact-checking, voice imitation, strategy, SEO, legal review, or code cleanup unless the user asks.

## Final acceptance gates

An edit or silent response is ready only when all are true:

1. The point, audience, requested action, format, and recognizable voice remain intact.
2. Facts, evidence, names, numbers, dates, links, claims, and locked text are unchanged unless the user authorized a change.
3. Every reported pattern is fixed in the cleaned draft.
4. The rewrite introduces no new member of a fixed pattern family.
5. The full response passes the hardban literal scan.
6. Channel limits, structure, required sections, and formatting constraints are satisfied.
7. The response obeys the selected mode exactly.
8. No taste-only or adjacent edits slipped in.

Never label a draft clean when an acceptance gate fails.

## Output contracts

If the scan produces no hits, do not edit the draft or promote a judgment-tier observation to fill the report. In Default mode, report zero hits and return the unchanged draft. In Diagnose mode, report zero hits with an empty findings list. In Silent mode, return only the unchanged draft in one fenced code block. Zero hits are valid and expected.

### Default

1. `## Deslop Report`
2. `**Hits:**` [N] patterns across [M] categories
3. `### Findings` with numbered items containing: **Pattern name**, location, short quote or code point label, fix, and category.
4. `### Cleaned Version` with the full rewritten prose in one fenced code block.
5. `**What changed:**` one or two factual sentences.

Count hits by distinct construction, not by paragraph. One bookend construction is one hit.

### Diagnose

Return the report and findings only. Do not rewrite or score the draft.

### Silent

Return only the cleaned version in one fenced code block. Do not add a heading, explanation, score, or findings list.
