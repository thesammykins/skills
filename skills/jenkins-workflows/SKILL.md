---
name: jenkins-workflows
description: Create, inspect, trigger, and monitor Jenkins CI/CD workflows on the user's Jenkins server instead of running substantial build/test/deploy work on the local Mac. Use when Codex is asked to set up Jenkins workflows, write Jenkinsfiles, move local commands to CI, trigger or monitor Jenkins jobs, inspect Jenkins agents/labels/plugins, or run build/test/package/release automation remotely through Jenkins.
---

# Jenkins Workflows

Use this skill to move substantial build, test, packaging, and release work onto Jenkins rather than running it directly from the local Codex shell.

## Instance Defaults

- Default URL: `http://your-jenkins-host:8080`
- Determine the exact version and user by running `python3 jenkins_job.py whoami`
- 1Password username ref: `op://your-vault/jenkins-api-key/username`
- 1Password API token ref: `op://your-vault/jenkins-api-key/credential`

## Authentication

Prefer session environment variables to avoid repeated 1Password prompts:

```bash
export JENKINS_URL="http://your-jenkins-host:8080"
export JENKINS_USER_ID="$(op read 'op://your-vault/jenkins-api-key/username')"
export JENKINS_API_TOKEN="$(op read 'op://your-vault/jenkins-api-key/credential')"
```

Or source the bundled helper:

```bash
source "$HOME/.agents/skills/jenkins-workflows/scripts/load_jenkins_env.sh"
```

Use the env vars first. If they are absent, read the 1Password refs just in time. Never print the token, write it into repo files, shell startup files, Jenkinsfiles, logs, or comments.

Use preemptive Basic Auth (`username:api_token`). Jenkins returns `403` or `401` without a negotiation round-trip, so commands should send auth on the first request.

## Decision Rules

1. Prefer Jenkins for non-trivial build/test/package/deploy work.
2. Use the local shell only for source inspection, small edits, local validation that cannot reasonably run in Jenkins, or when Jenkins is unreachable.
3. Prefer a repo-owned `Jenkinsfile` over UI-only job configuration.
4. Prefer Declarative Pipeline unless an existing job or plugin requires otherwise.
5. Inspect current nodes, labels, plugins, and jobs before selecting a pipeline pattern.
6. Do not assume Docker Pipeline support. This Jenkins did not have `docker-workflow` installed when checked on 2026-04-24.
7. Avoid the Jenkins controller/built-in node for arbitrary builds. If no matching non-controller agent exists, ask whether to run on the controller or set up an agent.

## Workflow

1. Inspect Jenkins read-only state:
   - `python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" whoami`
   - `python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" nodes`
   - `python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" jobs`
   - `python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" plugins`
2. Inspect the repository for existing CI files and project commands.
3. Choose an agent label from live Jenkins data.
4. Add or update `Jenkinsfile` using `references/pipeline-patterns.md`.
5. Trigger an existing safe build/test job only when the user asked for a run or clearly expects verification.
6. Follow queue/build output through Jenkins and report the final build URL and result.

## Safety Policy

- Read-only Jenkins API inspection is allowed without additional confirmation.
- Ask before creating, updating, disabling, enabling, or deleting Jenkins jobs.
- Ask before triggering deploys, release jobs, destructive cleanup, infrastructure changes, or expensive/long-running jobs.
- Ask before installing plugins, changing nodes/agents, changing credentials, or altering Jenkins global configuration.
- Use Jenkins credentials bindings for secrets in Pipeline. Do not hardcode secrets or interpolate secrets into Groovy strings.
- Use `timeout`, `buildDiscarder`, and workspace cleanup where appropriate.

## Helper Script

Use `scripts/jenkins_job.py` for Jenkins API operations. It reads `JENKINS_URL`, `JENKINS_USER_ID`, and `JENKINS_API_TOKEN` first, then falls back to the 1Password refs above.

Common commands:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" whoami
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" nodes
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" job-info your-smoke-job
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" trigger your-smoke-job --follow
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" console your-smoke-job --build lastBuild
```

Use `scripts/load_jenkins_env.sh` with `source` to populate session env vars once without persisting the token.

## References

- Read `references/pipeline-patterns.md` before writing a `Jenkinsfile`.
- Read `references/api-operations.md` before triggering or monitoring jobs directly through the API.
- Read `references/security-and-agents.md` before choosing labels, credentials, or controller/agent placement.
