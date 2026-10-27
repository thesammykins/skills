# Reviewed decisions and render plans (schema 2)

Coordinates always refer to the current original source, in top-left pixels. Times are source seconds. No camera geometry is prefilled or inferred to be approved.

## Decisions passed to `video_workflow.py plan`

```json
{
  "source_sha256": "COPY_FROM_THIS_JOBS_REVIEW_JSON",
  "editorial_reviewed": true,
  "edit_brief": {
    "purpose": "State the specific work and result the viewer should understand.",
    "pacing": "Record which idle waits and repeated setup were shortened and why.",
    "continuity": "Record how the useful action and visible result stay together.",
    "ending": "Preserve the complete source closing, its vocal release and natural room."
  },
  "accept_filler_ids": ["F0001", "F0004"],
  "retain_fillers": [],
  "cuts": [
    {"start": 41.2, "end": 43.7, "kind": "restart", "reason": "Complete replacement survives"}
  ],
  "camera_layouts": [],
  "zooms": [],
  "redactions": [],
  "postroll_seconds": 1.2,
  "fade_out_seconds": 0.45
}
```

Candidate IDs avoid repeating timestamps and metadata. Approve each against audio/context; do not bulk-approve by label or score. Add manually adjusted filler cuts to `cuts` instead of also accepting their IDs. `kind: "filler"` refines boundaries using the extracted full-source PCM. `snap: false` preserves a reviewed exact cut. The planner merges gaps up to 50ms; check useful speech survives.

`editorial_reviewed` records an actual review, not permission for the script to decide meaning. Do not set it merely to pass validation.

## Camera layout timeline

Each zoom must be completely inside exactly one `reviewed: true` layout. Each layout has `source_start`, `source_end`, `mode`, and `evidence_frames` containing sample IDs such as `S0002`. During compilation, evidence must include inspected frames within 1s of each zoom's start, midpoint and end. Add more samples around movement or transitions; sparse samples do not prove uninterrupted stability.

Modes:

- `absent`: explicitly verified screen-only interval; no camera crop.
- `overlay`: stable baked-in camera; requires `crop: [x,y,width,height]`, `shape`, and optional `erase_margin` (default 4px).
- `unknown`, `moving`, `multiple`, `full_camera`: document these intervals; the renderer rejects zooms there. Keep the original view or split into verified stable intervals.

Shapes: `rectangle`, `ellipse`, `rounded_rectangle`. Rounded rectangles require a measured `radius` in pixels; ellipses support unequal width/height. Bounds and erase margin must fit inside the source frame. Tight crops exclude drop shadows and desktop. For a camera touching the frame edge, do not force an invalid erase area; omit that zoom or review another composition.

Detection produces face boxes and possible panel bounds at the recording's actual resolution. It does not infer identity, prove overlay status, or reliably recover rounded boundaries. Model/human verification supplies final bounds, shape and timing. Different zooms may use different verified camera sizes, positions and shapes.

## Zooms

Each zoom: `source_start`, `source_end`, `scale` (1–2), `anchor_x`, `anchor_y` (0–1), `ease_seconds` (default .7s). Anchors describe position within the available crop offset, not source pixel coordinates. Ease is capped at half the retained interval. Intervals must be ordered, nonoverlapping and retain content. Keep relevant text inside the viewport throughout entry, peak and exit.

## Reviewed redactions

Each: `source_start`, `source_end`, `box: [x,y,width,height]`, `style: "solid"` or `"blur"`, `reviewed: true`, `reason`. Use padded bounds and review the whole interval. A sampled OCR detection alone does not establish when a value appears/disappears or where it moves. Solid masking is the reliable default for secrets; blur can remain readable. Use separate intervals/boxes or cover a stable enclosing panel while scrolling. Spoken sensitive content is a separate editorial decision.

Masks run before cuts, screen zooms and camera branching. This ensures the same masked source pixels feed all composites. Check the actual export at mask edges, transitions, zoom peaks and final held frame; rescan it. Do not deliver raw privacy frames or OCR evidence with the sanitized video.

## Compiled plan

The compiler adds `schema_version: 2`, source/manifest hashes, ordered end-exclusive integer `keep_frame_ranges`, and auditable cut decisions. The renderer verifies the source hash, preserves dimensions/FPS, and exports H.264/AAC with fast start. Audio/video use the same frame grid, including fractional FPS. Postroll is frame-quantized; fade must fit within it. Default added hold is 1.2s, final fade .45s; preserve natural source tail first.

Legacy `webcam` plans must be migrated to reviewed layouts. VFR input needs a normalized working copy before frame-based planning. Continuous narration with mono/stereo audio is supported; multitrack mixing and overlapping speakers need another workflow.

## Required filler and editorial decisions (v2.1)

Start from generated `decisions-draft.json`. It proposes acoustic um/uh cuts and interior-pause shortening with 0.5s retained room, but is unapproved. Check the whole speech, pauses and screen context before changing `editorial_reviewed`.

Add `edit_brief` with concise, specific strings for `purpose`, `pacing`, `continuity`, and `ending`. These record actual choices about the walkthrough's arc, useful pauses, coherent transitions and complete close.

Every source filler needs an approved ID, a manually adjusted cut covering it, or an entry in `retain_fillers`:

```json
{"id":"F0003","classification":"false_positive","spoken_words":"another","reason":"The detector overlaps a complete lexical word; its full pronunciation is required here."}
```

Allowed retained classifications are `false_positive` and `meaningful_vocalization`. Supply actual words and a specific reason. “Ambiguous,” “ASR overlap,” and omission are unresolved work. The source audit rejects missing decisions; an acoustic um overlapping a normal ASR word span needs boundary refinement, not a blanket keep rule.

For a manually adjusted filler span, add `candidate_id: "F0003"` to its `cuts` row and omit that ID from `accept_filler_ids`. The cut must overlap the candidate but may remove less than the detector's full span when that span includes a real neighboring word. This records resolution without creating a duplicate broad cut. A candidate wholly removed by another cut is resolved automatically.

Verification creates `residual-review.json` with export IDs `R0000` etc., exact video/scan hashes and mapped original-source intervals. Revise the original-source decisions for remaining fillers; do not cut repeatedly compressed exports. Genuine retained false positives need a separate JSON with matching `video_sha256`, `scan_sha256`, and `retain_fillers` entries in the same format. Pass it as `--filler-review`. Old reviews cannot approve a changed export.

Required privacy review is described in [sanitization.md](sanitization.md). Masks associated with one privacy group carry `privacy_group_sha256`; a shared region may instead carry `privacy_group_sha256s: ["hash-one", "hash-two"]`. Each linked group still needs its own decision and every retained observation must fit the mask. Merge only identical reviewed geometry/style/time spans; keep intervals separate when the UI changes. The singular field remains supported. These fields carry the hashes from the scan, allowing the verifier to check that retained sampled observations fall inside the reviewed source-time masks. This establishes coverage of observations, not unseen frames.
