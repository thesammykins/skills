---
name: happy-path-use-case-design
description: Design code around clear, typed happy-path use cases.
version: 0.1.0
author: Hona (Hona)
license: MIT
---

# Happy-Path Use-Case Design

Implement changes so the normal user flow dominates the reading experience.
Use established patterns only when they reduce total complexity; this is a
design discipline, not a mandate for architectural layers. Exactly like 
Luke Parker (Hona) would.

## When to Use

- Implementing or refactoring a feature with orchestration, domain rules, IO,
  or meaningful invariants.
- Reviewing code whose main flow is buried under mechanics, nesting, adapters,
  or speculative edge cases.
- Choosing whether a helper, service, port, repository, value object, or layer
  earns its cost.

Don't use for trivial one-line changes where the existing local pattern is
already obvious.

## References

- Read `references/design-vocabulary.md` when naming the design move or choosing
  among established patterns.
- Read `references/principles-and-examples.md` when the correct boundary or
  abstraction depth is unclear.
- Read `references/source-reading.md` for the original sources and deeper study.

## Procedure

1. **Trace the real flow.** Use `search_files` and `read_file` to inspect the
   entry point, every affected caller, data flow, tests, and nearby conventions.
   Completion: the actual use case and its existing boundaries are known.
2. **Write the happy path first.** Make the top-level operation read as a short,
   linear sequence of domain actions. Move parsing, protocols, process plumbing,
   and state surgery below narrow, intention-revealing boundaries only when
   they hide meaningful complexity. Completion: the normal flow is flat and
   visible without following mechanical details.
3. **Parse at trust boundaries.** Convert external, persisted, IPC, network, or
   user input into trusted domain values once. Use precise types, required
   parameters, discriminated states, constructors, or schemas to make illegal
   combinations hard or impossible to construct. Completion: internal code
   does not repeatedly validate loose input.
4. **Give behavior one owner.** Keep state and invariants together. Tell the
   owner to perform a domain operation rather than exposing state for callers
   to mutate. Keep domain decisions out of process, database, and network
   wrappers. Completion: each invariant has one clear enforcement point.
5. **Make patterns pay rent.** Count the interfaces, files, call hops,
   configuration, tests, and concepts introduced. Add an abstraction only when
   it hides real complexity, owns an invariant, supports real implementations,
   removes stable repetition, or isolates a proven boundary. Completion: no
   pass-through layer or speculative extension point remains.
6. **Keep failures proportional.** Use guards and fail-fast checks to remove
   invalid conditions before the normal flow. Handle observed operational
   failures; do not build machinery for hypothetical cases. Let errors reach
   the existing user-facing boundary unless recovery is a product requirement.
   Completion: defensive code does not obscure the valid path.
7. **Test stable behavior.** Add the smallest focused test at the use-case or
   other stable observable boundary. Prefer behavior and operation order over
   sentence-by-sentence helper tests. Completion: the check fails when the
   intended behavior breaks and passes through the real boundary.
8. **Simplify and verify.** Run the repository's focused checks, then remove
   stale compatibility paths, shallow helpers, duplicated validation, and
   temporary artifacts. Completion: the result is cohesive, typed, native to
   the repository, and no more complex than the observed problem requires.

## Decision Rules

- Start with a direct transaction script or vertical slice.
- Prefer guard clauses and a flat valid path over nested defensive branches.
- Prefer one deep operation over several shallow helpers.
- Prefer duplication over the wrong abstraction; extract after real examples
  reveal shared semantics.
- Change a poor internal interface rather than preserving it solely to avoid
  updating its callers.
- A pattern name describes a useful shape that emerged; it does not require
  manufacturing that shape.

## Pitfalls

- `Controller -> Service -> Repository` pass-through chains are cost, not proof
  of architecture.
- Screaming Architecture means domain and use cases are visible; it does not
  mean more layers.
- “Could”, “might”, and “what if” are not runtime evidence.
- Tiny helpers can reduce locality and force readers to reconstruct one action.
- Type wrappers that do not preserve validated knowledge merely rename strings.
- Do not simplify away trust-boundary validation, data-loss prevention,
  security controls, or explicit product requirements.

## Verification

- [ ] The main use case reads linearly and mostly in domain language.
- [ ] Invalid input becomes a trusted value at its boundary.
- [ ] State and invariants have one owner.
- [ ] IO mechanics do not contain domain decisions.
- [ ] Every introduced abstraction has a concrete current benefit.
- [ ] Common failures are clear; hypothetical failures do not dominate.
- [ ] A focused test proves observable behavior at a stable boundary.
- [ ] Repository checks pass and the final simplification pass is complete.
