# Maestro Flow Patterns

Use this reference when the task needs more than a single linear flow.

## Verify Before Using

Check the current docs for the exact feature:

- Flows overview: https://docs.maestro.dev/maestro-flows
- Writing a first flow: https://docs.maestro.dev/getting-started/writing-your-first-flow
- Commands index: https://docs.maestro.dev/api-reference/commands
- Selectors: https://docs.maestro.dev/api-reference/selectors
- Conditions: https://docs.maestro.dev/advanced/conditions
- CLI commands: https://docs.maestro.dev/maestro-cli/maestro-cli-commands-and-options

## Minimal reusable patterns

### Subflow with parameters

```yaml
appId: com.example.app

---
- runFlow:
    file: subflows/login.yaml
    env:
      USERNAME: tester@example.com
      PASSWORD: secret
```

```yaml
appId: com.example.app

---
- tapOn: "Username"
- inputText: ${USERNAME}
- tapOn: "Password"
- inputText: ${PASSWORD}
- tapOn: "Sign In"
```

Use this when the same interaction is reused in multiple journeys.

### Conditional subflow

```yaml
- runFlow:
    when:
      visible: "Allow"
    commands:
      - tapOn: "Allow"
```

Use conditional logic only for genuinely optional UI, such as permission prompts or dismissible interruptions.

### Platform-specific subflow

```yaml
- runFlow:
    when:
      platform: iOS
    file: subflows/ios-permissions.yaml

- runFlow:
    when:
      platform: Android
    file: subflows/android-permissions.yaml
```

Prefer this over packing platform branches into one long inline command list.

### Structured selector

```yaml
- tapOn:
    id: "saveButton"
    below:
      text: "Profile"
```

Prefer ids first. Add hierarchy or text constraints only when they improve precision.

## Hooks and workspace config

Check the current docs before relying on workspace-wide behavior:

- Workspace configuration: https://docs.maestro.dev/api-reference/configuration/workspace-configuration
- Flow configuration: https://docs.maestro.dev/api-reference/configuration/flow-configuration
- Hooks: https://docs.maestro.dev/advanced/onflowstart-onflowcomplete-hooks
- Tags: https://docs.maestro.dev/cli/tags

Use workspace config for shared defaults and hooks. Keep scenario-specific behavior in the flow itself.

Important current-docs nuance: Maestro Studio does not currently support `config.yaml` for local runs. It is still included in workspace uploads to Maestro Cloud.

## JavaScript

Check these docs before adding JavaScript:

- Using JavaScript in Maestro: https://docs.maestro.dev/advanced/javascript
- Run JavaScript in flows: https://docs.maestro.dev/reference/commands-available/runscript
- evalScript: https://docs.maestro.dev/api-reference/commands/evalscript

Prefer YAML-only flows first. Add JavaScript only when you need dynamic data, branching based on runtime values, or reusable computed outputs.

## Keep tests simple

Current Maestro guidance is clear:

- Avoid unnecessary conditions
- Prefer small flows
- Prefer reusable subflows over duplication
- Prefer stable selectors over timing hacks
