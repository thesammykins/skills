---
title: "Deslop Pattern Library"
created_by: "Ryan"
created_at: 2026-08-12
last_updated_by: "Ryan"
last_updated_at: 2026-08-17
content_type: reference
summary: "Pattern definitions and format-specific checks used by the Deslop skill."
status: active
last_reviewed_at: 2026-08-17
source_review: Imported from the provided archive; local paths adapted for this Mac.
review_cycle_days: 90
---

# /deslop pattern library

This bundled file is the authoritative pattern library for the company Deslop skill. It is self-contained and must be read on every invocation.

**last_reviewed:** 2026-08-17. The library combines deterministic expressions with context-sensitive editorial checks. Expressions help surface candidates; the manual read-through decides whether a construction is actually a problem in its format.

---

## Deterministic pattern expressions

Apply these expressions and count rules to the **scan surface** defined in SKILL.md. If a regex-capable tool is available, it may automate this pass. Otherwise, use the expressions as precise pattern descriptions during the manual read-through. Keep this as bullets, not a markdown table because several expressions contain pipe characters.

**Styled-unicode preprocessing (added 2026-08-04):** fold mathematical alphanumeric, enclosed, and fullwidth letterforms back to ASCII before scanning. Fake-bold text of the form used as inline headers on LinkedIn is invisible to every regex below; the Aug 4 published audit found a bridge phrase hiding inside it. When the available tools support targeted normalization, fold those styled letterforms before scanning. Do not use blanket NFKC because it rewrites the U+2026 ellipsis into three periods and would defeat the smart-typography rule.

**Coverage rule:** deterministic matches are candidates, not automatic verdicts, except for hardbans. Complete the manual scan even when this pass returns no hits.

- **Em dash + en dash** (HOT-LIST 1, `~/AGENTS.md`): `[\u2014\u2013]`
- **Contrastive, state form** (HOT-LIST 2a): `(?i)\b(is|are|was|were)n'?t\b[^.,]{1,80}[.,]\s*(it'?s|it was|they'?re|you'?re|that'?s|we'?re)\b`
- **Contrastive, bare-not form** (HOT-LIST 2b): `(?i)\b(it'?s|that'?s|this is|there'?s|you'?re|we'?re)\s+not\b[^.,]{1,80}[.,]?\s*(it'?s|they'?re|you'?re|that'?s|we'?re)\b`
- **Contrastive, possession form** (HOT-LIST 2c): `(?i)\b(you|we|they|i)\s+(do|does|did)n'?t (have|need|get|want)\b[^.,]{1,80}[.,]\s*(you|we|they|i)\s+(have|need|get|want|do)\b`
- **Contrastive, verb-negation form** (HOT-LIST 2d): `(?i)\b(it|that|this|they|you|we)\s+(do|does|did)n['\u2019]?t\s+\w+[^.,]{0,40}[.,]\s*(it|that|this|they)['\u2019]?(s|re)?\s`
- **Contrastive, frame form** (HOT-LIST 2e): `(?i)\b(on paper|in theory)\b[^.]{0,80}[.,]\s*(in practice|in reality|in fact)\b`
- **Hedge stacks** (HOT-LIST 3): `\b(might|maybe|perhaps|possibly)\b[^.]*\b(might|maybe|perhaps|possibly)\b`
- **Fragment triplets (No X. No Y. No Z.)** (HOT-LIST 4): `(?i)\bNo\s+[A-Za-z]+\.\s+No\s+[A-Za-z]+\.\s+No\s+[A-Za-z]+\.`
- **Narration sentence openers** (HOT-LIST 5a): `^(Here'?s the thing|Look,|The truth is,|Listen,)`
- **Standalone bridge sentences** (HOT-LIST 5b): `^(Here'?s what I mean( by that)?|Let me explain|Stay with me|Hear me out|Look at (that|the) (list|chart|table|graph|paragraph|line) again|Go back and read)[.:]?\s*$`
- **Announce-then-show narration** (HOT-LIST 5c): `^Here'?s (what|why|how) (it|this|that)\b[^.!?]{0,40}[.:]\s*$`
- **Reader-directed self-reference** (HOT-LIST 5d): `(?i)\b(notice the pattern|look at what just happened( there)?|read (that|it|those) (again|one more time))\b\??`
- **Open-ended bridge phrases** (HOT-LIST 5e): `(?i)^(to be (blunt|honest|clear|fair)|real talk|let['\u2019]?s be (honest|real|clear)|truth be told|make no mistake)\b[^.!?\n]{0,20}[:.,]`
- **Unanchored payoff announcer** (HOT-LIST 5f): `(?i)\bhere['\u2019]?s (the|what|why|how|my|your)\s+\w+[^.!?\n]{0,50}([:.]|$)`
- **Buzzword cluster** (HOT-LIST 6): `\b(robust|leverage|synergize|empower|illuminate|streamline)\b`
- **Rhetorical Q&A, closed-set answers** (HOT-LIST 7a): `\?\s+(Yes|No|Nope|Yep|Exactly|Absolutely|Of course|Not really|Kind of|Sort of)[.,!]`
- **Rhetorical Q&A, any short answer** (HOT-LIST 7b): `\?\s+[A-Z][\w'\u2019-]*( [\w'\u2019-]+){0,4}[.!]`
- **Sycophantic openers** (HOT-LIST 8): `^(Great|Perfect|Excellent|Absolutely)[\.,!]`
- **Adjective-noun stacks (Real X. Real Y.)** (HOT-LIST 9): `(?i)\bReal\s+[A-Za-z]+\.\s+Real\s+[A-Za-z]+\.\s+Real\s+[A-Za-z]+\.`
- **All-caps emphasis words** (HOT-LIST 10, case-sensitive): `\b(ALL|FULL|EVERY|NEVER|ALWAYS|ENTIRE|EXACTLY|EVERYTHING|NOTHING|ACTUALLY|LITERALLY|ONLY|HUGE|ZERO)\b`
- **Self-grading "best internal X"** (HOT-LIST 11): `(?i)\bbest\s+internal\s+\w+`
- **Hedge stacks, two-word** (HOT-LIST 13): `(?i)\b(almost|nearly|virtually|pretty much|more or less)\s+(never|always|every|impossible|none|all|the only)\b`
- **Smart typography (curly quotes + ellipsis)** (HOT-LIST 12): `[\u2018\u2019\u201C\u201D\u2026]`
- **Copula avoidance (common)** (ANTI-PATTERNS): `(?i)\b(serves as|stands as|boasts\s+\d+)\b`
- **Short-sentence stacking** (C-20260519-03): three or more consecutive sentences under ~8 words with no clause connectors. Detect this by reading three or more sentences in a row that each end in a period, contain about eight words or fewer, and have no comma or semicolon. Example: `It changed everything. We moved fast. The team shipped.` Fix by connecting at least two with a dependent clause.

---

## 1. Hardbans

| Pattern | Example | Fix | Src |
|---------|---------|-----|-----|
| Em / en dash | See regex row | Semicolons, periods, colons; hyphens for compounds only | C-20260324-02 |
| Smart typography | Unicode U+201C U+201D U+2018 U+2019, and U+2026 ellipsis | Straight `"` and `'`; three periods for an ellipsis | ANTI-PATTERNS |

---

## 2. AI writing tells

| Tell | Example | Fix | Src |
|------|---------|-----|-----|
| Repetitive short-structure | Stacked "We're here." / tricolons / fragment triplets / "Real X. Real Y." | Keep strongest line; fold into one sentence | C-20260324-03 |
| Short-sentence stacking | 3+ consecutive short declaratives as default rhythm: "It changed everything. We moved fast. The team shipped." Distinct from intentional emphasis. | Connect at least two with a dependent clause; keep one short sentence per section for genuine emphasis, not as the base rhythm | C-20260519-03 |
| One-sentence-per-line formatting | Five or more consecutive blank-line-separated blocks containing one sentence each, usually under 20 words. | Combine related sentences into fuller paragraphs. Mobile readability does not need every thought isolated. | C-20260519-03 |
| All-lowercase as fake casual | Three or more consecutive sentences that start lowercase, excluding intentional lowercase product names. | Use normal sentence capitalization. Casual register comes from word choice and brevity. | C-20260505-02 |
| Filler transitions | "Let me be clear," "Here's the thing," "Worth saying out loud:," "Worth noting:" | Delete; start at the point. The "worth saying/noting" variant usually rides a closing line and announces significance the line has not earned. | ANTI-PATTERNS |
| Noun-heavy prose | "Implementation of our strategy for optimization" | Verbs + named actors | ANTI-PATTERNS |
| Emotional escalation | "incredibly proud," "blew my mind" | Show evidence first | ANTI-PATTERNS |
| Payoff announcer | "And here's why that matters" | Deliver payoff | ANTI-PATTERNS |
| Significance inflation | "pivotal moment in the evolution of..." | Specific fact | ANTI-PATTERNS |
| -ing label analysis | "symbolizing... reflecting... showcasing" | Cut or real analysis | ANTI-PATTERNS |
| False range | "from startups to Fortune 500" | Name real segments or cut | ANTI-PATTERNS |
| Synonym cycling | hero / protagonist / central figure | Pick one term | ANTI-PATTERNS |
| Filler phrases | "In order to," "due to the fact that" | "To," "because," or delete | ANTI-PATTERNS |
| Formal register | "professionals," "utilize," spelled-out small numbers | "pros," "use," digits | ANTI-PATTERNS |
| Inline-header lists | **Speed:** sentence. **Quality:** sentence. | Prose or real list | ANTI-PATTERNS |
| Stacked negation reveal | "Not X. Not Y. Z." | One direct sentence | C-20260223-01 |
| 10x bait | "10x your workflow" | Measurable outcome or delete | ANTI-PATTERNS |
| Let that sink in | Standalone after a stat | Delete | ANTI-PATTERNS |
| Insider framing | "what nobody's talking about" | State claim | ANTI-PATTERNS |
| Cringe verbs | supercharge, unlock, future-proof | Specific verb + outcome | ANTI-PATTERNS |
| Rhetorical Q&A + fragment | "Working? Absolutely." | Declarative | C-20260403-01 |
| Hedge stacks | "almost never," "quite often" | One word | C-20260312-02 |
| Narration sentences | "That's what leadership means." | Delete if no new fact | C-20260312-09 |
| Generic question closer | "What surprised you?" | Substance close or specific question | C-20260312-09 |
| Bookend-as-negation | Close repeats open with a negation turn | Direct statement or cut | C-20260312-09 |
| Fabricated numbers | Invented stats to satisfy "numbers-forward" | `[NEED: source]` or ask | C-20260316-01 |
| Faux-insight setup | "The part everyone misses..." / "What nobody tells you..." | Delete the setup; state the claim | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Colon reveal | "The best part: it learns." | Rewrite as a plain sentence when the colon manufactures drama. Lists, labels, quotations, titles, code, established voice patterns, and a colon introduced to replace a banned dash are clean unless the edit invents drama the original lacked. The contrastive hardban still wins when a colon separates the false contrast. | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Vague attribution | "Experts agree..." / "Studies show..." with no named, checkable source | Name the source, cut the claim, or add `[NEED: source]` | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Summary-recap ending | "In conclusion..." / "Ultimately..." followed by a restatement | End on the last concrete point, takeaway, or next action | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Fake-profound kicker | Final cute metaphor, aphorism, or mic-drop line that restates the point | Delete it when the prior concrete sentence already closes the piece. Never replace it with a shinier metaphor. | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Specific fact smoothing | Replacing a number, date, named source, or mechanism with "significant impact" | Protect the specific fact; remove only the inflated wrapper | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Decorative formatting | Emoji headings, scattered bold emphasis, or a heading over two sentences | Keep formatting only when it clarifies real structure | Peter Yang no-ai-slop, Tier B, Aug 4 2026 |
| Chatbot artifact | "Certainly!" / "I hope this helps" / "Let me know if" / "Breaking this down" left in the deliverable | Delete the correspondence or reasoning scaffolding and keep the answer. Keep "Step 1" when the format is genuinely procedural | Deslop brief, Aug 17 2026 |
| False agency | "the data tells us," "the culture shifts," "the market rewards" | Name the known actor or state the observable change. Do not invent an actor | Deslop brief, Aug 17 2026 |
| Metronomic rhythm | Most sentences landing at nearly the same length with uniformly sized paragraphs | Vary rhythm only where it preserves the writer's voice. Distinct from short-sentence stacking | Deslop brief, Aug 17 2026 |
| Speculative gap-filling | A missing-information paragraph followed by invented detail, or a knowledge-cutoff disclaimer left in a draft | Cut the speculation, keep the uncertainty, or add `[NEED: source]` | Deslop brief, Aug 17 2026 |
| Lazy extremes | every, always, never, everyone, nobody used to fake authority | State the real scope. Keep the word when it is the writer's accurate claim, since narrowing it is scope drift | Deslop brief, Aug 17 2026 |
| Adverb pile | really, just, literally, genuinely, actually, simply, truly with no added meaning | Cut them, then reread the claim | Deslop brief, Aug 17 2026 |
| Aphorism formula | "X is the Y of Z," "the currency of," "the architecture of" | State the concrete claim instead of the pull-quote abstraction | Deslop brief, Aug 17 2026 |
| Forced rule of three | A third item added for rhythm rather than accuracy | Cut the filler item or replace it with the accurate one | Deslop brief, Aug 17 2026 |

---

## 3. Corporate voice

| Pattern | Example | Fix | Src |
|---------|---------|-----|-----|
| Rhetorical negation | Contrastive negation sentence pair | State the point directly | C-20260223-01 |
| Evaluative qualifiers | game-changing, truly transformative | Delete or prove | ANTI-PATTERNS |
| Hedge phrases | "I think," "I believe" (bylined thought leadership) | State it | ANTI-PATTERNS |
| Buzzword density | robust, synergy, leverage | Concrete nouns/verbs | ANTI-PATTERNS |
| Passive corporate | "It was decided that" | Name actor | ANTI-PATTERNS |
| Applause-sign closer | "The future is bright..." | Specific or stop | ANTI-PATTERNS |

---

## 4. Generic hook / opener formulas

Applies to **any** opening: post, email lede, landing hero, talk abstract.

| Template | Why it fails | Src |
|----------|--------------|-----|
| "Here's what I learned about X" | No tension | ANTI-PATTERNS |
| "N things about X that will change how you Y" | Listicle signal | ANTI-PATTERNS |
| "Most people think X. But actually Y." | Performative contrarian | ANTI-PATTERNS |
| "I used to think X. Then I realized Y." | Journey bait | ANTI-PATTERNS |
| "Unpopular opinion:" | Usually popular | ANTI-PATTERNS |
| "Stop doing X. Start doing Y." | Unearned commands | ANTI-PATTERNS |
| "The secret to X is Y." | Rarely pays off | ANTI-PATTERNS |
| "N years ago I... here's what happened" | Needs surprise payoff | ANTI-PATTERNS |
| Thread post repeats headline | Second post must add new fact | C-20260504-02 |
| Serial promos same lead | Rotate angle each time | C-20260504-02 |

**News-beat:** time-sensitive or named launch: name the event in the first ~10 words. See ANTI-PATTERNS "Missing the Forest" table for before/after examples.

---

## 5. Voice drift / structural (`~/AGENTS.md`)

| Pattern | Fix | Src |
|---------|-----|-----|
| Contrastive "It's not X, it's Y" | Direct statement | `~/AGENTS.md` |
| Fragment triplets / staccato stacks | Natural clauses | `~/AGENTS.md` |
| Adjective-noun stacks ("Real X. Real Y.") | One sentence | `~/AGENTS.md` |
| Rhetorical Q&A + fragment answer | Declarative | `~/AGENTS.md` |

---

## 6. Format-specific surface tells

Apply the general library first, then adjust sensitivity for the writing type. Hardbans and integrity rules always apply to authored prose.

### Social posts and captions

- Flag generic engagement questions, comment or DM bait, thread numbering used as decoration, fake scarcity, and platform cliches.
- Preserve intentional line breaks, platform-native brevity, locked hooks, and a specific call to action.
- Do not force every social post into a LinkedIn cadence. Short captions, community updates, and conversational replies can stay compact and informal.
- If the platform imposes a character limit, keep the rewrite within it or state the constraint.

### Email

- Flag "Sorry to bother," "Just checking in," "Per my previous," empty pleasantries, passive requests, and overlong context before the ask.
- Preserve greetings, signoffs, relationship cues, courtesy, and the exact requested action.
- Do not turn a warm note into a memo or remove context the recipient needs.

### Chat, DM, and text

- Preserve contractions, shorthand, lowercase starts, fragments, line breaks, and occasional emoji when they sound natural for the writer.
- Flag corporate stiffness, fake enthusiasm, multi-paragraph throat-clearing, and unnecessary recap.
- Do not apply article structure, formal transitions, or LinkedIn density to a one-to-one message.

### Marketing, advertising, lifecycle, and product copy

- Flag unsupported superlatives, fake urgency, vague benefits, empty transformation claims, invented proof, generic future language, and interchangeable buzzwords.
- Protect approved claims, product names, legal qualifiers, CTAs, message hierarchy, variants, and character limits.
- UI strings may require fragments and repeated terminology. Precision and consistency outrank stylistic variety.

### Articles, newsletters, blogs, and websites

- Flag SEO-title spam, fake authority, false ranges, inline-header AI layout, repeated conclusions, generic section openers, and recap padding.
- Preserve the argument, evidence, narrative sequence, citations, useful transitions, and publication register.
- Headings are allowed when they organize real sections. A heading over one or two sentences is usually decorative.

### Technical, instructional, and support writing

- Protect exact terminology, warnings, prerequisites, commands, ordered steps, API names, field labels, and repeated terms that prevent ambiguity.
- Flag unnecessary meta narration, inflated claims, and prose that obscures the procedure.
- Passive voice is acceptable when the actor is unknown or irrelevant. Repetition is acceptable when it improves safety or scannability.

### Business writing

- Protect decisions, owners, dates, metrics, risks, dependencies, status labels, and next actions.
- Flag passive ownership, noun piles, vague attribution, corporate fog, unsupported certainty, and conclusions that merely restate the document.
- Keep the register appropriate for the audience. Removing jargon does not require making an executive memo casual.

### Scripts, speeches, presentations, and spoken remarks

- Read aloud mentally. Preserve breath, callbacks, deliberate repetition, audience cues, and fragments that work in speech.
- Flag repetitive rhetorical scaffolding, fake applause lines, stacked reveals, and transitions that announce rather than advance the point.
- Slide titles and speaker notes serve different functions. Do not force either into article prose.

### Resumes, bios, applications, and personal statements

- Protect dates, role names, credentials, achievements, scope, and verifiable outcomes.
- Flag adjective stacks, unsupported leadership claims, generic passion language, inflated impact, and personal statements that could belong to anyone.
- Do not invent metrics or turn team outcomes into individual claims.

### Creative and personal writing

- Treat metaphor, unusual syntax, repetition, fragments, dialogue, dialect, ambiguity, and emotional intensity as potentially intentional.
- Flag only stock AI constructions, generic profundity, false specificity, or patterns that visibly weaken the requested effect.
- Do not standardize a creative voice or make every sentence conventionally complete.

### Policy, legal, compliance, HR, and regulated writing

- Treat defined terms, approved claims, disclosures, obligations, policy language, and quoted requirements as locked unless the user explicitly authorizes changes.
- Default to diagnosis for locked passages. Explain the writing concern without changing legal meaning.
- Never remove qualifiers, narrow or broaden obligations, increase certainty, or substitute a simpler term that changes scope.

### Academic and research writing

- Protect citations, discipline-specific terminology, hedging tied to evidence, limitations, methods, and distinctions between correlation and causation.
- Flag vague attribution, unsupported certainty, ornamental complexity, generic significance claims, and conclusions that outrun the evidence.
- Do not remove legitimate uncertainty merely because it resembles a hedge.

Broad words such as `foster`, `harness`, `realm`, `landscape`, `robust`, and `leverage` require context. A word is not a hit when it is the clearest accurate term. Flag the construction, not the vocabulary in isolation.

---

## 7. Cross-format integrity rules

These failures outrank style preferences in every format:

- **Fabrication:** adding a fact, number, quote, name, source, example, testimonial, credential, or result.
- **False precision:** changing a broad claim into a precise statistic, date, quantity, or guarantee without evidence.
- **Causality inflation:** turning association, sequence, or opinion into a causal claim.
- **Certainty inflation:** removing evidence-based uncertainty or converting a possibility into a promise.
- **Scope drift:** broadening or narrowing who, what, where, or when a statement covers.
- **Ownership drift:** assigning a team result to an individual or obscuring who owns an action.
- **Specific-fact smoothing:** replacing a concrete mechanism or result with generic importance language.
- **Meaning drift:** changing the writer's position while making the prose sound cleaner.
- **Format drift:** rewriting every surface into the same polished social-post voice.

---

## Maintenance notes

- Treat this bundled library as the source of truth for the company skill. Update it and the mandatory checklist in SKILL.md together.
- Test changes against positive controls, negative controls, mixed-format controls, and each output mode.
- Context-sensitive patterns such as colon reveals, attribution, conclusions, formatting, hedging, repetition, and fragments require a human read-through.
- When a new rule creates a false positive in a valid format, narrow the rule instead of flattening that format.
