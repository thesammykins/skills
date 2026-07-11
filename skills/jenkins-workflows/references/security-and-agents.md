# Security And Agents

Jenkins build scripts execute user-controlled code. Default to safe placement, narrow credentials, and explicit resource limits.

## Current Instance Facts

Discover the current state before making decisions:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" nodes
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" plugins
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" jobs
```

Key things to determine from live inspection:
- Jenkins version and whether CSRF crumbs are required
- Which nodes/agents are online and their labels
- Which plugins are installed (especially Pipeline, Docker Workflow, Credentials Binding)
- Whether existing jobs are Freestyle or Pipeline

Re-check live state before relying on cached facts.

## Agent Placement

- Prefer non-controller agents for arbitrary build/test/package work.
- Avoid `Built-In Node` unless explicitly accepted by the user or the work is a controller-only administrative inspection.
- Use a macOS agent or `macos && arm64` label expression for macOS/Apple Silicon workflows.
- If a Linux workflow has no non-controller agent available, ask whether to use the controller temporarily or set up a Linux agent.

## Secrets

- Store secrets in Jenkins credentials, not in repos or Jenkinsfiles.
- Scope credentials to the smallest stage and command block possible.
- Use `withCredentials` for nontrivial credential bindings.
- Use single-quoted Groovy strings for `sh`, `bat`, `powershell`, and `pwsh` blocks that reference secrets so secrets are expanded by the shell, not Groovy.
- Do not echo secrets. Jenkins masking reduces accidental disclosure but does not prevent all exfiltration.

## Pipeline Controls

- Add `timeout` to prevent stuck builds.
- Add `buildDiscarder` to control retained logs/artifacts.
- Use `disableConcurrentBuilds` or locking when jobs mutate shared resources.
- Use `junit` and `archiveArtifacts` for actionable results.
- Clean workspaces with `cleanWs` when the plugin is present.

## Pull Requests And Untrusted Code

- Treat PR builds as untrusted unless repository permissions prove otherwise.
- Do not expose trusted deployment credentials to untrusted PR branches.
- Avoid automatically running expensive jobs for public/untrusted PRs without filtering or approval.
- Prefer `when` guards and `input` gates for deployment stages.

## Mutations Requiring Confirmation

Ask before:

- Creating, reconfiguring, disabling, enabling, or deleting Jenkins jobs.
- Triggering deployments, releases, destructive cleanup, or long/expensive workflows.
- Installing/updating plugins.
- Changing nodes, labels, executors, security, global config, or credentials.
