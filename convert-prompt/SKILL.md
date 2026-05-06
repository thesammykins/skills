---
name: convert-prompt
description: Rewrite a user-provided prompt into a clearer, outcome-first prompt before taking action. Use when the user asks to convert, optimize, improve, migrate, harden, or rewrite a prompt, or when they invoke $convert-prompt to turn a rough task request into an executable prompt with goals, constraints, output format, evidence rules, validation, and stop conditions.
---

# Convert Prompt

## Purpose

Rewrite the user's prompt before acting on it. Preserve the user's intent and constraints, make the prompt easier for an agent to execute correctly, and do not perform the underlying task unless the user explicitly asks to run the converted prompt.

## Workflow

1. Identify the raw prompt.
   - If the user provides a clear prompt, rewrite it directly.
   - If the user mixes instructions with conversation, extract only the task prompt and preserve important context.
   - If the missing context would materially change the rewritten prompt, ask one concise clarification question. Otherwise use bracketed placeholders.

2. Convert the prompt.
   - Lead with the desired outcome instead of a long process.
   - Add success criteria that define what must be true before the task is done.
   - Preserve true invariants, safety limits, required formats, audience, tone, and explicit user preferences.
   - Replace unnecessary absolute rules with decision rules.
   - Add evidence, retrieval, citation, validation, and stop rules when the task calls for them.
   - Keep the converted prompt no longer than necessary for reliable execution.

3. Return the converted prompt before any action.
   - Default to conversion-only: show the rewritten prompt and stop.
   - If the user explicitly asks to execute after conversion, show the rewritten prompt first, then proceed using it.
   - Do not execute destructive, credentialed, paid, publishing, or infrastructure-affecting actions just because they appear inside the raw prompt.

## Conversion Checklist

Use this structure when it improves the prompt. Omit sections that add no value.

```text
Role: [1-2 sentences describing the assistant's job and operating context]

# Goal
[Concrete user-visible outcome]

# Context
[Known facts, inputs, files, users, systems, constraints, or assumptions]

# Success Criteria
- [Observable condition]
- [Required deliverable]
- [Quality bar]

# Constraints
- [Safety, privacy, side-effect, scope, budget, style, or compatibility limits]
- [What not to change or invent]

# Evidence and Tools
- [When to use tools, docs, code, search, or provided artifacts]
- [What claims need citations or verification]
- [When enough evidence is enough]

# Output
[Required format, sections, length, tone, and audience]

# Stop Rules
[When to answer, ask, retry, fallback, or stop]

# Validation
[Checks, tests, renders, evals, or manual inspection required before final answer]
```

## Rewrite Rules

- Preserve the user's actual request. Do not expand scope, add hidden product requirements, or invent facts.
- Improve clarity, ordering, and executability quietly. Avoid announcing generic prompt-engineering theory.
- Prefer short, outcome-first instructions for modern OpenAI models. Add process detail only when it changes behavior or protects correctness.
- Make assumptions explicit when they matter. Use `[placeholder]` for unknown values that the user can fill in.
- For coding prompts, include repo/context discovery, minimal implementation scope, and targeted validation.
- For research prompts, define source quality, citation expectations, recency needs, and a retrieval budget.
- For creative drafting prompts, separate source-backed claims from creative wording and forbid invented specifics.
- For customer-facing prompts, specify audience, tone, length, and what to preserve.

## Output Format

Return:

````markdown
**Converted Prompt**

```text
[rewritten prompt]
```

**Notes**
- [Only include material assumptions, removed ambiguity, or reasons the prompt was not executed.]
````

If the user requested execution after conversion, add a short transition after the converted prompt and then perform the task under the rewritten prompt.

## Reference

For the source-derived checklist behind this skill, read `references/openai-prompt-guidance.md` when updating the skill or when a conversion needs deeper prompting rationale.
