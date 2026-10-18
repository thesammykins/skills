---
name: anti-ai-slop
description: "Before pushing, strip AI-generated slop from the unpushed work so only the minimal, idiomatic change remains."
---

## Intent

This skill reviews **work not yet pushed** and removes changes that are likely “AI slop”: unnecessary, non-idiomatic, or inconsistent additions that do not materially contribute to the intended feature/fix.

**Guiding principle:** keep the **smallest change that accomplishes the goal**, and match the **local conventions** of each touched file.

Agent-written commits are dominated by smells rather than outright bugs, and
the smells compound: the next agent copies whatever pattern it finds. Removing
them before push is cheaper than any later cleanup.

## Scope and diff source

Operate only on this task's changes that haven't been pushed.

Establish the user-authorized scope and the comparison point first. Work is
trunk-based by default, so the base is usually the upstream of the current
branch (`@{u}`, normally `origin/main`). On a feature branch use the branch's
real base. Use a requested base when supplied; never guess.

Inspect all of these, restricted to the task's paths:

1. `git status --short` to identify staged, unstaged, and untracked work.
2. `git diff <base>...HEAD` for committed but unpushed changes.
3. `git diff --cached` for staged changes.
4. `git diff` for unstaged changes.
5. Read relevant untracked source files explicitly; Git diffs omit them.

These views are complementary, not fallbacks. Compare the combined changes
with the current files before editing: a later change may already fix an earlier
hunk. For a narrower user-requested review, inspect only that scope. If the base
cannot be resolved, state the coverage limitation; do not claim full coverage.
Preserve unrelated user changes and existing staging. Do not stage, reset, or
rewrite Git state to make review easier.

Perform one cleanup pass per meaningful task diff. If `simplify` already covered
a criterion on unchanged hunks, reuse that review; inspect only uncovered criteria
or newly changed hunks. Do not alternate cleanup skills until nothing changes.

Do not refactor unrelated code outside the displayed diff hunks.

## Non-goals

- Do **not** redesign architecture, rename APIs, or move code unless required by the feature/fix in the diff.
- Do **not** remove meaningful domain comments that encode invariants, reasoning, constraints, or known pitfalls.
- Do **not** remove validation at genuine trust boundaries (I/O, parsing, network, user input, third-party callbacks).
- Do **not** change formatting rules; follow repository tooling and the file’s established style.

## What counts as AI slop

### A) Comment and documentation bloat

Remove comments/docstrings that merely narrate the code, restate names, or are inconsistent with the file’s comment density and tone.

**Python (before):**
```python
def clamp(x: float, lo: float, hi: float) -> float:
    # Ensure x is not less than lo and not greater than hi
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
```

**Python (after):**
```python
def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
```

### B) Unnecessary defensive checks inside trusted codepaths

Remove checks that are redundant because upstream validation/types/invariants already guarantee inputs.

**Rust (before):**
```rust
pub fn normalize_tag(tag: &str) -> String {
    if tag.is_empty() {
        return String::new();
    }
    tag.trim().to_ascii_lowercase()
}
```

If the rest of the codebase treats empty tags as impossible here (validated earlier), keep only the essential logic:

**Rust (after):**
```rust
pub fn normalize_tag(tag: &str) -> String {
    tag.trim().to_ascii_lowercase()
}
```

### C) Try/catch / try blocks that add no value

Remove wrappers that only rethrow, add inconsistent logging, or hide errors without providing recovery.

**C++ (before):**
```cpp
void SaveRow(Db& db, const Row& row) {
  try {
    db.Save(row);
  } catch (const std::exception& e) {
    std::cerr << "Error saving row: " << e.what() << std::endl;
    throw;
  }
}
```

If the repository does not use log-and-rethrow at this layer, prefer:

**C++ (after):**
```cpp
void SaveRow(Db& db, const Row& row) {
  db.Save(row);
}
```

### D) Single-use variables and one-off helpers that should be inlined

Prefer inlining when it improves clarity and matches surrounding style.

**Python (before):**
```python
clean = s.strip().lower()
return clean
```

**Python (after):**
```python
return s.strip().lower()
```

**Rust (before):**
```rust
let key = format!("{}:{}", user.id, user.region);
cache.insert(key, value);
```

If `key` is not reused and inlining remains readable:

**Rust (after):**
```rust
cache.insert(format!("{}:{}", user.id, user.region), value);
```

### E) Redundant checks/casts duplicated at caller and callee

If a caller guarantees an invariant, remove repeated checks in the callee unless the subsystem consistently enforces invariants at every boundary.

**Python (before):**
```python
def handle(req: Request) -> Response:
    user = parse_user(req)  # guarantees user.id is present
    return do_work(user)

def do_work(user: User) -> Response:
    assert user.id is not None
    return Response(user.id)
```

**Python (after):**
```python
def do_work(user: User) -> Response:
    return Response(user.id)
```

### F) Style drift and inconsistency with the file

Remove or rewrite changes that introduce new patterns inconsistent with the file or repository norms, such as:

- Adding type annotations in a Python file that otherwise does not use them.
- Introducing novel error-handling idioms in Rust (e.g., custom `Result` wrappers) where the module uses simple `anyhow::Result` (or vice versa).
- Adding complex abstractions (factories/providers/managers) for small local logic.

### G) Noisy logging and narration

Remove logs that restate the line of code, are inconsistent with the module’s logging level, or spam hot paths.

**Rust (before):**
```rust
log::info!("Starting normalization");
let out = normalize_tag(tag);
log::info!("Finished normalization");
out
```

**Rust (after):**
```rust
normalize_tag(tag)
```

(Keep logs that support production debugging when the module’s convention calls for them.)

### H) Placeholder TODOs without a ticket/reference

Remove “TODO: handle edge cases” style notes that add no actionable guidance and are not aligned with repository practices.

### I) Unicode hazards and emoji noise in code/comments

Remove suspicious or unnecessary Unicode in **code and configs**, including:

- non-breaking spaces (`U+00A0`)
- zero-width characters (`U+200B`, `U+200D`)
- “smart quotes” (`“ ” ‘ ’`) in code/config
- homoglyphs in identifiers
- emojis in code comments/docs unless the repository explicitly uses them

**Python (before):**
```python
# ✅ Done! 🚀
name = "ab​c"  # zero-width space
```

**Python (after):**
```python
name = "abc"
```

(Do not “sanitize” legitimate localized/user-facing content unless it appears to be accidental.)

### J) Silent fallbacks that hide failure

Remove defaults that turn an error into plausible-looking data: `try?` on calls
whose failure matters, `?? ""` / `?? 0` on values that must exist, empty
`catch {}`, `except Exception: pass`. Let the error surface the way the module
already handles errors.

**Swift (before):**
```swift
let schedule = (try? store.loadSchedule(for: day)) ?? Schedule.empty
```

**Swift (after), when the caller already throws:**
```swift
let schedule = try store.loadSchedule(for: day)
```

### K) Compatibility for things that never shipped

Remove fallbacks, "legacy" branches, migration shims, deprecated aliases and
feature flags for code that only ever existed in this unpushed work or that
nobody asked to keep. Real compatibility (released data formats, public APIs)
stays.

### L) Reinvented helpers

Before keeping a new helper, search for an existing one (`rg` for the verb and
the type). A second date formatter, retry loop or path builder beside an
existing one is slop even when it's correct. Call the existing one.

### M) Speculative abstraction

Remove a protocol with one conformer, a generic with one concrete use, an
options/config parameter no caller sets, or a manager/factory/provider wrapping
a few lines. Add the layer when a second use arrives.

**Swift (before):**
```swift
protocol ShiftFormatting { func label(for shift: Shift) -> String }
struct DefaultShiftFormatter: ShiftFormatting { ... }
```

**Swift (after):** a plain function or a method on `Shift`.

### N) Test slop

Remove or rewrite tests that:

- restate the implementation (same constants, same branches) instead of an
  independent expectation;
- only assert that a mock was called, or test the mock;
- freeze copy, layout constants or trivial getters;
- use sleeps or retries to pass.

Revert any weakened assertion, `skip`/`XCTSkip`, deleted test or loosened
tolerance added to turn a failure green, and fix the cause instead.

### O) Phantom, stale or unrequested dependencies

Check every new API call against the SDK or library version the project
actually uses. Agents produce plausible methods that don't exist and patterns
from older versions. Remove new packages the task didn't need, and check that
any you keep exist under that exact name (similar-sounding names are a supply
chain risk).

### P) Conversation-shaped comments

Remove comments that refer to the task or the session rather than the code:
`// Updated to fix the bug`, `// New implementation`, `// As requested`,
`// Step 1:`, `// Changed from X to Y`. History belongs in the commit message.

### Q) Stray artifacts

Remove files and lines the change doesn't need: `SUMMARY.md`,
`IMPLEMENTATION_NOTES.md`, ad-hoc scripts, test output, screenshots outside the
repo's evidence paths, debug `print`/`console.log`, and commented-out code.

### R) Concurrency noise (Swift)

Remove blanket `@MainActor` on types that don't touch UI, `Task { }` wrappers
around synchronous work, `async` on functions that never suspend,
`[weak self]` in non-escaping closures, and `@unchecked Sendable` or
`nonisolated(unsafe)` added only to silence a warning. Fix the isolation
instead, following the module's existing model.

Prose slop in docs, commit messages and PR text is out of scope here: use
`deslop`, and `creating-pull-requests` for PR bodies.

## Trust boundaries: when defensive checks are appropriate

Defensive checks are generally appropriate at **untrusted boundaries**, such as:

- request/CLI/env input handling
- parsing and decoding (JSON, CSV, protobuf, HTML, etc.)
- network/RPC boundaries
- filesystem reads/writes of external data
- third-party callbacks and plugin systems

Defensive checks are often slop within **trusted internal pipelines**, such as:

- post-validated domain objects
- post-auth/permission middleware
- post-schema validation
- internal-only transforms with strong invariants

When in doubt, follow existing patterns in the same module/subsystem.

## Workflow checklist

1. Establish scope and inspect each applicable Git state as described above.
2. For each changed hunk:
   - Determine the intended behavior change.
   - Remove additions that are not required to achieve it.
   - Align with local style (naming, typing, error strategy, comment density).
3. Remove unused imports, dead code, and redundant helper layers introduced by this work.
4. Keep changes minimal: avoid unrelated refactors.
5. Ensure changes still satisfy **AGENTS.md** (and other repo policies).
6. If repository tooling exists (formatters/linters/tests), avoid introducing new warnings.

## Final report

Report the concrete cleanup, checks run or reused, and any coverage limitations.
When invoked within a larger task, include this in that task's final handoff;
do not override its requested format or omit verification evidence. A short
summary is enough when there are no material details to add.
