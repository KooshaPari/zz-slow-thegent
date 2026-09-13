# Tasks: Shared Modules Rollout 2026-02-28

## Phased WBS + DAG

| Phase | Task ID | Description                                                      | Depends On                                | Branch                           | Worktree                                                                                                       |
| ----- | ------- | ---------------------------------------------------------------- | ----------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A     | WT-01   | Extract reusable policy gate module and validate in `helios-cli` | none                                      | `mod/policy-gate-v1`             | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/helios-cli--mod-policy-gate-v1`                     |
| A     | WT-03   | Extract polyglot config core contract from `phenotype-config`    | none                                      | `mod/polyglot-config-core-v1`    | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/phenotype-config--mod-polyglot-config-core-v1`      |
| B     | WT-02   | Normalize CLI task surface module (`lint/test/build/release`)    | WT-01                                     | `mod/cli-task-surface-v1`        | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/helios-cli--mod-cli-task-surface-v1`                |
| B     | WT-04   | Extract provider ledger schema + tooling                         | WT-03                                     | `mod/provider-ledger-schema-v1`  | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/tokenledger--mod-provider-ledger-schema-v1`         |
| B     | WT-05   | Extract proxy auth/access SDK module                             | WT-03                                     | `mod/proxy-auth-access-sdk-v1`   | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/cliproxyapi-plusplus--mod-proxy-auth-access-sdk-v1` |
| C     | WT-06   | Extract queue orchestrator as reusable module                    | WT-02                                     | `mod/queue-orchestrator-v1`      | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/portage--mod-queue-orchestrator-v1`                 |
| C     | WT-07   | Extract OpenAPI+SSE agent client module                          | WT-05                                     | `mod/openapi-agent-client-v1`    | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/agentapi-plusplus--mod-openapi-agent-client-v1`     |
| D     | WT-08   | `thegent` app-composition cutover (orchestration-only)           | WT-01,WT-02,WT-03,WT-04,WT-05,WT-06,WT-07 | `mod/thegent-app-composition-v1` | `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/thegent--mod-app-composition-v1`                    |

## Lane Acceptance Checklist (applies to every WT-XX)

1. Module package metadata and versioning are present.
2. Public interface contract is documented.
3. Module-local tests pass.
4. At least one consumer integration test passes.
5. Lint/type/security checks pass in host repo.
6. Migration note identifies removed duplicate code paths.

## Stop Rules

1. If a lane changes files owned by another active lane, stop and split scope.
2. If contract tests fail in more than two consumer repos, open a contract-fix lane first.
3. If governance gate state is red in host repo, pause feature extraction and repair gates.
4. If merge-base drift causes replay conflicts, rebase lane and restage atomic commits before PR.

## Next 24 Tasks (Child-Lane Plan)

Status legend:

- `[todo]` not started
- `[in_progress]` actively executing
- `[blocked]` blocked by dependency or environment gate
- `[done]` completed and verified

| Phase | Child Lane | Task ID | [status] | Description                                                                                                      | Depends On                 |
| ----- | ---------- | ------- | -------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------- |
| C     | CA-L1      | CA-01   | [todo]   | Create reusable policy-gate module package skeleton in `helios-cli` lane with versioned contract surface.        | WT-01                      |
| C     | CA-L1      | CA-02   | [todo]   | Add policy-gate module tests and contract fixtures; enforce fail-fast behavior and remove legacy fallbacks.      | CA-01                      |
| C     | CA-L1      | CA-03   | [todo]   | Integrate policy-gate module into one consumer command path and delete duplicated host logic.                    | CA-02                      |
| C     | CA-L1      | CA-04   | [todo]   | Run lane quality gates (`lint`, `types`, `tests`) and publish lane evidence note for WT-01.                      | CA-03                      |
| C     | CA-L2      | CA-05   | [todo]   | Create polyglot config core module contract and schema package in `phenotype-config` lane.                       | WT-03                      |
| C     | CA-L2      | CA-06   | [todo]   | Add strict schema validation tests and negative contract tests for malformed config payloads.                    | CA-05                      |
| C     | CA-L2      | CA-07   | [todo]   | Replace one repo-local config parser with core module API and remove duplicated parser code.                     | CA-06                      |
| C     | CA-L2      | CA-08   | [todo]   | Run lane quality gates and capture migration note with removed legacy config paths.                              | CA-07                      |
| D     | CA-L3      | CA-09   | [todo]   | Implement CLI task surface module (`lint/test/build/release`) with thin wrapper adapters in `helios-cli`.        | WT-02, CA-04               |
| D     | CA-L3      | CA-10   | [todo]   | Add command contract tests for task surface parity and error-exit semantics.                                     | CA-09                      |
| D     | CA-L3      | CA-11   | [todo]   | Switch one host command group to module-backed execution and delete prior inline implementation.                 | CA-10                      |
| D     | CA-L3      | CA-12   | [todo]   | Validate module with targeted integration tests and produce lane handoff evidence.                               | CA-11                      |
| D     | CA-L4      | CA-13   | [todo]   | Extract provider ledger schema/tooling module in `tokenledger` lane with stable package entrypoints.             | WT-04, CA-08               |
| D     | CA-L4      | CA-14   | [todo]   | Add schema compatibility tests plus migration fixture validating existing ledger records.                        | CA-13                      |
| D     | CA-L4      | CA-15   | [todo]   | Replace one consumer ledger implementation with module import and remove duplicate types.                        | CA-14                      |
| D     | CA-L4      | CA-16   | [todo]   | Run quality gates and generate contract validation evidence for rollout index.                                   | CA-15                      |
| E     | CA-L5      | CA-17   | [todo]   | Extract proxy auth/access SDK module and publish explicit auth boundary contract.                                | WT-05, CA-08               |
| E     | CA-L5      | CA-18   | [todo]   | Add SDK integration tests covering token validation, permissions checks, and failure contracts.                  | CA-17                      |
| E     | CA-L5      | CA-19   | [todo]   | Migrate one host API path to SDK module and remove duplicate auth/access code path.                              | CA-18                      |
| E     | CA-L5      | CA-20   | [todo]   | Run lane quality/security gates and publish consumer migration checklist.                                        | CA-19                      |
| F     | CA-L6      | CA-21   | [todo]   | Execute `thegent` app-composition boundary contract update to orchestration-only ownership.                      | WT-08, CA-12, CA-16, CA-20 |
| F     | CA-L6      | CA-22   | [todo]   | Wire queue orchestrator and OpenAPI+SSE client modules into app composition layer.                               | WT-06, WT-07, CA-21        |
| F     | CA-L6      | CA-23   | [todo]   | Add end-to-end composition tests proving no domain ownership leakage in app layer.                               | CA-22                      |
| F     | CA-L6      | CA-24   | [todo]   | Final rollout closeout: run full quality gate, update tracker statuses, and prepare merge-ready evidence packet. | CA-23                      |

## Execution Notes

1. Child lanes are independent by module concern and can run in parallel up to dependency boundaries.
2. Any overlap with active files in another lane triggers Stop Rule 1 and immediate lane split.
3. Merge sequence should follow lane closeout evidence order: `CA-L1` -> `CA-L2` -> `CA-L3`/`CA-L4`/`CA-L5` -> `CA-L6`.

## Next 24 Tasks (Child-Lane Plan Wave 2)

| Phase | Child Lane | Task ID | [status] | Description                                                                                                                                     | Depends On  |
| ----- | ---------- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| G     | CG-L1      | CG-01   | [todo]   | Add policy-gate module contract version checks and explicit breaking-change guardrails.                                                         | CA-04       |
| G     | CG-L1      | CG-02   | [todo]   | Add golden tests for policy-gate error surfaces across consumer command variants.                                                               | CG-01       |
| G     | CG-L1      | CG-03   | [todo]   | Add config-core schema strictness profile for module consumers with no fallback modes.                                                          | CA-08       |
| G     | CG-L1      | CG-04   | [todo]   | Run cross-module compatibility tests for policy-gate + config-core in one integration lane.                                                     | CG-02,CG-03 |
| H     | CH-L2      | CH-01   | [todo]   | Add CLI task-surface telemetry hooks for command outcome and duration metrics.                                                                  | CA-12       |
| H     | CH-L2      | CH-02   | [todo]   | Add provider-ledger schema migration verifier command for pre-merge checks.                                                                     | CA-16       |
| H     | CH-L2      | CH-03   | [todo]   | Add contract tests for telemetry and schema verifier output stability.                                                                          | CH-01,CH-02 |
| H     | CH-L2      | CH-04   | [todo]   | Remove remaining duplicated task orchestration glue from host repo paths.                                                                       | CH-03       |
| I     | CI-L3      | CI-01   | [todo]   | Add proxy auth/access SDK resilience tests for revoked credentials and malformed claims.                                                        | CA-20       |
| I     | CI-L3      | CI-02   | [todo]   | Add API consumer migration matrix documenting per-endpoint SDK adoption status.                                                                 | CI-01       |
| I     | CI-L3      | CI-03   | [todo]   | Migrate second consumer path to SDK and delete old permission-check helpers.                                                                    | CI-02       |
| I     | CI-L3      | CI-04   | [todo]   | Run targeted integration/security checks for migrated SDK consumers.                                                                            | CI-03       |
| J     | CJ-L4      | CJ-01   | [todo]   | Add queue orchestrator contract tests for retry semantics and deterministic replay ordering.                                                    | CA-24       |
| J     | CJ-L4      | CJ-02   | [todo]   | Add OpenAPI+SSE client streaming compatibility tests against representative consumers.                                                          | CA-24       |
| J     | CJ-L4      | CJ-03   | [todo]   | Wire orchestration adapters for queue/client modules in one staging composition path.                                                           | CJ-01,CJ-02 |
| J     | CJ-L4      | CJ-04   | [todo]   | Run composition smoke suite validating no domain logic leakage into orchestration layer.                                                        | CJ-03       |
| K     | CK-L5      | CK-01   | [todo]   | Add static architecture checks enforcing orchestration-only boundaries in `thegent` app layer.                                                  | CA-24       |
| K     | CK-L5      | CK-02   | [todo]   | Add regression tests for app-composition command paths using only module interfaces.                                                            | CK-01       |
| K     | CK-L5      | CK-03   | [todo]   | Remove remaining boundary violations detected by architecture checks.                                                                           | CK-02       |
| K     | CK-L5      | CK-04   | [todo]   | Re-run full app-composition quality pipeline and capture boundary compliance evidence.                                                          | CK-03       |
| L     | CL-L6      | CL-01   | [todo]   | Add governance checklist automation for module adoption readiness gates.                                                                        | CK-04,CI-04 |
| L     | CL-L6      | CL-02   | [todo]   | Add evidence packet generator script (tests, lint, contract, migration, boundary checks).                                                       | CL-01       |
| L     | CL-L6      | CL-03   | [todo]   | Add merge-readiness validator for lane ordering and dependency completion.                                                                      | CL-02       |
| L     | CL-L6      | CL-04   | [todo]   | Publish Wave 2 closeout report and mark rollout tracker statuses for integration handoff.                                                       | CL-03       |
| L     | CL-L6      | CL-05   | [todo]   | Harden `templates/vitepress-unified` asset and base-url handling so generated docs do not 404 on CSS, JS, font, or favicon assets.              | CK-04       |
| L     | CL-L6      | CL-06   | [todo]   | Add a generated-site smoke check that classifies SES lockdown warnings, blocked RUM posts, and extension noise separately from app regressions. | CL-05       |

### Wave 2 Notes

1. Wave 2 starts only after `CA-24` reaches `[done]`.
2. Lanes `G/H/I/J/K` can execute in parallel after upstream dependencies complete.
3. Lane `L` is serialized closeout and merge-governance gating.
