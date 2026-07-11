# OpenAI Prompt Guidance Notes

Source: https://developers.openai.com/api/docs/guides/prompt-guidance
Accessed: 2026-04-30

## Core Transferable Guidance

- Prefer outcome-first prompts. Define the desired result, success criteria, constraints, available context, and final answer shape, then let the model choose an efficient path.
- Keep prompts short when the extra process detail does not change behavior. Avoid carrying old prompt stacks forward unchanged.
- Use absolute words such as "always", "never", "must", and "only" for real invariants, safety limits, and required output fields. Use decision rules for judgment calls.
- Define personality and collaboration style separately from task requirements when the prompt is for a customer-facing or conversational assistant.
- Use a short visible preamble for longer or tool-heavy workflows when the product surface benefits from progress updates.
- Specify output format, audience, tone, length, and structure. Preserve requested artifact type and length when rewriting or polishing.
- Add grounding rules for factual work: what needs support, what counts as sufficient evidence, how citations should appear, and what to do when evidence is missing.
- Add retrieval budgets so search stops once enough evidence exists and continues only for missing required facts, unresolved contradictions, exhaustive requests, or specific artifacts.
- For creative drafts, distinguish source-backed facts from creative wording. Do not invent names, metrics, roadmap claims, customer outcomes, or product capabilities.
- Ask the model to verify its work when validation is possible: tests for code, rendering inspection for visual artifacts, traceable implementation plans for engineering work.
- Add stop rules: when to answer, when to ask for missing information, when to retry, when to fallback, and when to abstain.
- Treat prompting as empirical. Re-run evals or realistic checks after meaningful prompt changes when the prompt is used in production or repeated workflows.

## Practical Conversion Heuristic

When converting a prompt, preserve the user's goal first, then add only the scaffolding needed for reliable execution:

1. Goal
2. Context and assumptions
3. Success criteria
4. Constraints and safety limits
5. Evidence/tool-use rules
6. Output format
7. Stop rules
8. Validation
