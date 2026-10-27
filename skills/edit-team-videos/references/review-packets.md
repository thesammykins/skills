# Pre-render review packets

Use these after compiling a plan, before investing in a full export. Keep packets in private task `work/`, never deliver them with the sanitized video: source clips and OCR crops may expose unmasked data. No new models or dependencies are needed.

```bash
PYTHON SKILL/scripts/review_packet.py \
  --plan work/plan.json --transcript work/prepared/transcript.json \
  --work work/review-packet-v1
```

Read `review-packet.json`: it records plan/source/transcript hashes, word-overlap warnings, output-time preview windows around splices, mask starts/ends, zoom entry/peak/exit, opening and ending. Nearby windows merge. Missing word timestamps are reported explicitly. Imported JSONL transcripts with word arrays are also accepted. Warnings use compiled frame boundaries and are advisory: ASR may absorb a hesitation into a word or miss soft speech. Inspect the original context before adjusting a cut. The source/export scans and delivery verifier remain mandatory.

Render selected P IDs by repeating the command into a **fresh** directory:

```bash
PYTHON SKILL/scripts/review_packet.py \
  --plan work/plan.json --transcript work/prepared/transcript.json \
  --work work/review-clips-v1 --render-preview P0000 --render-preview P0003
```

Open `index.html` locally for playable composed clips, original audio, transcript context and spectrograms. The renderer uses the same masks, camera mattes, zoom easing, cuts and audio assembly as the full plan, then trims on the output frame grid. Earlier frames may still be processed, so late previews are not guaranteed to be cheap. Choose representative splice types and every risky boundary; the ending window includes the final 20 seconds (or the entire clip when shorter). Inspect camera bounds, hair/chin, duplicate fragments, erasure edges and readability for each layout. Real camera footage remains necessary to validate detection and composition on that recording.

Direct renderer equivalent:

```bash
PYTHON SKILL/scripts/render_edit.py --plan work/plan.json \
  --work work/preview-render --output work/preview.mp4 \
  --preview-start 12 --preview-end 18
```

Times are **edited-output seconds**. Validation labels this a review preview and `delivery_candidate: false`. It must not replace the full export or its scans. Listening status starts `performed: false`; record actual clips heard and limitations in task evidence. Generating/reading spectrograms or transcripts never counts as listening. If playback is unavailable, disclose that limitation explicitly.

## Privacy crops and change ordering

Add `--privacy work/privacy-export/sensitive-candidates.json` and optionally `--prior-privacy work/privacy-source/sensitive-candidates.json`. The packet generates representative crops and groups every text hash, putting new text first, then changed boxes, then matches. Comparison is exact OCR hash and box geometry; source/export times differ and context is not inferred. Every current group remains unapproved, including matches. Review full frames, scene transitions and narration as well as crops; these previews do not establish between-sample coverage.

For stable sidebars/panels, reference all covered group hashes from a single reviewed mask using `privacy_group_sha256s`. This avoids repeated drawing operations without relaxing the existing per-group decision and per-observation coverage checks. Do not combine masks whose time intervals, style or geometry differ.
