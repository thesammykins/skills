# Script-first workflow

## Setup and scope

Use existing FFmpeg/FFprobe and Python 3.11+ with NumPy. Acoustic detection needs ONNX Runtime; required PII detection also uses tokenizers. Optional local ASR needs faster-whisper. Verify installed tools/APIs before adding dependencies. Keep an isolated environment and weights under task `work/`; no global settings changes, bundled environments, automatic downloads, or uploads.

Camera detection and sensitive-text scanning use built-in macOS Vision through `swiftc` (macOS 13+ and Command Line Tools). The native helper pins face/text request revision 3, rectangle revision 1, and CPU processing. CPU-only selection is deprecated but remains supported on the exercised host; change it only with a measured regression check. On another OS, provide equivalent reviewed frame evidence and a separately verified local detector; do not silently claim native analysis ran. A sandbox may deny image-buffer allocation: surface the specific error and request only the required host execution permission. No network access is needed.

Commands below use `PYTHON` and `SKILL` as placeholders for the selected environment executable and this skill directory, not literal paths to install. Each subcommand has `--help`. All jobs are task-local and refuse overwriting untracked evidence.

First run `python3 SKILL/scripts/runtime_info.py`. Where configured, it validates a host-local `~/.agents/resources/edit-team-videos-runtime.json` and reports the existing Python, model paths/hashes and tool availability. This avoids rediscovering/downloading the same runtime in a fresh chat. The profile is separate from the portable skill; paths are checked live and fail explicitly when removed. It may point to a prior task's retained work environment. Without a valid profile, follow setup above; never treat stale paths as installed capability. Profile schema: `schema_version: 1`, absolute `python`, `filler_model`, pinned `filler_model_sha256`, optional absolute `asr_model` directory, and `pii_model` directory with a pinned `pii_model_lock_sha256`. Creating a profile does not relocate or provision those assets.

## 1. Prepare

```bash
PYTHON SKILL/scripts/video_workflow.py prepare \
  --source ORIGINAL.mp4 --model LOCAL/uhm.onnx \
  --asr-model LOCAL/faster-whisper-model \
  --work work/prepared
```

Instead of `--asr-model`, use `--transcript work/existing.json` for existing segment-level ASR (`start`, `end`, `text`; optional word timestamps are preserved and validated). Local ASR produces word timestamps; preparation manifest script hashes invalidate older transcript caches. Use a fresh preparation directory after this helper upgrade. Without either, the packet explicitly reports no transcript. Do not approve content edits without reviewing complete spoken meaning by another available method.

Preparation validates CFR/frame count, extracts 16k mono and 48k original-channel PCM, runs acoustic detection, proposes quiet intervals, samples source frames every 15s plus opening/ending, runs face/rectangle detection, and makes contact sheets. Default quiet proposals are RMS below -42dBFS for at least .76s. Quiet is not necessarily idle; proposals never become automatic cuts.

Read `review-summary.json` first, then compact `candidates.tsv` and `transcript.txt`. Candidate rows refer to transcript IDs instead of repeating text. Generated `decisions-draft.json` preselects acoustic um/uh removals and proposes shortening long interior pauses; copy it to a separate decisions file. It starts unreviewed. The empty template is available for unusual cases, but omission does not resolve filler candidates. Open `review.json` only for detailed sample geometry. Contact-sheet cells are in sample-ID order, left-to-right then top-to-bottom, 12 per sheet. Inspect full-resolution samples to measure camera edges. A face box alone is insufficient; webpage portraits and full-camera scenes can trigger detection. Shapes remain unverified until visually checked.

Use `--interval SECONDS` and `--times 12,15,18` for targeted samples. After choosing zooms, prepare a fresh job with extra samples within 1s of their starts, midpoints, and ends. Include more around changes. Keep each job's configuration immutable; unchanged reruns reuse hash-verified stages. Failed/partial or changed evidence produces an explicit error; retain it for diagnosis and use a fresh directory. No claim of continuous tracking is made from sparse sampling.

The summary flags changes in detected face count, normalized face-center distance above .08, or face-area ratio above 1.6 between adjacent samples. These are deterministic attention cues, not proof of camera movement: posture and screen content can also change. Inspect flagged intervals more densely; missing hints do not prove a stable layout.

## 2. Review and compile

Read [recording-structure.md](recording-structure.md), write a concrete edit_brief, then compact decisions using [plan-format.md](plan-format.md): resolve every filler ID, supply semantic/manual cuts, and define camera intervals, zooms, and reviewed masks. ASR overlap alone does not justify keeping an acoustic um. Refine it and verify neighboring speech. Preserve all substantive points and caveats. Run the required local privacy scan/review before deciding masks. Source hashes bind decisions to this recording.

```bash
PYTHON SKILL/scripts/video_workflow.py plan \
  --prepared work/prepared --decisions work/decisions.json --output work/plan.json
```

The compiler rejects unaddressed filler candidates, resolves IDs, refines filler boundaries, computes retained frame ranges and zoom mappings, validates camera evidence and masks, and rejects unsupported layouts. It does not decide relevance. The compiler writes `plan-evidence/speech-risk-review.json` alongside its other evidence (using the chosen plan stem). Review flagged cuts against their final snapped boundaries; word overlap is advisory evidence, not a filler keep rule. Add postroll after the preserved natural source ending.

Before a full render, use [review-packets.md](review-packets.md) to build transition windows and render selected clips through the actual composition pipeline. Resolve speech/mask/camera problems here first. Previews preserve the full-plan timeline, including zoom easing; they avoid encoding the complete export but can still process earlier frames. They are private review evidence, never delivery candidates.

## 3. Required privacy pass, render, and verify

Read [sanitization.md](sanitization.md). Scan the source using the local trained PII model plus secret/context rules. Review groups and business context, choose necessary masks, and add reviewed redactions to the plan. Run the scanner again on the actual exported MP4.

```bash
PYTHON SKILL/scripts/scan_sensitive.py \
  --source ORIGINAL.mp4 --pii-model LOCAL/PII_MODEL --work work/privacy-source
PYTHON SKILL/scripts/render_edit.py \
  --plan work/plan.json --work work/render-v1 --output outputs/Edited-video-v1.mp4
PYTHON SKILL/scripts/scan_sensitive.py \
  --source outputs/Edited-video-v1.mp4 --pii-model LOCAL/PII_MODEL --work work/privacy-export
PYTHON SKILL/scripts/video_workflow.py verify \
  --plan work/plan.json --video outputs/Edited-video-v1.mp4 \
  --model LOCAL/uhm.onnx --work work/verified-v1 \
  --privacy-source work/privacy-source/sensitive-candidates.json \
  --privacy-export work/privacy-export/sensitive-candidates.json \
  --privacy-review work/privacy-review.json
```

Rendering applies masks in original-source time before branching/cutting, uses identical audio/video frame ranges, eases screen zooms, and mattes cameras only inside reviewed zoom intervals. It preserves dimensions/FPS, adds the ending hold/fade, then checks frame count, A/V duration and full decode. Those integrity checks cannot approve editorial or privacy quality.

Verification rescans the encoded audio and makes `residual-review.json` with stable IDs, export/scan hashes and original-source mappings. It also makes preview frames around splices and zooms. Review transition motion, neighboring speech and the complete ending. An unresolved acoustic candidate requires another edit or a specific retained false-positive/meaningful-vocalization decision. Pass genuine retained cases as `--filler-review work/residual-decisions.json`, bound to this exact export/scan; never copy reviews to a changed export.

**Exit code 2 means editorial/privacy work remains**, with `ready_for_delivery: false` and specific statuses in `review.json`. Missing source/export scans, a legacy regex-only scan, unreviewed privacy groups or unreviewed residual fillers cannot pass. Resolve the cause, rerender from the original when needed, rescan changed exports, and rerun verification. Do not convert an incomplete result into a polished delivery by adding a disclaimer.

Readiness records review of detected/sampled evidence, not proof that no filler or sensitive exposure exists. Inspect sound when available and state actual methods honestly. Do not describe ASR as listening. A user can explicitly change scope; do not infer a waiver from a minimal editing prompt.

## Acoustic model and exercised constraints

**Uhm by [Desert Ant Labs](https://desertant.com)**: [model card](https://huggingface.co/desert-ant-labs/uhm), [reference preprocessing](https://github.com/Desert-Ant-Labs/desert-ant-core/blob/main/Sources/Uhm/Detector.swift), [terms](https://license.desertant.com/1.0). At creation, the license allows business use below its scale threshold and requires attribution. Verify current terms for other releases; weights are not bundled. Do not substitute a non-commercial model for a work recording without resolving terms.

Input `(1,480000)` float32, 30s at 16k; output `(1,1499,6)` at 20ms. Normalize real samples by sample standard deviation plus `1e-7` before zero-padding. Aggregate `1-p_not_filler`; subtypes are secondary. Defaults: frame .50, event peak .75, minimum .08s; central spans of overlapping windows. Generic ASR missed audible hesitations in the original workflow. Preserve model SHA/configuration for source-versus-export comparisons.

Boundary snapping searches ±.18s around proposed edges with a distance penalty and constrains edges to opposite sides of the event midpoint. Without that constraint, both edges once moved into preceding silence and left the um intact. A reviewed `snap:false` cut handles ambiguous word releases. Click fades are 6ms; they cannot repair phonetic truncation.

Frame ranges are end-exclusive. Fractional FPS uses cumulative audio sample counts and at most one-sample adjustment per segment to avoid drift. FFmpeg select sums are balanced to avoid parser-depth failure with many cuts. VFR media needs a normalized working copy before planning; retain the source and record the mapping.

The final hold is reindexed onto the output frame grid before fading: an exercised screen-only zoom/blur chain carried an incorrectly scaled EOF timestamp into `tpad`, otherwise turning a short hold into thousands of duplicated frames. A separate encoded regression covers this path. Exact camera/blur cropping also preserves odd pixel dimensions instead of allowing chroma subsampling to round them down.

## Maintenance verification

```bash
PYTHON SKILL/scripts/test_workflow.py
```

Tests also exercise word-overlap warnings, malformed word timestamps, privacy delta ordering, shared-mask coverage, and an encoded fractional-FPS preview compared with the full two-camera render. These are synthetic camera checks; a real camera recording still requires its own review. Tests exercise unknown/overlapping camera rejection, variable positions/sizes/shapes, alpha corners, candidate-only detection, sensitive-text patterns, boundary bracketing, corrupt-cache rejection, and a real fractional-FPS render with two camera layouts and a source-time mask. Native OCR/face detection also need an integration run on the current macOS version; unit tests do not certify framework accuracy. Keep model weights and personal video fixtures outside this skill.

Optional model regression (requires existing pinned weights, downloads nothing):

```bash
PYTHON SKILL/scripts/test_local_pii.py --model LOCAL/PII_MODEL
```

It checks synthetic PII categories, an ordinary-UI negative control, token-window overflow and repeated inference. The full synthetic media integration additionally exercises required review failures, masked source/export scans, exact encoded frames and decode. Neither proves recall on arbitrary business recordings.
