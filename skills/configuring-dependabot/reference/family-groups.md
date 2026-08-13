# Family Group Examples

**Illustrative only.** These patterns show the *shape* of a useful Dependabot group — narrow enough to keep related libraries in lockstep, broad enough to actually batch — for a few well-known frameworks. The list below is not exhaustive and most projects will have clusters that are not covered here (in-house libraries, less-common frameworks, monorepo conventions, vendor-specific SDKs, etc.).

When configuring a repo, read its manifests, identify clusters by shared name prefix / organisation / framework, and invent groups that match. Within each ecosystem, order groups narrowest → broadest so Dependabot's first-match-wins assignment picks the most specific group.

**Only emit a group from the lists below if the repo's manifests actually contain 2+ distinct packages matching its patterns and those packages share a lockstep release/API relationship.** A pattern that resolves to a single package (e.g. `actions/*` in a repo whose only official action is `actions/checkout`) must be omitted — let it fall into `minor-and-patch`. Shared namespace alone is not justification.

## `npm`

- `next: ["next", "@next/*"]`
- `react: ["react", "react-*", "@types/react*"]`
- `vite: ["vite", "@vitejs/*"]`
- `vitest: ["vitest", "@vitest/*"]`
- `jest: ["jest", "@types/jest", "ts-jest", "babel-jest"]`
- `eslint: ["eslint", "eslint-*", "@eslint/*", "@typescript-eslint/*"]`
- `typescript: ["typescript", "tslib"]`

## `maven`

- `spring-boot: ["org.springframework*"]`
- `kotlin: ["org.jetbrains.kotlin*", "org.jetbrains.kotlinx*"]`
- `jackson: ["com.fasterxml.jackson*", "tools.jackson*"]`
- `aws-sdk: ["software.amazon.awssdk*"]`
- `testing: ["org.junit*", "io.mockk*", "org.testcontainers*", "org.mockito*"]`
- `maven-plugins: ["org.apache.maven.plugins*", "com.diffplug.spotless*"]`

## `gradle`

Mirror the `maven` families that apply.

## `gomod`

- `aws-sdk: ["github.com/aws/aws-sdk-go*"]`
- `kubernetes: ["k8s.io/*", "sigs.k8s.io/*"]`
- `opentelemetry: ["go.opentelemetry.io/*"]`

## `pip` / `uv`

- `pytest: ["pytest", "pytest-*"]`
- `django: ["django", "django-*"]`
- `aws: ["boto3", "botocore", "aws-*"]`

## `cargo`

- `tokio: ["tokio", "tokio-*"]`
- `serde: ["serde", "serde_*"]`

## `docker`

One group per shared base image when several Dockerfiles share it.

## `github-actions`

- `actions: ["actions/*"]` — only when the repo uses 2+ distinct official actions (e.g. `actions/checkout` *and* `actions/setup-node`). A repo with just `actions/checkout` should leave it ungrouped.

Most workflow repos do not need any family groups — third-party actions (`hashicorp/setup-terraform`, `slackapi/slack-github-action`, etc.) release independently and should fall into `minor-and-patch` unless several from the same vendor genuinely move in lockstep.
