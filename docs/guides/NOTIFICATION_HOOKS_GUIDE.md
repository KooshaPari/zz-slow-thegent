# Notification Hooks Guide

This repo now includes hook-driven desktop notifications with optional voice alerts.

## What Fires

- `Stop`: from Rust `hook-dispatcher` (`stop` mode), includes profile and failures.
- `TaskCompleted`: from `hooks/task-completed.sh`.
- `SessionEnd`: from `hooks/session-cleanup.sh`.
- `TeammateIdle`: from `hooks/teammate-idle.sh` when idle sentinel is detected.

## Main Script

- `hooks/notify-agent-event.sh`

It is best-effort and never fails callers.

## Session Complete Voice Contract

For `sessionend`, spoken/message output is forced to:

`Session Complete - Chat X - <NOTI>`

Where:

- `Chat X` is a static per-session label persisted from `SESSION_ID` mapping.
- `<NOTI>` is the moving topic from latest user prompt, truncated to keep speech near ~5s.
- Topic source is updated by `hooks/prompt-submit-guard.sh` into `.claude/notify-topic.txt`.

## Spoken Contract (All Events)

Voice output is normalized to:

`<STATE> - <Agent> says - <NOTI>`

Examples:

- `Stop Issues - Codex says - quality checks reported failures`
- `Session Complete - Cursor says - Session Complete - Chat 4 - finalize DAG sync`

## Harness Detection

Notification subtitle includes harness context. Detection order:

1. `THGENT_HARNESS` env var from wrappers/shims.
2. Parent process scan (`cursor`, `codex/dex`, `claude/clode`, `droid/roid`).
3. fallback: `thegent`.

## Config (Env Vars)

- `THGENT_NOTIFY_ENABLE=0|1` (default `1`)
- `THGENT_NOTIFY_DRY_RUN=1` prints only, no OS push/voice
- `THGENT_NOTIFY_COOLDOWN_SEC=<int>` dedupe window (default `8`)
- `THGENT_NOTIFY_VOICE_MODE=errors|all|off` (default `errors`)
- `THGENT_NOTIFY_VOICE_NAME=<voice>` (macOS `say` voice, default `Samantha`)

## Platform Backends

- macOS: `osascript` desktop notification fallback (subtitle+title, then title-only), `say` voice.
- Linux: `notify-send`/`dunstify`, `spd-say`/`espeak` voice.
- Windows shells: `powershell.exe` MessageBox fallback.
- Last resort: terminal bell + stderr line.

## Apply Changes

Reinstall wrappers:

```bash
uv run thegent install-shims --all --force
```

Deploy hook dispatcher (if needed):

```bash
cp ~/.claude/bin/hook-dispatcher ~/.claude/bin/hook-dispatcher.bak-$(date +%Y%m%d-%H%M%S)
cp hooks/hook-dispatcher/target/release/hook-dispatcher ~/.claude/bin/hook-dispatcher
chmod +x ~/.claude/bin/hook-dispatcher
```
