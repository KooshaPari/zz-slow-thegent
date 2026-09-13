# 00_SESSION_OVERVIEW

## Goal

Inventory local standalone git roots under `Phenotype/repos`, compare them to the public `KooshaPari` GitHub repo surface, and record exact overlap and gaps.

## Scope

- Local standalone git roots under `/Users/kooshapari/CodeProjects/Phenotype/repos`
- Public GitHub repositories under `KooshaPari`
- Case-insensitive basename comparison only

## Method

- Local inventory counted only directories with a direct `.git` entry at the repo root.
- Worktree lanes, archived mirrors, and nested non-root workspaces were not counted as standalone repos.
- GitHub inventory initially came from the public `GET /users/kooshapari/repos?per_page=100&page=N`
  endpoint, then from authenticated `gh repo list KooshaPari --visibility public|private`.

## Snapshot

- Local standalone git roots: `55`
- Public GitHub repos: `81`
- Authenticated GitHub repos: `131`
- Private repos visible to the token: `50`
- Archived repos visible to the token: `25`
- Forks visible to the token: `18`
- Exact basename overlap: `39`
- Local-only basenames: `16`
- GitHub-only basenames: `92`
- Snapshot timestamp: `2026-03-24T08:18:45Z`

## Key Result

- The two surfaces overlap on the core Phenotype/thegent/helios family, but the account-visible repo surface is much larger than the local standalone root set because it includes private, archived, and forked repositories.

## References

- `01_RESEARCH.md`
