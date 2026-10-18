# Selecting project skills

The shared catalog recommends capabilities; it neither installs skills nor changes
client enablement. Read only the selected skills when the task activates them.
Global scope is reserved for reusable agent workflows, not every available tool.

| Project evidence | Small initial selection | Add only when needed |
|---|---|---|
| Swift command-line tool or library | Existing repo workflow; concurrency or testing skill when exercised | No HIG, SwiftUI, simulator, or App Store skills merely because it is Swift |
| iOS/iPadOS app | Apple HIG reference and one build/debug provider; SwiftUI provider if used | SwiftData/Core Data, App Intents, performance, release capabilities |
| macOS app | Apple HIG reference and one macOS build/debug provider; actual UI framework | Signing, notarization, AppKit interop, SwiftPM packaging as applicable |
| Go or Rust project | Matching language profile | Provider/deployment skills only for configured infrastructure |
| Android app | Android tooling from the recorded source | Feature-specific emulator/performance/release skills |
| Web app | Actual framework skill from an available verified provider | Hosting, database, payments, or Apple-inspired UI only when adopted/requested |
| CI or cloud configuration | Matching provider profile | Do not infer providers from the language |

For a SwiftUI iOS app, a concrete candidate set is `swiftui-pro` from
`twostraws/SwiftUI-Agent-Skill`, `apple-human-interface-guidelines` from
`milistu/agent-skills`, and `xcodebuildmcp` from `getsentry/XcodeBuildMCP`.
The catalog records exact entrypoint paths where verified. Recheck sources and
pin revisions during installation. The HIG skill is an independent reference;
use Apple's current documentation for current platform claims.

If the active client already supplies `build-ios-apps:swiftui-ui-patterns` and
`build-ios-apps:ios-debugger-agent`, assess those before adding competing copies.
A debugger skill that requires XcodeBuildMCP is usable only when its tools are
available. A project record can document a client-provided capability, but cannot
make it portable to another client. Record the CLI fallback when appropriate.

## Install versus copy

- **Project-local managed install:** default for externally maintained skills;
  retain the installer lock and recorded source revision. Inspect actual paths
  and links to confirm scope. Never pass a global flag for project setup.
- **Project-owned copy:** appropriate for portable checked-in guidance or an
  intentional fork. Preserve required references and license, record upstream
  revision and local changes, and assign an update owner. Avoid machine-specific links.
- **Client-provided plugin:** reference the available capability and version;
  do not vendor cached implementation. Record any prerequisite tools and scope
  limitations. Use supported per-project enablement only when the client offers it.
- **Global workflow:** keep one shared install; reference it from project guidance.

Do not bulk-relocate existing global skills. First identify dependent projects,
prepare and verify their replacements, then obtain authorization for removal.
Installation scope and activation scope differ: selective invocation does not
remove a globally enabled plugin's catalog entries from the context.

## Project record

Copy `project-selection.template.json` to `.agents/project-skills.json` only
when setup is authorized. This is an agent-readable record, not a client-native
activation manifest or an executable installer. Replace every placeholder with
verified values. For each selected skill record why it belongs here, source and
revision, delivery method, update owner, and prerequisites. Keep rejected or
optional capabilities with their reason so future sessions do not rediscover them.

Revisit the record when the stack, delivery target, or skill source changes, not
on every turn. Read a locked selection first; recheck availability cheaply before
using it. Refresh sources when installing or updating, not for every ordinary task.
