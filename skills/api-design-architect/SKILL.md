---
name: api-design-architect
description: Design principles for REST and GraphQL APIs in 2025. Enforces OpenAPI-first, versioning strategies, and standardized error responses.
license: MIT
---

## What I do
- Design RESTful resources (Nouns not Verbs).
- Define OpenAPI 3.1 specs *before* coding (Design-First).
- Structure GraphQL schemas with Federation in mind.
- Standardize Error Handling (RFC 7807 Problem Details).

## When to use me
- When defining API endpoints.
- When creating Swagger/OpenAPI documentation.
- When asked "how to structure this API".
- Triggers: "rest api", "graphql", "openapi", "swagger", "endpoint design".

## Instructions

### 1. REST Best Practices
- **Naming**: Plural nouns (`/users`, not `/user`). Kebab-case URLs (`/verification-codes`).
- **Versioning**: URI Versioning (`/v1/users`) is the most pragmatic choice for 2025 startups.
- **Methods**:
  - `POST`: Create
  - `PUT`: Replace (Full)
  - `PATCH`: Update (Partial)
  - `DELETE`: Remove

### 2. The Contract (OpenAPI)
- **Rule**: No code without a spec.
- **Validation**: Use tools like `spectral` to lint the OpenAPI spec.
- **Components**: Reuse schemas. Don't copy-paste `User` object definition across 10 endpoints.

### 3. Response Standardization
- **Success**: Always wrap data? Debatable, but consistence is key.
  - Recommended: `{ "data": { ... }, "meta": { ... } }`
- **Errors**: Use **RFC 7807** "Problem Details for HTTP APIs".
  ```json
  {
    "type": "https://api.example.com/probs/out-of-credit",
    "title": "You do not have enough credit.",
    "status": 403,
    "instance": "/account/12345/msgs/abc"
  }
  ```

### 4. GraphQL specifics
- **Nullable by Default**: In distributed systems, fields fail. Make them nullable.
- **Pagination**: Use Relay Cursor Connections standard (`edges`, `node`, `pageInfo`).
- **Security**: Max Depth limiting and Complexity analysis are mandatory.
