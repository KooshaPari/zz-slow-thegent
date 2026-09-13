# 01_RESEARCH

## Method

- Collected local standalone git roots with direct `.git` entries.
- Scanned worktree-forest roots under the Phenotype parent directory.
- Used focused slice passes for the largest families to avoid a single monolithic scan.

## Slice Findings

| Slice                                                  | Standalone roots | Main blockers                                                                                               |
| ------------------------------------------------------ | ---------------: | ----------------------------------------------------------------------------------------------------------- |
| `agentapi-plusplus` / `bifrost` / `agentops`           |                8 | legacy `*-wtrees`, one detached lane, two initializing lanes                                                |
| `cliproxy` / `helios` / `colab`                        |               11 | `heliosApp` dirty 353, `heliosCLI` dirty 96, duplicate `cliproxy-wtress`                                    |
| `AgilePlus` / `phenotype*`                             |               10 | mixed canonical + legacy layouts, `phenotype-shared` out-of-root lane, `phenotypeActions` dual forest roots |
| `template-*`                                           |               12 | no adjacent worktree forests found                                                                          |
| `portage` / `trace` / `trash-cli` / `ralph-codex-loop` |                8 | `portage` prunable stale lanes, `trace` locked lane, `trash-cli` detached lane                              |
| `thegent`                                              |                2 | canonical `.worktrees` present, but detached dirty legacy lane remains                                      |

## Notable Cleanest Areas

- `template-*` repos were the cleanest slice: standalone roots only, no nearby worktree forests.
- `phenotype-infrakit` and `phenotype-go-kit` were the lowest-noise repos in the phenotype slice.

## Notable Blockers

- `cliproxy-wtress` appears to be a typo twin of `cliproxy-wtrees` and should be treated as legacy duplication.
- `portage` lists prunable worktrees whose gitdir pointers no longer exist.
- `trace-wtrees/codex-required-gates` is locked and initializing.
- `thegent` legacy lane `lane-split-modules-bootstrap-v2` is now conflict-free, but still detached and dirty.
