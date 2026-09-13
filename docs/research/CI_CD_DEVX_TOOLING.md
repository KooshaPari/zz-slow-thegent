<DONE>
# CI/CD and Developer Experience Tooling Research Report (2025-2026)

**Research Date:** February 2026
**Scope:** CI/CD Platforms, Quality Gates, Developer Experience, Monitoring & Feedback

---

## Executive Summary

This research provides a comprehensive analysis of the CI/CD and Developer Experience (DevEx) tooling landscape for 2025-2026. The ecosystem has evolved significantly toward AI-augmented workflows, autonomous validation, and integrated developer platforms.

**Key Findings:**

1. **GitHub Actions** dominates as the primary CI/CD platform with advanced matrix builds, reusable workflows, and native integrations
2. **Quality gates** now require multi-layer security scanning (SAST, DAST, dependency, secrets) integrated into CI pipelines
3. **Developer Experience** tools focus on preview environments, automated feedback loops, and AI-powered code review
4. **Build optimization** through caching, parallelization, and intelligent test execution is critical for fast CI feedback
5. **Monitoring** extends beyond build metrics to include Flaky test detection, performance budgets, and ChatOps integrations

**Recommendations:**

- Adopt GitHub Actions with composite reusable workflows for standardization
- Implement pre-commit hooks for local quality enforcement before CI
- Use multi-layer security scanning: CodeQL (SAST) + Snyk (dependencies) + gitleaks (secrets)
- Enable preview deployments for all PRs via Vercel or equivalent
- Implement Renovate for automated dependency updates

---

## 1. CI/CD Platforms & Workflows

### 1.1 Platform Comparison

| Platform            | Best For                         | Pricing (2025)                     | Key Strength                           |
| ------------------- | -------------------------------- | ---------------------------------- | -------------------------------------- |
| **GitHub Actions**  | Open-source, Microsoft ecosystem | Free (2K min/mo); $0.008/min after | Native GitHub integration, marketplace |
| **GitLab CI/CD**    | Full DevOps platform             | Free (CI limited); $19+/user/mo    | Integrated planning, source, CI/CD     |
| **CircleCI**        | Enterprise, scalability          | Free tier; paid from $15/mo        | Autonomous validation, AI features     |
| **Jenkins**         | Self-hosted, legacy systems      | Free (open-source)                 | Full control, extensive plugins        |
| **AWS CodeBuild**   | AWS ecosystem                    | Pay-per-use ($0.005/min Linux)     | Native AWS integration                 |
| **Azure Pipelines** | Microsoft enterprise             | Free (1.8K min/mo); $40/vCPU-hr    | Cross-platform, Azure integration      |

### 1.2 GitHub Actions Advanced Workflows

GitHub Actions remains the dominant choice for modern CI/CD due to its marketplace ecosystem and native integration.

#### Matrix Builds for Multi-Version Testing

```yaml
# Example: Matrix build for Node.js, Python, and multiple OS
name: Matrix Build

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        python-version: [3.10, 3.11, 3.12]
        include:
          - os: ubuntu-latest
            node-version: 22
            python-version: 3.12
            coverage: true

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: "npm"

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Install dependencies
        run: |
          npm ci
          pip install -r requirements.txt

      - name: Run tests
        run: npm test

      - name: Upload coverage
        if: matrix.coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

#### Reusable Workflows for Standardization

```yaml
# .github/workflows/reusable-lint.yml
name: Reusable Lint Workflow

on:
  workflow_call:
    inputs:
      language:
        type: string
        required: true
      linter:
        type: string
        default: "eslint"
    secrets:
      token:
        required: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup ${{ inputs.language }}
        uses: actions/setup-${{ inputs.language }}-@v4
        with:
          ${{ inputs.language }}-version: "latest"

      - name: Run linter
        run: |
          npx ${{ inputs.linter }} .
        env:
          GITHUB_TOKEN: ${{ secrets.token }}
```

#### Build Caching Strategies

```yaml
# Caching for npm, pip, and build outputs
name: Build with Caching

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # npm cache
      - name: Cache npm packages
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-npm-

      # pip cache
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # Build artifacts cache
      - name: Cache build outputs
        uses: actions/cache@v4
        with:
          path: |
            dist/
            build/
          key: ${{ runner.os }}-build-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-build-

      - name: Install and build
        run: npm ci && npm run build
```

### 1.3 Self-Hosted vs. Cloud Runners

| Factor            | Cloud Runners  | Self-Hosted Runners     |
| ----------------- | -------------- | ----------------------- |
| **Setup Time**    | Instant        | 1-2 hours               |
| **Cost**          | Pay-per-minute | Fixed infrastructure    |
| **Security**      | Vendor-managed | Full data control       |
| **Customization** | Limited        | Full OS/package control |
| **Scalability**   | Auto-scale     | Manual/provisioned      |
| **Maintenance**   | Zero           | Team responsibility     |

**Recommendation:**

- **Cloud**: For startups and small teams (GitHub-hosted runners)
- **Self-hosted**: For enterprise with compliance requirements, large builds, or private network access
- **Hybrid**: Cloud for PR checks, self-hosted for production builds

---

## 2. Quality Gates & Automation

### 2.1 Pre-Commit Hooks with pre-commit

[pre-commit](https://pre-commit.com/) provides local quality enforcement before code reaches CI.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 0.32.0
    hooks:
      - id: check-github-workflows
      - id: check-github-actionschemas

  - repo: https://github.com/shellcheck-py/shellcheck-precommit
    rev: v0.4.1
    hooks:
      - id: shellcheck

  - repo: local
    hooks:
      - id: custom-secret-scan
        name: Secret Detection
        entry: python -m detect_secrets
        language: system
        types: [python, yaml, json]
        pass_filenames: true
```

**Installation:**

```bash
pip install pre-commit
pre-commit install --install-hooks
```

**CI Integration:**

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit

on:
  pull_request:
  push:
    branches: [main]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: pre-commit/action@v3.0.1
```

### 2.2 Code Coverage Integration

[Codecov](https://about.codecov.io/) provides unified coverage reporting with AI-powered insights.

```yaml
# .github/workflows/test-coverage.yml
name: Test Coverage

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm test -- --coverage

      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: false
```

**Coverage Thresholds:**

```yaml
# codecov.yml
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 1%
        if_ci_failed: success
    patch:
      default:
        target: 80%
```

### 2.3 Security Scanning Stack

#### SAST with CodeQL

[CodeQL](https://codeql.github.com/) is "free for research and open source" and identifies vulnerabilities across codebases.

```yaml
# .github/workflows/codeql.yml
name: CodeQL Security Analysis

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  codeql:
    name: CodeQL
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript, typescript, python
          queries: security-extended

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{matrix.language}}"
          upload: true
```

#### Dependency Scanning with Snyk

[Snyk](https://snyk.io/) provides multi-layer security scanning.

```yaml
# .github/workflows/snyk.yml
name: Snyk Security

on:
  push:
    branches: [main]
  pull_request:

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload results to GitHub Security tab
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --sarif-file-output=snyk.sarif

      - name: Upload result to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: snyk.sarif
```

#### Secrets Detection with gitleaks

```yaml
# .github/workflows/secrets.yml
name: Secrets Detection

on:
  push:
    branches: [main]
  pull_request:

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_CONFIG_PATH: .gitleaks.toml
```

### 2.4 Complete Quality Gates Workflow

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  pull_request:
    branches: [main]

jobs:
  pre-commit:
    name: Pre-commit Hooks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: pre-commit/action@v3.0.1

  lint:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript, typescript, python
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  build:
    name: Build Check
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run build
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

---

## 3. Developer Experience

### 3.1 Pull Request Automation

#### Automating Dependency Updates with Renovate

[Renovate](https://github.com/renovatebot/renovate) supports 90+ package managers and connects with GitHub, GitLab, Bitbucket, and Azure DevOps.

```json
// renovate.json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "group:allNonMajor", "schedule:weekly"],
  "packageRules": [
    {
      "matchPackagePatterns": ["*"],
      "matchUpdateTypes": ["minor", "patch"],
      "groupName": "all non-major dependencies",
      "automerge": true,
      "automergeType": "pr"
    },
    {
      "matchPackagePatterns": ["eslint", "prettier"],
      "matchUpdateTypes": ["major"],
      "labels": ["breaking"]
    }
  ],
  "prHourlyLimit": 2,
  "prConcurrentLimit": 10
}
```

**GitHub App Setup:**

1. Install Renovate from GitHub Marketplace
2. Select repositories to manage
3. Renovate creates PRs automatically based on schedule

### 3.2 Preview Environments

#### Vercel Previews

[Vercel](https://vercel.com/features/previews) provides automatic preview deployments for every PR with built-in feedback tools.

**Features:**

- "A deployment for every idea"
- "Zero-config to deploy. Instantly share your work."
- Vercel Toolbar for iteration on localhost, staging, or production
- Built-in commenting on deployments
- Feature flags for experimentation
- Accessibility auditing
- Layout shift analysis

**Configuration:**

```json
// vercel.json
{
  "github": {
    "enabled": true,
    "autoJobCancelation": true
  },
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    }
  ]
}
```

#### Self-Hosted Preview with ngrok/tunnel

For self-hosted solutions, create preview environments:

```yaml
# .github/workflows/preview.yml
name: Preview Environment

on:
  pull_request:

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install and build
        run: npm ci && npm run build

      - name: Start preview server
        run: npm run preview &

      - name: Create tunnel with ngrok
        uses: ngrok/ngrok-api-action@v2
        with:
          authtoken: ${{ secrets.NGROK_AUTHTOKEN }}
          port: 3000
          subdomain: pr-${{ github.event.pull_request.number }}

      - name: Comment PR with preview URL
        uses: actions/github-script@v7
        with:
          script: |
            const url = '${{ steps.ngrok.outputs.url }}';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `Preview deployed: ${url}`
            })
```

### 3.3 ChatOps Integrations

#### Slack Notifications

```yaml
# .github/workflows/notify-slack.yml
name: Slack Notification

on:
  workflow_run:
    workflows: [Quality Gate]
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion }}
    steps:
      - name: Slack Notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author,took
          author_name: CI Pipeline
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Discord Notifications

```yaml
# .github/workflows/discord-notify.yml
name: Discord Notification

on:
  push:
    branches: [main]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Discord notification
        uses: somewhere2/discord-webhook-action@v1
        with:
          webhook-url: ${{ secrets.DISCORD_WEBHOOK_URL }}
          username: CI Bot
          content: "Build ${{ github.run_number }} ${{ job.status }}"
```

### 3.4 Developer Portals

| Tool          | Purpose                   | Best For                    |
| ------------- | ------------------------- | --------------------------- |
| **Backstage** | Internal developer portal | Enterprise, service catalog |
| **Port**      | Developer portal          | Self-service, IaC           |
| **Roadie**    | Backstage as a service    | Quick Backstage setup       |
| **Doppler**   | Secrets management        | Env var management          |
| **ApiTree**   | API documentation         | API-first teams             |

---

## 4. Monitoring & Feedback

### 4.1 CI/CD Metrics & Observability

#### Key Metrics to Track

| Metric               | Description                               | Target     |
| -------------------- | ----------------------------------------- | ---------- |
| **Build Duration**   | Time from trigger to completion           | < 10 min   |
| **Flaky Test Rate**  | % of tests with non-deterministic results | < 2%       |
| **MTTR**             | Mean time to recover from failures        | < 30 min   |
| **PR Cycle Time**    | Time from PR open to merge                | < 24 hours |
| **Code Review Time** | Time to first review                      | < 4 hours  |
| **Pass Rate**        | % of builds passing                       | > 90%      |

#### GitHub Actions Insights

```yaml
# .github/workflows/metrics.yml
name: CI Metrics

on:
  workflow_run:
    workflows: [Quality Gate]
    types: [completed]

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - name: Extract workflow metrics
        id: metrics
        run: |
          echo "build_time=${{ github.event.workflow_run.run_started_at }}" >> $GITHUB_OUTPUT

      - name: Send to Datadog
        if: success()
        run: |
          curl -X POST "https://api.datadoghq.com/api/v1/series" \
            -H "Content-Type: application/json" \
            -H "DD-API-KEY: ${{ secrets.DD_API_KEY }}" \
            -d '{
              "series": [{
                "metric": "ci.build.success",
                "type": "count",
                "points": [[{{ timestamp }}, 1]]
              }]
            }'
```

### 4.2 Build Failure Diagnostics

```yaml
# Enhanced error reporting
name: Enhanced Build Diagnostics

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests with verbose output
        run: npm test 2>&1 | tee test-output.log

      - name: Upload diagnostics on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-diagnostics
          path: |
            test-output.log
            .npm/_logs/
            coverage/

      - name: Comment failures to PR
        if: failure() && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const log = fs.readFileSync('test-output.log', 'utf8');
            const lastLines = log.split('\n').slice(-50).join('\n');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `Build failed. Last 50 lines of test output:\n\`\`\`\n${lastLines}\n\`\`\``
            })
```

### 4.3 Integrated Monitoring Stack

```yaml
# Complete observability pipeline
name: Full Observability

on:
  push:
    branches: [main]
  pull_request:

jobs:
  # Performance budget check
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            https://example.com
          budgetPath: ./lighthouse-budget.json
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}

  # Bundle size tracking
  bundle:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm run build

      - name: Check bundle size
        uses: andresz1/size-limit-action@v2
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

  # Uptime monitoring
  uptime:
    runs-on: ubuntu-latest
    steps:
      - name: Post-deployment check
        run: |
          curl -f https://example.com/health || exit 1
```

---

## 5. Recommended Tooling Stack (2026)

### 2025-5.1 Tier 1: Essential (Free/Open Source)

| Category   | Tool                          | Purpose                   |
| ---------- | ----------------------------- | ------------------------- |
| CI/CD      | GitHub Actions                | Primary CI/CD platform    |
| Pre-commit | pre-commit                    | Local quality enforcement |
| Linting    | ruff (Python), eslint (JS/TS) | Code quality              |
| Formatting | ruff-format, prettier         | Code formatting           |
| Coverage   | codecov                       | Coverage reporting        |
| Secrets    | gitleaks                      | Secrets detection         |
| SAST       | CodeQL                        | Static analysis           |

### 5.2 Tier 2: Enhanced (Free Tier/Paid)

| Category           | Tool          | Cost      | Purpose                |
| ------------------ | ------------- | --------- | ---------------------- |
| Dependency Updates | Renovate      | Free/Paid | Automated PRs          |
| Preview Deploys    | Vercel        | Free tier | PR previews            |
| Security           | Snyk          | Free/Paid | Vulnerability scanning |
| Notifications      | Slack/Discord | Free      | Team alerts            |

### 5.3 Tier 3: Enterprise

| Category              | Tool              | Purpose                  |
| --------------------- | ----------------- | ------------------------ |
| Developer Portal      | Backstage         | Service catalog          |
| Release Orchestration | Octopus Deploy    | Complex deployments      |
| Enterprise CI         | GitLab Ultimate   | Full DevOps platform     |
| Monitoring            | Datadog/New Relic | Full-stack observability |

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

1. Set up GitHub Actions workflows
2. Configure pre-commit hooks
3. Add basic linting (ruff, eslint)
4. Enable codecov integration
5. Set up secrets scanning

### Phase 2: Security (Week 3-4)

1. Add CodeQL analysis
2. Integrate Snyk dependency scanning
3. Configure dependency updates with Renovate
4. Set up security code scanning alerts

### Phase 3: Developer Experience (Week 5-6)

1. Configure preview deployments
2. Set up ChatOps notifications
3. Add performance budgets
4. Implement bundle size tracking

### Phase 4: Observability (Week 7-8)

1. Set up CI/CD metrics dashboard
2. Configure build failure diagnostics
3. Add Flaky test detection
4. Implement MTTR tracking

---

## Appendix A: GitHub Actions Best Practices Checklist

- [ ] Use `actions/checkout@v4` (latest major version)
- [ ] Always specify version tags, not `@master` or `@main`
- [ ] Use caching for npm, pip, and build outputs
- [ ] Implement matrix builds for multi-version testing
- [ ] Use reusable workflows for common patterns
- [ ] Set appropriate concurrency groups to cancel outdated runs
- [ ] Add timeout-minutes to prevent stuck jobs
- [ ] Use conditional steps with `if:` to skip unnecessary work
- [ ] Upload build artifacts for debugging failed builds
- [ ] Use environment protections for production deployments

---

## Appendix B: Sample .github Directory Structure

```
.github/
├── ISSUE_TEMPLATE/
│   └── bug_report.md
├── workflows/
│   ├── quality-gate.yml      # Main CI pipeline
│   ├── security.yml         # Security scanning
│   ├── preview.yml          # Preview deployments
│   ├── release.yml         # Release automation
│   └── metrics.yml          # Observability
├── dependabot.yml           # Dependency updates
└── renovate.json            # Renovate config
```

---

## Appendix C: Security Scanning Matrix

| Tool           | Type            | Languages | Free         | Integration    |
| -------------- | --------------- | --------- | ------------ | -------------- |
| **CodeQL**     | SAST            | 20+       | OSS/Research | GitHub         |
| **Snyk**       | DAST/Dependency | 20+       | Limited      | GitHub, GitLab |
| **SonarQube**  | SAST            | 20+       | Community    | GitHub, GitLab |
| **Semgrep**    | SAST            | 20+       | Yes          | GitHub, GitLab |
| **bandit**     | SAST            | Python    | Yes          | GitHub Actions |
| **trufflehog** | Secrets         | All       | Yes          | GitHub Actions |
| **gitleaks**   | Secrets         | All       | Yes          | GitHub Actions |

---

## Appendix D: References & Sources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pre-commit Documentation](https://pre-commit.com/)
- [CircleCI Platform](https://circleci.com/product/)
- [CodeQL](https://codeql.github.com/)
- [Snyk Security](https://snyk.io/)
- [Codecov](https://about.codecov.io/)
- [Renovate](https://github.com/renovatebot/renovate)
- [Vercel Previews](https://vercel.com/features/previews)

---

## 7. Pipeline Examples

### 7.1 Complete Quality Gate Pipeline

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  pull_request:
    branches: [main]

env:
  NODE_VERSION: "20"
  PYTHON_VERSION: "3.11"

jobs:
  # Phase 1: Static Analysis
  static-analysis:
    name: Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"

      - name: Install dependencies
        run: |
          pip install ruff pre-commit
          npm ci

      - name: Run pre-commit
        uses: pre-commit/action@v3.0.1

      - name: Run ruff linter
        run: ruff check .

      - name: Run ruff formatter check
        run: ruff format --check .

      - name: Run type checking (Python)
        run: pyright src/ || true

      - name: Run type checking (TypeScript)
        run: npx tsc --noEmit

  # Phase 2: Unit Tests
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: static-analysis
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
        include:
          - os: ubuntu-latest
            python-version: "3.11"
            coverage: true

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"

      - name: Install Python dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov

      - name: Install Node dependencies
        run: npm ci

      - name: Run Python tests
        run: pytest tests/ --cov=src --cov-report=xml
        if: matrix.python-version != '3.10'

      - name: Run Python tests (3.10)
        run: pytest tests/ --ignore=tests/test_type_heavy.py
        if: matrix.python-version == '3.10'

      - name: Run Node.js tests
        run: npm test

      - name: Upload coverage
        if: matrix.coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  # Phase 3: Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -e .[test]
          pip install pytest-asyncio httpx

      - name: Start MCP server
        run: |
          python -m thegent serve &
          sleep 5

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Collect logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: integration-logs
          path: logs/

  # Phase 4: Security Scan
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4

      - name: Run CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python, typescript
          queries: security-extended

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Run dependency audit
        uses: actions/github-script@v7
        with:
          script: |
            const { execSync } = require('child_process');
            try {
              execSync('pip-audit', { stdio: 'inherit' });
            } catch (e) {
              console.log('Vulnerabilities found');
            }

  # Phase 5: Build Verification
  build:
    name: Build
    runs-on: ubuntu-latest
    needs: security-scan
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"

      - name: Install and build
        run: |
          pip install -e .
          npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

### 7.2 thegent Remote Execution Pipeline

```yaml
# .github/workflows/remote-execution.yml
name: Remote Execution

on:
  workflow_dispatch:
    inputs:
      host:
        description: "Target host (windows-pc)"
        required: true
        default: "windows-pc"
      command:
        description: "Command to execute"
        required: true
      environment:
        description: "Environment (dev|staging|prod)"
        required: false
        default: "dev"

jobs:
  execute:
    name: Execute on ${{ github.event.inputs.host }}
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Sync to remote
        run: |
          rsync -avz --delete \
            --exclude='.venv' \
            --exclude='node_modules' \
            --exclude='dist' \
            --exclude='.git' \
            ./ "developer@${{ github.event.inputs.host }}:D:/kush/"

      - name: Execute command
        run: |
          ssh "developer@${{ github.event.inputs.host }}" << 'EOF'
            cd D:/kush
            ${{ github.event.inputs.command }}
          EOF

      - name: Sync back artifacts
        if: always()
        run: |
          rsync -avz \
            "developer@${{ github.event.inputs.host }}:D:/kush/dist/" \
            ./dist/

      - name: Upload artifacts
        if: success()
        uses: actions/upload-artifact@v4
        with:
          name: remote-artifacts
          path: dist/
```

### 7.3 Matrix Build Pipeline

```yaml
# .github/workflows/matrix-build.yml
name: Matrix Build

on:
  push:
    branches: [main]
  pull_request:

jobs:
  matrix-build:
    name: Build (${{ matrix.os }} / Python ${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
        exclude:
          # Skip macOS with Python 3.12 (not yet available)
          - os: macos-latest
            python-version: "3.12"

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Setup uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv pip install -e .[dev]

      - name: Run tests
        run: pytest tests/ -v --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.xml
          flags: ${{ matrix.os }}-${{ matrix.python-version }}

  # Additional platform-specific builds
  platform-specific:
    name: Platform-Specific Tests
    runs-on: ${{ matrix.runner }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - runner: windows-latest
            task: "task test-windows"
          - runner: macos-latest
            task: "task test-macos"

    steps:
      - uses: actions/checkout@v4

      - name: Run platform-specific task
        run: ${{ matrix.task }}
```

### 7.4 Scheduled Maintenance Pipeline

```yaml
# .github/workflows/maintenance.yml
name: Scheduled Maintenance

on:
  schedule:
    # Daily at 2 AM UTC
    - cron: "0 2 * * *"
  # Manual trigger
  workflow_dispatch:

jobs:
  dependency-update:
    name: Check Dependency Updates
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run pip-compile
        uses: app-actions/tools@v1
        with:
          cmd: |
            pip install pip-tools
            pip-compile --output-file=requirements.txt pyproject.toml --upgrade

      - name: Create PR if updates available
        uses: peter-evans/create-pull-request@v6
        with:
          title: "chore: Update dependencies"
          commit-message: "chore: Update dependencies"
          body: "Automated dependency updates"
          branch: dependency-updates

      - name: Report updates
        if: steps.cpr.outputs.pull-request-number
        run: |
          echo "PR created: ${{ steps.cpr.outputs.pull-request-url }}"
          gh pr comment ${{ steps.cpr.outputs.pull-request-number }} \
            --body "Dependency updates ready for review"

  cleanup:
    name: Cleanup Old Artifacts
    runs-on: ubuntu-latest
    steps:
      - name: Delete old artifacts
        uses: c-hive/gha-remove-artifacts@v1
        with:
          age: "7 days"

      - name: Delete old runs
        uses: matiev-dev/delete-workflow-runs@v1
        with:
          age: "30 days"
          keep-min: 10

  health-check:
    name: System Health Check
    runs-on: ubuntu-latest
    steps:
      - name: Check GitHub Actions
        run: curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/${{ github.repository }}/actions

      - name: Check external services
        run: |
          curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/thegent/json || echo "PyPI check failed"
          curl -s -o /dev/null -w "%{http_code}" https://npmjs.com/package/thegent || echo "NPM check failed"

      - name: Report health
        uses: slackapi/slack-github-action@v1.25.0
        with:
          payload: |
            {
              "text": "Daily health check completed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Daily Health Check*\nStatus: ✅ Complete\nTime: ${{ github.event.repository.updated_at }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 8. Cross-References

| Topic               | Reference                                           |
| ------------------- | --------------------------------------------------- |
| CLI Patterns        | `API_CLI_DEVOPS_TOOLING.md`                         |
| TUI/Queue Design    | `USER_QUEUE_TUI_AND_AGENT_POLL.md`                  |
| Hybrid Environment  | `../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md` |
| Implementation Plan | `../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md`        |

---

## 9. Extension Summary

### Added in This Extension

| Section                  | Description                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| **7. Pipeline Examples** | Added complete quality gate, remote execution, matrix build, and scheduled maintenance pipelines |
| **8. Cross-References**  | Added links to related documentation                                                             |
| **9. Extension Summary** | This summary section                                                                             |

### Key Pipeline Patterns

| Example              | Purpose                                                            |
| -------------------- | ------------------------------------------------------------------ |
| 7.1 Quality Gate     | Multi-phase CI/CD with static analysis, tests, security, and build |
| 7.2 Remote Execution | SSH-based remote command execution                                 |
| 7.3 Matrix Build     | Multi-platform, multi-version testing                              |
| 7.4 Maintenance      | Scheduled cleanup and health checks                                |

### Integration Points

| Pipeline         | Integrates With                         |
| ---------------- | --------------------------------------- |
| Quality Gate     | Ruff, pytest, CodeQL, gitleaks, codecov |
| Remote Execution | SSH, rsync, GitHub Actions              |
| Matrix Build     | uv, pytest, codecov                     |
| Maintenance      | pip-tools, Slack                        |

---

**Document Version:** 1.1
**Last Updated:** 2026-02-17
**Extension:** Pipeline Examples, Cross-References, Extension Summary

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [API_CLI_DEVOPS_TOOLING.md](./API_CLI_DEVOPS_TOOLING.md) - API/CLI tooling
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
