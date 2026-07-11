---
name: figma
description: Use the Figma MCP server for Figma URLs, node IDs, design-to-code implementation, and MCP setup or troubleshooting.
---

# Figma MCP

Use this skill for any Figma-driven implementation, design-to-code translation, or Figma MCP troubleshooting.

## Required flow
1. If the Figma MCP connection is missing, connect it first and only stop to ask the user to restart if setup blocks progress.
2. Run `get_design_context` for the exact node.
3. If the response is too large or truncated, run `get_metadata`, identify the needed child nodes, and re-fetch only those nodes.
4. Run `get_screenshot` for the same node and treat it as the visual source of truth.
5. Download or use the assets returned by Figma before implementation, including localhost-hosted image or SVG assets when provided.
6. Translate the design into the project's components, tokens, and framework conventions.
7. Validate visual parity and interaction states before marking the work complete.

## Rules
- Treat the Figma output as design intent, not as final repository style.
- Reuse existing components, tokens, and spacing systems whenever possible.
- If Figma provides hosted assets, use them directly; do not invent placeholders or add new icon packages.
- If localhost or SVG assets are returned, use those exact assets rather than recreating them manually.
- Prefer project design tokens when they are close enough, but adjust carefully to preserve visual parity.
- Respect the project's routing, state, and data-fetching patterns.

## Setup fallback
- Add MCP if missing: `codex mcp add figma --url https://mcp.figma.com/mcp`
- Log in if needed: `codex mcp login figma`
- If setup requires a restart, stop cleanly and tell the user exactly what to rerun afterward.

## References
- `references/figma-mcp-config.md`
- `references/figma-tools-and-prompts.md`
