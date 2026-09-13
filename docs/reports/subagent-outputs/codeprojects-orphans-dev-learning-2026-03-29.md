# CodeProjects inventory: orphans, Dev, learning

**Generated:** 2026-03-29  
**Scope:** Local directories under `~/CodeProjects/orphans`, `~/CodeProjects/Dev`, and `~/CodeProjects/learning`.

## Method

- **orphans / Dev:** Immediate child directories only (depth 1 under each base). Excluded: `node_modules` as a top-level child (none present).
- **learning:** Immediate children of `learning/`; where `learning/courses/` exists, each immediate child under `courses/` is listed as a separate row (effective depth 3 from `learning`: `learning/courses/<course>`).
- **Project-like:** Treated any immediate directory (except `node_modules`) as a candidate project folder.
- **README:** Yes if any of `README.md`, `README.rst`, `README`, `README.txt`, `readme.md`, `Readme.md` exists at that directory root.
- **Size:** `du -sh <path>` (total disk use of that tree).

## Base path status

| Path                                      | Status  |
| ----------------------------------------- | ------- |
| `/Users/kooshapari/CodeProjects/orphans`  | Present |
| `/Users/kooshapari/CodeProjects/Dev`      | Present |
| `/Users/kooshapari/CodeProjects/learning` | Present |

## `/Users/kooshapari/CodeProjects/orphans`

| Path                                                    | `.git` | README | Approx. size |
| ------------------------------------------------------- | ------ | ------ | ------------ |
| `/Users/kooshapari/CodeProjects/orphans/agslag-new`     | no     | no     | 3.6M         |
| `/Users/kooshapari/CodeProjects/orphans/can-2`          | no     | no     | 35M          |
| `/Users/kooshapari/CodeProjects/orphans/canvasApp`      | yes    | yes    | 166M         |
| `/Users/kooshapari/CodeProjects/orphans/experiments`    | no     | no     | 0B           |
| `/Users/kooshapari/CodeProjects/orphans/heliosHarness`  | no     | no     | 8.0K         |
| `/Users/kooshapari/CodeProjects/orphans/hoohacks`       | no     | no     | 183M         |
| `/Users/kooshapari/CodeProjects/orphans/infrastructure` | no     | no     | 0B           |
| `/Users/kooshapari/CodeProjects/orphans/ob`             | no     | yes    | 88M          |
| `/Users/kooshapari/CodeProjects/orphans/personal-docs`  | no     | no     | 384K         |
| `/Users/kooshapari/CodeProjects/orphans/schizo`         | no     | no     | 17M          |
| `/Users/kooshapari/CodeProjects/orphans/smartcp`        | no     | no     | 4.0K         |
| `/Users/kooshapari/CodeProjects/orphans/swift`          | no     | no     | 468K         |
| `/Users/kooshapari/CodeProjects/orphans/test-vendor`    | no     | no     | 6.6M         |

## `/Users/kooshapari/CodeProjects/Dev`

| Path                                            | `.git` | README | Approx. size |
| ----------------------------------------------- | ------ | ------ | ------------ |
| `/Users/kooshapari/CodeProjects/Dev/job-hunter` | no     | no     | 96K          |

## `/Users/kooshapari/CodeProjects/learning`

Only immediate subdirectory observed: `courses/`. Rows below are **immediate children of `learning/courses/`** (per maxdepth-3 course layout).

| Path                                                    | `.git` | README | Approx. size |
| ------------------------------------------------------- | ------ | ------ | ------------ |
| `/Users/kooshapari/CodeProjects/learning/courses/atoms` | no     | no     | 563M         |
| `/Users/kooshapari/CodeProjects/learning/courses/prior` | no     | no     | 1.5G         |
| `/Users/kooshapari/CodeProjects/learning/courses/spr26` | no     | yes    | 98M          |

## Summary counts

| Base                        | Project-like rows |
| --------------------------- | ----------------- |
| orphans                     | 13                |
| Dev                         | 1                 |
| learning (courses children) | 3                 |
| **Total**                   | **17**            |
