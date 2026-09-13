# Track 1 Quick Reference: Task Grid & Commands

## Task Dependency DAG

```
           T1.1 (test)
              ↓
           T1.2 (impl)
              ↓
           T1.3 (impl)
              ↓
           T1.4 (api)
              ↓
           T1.5 (parity)
              ↓
     ┌───────┬───────┬───────┐
     ↓       ↓       ↓       ↓
   T2.1    T3.1    T4.1    (verify)
     ↓       ↓       ↓
   T2.2    T3.2    T4.2    (parallel)
     ↓       ↓       ↓
   T2.3    T3.3    T4.3
     └───────┴───────┴───────┘
              ↓
           T5.1 (test)
              ↓
           T5.2 (impl)
              ↓
           T5.3 (cleanup)
              ↓
           T5.4 (e2e)
              ↓
           T5.5 (parity)
              ↓
           T0.0 (smoke)
```

## 1-Page Task Checklist

| Task     | Work Stream                          | Duration | Status | Verification                                           |
| -------- | ------------------------------------ | -------- | ------ | ------------------------------------------------------ |
| **T1.1** | Pareto frontier routing              | 30m      | ⏳     | `go test -run TestPareto...`                           |
| **T1.2** | Pareto router impl                   | 2h       | ⏳     | `go test -run TestPareto...`                           |
| **T1.3** | Task classifier                      | 1.5h     | ⏳     | `go test -run TestTaskClassifier...`                   |
| **T1.4** | /v1/routing/select endpoint          | 1.5h     | ⏳     | `curl -X POST http://localhost:8317/v1/routing/select` |
| **T1.5** | Parity test (routing)                | 1h       | ⏳     | `pytest test_parity_pareto_router_vs_cliproxy.py`      |
| **T2.1** | ACP adapter test                     | 30m      | ⏳     | `go test -run TestACPAdapter...`                       |
| **T2.2** | ACP adapter impl                     | 1.5h     | ⏳     | `go test -run TestACPAdapter...`                       |
| **T2.3** | Parity test (adapters)               | 1h       | ⏳     | `pytest test_parity_adapters_vs_cliproxy.py`           |
| **T3.1** | OAuth token test                     | 30m      | ⏳     | `go test -run TestOAuthTokenManager...`                |
| **T3.2** | OAuth manager impl                   | 1.5h     | ⏳     | `go test -run TestOAuthTokenManager... -race`          |
| **T3.3** | Parity test (auth)                   | 1h       | ⏳     | `pytest test_parity_oauth_vs_cliproxy.py`              |
| **T4.1** | Quota enforcer test                  | 30m      | ⏳     | `go test -run TestQuotaEnforcer...`                    |
| **T4.2** | Quota enforcer impl                  | 1.5h     | ⏳     | `go test -run TestQuotaEnforcer... -race`              |
| **T4.3** | Parity test (quota)                  | 1h       | ⏳     | `pytest test_parity_quota_vs_cliproxy.py`              |
| **T5.1** | CLIProxy integration test            | 30m      | ⏳     | `pytest test_cliproxy_integration_routing.py`          |
| **T5.2** | TaskRouter → CLIProxy                | 2h       | ⏳     | `pytest test_cliproxy_integration_routing.py`          |
| **T5.3** | Remove old modules, update tach.toml | 1h       | ⏳     | `tach check`                                           |
| **T5.4** | E2E test                             | 1.5h     | ⏳     | `pytest test_e2e_thegent_cliproxy_provider.py`         |
| **T5.5** | Full parity suite                    | 2h       | ⏳     | `pytest test_parity_legacy_vs_cliproxy_migration.py`   |
| **T0.0** | Endpoint smoke test                  | 30m      | ⏳     | `go test -run TestAllRouting...`                       |

---

## File Map (Where to Add/Edit)

### CLIProxy (Go)

**Routing (T1.x):**

```
/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/
├─ pkg/llmproxy/registry/
│  ├─ pareto_router.go (NEW - T1.2)
│  ├─ pareto_types.go (NEW - T1.2)
│  ├─ pareto_router_test.go (NEW - T1.1)
│  ├─ task_classifier.go (NEW - T1.3)
│  ├─ task_classifier_test.go (NEW - T1.3)
│  └─ routing_pareto_integration_test.go (NEW - T1.1)
└─ pkg/llmproxy/api/
   ├─ routing_handler.go (NEW - T1.4)
   ├─ routing_handler_test.go (NEW - T1.4)
   └─ endpoints_integration_test.go (NEW - T0.0)
```

**Adapters (T2.x):**

```
├─ pkg/llmproxy/translator/acp/
│  ├─ acp_adapter.go (NEW - T2.2)
│  ├─ acp_request.go (NEW - T2.2)
│  ├─ acp_response.go (NEW - T2.2)
│  └─ acp_adapter_registry_test.go (NEW - T2.1)
```

**Auth (T3.x):**

```
└─ pkg/llmproxy/auth/
   ├─ oauth_token_manager.go (NEW - T3.2)
   ├─ oauth_types.go (NEW - T3.2)
   └─ oauth_token_manager_test.go (NEW - T3.1)
```

**Quota (T4.x):**

```
└─ pkg/llmproxy/usage/
   ├─ quota_enforcer.go (NEW - T4.2)
   ├─ quota_types.go (NEW - T4.2)
   └─ quota_enforcer_test.go (NEW - T4.1)
```

### thegent (Python)

**Routing (T5.x):**

```
/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/
├─ src/thegent/routing/
│  ├─ cliproxy_client.py (NEW - T5.2)
│  ├─ task_router.py (EDIT - T5.2, thin wrapper)
│  └─ pareto_router.py (DELETE - T5.3)
├─ tests/routing/
│  └─ test_parity_pareto_router_vs_cliproxy.py (NEW - T1.5)
├─ tests/adapters/
│  └─ test_parity_adapters_vs_cliproxy.py (NEW - T2.3)
├─ tests/auth/
│  └─ test_parity_oauth_vs_cliproxy.py (NEW - T3.3)
├─ tests/quota/
│  └─ test_parity_quota_vs_cliproxy.py (NEW - T4.3)
├─ tests/integration/
│  ├─ test_cliproxy_integration_routing.py (NEW - T5.1)
│  ├─ test_e2e_thegent_cliproxy_provider.py (NEW - T5.4)
│  └─ test_parity_legacy_vs_cliproxy_migration.py (NEW - T5.5)
└─ tach.toml (EDIT - T5.3)
```

---

## Starting Commands (Copy-Paste Ready)

### Work Stream 1: Pareto Router (Go)

```bash
# T1.1: Create failing test
touch /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/routing_pareto_integration_test.go
# (Edit file with test code from plan)

# Run test (expect failure)
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestParetoRoutingSelectsOptimalModelGivenConstraints ./pkg/llmproxy/registry -v

# T1.2: Implement Pareto router
touch pkg/llmproxy/registry/pareto_router.go
touch pkg/llmproxy/registry/pareto_types.go
# (Edit with implementation)

# Run test (expect pass)
go test -run TestPareto ./pkg/llmproxy/registry -v

# T1.3: Add task classifier
touch pkg/llmproxy/registry/task_classifier.go
touch pkg/llmproxy/registry/task_classifier_test.go
go test -run TestTaskClassifier ./pkg/llmproxy/registry -v

# T1.4: Add HTTP endpoint
touch pkg/llmproxy/api/routing_handler.go
touch pkg/llmproxy/api/routing_handler_test.go
go test -run TestPOSTRoutingSelect ./pkg/llmproxy/api -v

# Test curl
curl -X POST http://localhost:8317/v1/routing/select \
  -H "Content-Type: application/json" \
  -d '{"taskComplexity":"NORMAL","maxCostPerCall":0.01,"maxLatencyMs":5000,"minQualityScore":0.75}'
```

### Work Stream 5: Thegent Integration (Python)

```bash
# T5.1: Create failing test
touch /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/integration/test_cliproxy_integration_routing.py
# (Edit file)

# Run test (expect failure)
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
pytest tests/integration/test_cliproxy_integration_routing.py -v

# T5.2: Implement CLIProxy client
touch src/thegent/routing/cliproxy_client.py
# (Edit with implementation)

# Update task_router.py to use cliproxy_client
# (Edit src/thegent/routing/task_router.py)

# Run test (expect pass)
pytest tests/integration/test_cliproxy_integration_routing.py -v

# T5.3: Remove old modules
rm src/thegent/routing/pareto_router.py
# (Update tach.toml)

# Verify boundaries
tach check

# T5.4: Run E2E test
pytest tests/integration/test_e2e_thegent_cliproxy_provider.py -v -s

# T5.5: Run parity suite
pytest tests/integration/test_parity_legacy_vs_cliproxy_migration.py -v
```

---

## Parallel Execution Strategy

### Option 1: Sequential (Safe, Default)

```bash
# Day 1: Work Stream 1 (T1.1–T1.5)
# Then: Work Streams 2–4 in parallel (after T1.4)
# Day 2: Work Stream 5 (T5.1–T5.5)

thegent free "Execute T1.1–T1.5" --do-next --repeat 5
thegent free "Execute T2.1–T2.3" &
thegent free "Execute T3.1–T3.3" &
thegent free "Execute T4.1–T4.3" &
wait

thegent free "Execute T5.1–T5.5" --do-next --repeat 5
```

### Option 2: Parallel Subagents

```bash
# Start multiple subagents in parallel
thegent free "Work Stream 1: Implement Pareto router (T1.1–T1.5)" &
WS1_PID=$!

thegent free "Work Stream 2: Add ACP adapter (T2.1–T2.3)" &
WS2_PID=$!

thegent free "Work Stream 3: Add OAuth manager (T3.1–T3.3)" &
WS3_PID=$!

thegent free "Work Stream 4: Add quota enforcer (T4.1–T4.3)" &
WS4_PID=$!

# Wait for all to complete
wait $WS1_PID $WS2_PID $WS3_PID $WS4_PID

# Then sequential
thegent free "Work Stream 5: Thegent integration (T5.1–T5.5)" --do-next --repeat 5
```

---

## Quality Gates (Run Before Merging)

```bash
# Go (CLIProxy)
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test ./pkg/llmproxy/... -v -race
go vet ./pkg/llmproxy/...
go fmt ./pkg/llmproxy/...

# Python (thegent)
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
pytest tests/ -k "parity or integration or e2e" -v
pytest tests/ -x  # Stop on first failure
tach check
ruff check src/
mypy src/thegent/routing/
```

---

## Verification Checklist

After all tasks complete:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`, `go vet ./...`
- [ ] Parity suite 100%: `pytest tests/integration/test_parity_* -v`
- [ ] Boundaries correct: `tach check`
- [ ] Old modules deleted: `ls src/thegent/routing/pareto_router.py` → NOT FOUND
- [ ] CLIProxy endpoints live: `curl -s http://localhost:8317/v1/routing/select` → 200 (or 400 on bad input)
- [ ] E2E flow works: `pytest tests/integration/test_e2e_... -v -s`
- [ ] No LiteLLM imports: `grep -r "litellm" src/thegent/routing/` → NOT FOUND
- [ ] Commit history clean: 20 commits, each with clear message and `@trace` tag

---

## Gotchas & Tips

1. **CLIProxy must be running** for thegent parity tests:

   ```bash
   /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/bin/cliproxy server &
   ```

2. **Test tolerance for floats:**
   - Cost: within 0.1% (0.0001)
   - Latency: within 10ms
   - Quality: exact match

3. **Don't delete task_router.py**, just make it a thin wrapper calling CLIProxy.

4. **Update all imports** when moving to CLIProxyRoutingClient:

   ```bash
   grep -r "from thegent.routing.pareto_router import" src/
   grep -r "from thegent.routing.task_router import" src/
   ```

5. **Thread safety for Go:** Always run tests with `-race` flag.

6. **Parity test requires both systems running:**
   - thegent at localhost (or wherever)
   - CLIProxy at localhost:8317

---

## Example Full Session (20m Demo)

```bash
# 1. Start CLIProxy
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go build -o bin/cliproxy ./cmd/cliproxy
./bin/cliproxy server &

# 2. Run T1.1–T1.4 (Pareto router)
go test -run TestPareto ./pkg/llmproxy/registry -v
go test -run TestTaskClassifier ./pkg/llmproxy/registry -v
go test -run TestPOSTRoutingSelect ./pkg/llmproxy/api -v

# 3. Test endpoint
curl -X POST http://localhost:8317/v1/routing/select \
  -H "Content-Type: application/json" \
  -d '{"taskComplexity":"NORMAL","maxCostPerCall":0.01,"maxLatencyMs":5000,"minQualityScore":0.75}' | jq

# 4. Run thegent parity test
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
pytest tests/routing/test_parity_pareto_router_vs_cliproxy.py -v

# 5. Verify all CLIProxy endpoints
go test -run TestAllRoutingEndpoints /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/api -v
```

Done! Track 1 is complete.
