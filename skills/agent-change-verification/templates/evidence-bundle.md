# Evidence Bundle Template

Copy only the sections justified by the change. Empty ceremony is not evidence.

```markdown
# Verification: <change>

Revision: <commit/SHA/artifact digest>
Environment: <local/CI/staging/production + material versions>
Verifier: <agent/person/tool distinct from implementer when applicable>

## Contract
- Outcome:
- Must not change:
- Acceptance criteria:
- Material invariants:

## Risk map
| Risk / blast radius | Failure signal | Verification | Result |
|---|---|---|---|
| | | | |

## Changed artifacts
| Artifact | Why changed | Identity/read-back |
|---|---|---|
| | | |

## Automated checks
| Command | Scope | Exit/result | Evidence path |
|---|---|---|---|
| | | | |

## Real-path demonstration
- Setup:
- Actions:
- Expected observable outcome:
- Actual outcome:
- Trace/video/screenshots/logs:

## Visual and motion evidence
- Recording path and digest:
- Capture method/environment/viewport/DPR:
- Duration, dimensions, measured FPS/frame count:
- Trace path:
- Frame extraction method and output path:
- Frames/timestamps inspected:
- Jitter/flash/layout-shift/interruption/end-state findings:
- Reduced-motion/responsive variants:
- Capture limitations/residual uncertainty:

## Compatibility matrix
| Dimension/cell | Reason included | Result | Evidence |
|---|---|---|---|
| | | | |

Excluded cells: <what and why unaffected>

## Negative and failure paths
- Unauthorized/invalid input:
- Dependency/source failure:
- Retry/duplicate/idempotency:
- Rollback/recovery:

## Provenance
- Source revision:
- Built artifact digest:
- Builder/workflow identity:
- Attestation verification:

## Residual uncertainty
- Untested:
- Assumptions:
- Operational observation still required:

## Verdict
PASS | PASS WITH RESIDUAL RISK | FAIL | BLOCKED
Reason:
```

## Verdict rules

- **PASS:** every material criterion has evidence tied to the final revision; no unresolved blocker.
- **PASS WITH RESIDUAL RISK:** requirements pass, but a named non-blocking uncertainty remains with owner/follow-up.
- **FAIL:** evidence contradicts a criterion or invariant.
- **BLOCKED:** a prerequisite prevents meaningful verification; never convert this to PASS because available tests are green.

## Evidence naming

Use stable, collision-resistant paths such as:

`verification/<revision>/<surface>/<artifact>`

Examples:

- `verification/a1b2c3/web/checkout-trace.zip`
- `verification/a1b2c3/visual/checkout.webm`
- `verification/a1b2c3/visual/frames/frame-000000001234.png`
- `verification/a1b2c3/cli/macos-arm64.txt`
- `verification/a1b2c3/matrix.md`

Do not retain secrets, tokens, raw customer payloads, or unnecessary personal data.
