# Cap recordings and editable cuts

Use Cap's CLI for project inspection, configuration and export; use the native
app for controls the CLI does not expose. Recheck installed capabilities first.
The findings below were exercised on macOS with Cap 0.6.1 on 2026-10-23.

- [Discover and control Cap](#discover-and-control-cap)
- [Generate captions automatically](#generate-captions-automatically-before-detecting-words)
- [Tested native cut strategy](#tested-native-cut-strategy)
- [Automation limits](#automation-and-upstream-integration-limits)

## Discover and control Cap

Resolve `cap` on PATH. A desktop installation may provide `~/.cap/bin/cap`; on
macOS the bundled executable is `/Applications/Cap.app/Contents/MacOS/cap-cli`.
Use an absolute executable when a GUI task or subprocess has a different PATH.
Run project commands through `mise exec --` with existing runtime pins. Never
install or update Cap, models or tooling implicitly.

```bash
mise exec -- cap version --json
mise exec -- cap guide --json
mise exec -- cap recordings list --json
mise exec -- cap project inspect "/path/source.cap" --json
mise exec -- cap project validate "/path/source.cap" --json
mise exec -- cap automations list --json
```

Discover recording paths from the library instead of guessing from display
names. Inspect `meta` and `config`; metadata uses snake_case, editor configuration
uses camelCase. Record the app version and active desktop implementation.
Cap 0.6.1 ships GPUI; older Tauri source is not evidence of shipping behavior.

To open an editable project on macOS, use the app's registered `.cap` file
handler with the exact local path. Load the available native computer-control
skill before operating the GUI. Check the selected recording/window and capture
fresh state before input. A GPUI canvas may expose little accessibility data;
use observed screenshots when necessary. Do not invent control IDs, click stale
coordinates or infer success from a successful launch request. Verify the exact
project path through app state or the editor load log when available.

## Generate captions automatically before detecting words

Preserve the original. Work on a separate `.cap` copy, retaining screen, camera,
microphone, system audio and cursor assets. Wait for recording finalization and
validate the copy before editing. Do not modify a project while its editor may
save stale configuration over the change.

When source-timed word captions are absent, generate them locally as part of
the agent workflow; do not routinely hand this prerequisite back to the user.
Prefer an installed Cap transcription model and an exposed local command if the
current version provides one. In 0.6.1, local transcription is available in the
editor's Captions tab, but has no CLI or deep-link action. Use supported GUI
control to select the installed model and Generate Captions, then wait and
inspect persisted caption data. This GUI automation path needs its own runtime
verification; the accepted trial used a human click to generate captions.
If controls or models are unavailable, report that concrete blocker. Never
claim automatic captions were generated when they were not.

Require `config.captions.sourceTimed == true` and valid per-word `text`, `start`
and `end`. Empty text-only captions are insufficient for word cuts. Do not upload
a recording to obtain captions as a substitute: hosted Cap transcript APIs/MCP
tools do not transcribe the local Studio project. An existing local ASR runtime
is another option only with verified word timestamps and source-time alignment.

## Tested native cut strategy

The accepted trial kept capture media intact and changed the editable timeline.
It removed seven transcript `um`/`uh` spans, reducing 23.59 seconds to 19.67
seconds. Cap reopened and exported the copy, full decoding passed, hashes
matched, and the user listened and accepted the cuts. This establishes one
transcript-based trial, not acoustic recall or unattended cleanup quality.

For the same narrow strategy:

1. Require one unedited timeline clip: `recordingSegment: 0`, `start: 0`,
   `timescale: 1`, positive finite `end`, and one recording segment in metadata.
   Refuse existing zooms, holds, transitions, masks, imported audio and other
   timed overlays unless the editing implementation explicitly retimes them.
2. Validate finite word intervals within the source duration. Refuse overlapping
   words rather than clipping neighboring speech. Match whole English hesitation
   tokens such as `um`, `ummm`, `uh`, `uhhh`, allowing punctuation and initial
   capitalization. Preserve acronyms `UM`/`UH`, `hmm`, `like`, `uh-oh` and lexical
   substrings. In other languages, `um` can be a real word; require language
   review. Transcript detection can miss audible hesitations.
3. Merge cut intervals and compute their complement over the full source
   duration. Refuse removal of the entire recording. Clone the original clip
   for every retained interval, changing only `start` and `end`; these stay in
   original source seconds. Preserve the opening, final word and natural release.
4. Clear derived `timeline.captionSegments` so Cap projects captions through
   the edit list again. The trial removed matched words from source caption
   blocks and rebuilt their text/bounds. Retain the original transcript in the
   untouched source copy; do not replace it with output-time word timestamps.
5. Write the complete copied configuration using `cap project config set` and
   `--settings-json`. Omitted fields reset to defaults. Pass JSON as one argument
   with a subprocess argument array; never interpolate transcript text into a
   shell command. Give the output copy a distinct `pretty_name` in metadata.
6. Read back with `project inspect`, compare retained intervals and substantive
   words, then require `project validate` to return `valid: true`. Compare source
   hashes before/after and copied `content/` hashes to prove media preservation.

For edited, multi-segment, reordered or retimed projects, implement source-to-
output mapping and ripple all affected tracks using the current native edit
helpers. Do not apply the single-clip strategy to those projects.

```bash
mise exec -- cap export "/path/cleaned.cap" --output "/path/preview.mp4" --resolution 1280x720 --fps 30 --json
```

Inspect the exported beginning, splice points, camera/cursor/captions and ending;
decode the complete file and listen to transitions before accepting the edit.
A GPU sandbox failure requires the appropriate execution permission, not a
claim of successful export. Keep trial evidence separate from the full skill's
required editorial, acoustic-filler and privacy delivery review.

## Automation and upstream integration limits

In installed GPUI 0.6.1, Settings > Automations saves rules but explicitly says
the app does not run them yet. The CLI lists those shared rules and can execute
command actions after CLI recordings; GUI Studio completion does not invoke
that engine. A saved rule is not evidence of execution. Do not silently enable a
watcher, background service or app patch, or claim cleanup occurs before Studio
opens. Those require separate implementation and real recording-stop evidence.

For native contribution work, inspect current `apps/desktop-gpui` transcription,
caption projection, history and ripple-edit helpers. [PR 1880](https://github.com/CapSoftware/Cap/pull/1880)
is relevant prior art, but was closed unmerged after the move from Tauri. Read
its discussion and timing work; do not transplant the retired UI. Native filler
removal and general Studio automation execution are separate changes.
