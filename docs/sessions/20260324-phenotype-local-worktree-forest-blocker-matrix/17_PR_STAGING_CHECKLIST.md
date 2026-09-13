# PR staging checklist — Tier 2 wave (2026-03-24)

Use this when turning **Tier 2** deliverables into **one PR per repo** (or one stacked PR per policy). **Preflight:** `git fetch --all` on each remote; prefer authoring from a **worktree** branch per [AGENTS.md](../../../../../AGENTS.md).

---

## 1. heliosApp

| Path                                       | Role                                     |
| ------------------------------------------ | ---------------------------------------- |
| `.github/workflows/ci.yml`                 | Bun **1.2.20** on all jobs               |
| `.github/workflows/vitepress-pages.yml`    | Bun **1.2.20** (parity with `ci.yml`)    |
| `.github/workflows/compliance-check.yml`   | Bun pin                                  |
| `.github/workflows/quality-gates.yml`      | Bun pin                                  |
| `.github/pull_request_template.md`         | Worktree + runtime / quality-gates notes |
| `CHANGELOG.md`                             | Unreleased + link                        |
| `docs/guides/troubleshooting-local-dev.md` | ENOSPC / `.tmp` / Bun / secrets          |

**Verify before PR:**

```bash
rg 'bun-version' .github/workflows
# Expect 1.2.20 everywhere; no `latest`.
```

**Stage (adjust paths if your checkout differs):**

```bash
git add \
  .github/workflows/ci.yml \
  .github/workflows/vitepress-pages.yml \
  .github/workflows/compliance-check.yml \
  .github/workflows/quality-gates.yml \
  .github/pull_request_template.md \
  CHANGELOG.md \
  docs/guides/troubleshooting-local-dev.md
```

**Commit message (example):**

`chore(ci,docs): pin Bun 1.2.20 across workflows, PR template, CHANGELOG, local dev troubleshooting`

---

## 2. colab

| Path              | Role               |
| ----------------- | ------------------ |
| `CONTRIBUTING.md` | New                |
| `.gitignore`      | `.tmp/`, IDE stubs |

```bash
git add CONTRIBUTING.md .gitignore
```

**Commit message (example):** `docs: add CONTRIBUTING and ignore scratch paths`

---

## 3. helMo

| Path              | Role     |
| ----------------- | -------- |
| `CONTRIBUTING.md` | New      |
| `.gitignore`      | Expanded |

```bash
git add CONTRIBUTING.md .gitignore
```

**Commit message (example):** `docs: add CONTRIBUTING and expand gitignore`

---

## 4. helios-cli

| Path                   | Role                     |
| ---------------------- | ------------------------ |
| `docs/contributing.md` | Scratch / `.tmp` section |
| `.gitignore`           | `.tmp/`                  |

```bash
git add docs/contributing.md .gitignore
```

**Commit message (example):** `docs: document scratch dirs and ignore .tmp`

**Note:** If your branch is already a long-lived chore branch (for example `chore/normalize-dirty-*`), confirm with maintainers whether to **rebase onto `main`** and open a fresh PR or **continue** the existing branch.

---

## 5. Phenotype `repos/` hub README (not a git repo)

`Phenotype/repos/README.md` is **not** inside a git repository; it is a **filesystem** index for the multi-repo hub.

**Canonical, versioned copy:** [phenotype_repos_hub.md](../../../reference/phenotype_repos_hub.md) in **thegent**.

After merging thegent, **sync** the markdown body to `repos/README.md` (same content as the “hub” section of the reference doc, with `./AGENTS.md` links as in the on-disk file).

---

## 6. thegent (session + reference)

| Path                                                                                               | Role                |
| -------------------------------------------------------------------------------------------------- | ------------------- |
| `docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/16_PARALLEL_AGENT_AUDIT.md` | Tier 1–2 audit      |
| `docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/17_PR_STAGING_CHECKLIST.md` | This checklist      |
| `docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/ACTIVE_BACKLOG.md`          | Session log         |
| `docs/reference/phenotype_repos_hub.md`                                                            | Versioned hub index |

```bash
git add \
  docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/16_PARALLEL_AGENT_AUDIT.md \
  docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/17_PR_STAGING_CHECKLIST.md \
  docs/sessions/20260324-phenotype-local-worktree-forest-blocker-matrix/ACTIVE_BACKLOG.md \
  docs/reference/phenotype_repos_hub.md
```

**Commit message (example):** `docs(session): PR staging checklist and versioned Phenotype repos hub reference`

---

## Optional: open PRs with GitHub CLI

```bash
gh pr create --title "..." --body-file ...
```

Use **one PR per repo** unless your stack policy requires otherwise. **Do not merge** while required checks are red (including **Actions billing** issues on **thegent**).

---

## Cross-links

- Tier 2 inventory: **`16_PARALLEL_AGENT_AUDIT.md`** (executed table).
- Blockers: **`05_KNOWN_ISSUES.md`**.
