---
name: agent-browser
description: Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating browser actions.
allowed-tools: Bash(agent-browser:*)
---

# Browser Automation with agent-browser

## Quick preflight

Before starting a session, verify the tool is installed and check whether a reusable session already exists.

```bash
agent-browser --version
agent-browser session list
```

## Core Workflow

Every browser automation follows this pattern:

1. Navigate: `agent-browser open <url>`
2. Snapshot: `agent-browser snapshot -i`
3. Interact using refs like `@e1`
4. Re-snapshot after navigation or major DOM changes

## Essential Commands

```bash
# Navigation
agent-browser open <url>
agent-browser back
agent-browser forward
agent-browser reload
agent-browser close

# Snapshot
agent-browser snapshot -i
agent-browser snapshot -i -C
agent-browser snapshot -s "#selector"

# Interaction
agent-browser click @e1
agent-browser fill @e2 "text"
agent-browser type @e2 "text"
agent-browser select @e1 "option"
agent-browser check @e1
agent-browser press Enter
agent-browser scroll down 500

# Get information
agent-browser get text @e1
agent-browser get value @e1
agent-browser get url
agent-browser get title

# Wait
agent-browser wait @e1
agent-browser wait --load networkidle
agent-browser wait --url "**/page"
agent-browser wait 2000

# Capture
agent-browser screenshot
agent-browser screenshot --full
agent-browser pdf output.pdf

# Debugging
agent-browser console
agent-browser errors
```

Use `--json` when you need machine-readable output from snapshots or getters.

## Common Patterns

### Form Submission

```bash
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "Jane Doe"
agent-browser fill @e2 "jane@example.com"
agent-browser select @e3 "California"
agent-browser check @e4
agent-browser click @e5
agent-browser wait --load networkidle
```

### Authentication with State Persistence

```bash
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "$USERNAME"
agent-browser fill @e2 "$PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

### Data Extraction

```bash
agent-browser open https://example.com/products
agent-browser snapshot -i
agent-browser get text @e5
agent-browser get text body > page.txt
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

### Parallel Sessions

```bash
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com
agent-browser --session site1 snapshot -i
agent-browser --session site2 snapshot -i
agent-browser session list
```

### Visual Browser

```bash
agent-browser --headed open https://example.com
agent-browser highlight @e1
agent-browser record start demo.webm
```

### Local Files

```bash
agent-browser --allow-file-access open file:///path/to/document.pdf
agent-browser --allow-file-access open file:///path/to/page.html
agent-browser screenshot output.png
```

### iOS Simulator

```bash
agent-browser device list
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1
agent-browser -p ios fill @e2 "text"
agent-browser -p ios swipe up
agent-browser -p ios screenshot mobile.png
agent-browser -p ios close
```

Requirements: macOS with Xcode, Appium (`npm install -g appium && appium driver install xcuitest`).

## Ref Lifecycle

Refs are invalid after navigation, reloads, form submissions, and major DOM changes. Re-snapshot before the next targeted interaction.

## Semantic Locators

```bash
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find role button click --name "Submit"
agent-browser find placeholder "Search" type "query"
agent-browser find testid "submit-btn" click
```
