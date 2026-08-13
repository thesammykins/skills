# Amp adapter

Use the available browser automation capability for the current executor. If one is not available, say so and do not claim interactive coverage.

- For browser/UI evidence, capture screenshots or recordings in the workspace and inspect them with Amp's media-inspection capability before reporting a visual finding.
- Use an Amp browser skill or configured browser MCP only when it is available in the current thread; do not assume an orb has a browser, authentication, or local development server.
- Re-snapshot after navigation, scrolling, modal changes, and other state transitions. Record the viewport and test account/state with each finding.
- Keep generated evidence under the requested output directory so it can be handed off from the executor when necessary.
