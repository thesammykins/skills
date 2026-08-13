# Visual and Motion Verification

Use this whenever a change affects animation, transition timing, scrolling, drag behavior, responsive layout, visual state, canvas/WebGL output, video, or any interaction whose correctness unfolds over time. This operationalizes the podcast pattern at 00:14:17–00:16:59 and 00:25:55–00:26:40: make the agent record the real interaction, inspect the recording, and for motion inspect frames rather than trusting a polished summary or final screenshot.

## Non-negotiable rule

A visual or temporal claim requires a recording of the final artifact and inspection of that recording. A still screenshot can verify a state; it cannot verify a transition. Creating a video without opening it and examining frames is not verification.

## Capture contract

Before recording, state:

```markdown
Revision/artifact:
Environment/browser/device:
Viewport and device pixel ratio:
Input method:
Reduced-motion state:
Scenario and start state:
Expected key states and timing:
Regions that must remain fixed:
Recording method, container, dimensions and measured FPS:
```

Control sources of nondeterminism where possible: fixed seed/data, animations started from a known state, fonts loaded, network settled, stable viewport, no unrelated overlays/notifications, and consistent zoom/device scale. Record the whole user path, not a hand-edited highlight reel.

## Capture hierarchy

Stop at the first reliable existing method:

1. **Project-native recorder/test artifact** — reuse Playwright/Cypress/Webdriver/app test recording already in the repository.
2. **Browser automation recording** — for Playwright, enable video and trace; close the browser context so the video is flushed. Set viewport and video size deliberately because Playwright may scale recordings to fit its default video bounds.
3. **Platform-native app recording** — use the established simulator/device/app test capture path.
4. **OS screen recording** — last resort; document display scale, crop, frame rate and whether frames may be duplicated/dropped.

Do not add a recording framework when an existing one can capture the relevant surface. Use traces alongside video for browser interactions: traces provide DOM snapshots, actions, console, errors and network; video provides temporal appearance.

## Validate the recording before analysis

Use `terminal` with the installed `ffprobe` when available:

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames,duration \
  -of json verification/<revision>/visual/interaction.webm
```

Check:

- file exists and opens;
- duration covers setup through settled final state;
- dimensions/viewport are expected;
- measured frame rate is adequate for the claim;
- no unintended scaling/cropping hides the changed region;
- recording belongs to the final revision.

A nominal 120 FPS setting is not proof of 120 distinct captured frames. Inspect metadata and the decoded sequence; virtual/browser recorders may cap, resample, duplicate, or use variable frame rate.

## Extract frames reliably

Prefer FFmpeg when installed. Run commands through `terminal`; paths below are examples, not fixed machine paths.

### Every decoded frame with presentation timestamps

```bash
mkdir -p verification/<revision>/visual/frames
ffmpeg -v error -i interaction.webm -vsync 0 \
  -frame_pts 1 verification/<revision>/visual/frames/frame-%012d.png
```

`-vsync 0` avoids deliberately duplicating/dropping frames during extraction; `-frame_pts 1` names frames from presentation timestamps. Preserve the source recording—never inspect only a transcoded derivative.

### Fixed-rate sampling for overview

```bash
ffmpeg -v error -i interaction.webm -vf "fps=10" \
  verification/<revision>/visual/sample-%06d.png
```

Use this to locate transitions, not to rule out one-frame glitches. Once a suspicious interval is known, extract every decoded frame from that interval:

```bash
ffmpeg -v error -ss 00:00:01.200 -to 00:00:01.800 -i interaction.webm \
  -vsync 0 -frame_pts 1 verification/<revision>/visual/interval-%012d.png
```

### Contact sheet for human/agent review

```bash
ffmpeg -v error -i interaction.webm \
  -vf "fps=8,scale=320:-1,tile=4x4" -frames:v 1 \
  verification/<revision>/visual/contact-sheet.png
```

A single sheet covers only its selected sample. Use multiple sheets or inspect individual frames for longer motion.

If FFmpeg is unavailable, use an existing project/library decoder that preserves timestamps. Do not use a convenience screenshot loop that seeks approximately and silently skips variable-frame-rate content unless its ceiling is stated as residual uncertainty.

## Inspection procedure

1. **Watch once at normal speed.** Look for obvious jitter, flicker, wrong sequencing, delayed response, abrupt easing, clipping, focus loss and unexpected layout movement.
2. **Watch slowly and scrub.** Locate start/end timestamps for each transition and any suspicious interval.
3. **Inspect extracted frames.** Open contact sheets and suspicious individual frames with an available media-inspection capability; do not infer frame contents from filenames or extraction success.
4. **Track anchors.** Select stable landmarks—the toggle, panel edge, baseline, cursor target, fixed header—and compare position/size across frames. Unexpected movement is evidence; tiny compression/color variation alone is not.
5. **Check continuity.** Look for duplicated/stalled frames, one-frame reversals, teleporting elements, transient overlap, tearing-like partial states, z-index flashes, missing frames and inconsistent opacity/transform progression.
6. **Check endpoints.** First and settled final frames must match expected layout, hit targets, focus and content; transitions must not leave stale styles or inaccessible hidden controls.
7. **Check responsive/input variants only when implicated.** Mouse, keyboard/touch, desktop/mobile, zoom/reflow, reduced motion and high-DPI can change the motion path.
8. **Correlate with trace/runtime evidence.** For browser changes, inspect console/network/errors and DOM snapshots around suspicious timestamps; the video shows symptom, not necessarily cause.
9. **Record findings precisely.** Cite recording path, measured metadata, frame/PTS or timestamp, affected region, expected behavior and observed defect.
10. **Rerun after fixes.** Capture a new recording from the final revision and repeat the affected inspection. Old video is stale evidence.

## Automated comparison boundaries

Pixel or image diffs are useful for deterministic key states and selected anchor crops. They are poor standalone judges of animation quality because antialiasing, font rendering, GPU output, video compression and subpixel motion create noise.

When using automated frame comparisons:

- compare source screenshots or lossless extracted frames, not social/compressed video;
- mask known volatile regions;
- use stable crops/anchors and a documented threshold;
- retain diff images;
- require human/agent visual inspection of failures and suspicious passes;
- never convert “pixel diff under threshold” into “motion is smooth.”

## Motion-specific failure catalogue

- **Jitter:** non-monotonic or uneven anchor movement not explained by easing.
- **Stall:** repeated visual state while time advances, followed by a jump.
- **Flash:** one/few frames show wrong content, background, z-index or unstyled state.
- **Layout shift:** supposedly fixed controls/containers move during sibling animation.
- **Clipping/overflow:** content crosses mask/container bounds transiently.
- **Input desync:** visual state lags or contradicts pointer/keyboard action.
- **Interrupted-state failure:** rapid toggle, back navigation or repeated input leaves impossible state.
- **Endpoint drift:** final layout differs depending on path, direction or interruption.
- **Reduced-motion failure:** motion remains excessive or functionality disappears when reduced motion is requested.
- **Responsive divergence:** transition works at one viewport but overlaps/jumps at another.

## Evidence required for a visual PASS

- original recording tied to final revision;
- capture contract and `ffprobe` metadata (or equivalent);
- trace when browser runtime behavior is involved;
- extracted frame set/contact sheets for temporal changes;
- named frames/timestamps inspected, including suspicious intervals and endpoints;
- findings or explicit “no issue observed” with stated capture limits;
- residual uncertainty, especially recorder FPS/scaling/GPU differences.

## Primary resources

- Podcast transcript: 00:14:17–00:16:59 and 00:25:55–00:26:40 in the source transcript used to derive this skill.
- Playwright video recording: https://playwright.dev/docs/videos
- Playwright trace inspection: https://playwright.dev/docs/trace-viewer
- Playwright screenshots: https://playwright.dev/docs/screenshots
- FFmpeg frame extraction and stream handling: https://ffmpeg.org/ffmpeg.html
- FFmpeg filters, including `fps`, `select`, and `tile`: https://ffmpeg.org/ffmpeg-filters.html
