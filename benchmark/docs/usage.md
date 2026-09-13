# Usage

## Local Docker (default)

```bash
harbor jobs start \
  --dataset terminal-bench-sample@2.0 \
  --agent codex \
  --model minimax-m2.5 \
  --n-concurrent 4
```

## Lightweight Options

```bash
# Limit CPU/memory
harbor jobs start --override-cpus 1 --override-memory 512 --delete
```

## Alternative Environments

- docker (local)
- daytona (cloud)
- e2b, modal, gke (cloud options)
