# Security and Live Buildkite Operations

Use this reference before handling credentials, deployment access, queues, clusters, live Buildkite settings, or MCP/API mutations.

## Official References

- Pipelines API: https://buildkite.com/docs/apis/rest-api/pipelines
- Builds API: https://buildkite.com/docs/apis/rest-api/builds
- Buildkite Secrets overview: https://buildkite.com/docs/pipelines/security/secrets
- Buildkite Secrets: https://buildkite.com/docs/pipelines/security/secrets/buildkite-secrets
- OIDC: https://buildkite.com/docs/pipelines/security/oidc
- Security overview: https://buildkite.com/docs/pipelines/security
- Managing queues: https://buildkite.com/docs/pipelines/clusters/manage-queues

## Secrets and Identity

- Prefer OIDC for cloud access when the target platform supports short-lived federated credentials.
- Prefer Buildkite Secrets or an existing managed secret store for static secrets.
- Never commit secret values, generated tokens, private keys, signing certificates, `.env` contents, or unredacted API responses.
- In generated pipeline YAML, reference secret names or retrieval commands only. Do not invent real values.
- Scope credentials to the minimum pipeline, cluster, queue, branch, tag, and environment practical.

## Runner and Queue Safety

- Treat agent queues as trust boundaries.
- Use specialized queues for deploys, signing, production networking, privileged Docker, macOS/iOS, GPU, or regulated workloads.
- Do not route untrusted pull request builds onto deployment or signing queues.
- Prefer ephemeral or tightly isolated agents for jobs that execute untrusted code.

## Live Operation Rules

Local repo changes can proceed without live Buildkite access. Live operations require explicit confirmation when they mutate state.

Read-only operations are appropriate for discovery:

- `list_pipelines`: find candidate pipeline slugs, repository URLs, current status, and tags.
- `get_pipeline`: inspect configuration, repository URL, default branch, cluster, skip/cancel settings, and existing YAML.
- `list_builds`: inspect recent pass/fail state before changing a pipeline.
- `list_annotations`: inspect build output summaries or validation annotations.

Mutation operations require confirmation of org slug, pipeline slug/name, repository URL, default branch, and intended change:

- `update_pipeline`: changes live pipeline configuration or metadata.
- `create_build`: triggers a build.
- `rebuild_build`: retries a build.
- `cancel_build`: cancels a running build.

If a tool for live pipeline creation is unavailable, produce the REST API request shape instead of improvising another mutation path.

## Recommended Live Metadata

When creating or updating a live pipeline, capture these settings separately from repo YAML:

- `repository_url`
- `default_branch`
- `cluster_id` or queue assumptions
- `skip_queued_branch_builds`
- `cancel_running_branch_builds`
- tags for ownership, stack, criticality, and environment
- provider trigger settings or branch filters

Good defaults for active application repos are:

- skip queued intermediate builds on non-release branches
- cancel running branch builds on fast-moving development branches
- avoid canceling protected release, deploy, or long-running migration branches unless the user confirms

## Deployment Defaults

- Default production release steps to protected branch or tag conditions plus a manual `block`.
- Keep deploy credentials out of test and pull-request queues.
- Split build/package from deploy when artifacts should be promoted rather than rebuilt.
- Add annotations for release summaries, artifact locations, and deployment targets.
- Do not auto-submit to app stores, production releases, or irreversible infrastructure changes unless the user explicitly asks for that exact behavior.

## Failure Handling

- If live settings conflict with repo YAML, report the conflict before changing anything.
- If a build fails after setup, inspect annotations and recent builds before retrying.
- If Buildkite access is missing or tools fail authorization, finish with local pipeline files plus the exact live settings the user or administrator needs to apply.
