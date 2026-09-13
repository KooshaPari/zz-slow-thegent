<DONE>
# Research: Remote Compute Implementation (Phase 4)

## Overview

Remote compute allows `thegent` to offload execution of agents and entire runs to a remote host (e.g. a powerful Linux server from a Mac). This is useful for:

- Environment parity: running in the same OS as the target project.
- Compute power: offloading LLM or tool execution to a more powerful machine.
- Geographic presence: running from a specific region/IP.

## Implementation Details

### CLI Interface

- `thegent run --remote user@host PROMPT [AGENT]`
- `thegent bg --remote user@host PROMPT [AGENT]`

### Process Flow

1.  **Local Preparation**:
    - Resolve agents, models, and routing policies.
    - Check budgets and trust boundaries.
    - Audit and sign the run metadata.
2.  **File Synchronization**:
    - The current working directory (project) is synced to the remote host using `rsync` over SSH.
    - Destination: `/tmp/thegent-run-<run_id>`.
3.  **Remote Execution**:
    - The `thegent` command is reconstructed (minus `--remote`) and executed on the remote host via SSH.
    - For `run` (foreground), it streams output back to the local terminal.
    - For `bg` (background), it uses `nohup` on the remote to ensure persistence.
4.  **Cleanup**:
    - (Future) Sync back modified files to local.
    - (Future) Delete remote temporary directory.

### Code Structure

- `thegent/src/thegent/research/remote_compute.py`: `RemoteComputeClient` handles SSH and `rsync` operations.
- `thegent/src/thegent/cli_impl.py`: `run_impl` and `bg_impl` intercept the `--remote` flag to offload execution.
- `thegent/src/thegent/cli.py`: Added `--remote` option to `run` and `bg` commands.

## Prerequisites

- `ssh` and `rsync` must be installed on the local machine.
- `thegent` must be installed and configured on the remote host.
- SSH key-based authentication is recommended for a seamless experience.

## Future Enhancements

- **Bi-directional Sync**: Automatically pull back changes made by the remote agent.
- **Remote Registry Consolidation**: View remote runs in the local `thegent ps` / `thegent history`.
- **Target Profiles**: Configure remote targets in `~/.thegent/config.yaml` with short aliases (e.g. `--remote dev-box`).
- **MCP Offload**: Only offload specific MCP tools or agent calls while keeping orchestration local.
- **Docker Integration**: Instead of a remote host, offload to a local or remote Docker container.
