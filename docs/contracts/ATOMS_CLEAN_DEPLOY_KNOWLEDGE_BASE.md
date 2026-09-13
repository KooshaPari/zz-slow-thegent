# Atoms Clean/Deploy Knowledge Base

## Purpose

This document is the cross-repo baseline for `atoms` clean/deploy behavior and environment discovery.
It codifies the canonical path and operational defaults used by this repo's automation and docs.

## 81) Cross-Repo Clean/Deploy Inventory

### `../atoms-mcp-prod`

| Surface                  | Source                                | Status                        |
| ------------------------ | ------------------------------------- | ----------------------------- |
| Clean entrypoint         | `Taskfile.yml` -> `clean` target      | Canonical                     |
| Clean CLI command        | `cli.py` -> `clean()` (`atoms clean`) | Canonical                     |
| Vercel deployment config | `vercel.json`                         | Canonical                     |
| Deployment guide         | `docs/DEPLOYMENT_GUIDE.md`            | Canonical                     |
| Cloud Run helper         | `scripts/deploy_gcp.sh`               | Non-canonical (legacy helper) |

### `../agentapi/atomsAgent`

| Surface                   | Source                                                  | Status     |
| ------------------------- | ------------------------------------------------------- | ---------- |
| Cloud Run command surface | `src/atomsAgent/cli/commands/cloud_run.py`              | Canonical  |
| Cloud Run deploy docs     | `docs/guides/deployment.md`                             | Canonical  |
| Infrastructure target     | `infrastructure/README.md` (IAC: SST Ion for Cloud Run) | Canonical  |
| Legacy deploy path        | Pulumi references removed from current flow             | Deprecated |

## 82) Canonical Clean/Deploy Path (as used by thegent)

### Canonical path recommendation

For shared operations documented in thegent, **prefer Vercel-first clean/deploy for `atoms-mcp-prod` and SST/Cloud Run for `atomsAgent`**.

- Canonical for MCP server: `../atoms-mcp-prod`
  - Clean via `atoms clean` (`../atoms-mcp-prod/cli.py` / `Taskfile.yml`).
  - Deploy via Vercel (`vercel.json` + `docs/DEPLOYMENT_GUIDE.md`).
- Canonical for Agent API service: `../agentapi/atomsAgent`
  - Deploy via `atoms-agent cloud-run deploy` (`src/atomsAgent/cli/commands/cloud_run.py`).
  - IAC is driven by SST (`infrastructure/README.md`).

### Deprecated/legacy paths

- Legacy Pulumi flows and older Cloud Run wrappers are explicitly treated as non-canonical and should not be used for standard delivery paths.

## 83) Env-Discovery Contract (Institutionalized)

### Contract objective

Any tooling that needs Atoms deployment secrets/environment values MUST resolve them through an explicit, ordered search order before failing. This prevents implicit environment drift and makes local/CI behavior deterministic.

### Canonical discovery order (hard requirement)

1. In-process explicit environment variables.
2. Workspace-specific overrides in the current repo (`.env`, `.env.local`).
3. Canonical project-level `atoms.tech` env files in the sibling `clean/deploy/atoms.tech` workspace:
   - `../clean/deploy/atoms.tech/.env.local`
   - `../clean/deploy/atoms.tech/.env`
4. Upward workspace fallback `atoms.tech/.env` siblings when present in parent locations.
5. `config/secrets.yml` (repo-level secret file when allowed by deployment mode).

### Hard-fail check definition

The contract is now executable and SHALL fail hard when required variables are missing.

- Required for `atoms-mcp-prod` canonical deploy:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN`
  - `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL`
  - `WORKOS_API_KEY`
  - `WORKOS_CLIENT_ID`
  - `CRON_SECRET`
- Required for `atomsAgent` canonical deploy:
  - `ATOMS_SECRET_AUTHKIT_JWKS_URL`
  - `ATOMS_SECRET_SUPABASE_URL`
  - `ATOMS_SECRET_SUPABASE_KEY`
  - `ATOMS_SECRET_VERTEX_PROJECT_ID`
  - `ATOMS_SECRET_VERTEX_LOCATION`

Legacy or optional variables (for debug/local workflows only) must never be treated as canonical gates.

Operational check command:

```bash
uv run python scripts/validate_atoms_env_discovery.py --repo atoms-mcp-prod
uv run python scripts/validate_atoms_env_discovery.py --repo atomsagent
```

Contract checks fail with non-zero exit codes and emit strict error details for the missing variable and the expected source path.

### Contract implementation notes

- `agentapi/atomsAgent/scripts/generate_supabase_models.py` follows this ordered fallback for env and secret lookup and remains the operational reference for DB model tooling.
- `thegent/scripts/validate_atoms_env_discovery.py` is the canonical hard-fail checker used by the gent for pre-deploy/CI validation.
- CI/ops tasks should treat missing mandatory environment variables as hard failures once this contract scope is invoked.
- Future env loader changes in sibling repos must update this section and the checker together in the same task.

## Operational Check

Before any release-like cleanup/deploy operation:

1. Verify the target repo path matches the canonical entry above.
2. Verify the command matches canonical clean/deploy operation.
3. Verify env inputs are present in at least one allowed source from the contract.
4. If env resolution requires additional sources, update this contract and source code together in the same task.
