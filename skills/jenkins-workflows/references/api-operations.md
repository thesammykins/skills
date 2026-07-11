# Jenkins API Operations

Use `scripts/jenkins_job.py` for normal operations. It sends preemptive Basic Auth, avoids printing secrets, and supports folder job paths.

## Session Environment

Set these once per terminal session to avoid repeated 1Password prompts:

```bash
export JENKINS_URL="http://your-jenkins-host:8080"
export JENKINS_USER_ID="$(op read 'op://your-vault/jenkins-api-key/username')"
export JENKINS_API_TOKEN="$(op read 'op://your-vault/jenkins-api-key/credential')"
```

Do not persist `JENKINS_API_TOKEN` in shell startup files or project files.

You can also load these with the bundled sourceable helper:

```bash
source "$HOME/.agents/skills/jenkins-workflows/scripts/load_jenkins_env.sh"
```

## Read-Only Inspection

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" whoami
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" root
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" jobs
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" nodes
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" plugins
```

## Job Paths

Pass simple jobs as `job-name` and folder jobs as `folder/subfolder/job-name`. The helper converts these to Jenkins' `/job/folder/job/subfolder/job/job-name` URL form.

Examples:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" job-info your-smoke-job
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" job-info folder-name/job-name
```
...
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" trigger your-smoke-job --follow
```

Pass parameters as `KEY=VALUE`:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" trigger release-job \
  -p TARGET=staging \
  -p RUN_E2E=true \
  --follow
```

Use `console` for existing builds:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" console your-smoke-job --build lastBuild
```

## Raw API

Use `api` only when the named commands are not enough:

```bash
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" api GET /whoAmI/api/json
python3 "$HOME/.agents/skills/jenkins-workflows/scripts/jenkins_job.py" api GET '/computer/api/json?tree=computer[displayName,offline,assignedLabels[name]]'
```

For POST requests, the helper can include a Jenkins crumb with `--crumb`. API-token Basic Auth is normally exempt from CSRF crumbs, but crumb support is useful for compatibility.

## Response Handling

- `401`: bad username/token. Re-read 1Password refs and verify `JENKINS_USER_ID`.
- `403`: missing permission or missing crumb for a mutating request.
- `404`: bad job path or missing permission hiding the job.
- Queue item never starts: inspect nodes/labels and executor availability.
- Build result not `SUCCESS`: treat the Jenkins run as failed and inspect console output.
