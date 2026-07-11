---
name: testing-strategist
description: Strategic testing for modern stacks. Combines high-speed Unit Testing (Vitest) with reliable E2E (Playwright). Bypasses implementation-detail testing.
license: MIT
---

## What I do
- Write robust, non-flaky tests using the "Testing Trophy" philosophy.
- Setup Playwright for E2E (auth setup, traces, video).
- Configure Vitest for fast feedback loops.
- Prevent "Testing Implementation Details" (testing internal state vs user behavior).

## When to use me
- When writing tests or setting up a test runner.
- When CI builds are flaky.
- When asked "how to test this component".
- Triggers: "write test", "playwright", "vitest", "jest", "e2e".

## Instructions

### 1. The Strategy (Trophy)
- **Static**: TypeScript/Eslint (The base).
- **Unit**: Vitest. Test pure functions and complex logic hooks. Mock network calls.
- **Integration**: Test several units together.
- **E2E**: Playwright. Test critical user flows (Login -> Checkout). Costly but necessary.

### 2. Playwright Best Practices
- **Locators**: Use User-facing locators.
  - GOOD: `page.getByRole('button', { name: 'Submit' })`
  - BAD: `page.locator('div.submit-btn')`
- **Auth**: Use `global-setup` to save storage state (cookies) and reuse across tests. Don't login in every single test file.
- **Waiting**: Never use `page.waitForTimeout(5000)`. Use `expect(...).toBeVisible()` assertions which auto-retry.

### 3. Unit Testing (Vitest)
- **In-Source Testing**: For small util functions, putting `if (import.meta.vitest) { ... }` inside the source file is acceptable in 2025 for co-location.
- **Mocking**: Use `vi.mock()` sparingly. Prefer Dependency Injection where possible.

### 4. Flakiness Prevention
- **Isolation**: Every test must be independent. Clean up DB state between runs (or use transaction rollbacks).
- **Network**: Deterministic API mocks (MSW - Mock Service Worker) are preferred over hitting real dev APIs for Integration tests.
