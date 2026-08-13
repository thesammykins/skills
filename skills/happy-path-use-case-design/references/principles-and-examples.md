# Principles and Examples

## Happy-Path-First Orchestration

Keep the use case visible:

```ts
async function update(version: Version) {
  await server.stop()
  await cli.install(version)
  await cli.requireVersion(version)
  await server.start()
}
```

Parsing commands, collecting process output, and interpreting versions belong in the smallest lower boundary that owns those mechanics. Do not split the four obvious orchestration lines merely to create layers.

## Parse Once, Preserve What Was Proved

Avoid validation that discards its result:

```ts
validateVersion(input)
await install(input) // still string
```

Create a trusted value:

```ts
const version = Version.parse(input)
await install(version)
```

Model legal states directly:

```ts
type ServerState =
  | { kind: "stopped" }
  | { kind: "starting" }
  | { kind: "ready"; url: ServerUrl }
  | { kind: "failed"; error: ServerError }
```

This is preferable to unrelated booleans and nullable fields that permit contradictory combinations.

## Patterns Must Pay Rent

A pass-through chain adds call hops without hiding complexity:

```ts
class UserController {
  constructor(private service: UserService) {}
  get(id: UserID) { return this.service.get(id) }
}

class UserService {
  constructor(private repository: UserRepository) {}
  get(id: UserID) { return this.repository.get(id) }
}
```

If data access is obvious and no domain port exists, keep it direct:

```ts
async function getUser(id: UserID) {
  return database.selectUser(id)
}
```

Add a repository when it hides stable query complexity, enforces persistence semantics, or represents a real domain boundary—not because a diagram expects one.

## Flat Control Flow

Reject invalid conditions before the valid path:

```ts
if (!config) return
if (!config.enabled) return
assert(server.ready)
return run(config)
```

Do not nest the valid flow under every defensive condition. Recovery deserves code when it is an explicit requirement or supported by runtime evidence.

## Deep Modules, Not Helper Shrapnel

Avoid shallow sequencing helpers such as `prepareUpdate`, `doUpdate`, and `finishUpdate` when readers must open all three to understand one operation. Keep simple related code together, or expose one meaningful operation such as:

```ts
await cli.installExactVersion(version)
```

The interface is valuable only if it hides substantial mechanics or a stable invariant.

## State Ownership

Avoid asking for internal state and mutating it elsewhere:

```ts
if (session.status() === "pending") {
  session.messages().push(message)
  session.setStatus("active")
}
```

Tell the owner the domain operation:

```ts
session.promote(message)
```

The owner enforces the transition and related invariants once.

## Domain and Infrastructure

Keep process, network, and persistence work outside domain decisions:

```ts
const event = session.promote(message)
await sessionStore.append(event)
```

Use ports and adapters only where this boundary is real. A wrapper that merely renames one database or HTTP call is shallow.

## Stable-Boundary Tests

Prefer the observable use case and order:

```ts
await controller.update("Debian")
expect(events).toEqual(["stop", "install", "verify", "start"])
```

Avoid tests that duplicate each one-line helper's implementation. Tests should survive harmless refactoring while failing when behavior changes.

## Evidence Before Complexity

Do not build retry maps, lifecycle frameworks, stale-owner checks, and fallback chains for an imagined race. Implement the observed flow. If production later reports `Text file busy`, fix the owner—for example, make `stopServer` await process exit before installation—and leave a focused regression check.
