# Design Vocabulary

Use these names to describe a design that earns its place, not as a checklist of patterns to install.

| Desired quality | Established terminology |
|---|---|
| Main method reads almost like English | Composed Method; intention-revealing interface; use-case orchestration |
| Orchestrator coordinates named operations | Application Service; Use Case Interactor; Transaction Script |
| Mechanics sit behind a small interface | Information hiding; deep module; complexity pulled downward |
| Domain decisions are separated from IO | Functional Core / Imperative Shell; Ports and Adapters |
| Structure reveals user behavior | Vertical Slice Architecture; use-case-driven architecture; Screaming Architecture |
| Types enforce legal states | Type-driven design; making illegal states unrepresentable |
| Boundary checks create trusted values | Parse, Don't Validate; smart constructors; refinement types |
| Contracts are executable | Design by Contract; preconditions; postconditions; invariants |
| Invalid conditions exit early | Guard clauses; fail-fast design |
| Imagined requirements create no code | YAGNI; evolutionary design; avoid speculative generality |
| Reuse follows real repetition | Rule of Three; semantic compression; AHA programming |
| A small interface hides substantial work | Deep rather than shallow modules |
| Related behavior stays discoverable | Locality of behavior |
| State and behavior share one owner | Encapsulation; Tell, Don't Ask; Information Expert |

## Selection Heuristic

Begin with a direct use-case implementation. Introduce one of these shapes only when it has a concrete present-tense benefit: it owns an invariant, hides meaningful mechanics, separates a trust or IO boundary, supports multiple real implementations, or compresses repetition whose semantics are now stable.
