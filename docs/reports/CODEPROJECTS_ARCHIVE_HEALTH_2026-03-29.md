# CodeProjects/archive local health pass (2026-03-29)

Scope: `/Users/kooshapari/CodeProjects/archive` top-level directories **excluding** large `.zip.zst` / `.zst` blobs (cold storage, not working trees).

## Directory signals

| Directory                 | Approx size | FS mtime   | Git repo | README |
| ------------------------- | ----------- | ---------- | -------- | ------ |
| ai-agents                 | 59M         | 2026-03-24 | no       | no     |
| APIAgent                  | 183M        | 2026-03-24 | no       | no     |
| dmouse                    | 2.5G        | 2026-03-24 | no       | no     |
| Kinfra                    | 75M         | 2025-10-29 | no       | no     |
| local2                    | 342M        | 2025-05-09 | **yes**  | yes    |
| localbase                 | 109M        | 2026-02-27 | no       | yes    |
| netweave-3                | 213M        | 2025-07-15 | **yes**  | yes    |
| ProjectManagementPlatform | 134M        | 2025-06-22 | no       | no     |
| Rust                      | 4.5G        | 2024-09-22 | no       | no     |
| TripleM                   | 201M        | 2026-02-27 | **yes**  | yes    |
| archived                  | 0B          | 2026-02-24 | no       | no     |

## Interpretation

- **Largest disk sinks:** `Rust/`, `dmouse/` — candidates for compress + document + deduplicate against GitHub remotes.
- **Git-backed:** `local2`, `netweave-3`, `TripleM` — attach remotes, branch, or archive intentionally.
- **No README / no git:** higher friction; add provenance `README.md` or delete after snapshot.

## Blobs (same folder)

`Archive.zip.zst`, `Archive 2.zip.zst`, `mcp.zip.zst`, `mcp_official-2.zip.zst`, `ProjectManagementPlatform.zip.zst`, `amp.zst` — optional `archive/MANIFEST.md` follow-up.

## Related GitHub state

Names overlap **GitHub-archived** repos (`TripleM`, `localbase` family). Verify `git remote -v` before any push.
