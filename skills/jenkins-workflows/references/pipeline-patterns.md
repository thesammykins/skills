# Jenkins Pipeline Patterns

Use Declarative Pipeline by default. Keep Groovy thin and put real work in repo scripts or single shell blocks so execution happens on the agent, not the controller.

## Baseline Pipeline

```groovy
pipeline {
    agent { label 'your-macos-agent' }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds(abortPrevious: true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
./scripts/ci.sh
'''
            }
        }
    }

    post {
        always {
            junit testResults: '**/test-results/**/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'artifacts/**/*', allowEmptyArchive: true, fingerprint: true
            cleanWs(deleteDirs: true, disableDeferredWipeout: true, notFailBuild: true)
        }
    }
}
```

## Label Selection

Inspect live labels first with `jenkins_job.py nodes`.

Known labels (replace with your own from `jenkins_job.py nodes`):

- `your-macos-agent`
- `your-agent-prefix`
- `apple-silicon`
- `arm64`
- `macos`
- `built-in`

Prefer `your-macos-agent` for macOS/Apple Silicon jobs. Avoid `built-in` unless the user explicitly accepts controller execution or there is no suitable agent.

Use label expressions when useful:

```groovy
agent { label 'macos && arm64' }
```

## Project Command Discovery

Match the repo's package manager and scripts. Examples:

```groovy
stage('Node Verify') {
    steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
corepack enable
pnpm install --frozen-lockfile
pnpm test
pnpm build
'''
    }
}
```

```groovy
stage('Swift Verify') {
    steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
swift test
'''
    }
}
```

```groovy
stage('Python Verify') {
    steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
uv sync --frozen
uv run ruff check .
uv run pytest
'''
    }
}
```

## Parameters

Use parameters for explicit runtime choices, not secrets:

```groovy
parameters {
    choice(name: 'TARGET', choices: ['staging', 'production'], description: 'Deployment target')
    booleanParam(name: 'RUN_E2E', defaultValue: false, description: 'Run E2E tests')
}
```

Gate risky stages:

```groovy
stage('Deploy') {
    when {
        beforeAgent true
        branch 'main'
    }
    input {
        message "Deploy to ${params.TARGET}?"
        ok 'Deploy'
    }
    steps {
        sh './scripts/deploy.sh "$TARGET"'
    }
}
```

## Secrets

Use Jenkins credentials, scoped as narrowly as possible:

```groovy
stage('Publish') {
    steps {
        withCredentials([string(credentialsId: 'npm-token', variable: 'NPM_TOKEN')]) {
            sh '''#!/usr/bin/env bash
set -euo pipefail
npm config set //registry.npmjs.org/:_authToken "$NPM_TOKEN"
npm publish
'''
        }
    }
}
```

Use single-quoted Groovy strings for shell scripts that reference secrets. Let the shell expand environment variables; do not use Groovy interpolation for secret values.

## Docker

Do not emit `agent { docker ... }` unless `docker-workflow` is installed and a Docker-capable agent label exists. This Jenkins did not have `docker-workflow` installed when checked on 2026-04-24.

If Docker support is later installed, prefer pinned images and explicit labels:

```groovy
pipeline {
    agent {
        docker {
            image 'node:24.15.0-alpine3.23'
            label 'linux && docker'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh 'node --version && npm test'
            }
        }
    }
}
```
