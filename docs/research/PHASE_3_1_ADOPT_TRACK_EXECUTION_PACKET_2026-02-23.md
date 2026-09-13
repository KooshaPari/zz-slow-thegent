<DONE>
# Phase 3.1 Adopt Track Execution Packet

Date: February 23, 2026

## Scope

- Advanced to post-research execution track `1` from `docs/research/PHASE_2_FINAL_COMPLETION_SUMMARY_2026-02-23.md`.
- Created adopt-lane integration playbooks for all 16 `adopt` repos.

## Playbook Artifacts

- `docs/research/PHASE3_ADOPT_LANE_1_PLAYBOOK.md`
- `docs/research/PHASE3_ADOPT_LANE_2_PLAYBOOK.md`
- `docs/research/PHASE3_ADOPT_LANE_3_PLAYBOOK.md`
- `docs/research/PHASE3_ADOPT_LANE_4_PLAYBOOK.md`

## Immediate Spike Queue (Execution Order)

1. `https://github.com/errata-ai/vale`
2. `https://github.com/upstash/context7`
3. `https://github.com/steveyegge/beads`
4. `https://github.com/getzep/graphiti`
5. `https://github.com/nats-io/nats-server`
6. `https://github.com/LMCache/LMCache`

## Why This Order

- Prioritizes direct value to `thegent` + `cliproxy` governance and agent reliability surfaces.
- Starts with low-risk/high-leverage integration (`vale`) before memory/runtime infra.
- Defers heavier platform moves (`ory/kratos`, `zed`, `pocketbase`) until first spike batch proves governance gates and rollback flow.

## Gate Contract (Required For Each Spike)

- Security: policy presence + dependency scan path.
- License: explicit license compatibility check.
- CI: reproducible build/test in isolated lane.
- Release: pinned version/tag and documented rollback command.

## Exit Criteria

- Each spike has:
  - integration diff in dedicated worktree/branch
  - pass/fail result on target acceptance checks
  - rollback verified
  - short report appended under `docs/research/`

## Status

- Phase 3.1 planning/execution packet: complete.
- Next action: implement Spike Batch A (items 1-3).
