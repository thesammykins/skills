---
name: docker-container-pro
description: Production-grade Docker/OCI image creation. Enforces security (non-root, SBOM), minimalism (multi-stage), and reproducibility (pinned versions).
license: MIT
---

## What I do
- Write optimized `Dockerfile`s using multi-stage builds.
- secure containers by enforcing non-root user execution.
- Reduce image size (Alpine/Distroless).
- Generate SBOMs (Software Bill of Materials).

## When to use me
- When creating a `Dockerfile` or `docker-compose.yml`.
- When optimizing CI/CD build times.
- When hardening container security.
- Triggers: "dockerfile", "containerize", "docker compose".

## Instructions

### 1. The Multi-Stage Standard
- **Pattern**:
  1.  `base`: Install dependencies.
  2.  `builder`: Compile/Build code.
  3.  `runner`: Minimal runtime (distroless or alpine) with ONLY artifacts.
- **Example**:
  ```dockerfile
  # Stage 1: Dep Install
  FROM node:20-alpine AS deps
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci

  # Stage 2: Build
  FROM node:20-alpine AS builder
  COPY --from=deps /app/node_modules ./node_modules
  COPY . .
  RUN npm run build

  # Stage 3: Run
  FROM gcr.io/distroless/nodejs20-debian11 AS runner
  COPY --from=builder /app/dist ./dist
  USER nonroot
  CMD ["dist/index.js"]
  ```

### 2. Security Hardening
- **User**: NEVER run as root. Create a user or use the image's provided non-root user (e.g., `node` user).
- **Secrets**: NEVER `COPY .env` into the image. Use secret mounts or environment variables at runtime.
- **Updates**: Run `apk update && apk upgrade` (or apt equivalent) in the build stage to patch vulnerabilities.

### 3. Reproducibility
- **Pinning**:
  - BAD: `FROM node:latest`
  - GOOD: `FROM node:20.12.0-alpine3.19` (SHA digest is even better for high security).
- **Lockfiles**: Always copy `package-lock.json` / `pnpm-lock.yaml` and use `npm ci` / `pnpm install --frozen-lockfile`.

### 4. Docker Compose Anti-Patterns
- **Version Field**: Don't use `version: '3.8'`. It's obsolete in the new Compose spec.
- **Restart Policy**: Use `restart: always` or `unless-stopped` for production services.
- **Healthchecks**: Mandatory for DBs and dependent services.
