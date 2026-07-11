# SDK Structured Output And Events

Read this file when the integration needs machine-readable output, event streaming, or tighter runtime verification.

## Structured output

- Check the installed SDK types for the exact request field name before coding. The docs currently use both `format` and `outputFormat` in different sections.
- Use a small JSON schema with clear property descriptions and required fields.
- Read the validated payload from `result.data.info.structured_output`.
- Handle `StructuredOutputError` explicitly instead of silently falling back to prose parsing.

```ts
const result = await client.session.prompt({
  path: { id: sessionId },
  body: {
    parts: [{ type: "text", text: "Return structured company info." }],
    format: {
      type: "json_schema",
      schema: {
        type: "object",
        properties: {
          company: { type: "string", description: "Company name" },
        },
        required: ["company"],
      },
    },
  },
})
```

If the installed SDK version uses a different request field than `format`, change the example to match the local types before implementation.

## Event streaming

- Use `client.event.subscribe()` for live status, progress, or observability.
- Consume the stream with `for await`.
- Treat the first `server.connected` event as transport confirmation.
- Stop listening when the process ends; do not leave long-lived subscriptions dangling.
- Re-fetch final state through normal SDK calls instead of treating the stream as the only source of truth.

```ts
const events = await client.event.subscribe()

for await (const event of events.stream) {
  if (event.type === "server.connected") continue
  // handle relevant events
}
```

## Verification checklist

- Confirm `client.global.health()` succeeds.
- Verify one disposable session can produce a normal reply.
- Verify structured output on both success and failure paths if the integration depends on it.
- Verify the event stream emits at least one event beyond the initial handshake.
- Do not rely only on static typing; make real calls.
