<DONE>
# Research: CLI-Share Strategies & Nested Isolation (L1/L2)

**Date**: 2026-02-19
**Status**: Deep-Research / Architecture Specification
**Focus**: Optimizing CLI resource usage through Speculative Execution, Debouncing, Merging, and Queuing within the Nested Isolation Model.

---

## 1. The CLI-Share Philosophy

"CLI-Share" is the collective set of strategies `thegent` uses to ensure that multiple agents (L2) working under the same management (L1) do not duplicate expensive OS-level work. It transforms the CLI from a series of isolated processes into a **cooperative execution mesh**.

---

## 2. Speculative Execution & L1/L2 Mapping

When an agent invokes a `--speculative` command, it is effectively branching the execution tree.

### 2.1 Speculation Isolation

- **Mechanism**: Each speculative path is assigned a dedicated **L2 Sub-user** with a T2 (OverlayFS) isolation tier.
- **L1 Context**: All speculative L2s share the same **L1 OS User** identity and project-level build caches (e.g., `target/`, `node_modules/`).
- **Nesting**:
  - `L1 (Lead)`: Owns the persistent cache and project lock.
  - `L2 (Spec_A)`: Ephemeral workspace for Path A.
  - `L2 (Spec_B)`: Ephemeral workspace for Path B.

### 2.2 Result Racing (RACE_FIRST / RACE_BEST)

- **Shared State**: A `results.jsonl` file in the L1 home directory acts as the "Race Track."
- **Early Termination**: As soon as `Spec_A` finishes with a passing test, the L1 Lead sends a `SIGKILL` to the `PGID` of `Spec_B` to reclaim resources immediately.

---

## 3. Command Debouncing & "Command Sharing"

If two specialists (L2) concurrently decide to run a heavy setup command like `npm install` or `uv sync`.

### 3.1 The Global Command Lock

- **Location**: `.thegent/locks/cmd_<hash>.lock`
- **Detection**: Before execution, the `SubUserIsolationProvider` hashes the command and the current `package-lock.json` or `Cargo.lock`.
- **Debouncing**: If a lock exists and is active, the second agent **attaches** to the first agent's stdout/stderr stream instead of spawning a new process.

### 3.2 Output Merging

- Once the first command finishes, the output is cached in the L1 layer.
- The second agent receives the cached output instantly, fulfilling the "share" promise.

---

## 4. Cross-Project Queuing & Concurrency

### 4.1 Similarity Queuing

- **Scenario**: You are running `thegent` in Project A and Project B simultaneously.
- **Strategy**: If Project B attempts a heavy build that overlaps with Project A's resource usage, the `ConcurrencyController` places Project B into a **Resource Queue**.
- **Burst Mode**: If the system detects a "Burst Load," it automatically de-prioritizes non-critical L2 agents (e.g., documentation researchers) to give full CPU/IO priority to the L1 task currently in the foreground.

### 4.2 Escalation & SLA

- Queued tasks that exceed their **SLA** (e.g., 60 seconds) are automatically moved to the `EscalationQueue`.
- The user receives a notification: _"Speculative task for Project B is blocked. Increase resource budget?"_

---

## 5. Smart Merge (Structural & AST)

Merging an L2's ephemeral changes back into the L1's persistent state requires more than just `git merge`.

### 5.1 AST-Aware Merging (Mergiraf)

- **Protocol**: When an L2 finishes, it generates an `Intent` (diff + AST metadata).
- **Conflict Prediction**: The L1 Lead compares the `Intents` of all active L2s. If `L2_A` and `L2_B` both intend to modify `AuthService.ts`, the L1 enforces a **Structural Lock** on that file, forcing `L2_B` to wait until `L2_A` merges.
- **Import Union**: The `SmartMerger` automatically resolves common merge conflicts in Python/JS imports by taking the union of both sets.

---

## 6. Security & Interop Implications

### 6.1 The Bridge (MaildirQueue)

- Communication between L1 and L2 uses a **Maildir-style IPC** in `/tmp/thegent-bridge`.
- This is file-system based, ensuring that even if an L2 is heavily sandboxed (T3 Landlock), it can still "post" its command requests and results to the L1 Lead without needing a network socket.

### 6.2 Permission Handover

- L2 sub-users are created with **No-New-Privs**.
- If an L2 needs a privileged operation (e.g., `thegent install`), it must send a **Capability Request** to the L1 Lead. The L1 Lead performs the operation and "shares" the resulting files back to the L2's OverlayFS layer.

---

## 7. Next Steps for Polish

1. **Implement `thegent.orchestration.cmd_share`**: A module to handle command hashing and lock-attachment.
2. **Refine `SmartMerger`**: Integrate Mergiraf more deeply into the `SubUserIsolationProvider.cleanup_tenant` flow.
3. **Expand `ConcurrencyController`**: Add "Project Priority" weights to handle multi-project queuing fairly.
