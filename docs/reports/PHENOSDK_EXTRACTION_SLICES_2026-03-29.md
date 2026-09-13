# phenoSDK extraction slices (2026-03-29)

**Source tree:** `repos/worktrees/phenoSDK/main` (clone of `github.com/KooshaPari/phenoSDK`)  
**Governance:** `docs/governance/23_ARCHITECTURAL_GOVERNANCE.md`

## Reality check

- **Python-first** monolith; publish other languages as separate Phenotype libs with SDD contracts.
- `src/pheno/` names `domain`, `application`, `ports`, `adapters` — use as migration compass; expect boundary leakage.

## Top packages by `.py` file count

| Package       | ~Files | Extraction theme                                            |
| ------------- | -----: | ----------------------------------------------------------- |
| testing       |    198 | QA harness → `phenotype-evaluation`, `template-program-ops` |
| infra         |    198 | Adapters → `phenotype-infrakit`, `phenotype-ops`            |
| kits          |    117 | Optional meta-packages, not core SDK                        |
| mcp           |    104 | MCP → `phenotype-thegent-mcp` patterns + contracts          |
| ui            |     97 | Thin client; decouple from domain                           |
| cli           |     74 | `phenotype-cli-core` or dedicated CLI product repo          |
| dev           |     71 | Dev UX → thegent/skills, not runtime SDK                    |
| deployment    |     66 | `phenotype-infrakit`, IaC templates                         |
| quality       |     64 | `phenotype-dep-guard`, shared hooks                         |
| adapters      |     60 | Keep pattern; move impls to infra repos                     |
| shared        |     54 | Dedup → `phenotype-shared`                                  |
| workflow      |     51 | Task/agent engines                                          |
| domain        |     50 | Smallest public “core” API                                  |
| database      |     31 | Ports + one reference adapter per store                     |
| vector        |     29 | Port + optional Rust hot path later                         |
| application   |     26 | Migrate with domain                                         |
| observability |     23 | `phenotype-logging-zig`, OTel helpers                       |
| credentials   |     23 | Dedicated small lib                                         |
| clink         |     23 | Optional sidecar                                            |
| tools         |     22 | Scripts → ops templates or archive                          |
| auth          |     22 | Parity with `phenotype-auth-ts` / Python kits               |
| security      |     21 | Align `policy-contract`                                     |
| patterns      |     20 | Docs or `hexagonal-py` examples                             |
| analytics     |     20 | Split generic vs product before move                        |
| ports         |     19 | **SDD source of truth** — OpenAPI/Proto                     |
| logging       |     18 | Shared facades                                              |
| llm           |     16 | Provider ports; adapters elsewhere                          |
| cicd          |     11 | Templates only                                              |

**Debt:** `infra` and `infrastructure` both exist — converge naming before publish.

## Waves

1. **A — Contracts (SDD):** `ports/` + public DTOs → versioned packages; generate TS/Go clients.
2. **B — Domain + application:** → `libs/python/…` + import-linter / `hexagonal-py`.
3. **C — Cross-cutting:** `auth`, `credentials`, `security`, `logging`, `observability`.
4. **D — Integrations:** `mcp`, `llm`, `providers`, `clink`, `vector` → optional extras or separate repos.
5. **E — Ops:** `deployment`, `cicd`, `kits`, `infra` → infrakit/templates.
6. **F — CLI / UI:** bind last to stable APIs.

## PyO3 / native

Only after profiling; one narrow extension behind a Python port; align with existing Phenotype Rust/Zig logging patterns.

## AgilePlus

Child feature: `phenosdk-wave-a-contracts` (specify → plan → implement per wave).

**Ports inventory:** `PHENOSDK_PORTS_INVENTORY_2026-03-29.md`
