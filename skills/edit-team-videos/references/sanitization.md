# Required local secrets, PII and business-context review

Default to an external-sharing standard unless the user sets another scope. Run this pass even for “edit this file.” A source/export scan, explicit findings review, appropriate masks, and contextual inspection are completion requirements; no automatic claim of security is made.

## Detection layers

1. **OCR:** native Apple Vision accurate text recognition on sampled full-resolution frames. [Apple documents on-device processing](https://developer.apple.com/documentation/vision/recognizing-text-in-images). Small, blurred, clipped, rotated or briefly exposed text can be missed.
2. **Trained PII model:** [Gravitee BERT-small PII](https://huggingface.co/gravitee-io/bert-small-pii-detection), an English token classifier with an Apache 2.0 license. The exercised INT8 ONNX weights are about 29MB, revision `f8c27a85c51c0168f07b9dcf00265bf0a4097939`. It detects categories including people, contact details, addresses, passwords, identity/bank/card numbers and organizations. Four nearby OCR lines supply context; token windows overlap. CPU inference, thresholds and asset hashes are recorded; telemetry is disabled. Model-card scores do not establish accuracy on this video.
3. **Offline rules:** credential formats, bearer tokens, JWT-like strings, private-key headers, credential connection URLs, sensitive assignments, emails/IPs/URLs, Luhn-valid card-like values, optional literals, Australian identifier context and business/security keywords. These are explicit heuristics, not an exhaustive secret detector. Never test a suspected key against a live API.
4. **Contextual inspection:** review what screens and narration disclose. A PII model does not decide whether an architecture diagram, internal ticket, customer issue, access policy, incident detail, roadmap or financial dashboard is confidential. Inspect those scenes even when OCR reports zero candidates.

The lightweight model works with existing ONNX Runtime and tokenizers; no new software package was needed on the exercised host. Model assets and their lockfile are outside the portable skill and discovered through the host runtime profile. Other hosts need a separately authorized, license-checked setup. Piiranha and Isotonic alternatives were excluded because their current primary cards specify noncommercial licenses; do not rely on older MIT claims or an exporter changing a license label.

## What to inspect for external sharing

- Credentials, API/session tokens, authorization headers, .env files, private/signing keys, passwords, one-time/recovery codes, authentication QR codes and credential-bearing links.
- Personal/customer names, contact details, addresses, identifiers, payment/bank information, private conversations and health/employment information that the demonstration does not need.
- Internal tickets/chats/logs, customer cases, employee access details, nonpublic security configuration or vulnerabilities, private endpoints, business plans, contracts and financial information. A benign-looking identifier can be sensitive through context.
- Spoken values as well as visible ones. Visual masks leave audio intact; decide the smallest honest cut/mute treatment separately. Preserve useful narration and do not synthesize claims.

Keep public product names, generic labels, synthetic examples and necessary nonsecret workflow context. Preserve the ability to understand the action/result while hiding real private values. Use specific keep reasons for false positives; “internal audience” is not a default exemption from this external-sharing review.

## Run and review

```bash
PYTHON SKILL/scripts/scan_sensitive.py \
  --source ORIGINAL.mp4 --pii-model LOCAL/PII_MODEL \
  --work work/privacy-source --interval 1
```

The default is one frame per second; supported intervals are .1–30s. Increase sampling around UI changes, scrolling, authentication screens and brief exposures. Sparse observations do not prove continuous coverage. English OCR/PII is the exercised configuration.

Optional `--terms work/private-terms.json` flags literal names/IDs by case-insensitive substring. Keep private terms outside the installed skill and deliverables.

Start with `sensitive-summary.json`. It groups repeated OCR hashes with representative frames; first/last observations are not continuous exposure intervals. Detailed candidates include source times, padded boxes, labels and confidence. Raw OCR strings are not saved in reports/logs; raw frames remain in a private 0700 job directory. Hashes are correlation identifiers, not anonymization of guessable values. Keep detection local and do not send raw matched secrets to external services. If the user requires all review to stay local, use local viewers/models or user review for context too.

`mask-draft.json` proposes opaque masks for near-stationary observation runs, merging nearby boxes/times. Every proposal starts `reviewed: false`. It can miss movement between samples and mask too much; inspect bounds, timing, context and omitted frames before approving. Do not blindly mark all proposals reviewed.

Copy `privacy-review-template.json` to a separate review file. It binds the source and exact report hashes and starts unapproved. Each unique `text_sha256` group needs `action: "keep"` or `"mask"` and a specific reason. Set `context_reviewed: true` only after the scene/narration inspection, with a concrete `context_note`. Marked masks must appear in the plan as reviewed `redactions` with matching `privacy_group_sha256`. For repeated findings in one stable panel, use one reviewed redaction with `privacy_group_sha256s` listing its groups, rather than duplicating the same drawing operation. Preserve separate decisions per group. The verifier checks that retained sampled source observations fit within those masks. It cannot prove coverage between samples.

Prefer solid masks for secrets; blur may be reversible or readable. Use separate intervals for moving text or cover a stable enclosing region while preserving relevant controls. Masks apply before cuts, zooms and camera compositing. Inspect mask appearance/disappearance, zooms, scrolling, the final hold/fade and exported audio.

## Verify the exported file

Run the same scanner on the actual MP4 in `work/privacy-export`. Review its groups separately. The private review packet can compare it with a previous scan and order new text and changed boxes first. Same text/box hashes are navigation hints, not proof of equivalent scene context or authorization to reuse an approval. Combine the two reviewed templates under `source` and `export` keys in `work/privacy-review.json`, then pass it and both reports to `video_workflow.py verify`.

An export group containing a real remaining sensitive value requires a new source-time mask/edit and a new export/scan. Remaining harmless labels require explicit keep reasons. Mask actions in an export review do not hide anything by themselves. Verification exits 2 while scans/reviews are missing or unresolved; `ready_for_delivery` must be true before reporting a completed edit. Even then, describe sampled checks and material limits rather than certifying “safe to share.”

## Further local options

[Gitleaks](https://github.com/gitleaks/gitleaks) offers a broader offline secret-rule library for files/stdin; it was researched, not installed. [Presidio](https://microsoft.github.io/presidio/installation/) combines OCR and entity detection with additional runtime/model dependencies. [Qwen3-VL](https://ollama.com/library/qwen3-vl:4b) is a possible local visual-context reviewer, not a validated universal confidentiality detector. No new package/service or large model is installed silently. Verify current license, versions, locality and repeatability before adoption.

Private-key rules flag the whole visible BEGIN/END block, and split credential-field labels also flag the following value line. A high-entropy-token heuristic adds review flags for mixed-character tokens; hashes and identifiers may be harmless false positives. Neither heuristic establishes that a token is a working secret. The scanner always includes a final-frame sample in addition to its interval grid; this still cannot detect every brief intervening exposure.
