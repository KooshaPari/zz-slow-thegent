# Track 1 TDD Implementation Plan: Migrate Routing/Adapters/Auth to CLIProxyAPI++

## Executive Summary

Track 1 migrates ~30K LOC of thegent's LLM routing, provider adapters, and auth integrations from Python to Go (CLIProxy). This plan uses strict TDD with bite-sized tasks, failing tests first, and parity verification.

**Scope:**
- **thegent.routing** (~11.5K LOC): Pareto frontier routing, TaskRouter, cost/quality constraints
- **thegent.adapters** (~1.4K LOC): Provider adapters (ACP client, MCP bridge, server)
- **thegent.integrations.connector_quota** (~150 LOC): Quota tracking
- **thegent.integrations.connector_cost_accounting** (~100 LOC): Cost tracking

**Target:** All LLM calls flow through CLIProxy localhost:8317 instead of LiteLLM. Thegent becomes a thin orchestration layer calling CLIProxy for all provider routing decisions.

**Timeline:** 5 parallel work streams, each 3-5 iterations

---

## Work Streams & Tasks

### Work Stream 1: Pareto Frontier Algorithm Port (Go)

**Dependency:** None (foundational)
**Target Duration:** ~8 wall-clock hours (3-4 parallel subagents)

The Pareto frontier algorithm is the core routing logic. We port it from Python to Go and expose it via CLIProxy's routing API endpoint (`POST /v1/routing/select`).

#### T1.1: Write Failing Integration Test for Pareto Route Selection

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/routing_pareto_integration_test.go`

**Test:** Pareto frontier selection with hard constraints (quality threshold, cost cap, latency cap).

```go
func TestParetoRoutingSelectsOptimalModelGivenConstraints(t *testing.T) {
    // Arrange: Define routing request with constraints
    req := &RoutingRequest{
        TaskComplexity: "NORMAL",      // Classified task
        MaxCostPerCall: 0.01,          // Hard constraint: <$0.01
        MaxLatencyMs:   5000,          // Hard constraint: <5s
        MinQualityScore: 0.75,         // Hard constraint: ≥75% quality
        TaskMetadata: map[string]string{
            "category": "code_analysis",
            "tokens_in": "2500",
        },
    }

    // Act: Call Pareto router
    selected, err := paretoRouter.SelectModel(ctx, req)

    // Assert:
    // - Selected model is on Pareto frontier (not dominated by others)
    // - Selected model satisfies all hard constraints
    // - Selected model is lexicographically optimal (speed → cost → quality)
    assert.NoError(t, err)
    assert.NotNil(t, selected)
    assert.LessOrEqual(t, selected.EstimatedCost, req.MaxCostPerCall)
    assert.LessOrEqual(t, selected.EstimatedLatencyMs, req.MaxLatencyMs)
    assert.GreaterOrEqual(t, selected.QualityScore, req.MinQualityScore)
}
```

**Acceptance Criteria:**
- Test compiles and runs
- Test fails because `paretoRouter` doesn't exist
- `RoutingRequest` struct has all required fields
- Response includes model ID, cost, latency, quality score

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestParetoRoutingSelectsOptimalModelGivenConstraints ./pkg/llmproxy/registry -v
```

**Commit:**
```
test: add failing test for Pareto frontier routing selection

Adds integration test for optimal model selection under hard constraints
(cost, latency, quality thresholds). Test verifies lexicographic ordering
(speed → cost → quality) on Pareto frontier.

@trace FR-ROUTING-001
```

---

#### T1.2: Implement Basic Pareto Router Type & Route Selection Algorithm

**Files:**
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/pareto_router.go`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/pareto_types.go`

**Implementation:** Port the Pareto frontier algorithm from thegent Python (reference: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/pareto_router.py`, ~600 LOC).

Key steps:
1. Parse Terminal Bench 2.0 metrics from model registry
2. Filter models that violate hard constraints
3. Build Pareto frontier (remove dominated models)
4. Lexicographic selection: speed → cost → quality

**Minimal Implementation:**

```go
// pareto_types.go
type RoutingRequest struct {
    TaskComplexity    string
    MaxCostPerCall    float64
    MaxLatencyMs      int
    MinQualityScore   float64
    TaskMetadata      map[string]string
}

type RoutingCandidate struct {
    ModelID             string
    EstimatedCost       float64
    EstimatedLatencyMs  int
    QualityScore        float64
    Provider            string
}

// pareto_router.go
type ParetoRouter struct {
    modelRegistry *ModelRegistry
}

func (p *ParetoRouter) SelectModel(ctx context.Context, req *RoutingRequest) (*RoutingCandidate, error) {
    // 1. Get all models from registry
    allModels := p.modelRegistry.ListModels()

    // 2. Filter by hard constraints
    feasible := filterByConstraints(allModels, req)
    if len(feasible) == 0 {
        return nil, fmt.Errorf("no models satisfy constraints")
    }

    // 3. Build Pareto frontier
    frontier := computeParetoFrontier(feasible)

    // 4. Lexicographic selection
    selected := lexicographicSelect(frontier)

    return selected, nil
}

func filterByConstraints(models []ModelDef, req *RoutingRequest) []*RoutingCandidate {
    // Return candidates where:
    // - cost <= maxCostPerCall
    // - latency <= maxLatencyMs
    // - quality >= minQualityScore
}

func computeParetoFrontier(candidates []*RoutingCandidate) []*RoutingCandidate {
    // Remove dominated models (lower quality, higher cost/latency)
    // Keep only Pareto-optimal models
}

func lexicographicSelect(frontier []*RoutingCandidate) *RoutingCandidate {
    // Sort by: speed (ascending) → cost (ascending) → quality (descending)
    // Return first (best) candidate
}
```

**Acceptance Criteria:**
- T1.1 test passes
- All constraint violations are rejected
- Pareto frontier correctly removes dominated models
- Lexicographic ordering is deterministic

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestPareto ./pkg/llmproxy/registry -v
go vet ./pkg/llmproxy/registry
```

**Commit:**
```
feat(routing): implement Pareto frontier algorithm in Go

Ports terminal-bench-2.0-aware routing from thegent Python to CLIProxy Go.
Implements constraint filtering, Pareto frontier computation, and
lexicographic selection (speed → cost → quality).

Tested against hard constraints (cost, latency, quality thresholds).

@trace FR-ROUTING-001 FR-ROUTING-002 FR-ROUTING-003
```

---

#### T1.3: Add TaskClassifier (Complexity Categorizer)

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/task_classifier.go`

**Test:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/task_classifier_test.go`

**Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/task_router.py` (TaskClassifier class, ~150 LOC)

Task classification determines which Pareto frontier to use:
- FAST: Token count < 500, latency < 1s
- NORMAL: Token count 500–5000, latency < 5s
- COMPLEX: Token count 5000–50K, latency < 30s
- HIGH_COMPLEX: Token count > 50K, latency < 120s

**Failing Test:**

```go
func TestTaskClassifierCategorizesFast(t *testing.T) {
    tc := NewTaskClassifier()

    req := &TaskClassificationRequest{
        TokensIn: 250,
        TokensOut: 100,
        Metadata: map[string]string{
            "category": "quick_lookup",
        },
    }

    category, err := tc.Classify(context.Background(), req)

    assert.NoError(t, err)
    assert.Equal(t, "FAST", category)
}

func TestTaskClassifierCategorizesComplex(t *testing.T) {
    tc := NewTaskClassifier()

    req := &TaskClassificationRequest{
        TokensIn: 25000,
        TokensOut: 5000,
    }

    category, err := tc.Classify(context.Background(), req)

    assert.NoError(t, err)
    assert.Equal(t, "COMPLEX", category)
}

func TestTaskClassifierCategorizesHighComplex(t *testing.T) {
    tc := NewTaskClassifier()

    req := &TaskClassificationRequest{
        TokensIn: 100000,
    }

    category, err := tc.Classify(context.Background(), req)

    assert.NoError(t, err)
    assert.Equal(t, "HIGH_COMPLEX", category)
}
```

**Minimal Implementation:**

```go
type TaskClassificationRequest struct {
    TokensIn  int
    TokensOut int
    Metadata  map[string]string
}

type TaskClassifier struct{}

func (tc *TaskClassifier) Classify(ctx context.Context, req *TaskClassificationRequest) (string, error) {
    totalTokens := req.TokensIn + req.TokensOut

    if totalTokens < 500 {
        return "FAST", nil
    }
    if totalTokens < 5000 {
        return "NORMAL", nil
    }
    if totalTokens < 50000 {
        return "COMPLEX", nil
    }
    return "HIGH_COMPLEX", nil
}
```

**Acceptance Criteria:**
- All classification test cases pass
- Classification is deterministic
- Boundary cases are covered (499, 500, 4999, 5000, etc.)

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestTaskClassifier ./pkg/llmproxy/registry -v
```

**Commit:**
```
feat(routing): add task classifier for complexity categorization

Categorizes tasks into FAST/NORMAL/COMPLEX/HIGH_COMPLEX based on token
counts. Enables separate Pareto frontiers per complexity tier.

@trace FR-ROUTING-004
```

---

#### T1.4: Expose /v1/routing/select HTTP Endpoint

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/api/routing_handler.go`

**Test:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/api/routing_handler_test.go`

**Failing HTTP Test:**

```go
func TestPOSTRoutingSelectReturnsOptimalModel(t *testing.T) {
    router := setupRouter()

    reqBody := map[string]interface{}{
        "taskComplexity": "NORMAL",
        "maxCostPerCall": 0.01,
        "maxLatencyMs": 5000,
        "minQualityScore": 0.75,
    }

    payload, _ := json.Marshal(reqBody)
    req := httptest.NewRequest("POST", "/v1/routing/select", bytes.NewReader(payload))
    w := httptest.NewRecorder()

    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)

    var resp map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &resp)
    assert.NotEmpty(t, resp["model_id"])
    assert.NotEmpty(t, resp["provider"])
    assert.NotZero(t, resp["estimated_cost"])
}
```

**Minimal Handler:**

```go
type RoutingSelectRequest struct {
    TaskComplexity  string  `json:"taskComplexity"`
    MaxCostPerCall  float64 `json:"maxCostPerCall"`
    MaxLatencyMs    int     `json:"maxLatencyMs"`
    MinQualityScore float64 `json:"minQualityScore"`
}

type RoutingSelectResponse struct {
    ModelID             string  `json:"model_id"`
    Provider            string  `json:"provider"`
    EstimatedCost       float64 `json:"estimated_cost"`
    EstimatedLatencyMs  int     `json:"estimated_latency_ms"`
    QualityScore        float64 `json:"quality_score"`
}

func (h *RoutingHandler) POSTRoutingSelect(w http.ResponseWriter, r *http.Request) {
    var req RoutingSelectRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    routingReq := &RoutingRequest{
        TaskComplexity:  req.TaskComplexity,
        MaxCostPerCall:  req.MaxCostPerCall,
        MaxLatencyMs:    req.MaxLatencyMs,
        MinQualityScore: req.MinQualityScore,
    }

    selected, err := h.paretoRouter.SelectModel(r.Context(), routingReq)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    resp := RoutingSelectResponse{
        ModelID:             selected.ModelID,
        Provider:            selected.Provider,
        EstimatedCost:       selected.EstimatedCost,
        EstimatedLatencyMs:  selected.EstimatedLatencyMs,
        QualityScore:        selected.QualityScore,
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}
```

**Acceptance Criteria:**
- Endpoint responds on `POST /v1/routing/select`
- Request JSON is correctly parsed
- Response includes all required fields (model_id, provider, costs, latency, quality)
- HTTP 400 on invalid constraints
- HTTP 200 on success

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestPOSTRoutingSelect ./pkg/llmproxy/api -v
curl -X POST http://localhost:8317/v1/routing/select \
  -H "Content-Type: application/json" \
  -d '{"taskComplexity":"NORMAL","maxCostPerCall":0.01,"maxLatencyMs":5000,"minQualityScore":0.75}'
```

**Commit:**
```
feat(api): expose /v1/routing/select endpoint for Pareto model selection

Exposes Pareto router as HTTP endpoint. Accepts task constraints, returns
optimal model ID, provider, estimated cost/latency/quality.

@trace FR-ROUTING-005
```

---

#### T1.5: Parity Test — thegent.routing.ParetoRouter vs CLIProxy /v1/routing/select

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/routing/test_parity_pareto_router_vs_cliproxy.py`

**Test Strategy:** Verify thegent and CLIProxy select identical models under same constraints.

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-ROUTING-PARITY-001")
def test_pareto_router_parity_thegent_vs_cliproxy():
    """Verify thegent ParetoRouter and CLIProxy /v1/routing/select select same model."""

    # Test cases: vary complexity, cost caps, quality thresholds
    test_cases = [
        {
            "taskComplexity": "FAST",
            "maxCostPerCall": 0.001,
            "maxLatencyMs": 1000,
            "minQualityScore": 0.7,
        },
        {
            "taskComplexity": "NORMAL",
            "maxCostPerCall": 0.01,
            "maxLatencyMs": 5000,
            "minQualityScore": 0.75,
        },
        {
            "taskComplexity": "COMPLEX",
            "maxCostPerCall": 0.05,
            "maxLatencyMs": 30000,
            "minQualityScore": 0.8,
        },
    ]

    # Start CLIProxy (assume localhost:8317)
    cliproxy_client = httpx.Client(base_url="http://localhost:8317")
    thegent_router = ParetoRouter()

    for case in test_cases:
        # Call thegent router
        thegent_result = thegent_router.select_model(case)

        # Call CLIProxy endpoint
        cliproxy_result = cliproxy_client.post("/v1/routing/select", json=case).json()

        # Assert identical model selected
        assert thegent_result["model_id"] == cliproxy_result["model_id"], (
            f"Model mismatch for {case}: thegent={thegent_result['model_id']}, cliproxy={cliproxy_result['model_id']}"
        )

        # Assert costs within 0.1% (floating-point tolerance)
        assert abs(thegent_result["cost"] - cliproxy_result["estimated_cost"]) < 0.0001, f"Cost mismatch for {case}"

        # Assert latency within 10ms (network latency tolerance)
        assert abs(thegent_result["latency_ms"] - cliproxy_result["estimated_latency_ms"]) <= 10, (
            f"Latency mismatch for {case}"
        )
```

**Acceptance Criteria:**
- Parity test runs and passes for all test cases
- Same model selected by both implementations
- Costs and latencies match (within tolerance)
- No constraints violated in either implementation

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

# Start CLIProxy in background
/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/bin/cliproxy server &

# Run parity test
pytest tests/routing/test_parity_pareto_router_vs_cliproxy.py -v -s

# Verify models match
pytest tests/routing/test_parity_pareto_router_vs_cliproxy.py::test_pareto_router_parity_thegent_vs_cliproxy -v
```

**Commit:**
```
test(routing): add parity test for Pareto router (thegent vs CLIProxy)

Verifies thegent.routing.ParetoRouter and CLIProxy /v1/routing/select
produce identical model selections, costs, and latencies across FAST/NORMAL/
COMPLEX/HIGH_COMPLEX categories.

@trace FR-ROUTING-PARITY-001
```

---

### Work Stream 2: Provider Adapters & Translators (Go)

**Dependency:** Work Stream 1 (Pareto router available)
**Target Duration:** ~6 wall-clock hours

CLIProxy already has translators for Gemini, OpenAI, Claude, etc. We consolidate thegent's ACP adapters into CLIProxy's translator registry.

#### T2.1: Add Failing Test for ACP Adapter Registration

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/translator/acp_adapter_registry_test.go`

```go
func TestACPAdapterIsRegisteredAndAvailable(t *testing.T) {
    registry := NewTranslatorRegistry()

    // Act: Check if ACP adapter is registered
    adapterExists := registry.HasTranslator("acp")

    // Assert: ACP adapter must exist
    assert.True(t, adapterExists, "ACP adapter not registered in translator registry")
}

func TestACPAdapterTransformsClaudeToACP(t *testing.T) {
    registry := NewTranslatorRegistry()
    adapter := registry.GetTranslator("acp")

    // Request in Claude API format
    claudeReq := &ChatCompletionRequest{
        Model: "claude-opus-4-6",
        Messages: []Message{
            {Role: "user", Content: "Hello"},
        },
    }

    // Transform to ACP format
    acpReq, err := adapter.Translate(context.Background(), claudeReq)

    assert.NoError(t, err)
    assert.NotNil(t, acpReq)
    assert.Equal(t, "claude-opus-4-6", acpReq.Model)
}
```

**Acceptance Criteria:**
- Test compiles and runs
- Test fails (adapter not registered)
- Error message is clear

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestACPAdapterIsRegistered ./pkg/llmproxy/translator -v
```

**Commit:**
```
test: add failing test for ACP adapter registration in CLIProxy

Verifies ACP adapter exists in translator registry and can translate
Claude API requests to ACP format.

@trace FR-ADAPTERS-001
```

---

#### T2.2: Implement ACP Adapter in CLIProxy Translator Registry

**Files:**
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/translator/acp/acp_adapter.go`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/translator/acp/acp_request.go`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/translator/acp/acp_response.go`

**Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/adapters/acp_client.py` (~10K LOC)

**Minimal Implementation:**

```go
// acp_adapter.go
type ACPAdapter struct {
    baseURL string
    client  *http.Client
}

func NewACPAdapter(baseURL string) *ACPAdapter {
    return &ACPAdapter{
        baseURL: baseURL,
        client:  &http.Client{Timeout: 30 * time.Second},
    }
}

func (a *ACPAdapter) Translate(ctx context.Context, req interface{}) (interface{}, error) {
    // Convert Claude/OpenAI format to ACP format
    if claudeReq, ok := req.(*ChatCompletionRequest); ok {
        return a.translateClaudeToACP(claudeReq)
    }
    return nil, fmt.Errorf("unsupported request type: %T", req)
}

func (a *ACPAdapter) translateClaudeToACP(req *ChatCompletionRequest) (*ACPRequest, error) {
    return &ACPRequest{
        Model:    req.Model,
        Messages: req.Messages,
    }, nil
}

// Register in translator registry
func init() {
    translatorRegistry.Register("acp", NewACPAdapter("http://localhost:9000"))
}
```

**Acceptance Criteria:**
- T2.1 test passes
- ACP adapter is registered and retrievable
- Claude API requests are translated to ACP format
- Response is translated back to Claude API format

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestACPAdapter ./pkg/llmproxy/translator -v
```

**Commit:**
```
feat(adapters): add ACP translator to CLIProxy

Implements ACP adapter for translating Claude/OpenAI API requests to
ACP format. Registers in translator registry for automatic use.

Reference: thegent acp_client.py

@trace FR-ADAPTERS-001 FR-ADAPTERS-002
```

---

#### T2.3: Consolidate Provider Adapter Tests (Parity)

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/adapters/test_parity_adapters_vs_cliproxy.py`

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-ADAPTERS-PARITY-001")
def test_acp_adapter_parity_thegent_vs_cliproxy():
    """Verify thegent ACP adapter and CLIProxy ACP translator handle requests identically."""

    # Test request in Claude format
    claude_req = {
        "model": "claude-opus-4-6",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    # thegent adapter
    thegent_adapter = ACPClient("http://localhost:9000")
    thegent_acp_req = thegent_adapter.translate_to_acp(claude_req)

    # CLIProxy translator
    cliproxy_resp = httpx.post("http://localhost:8317/v1/translate/acp", json=claude_req).json()

    # Assert identical transformations
    assert thegent_acp_req["model"] == cliproxy_resp["model"]
    assert thegent_acp_req["messages"] == cliproxy_resp["messages"]
```

**Acceptance Criteria:**
- Parity test runs and passes
- thegent and CLIProxy produce identical request/response transformations
- No data loss or corruption in translation

**Verification Command:**
```bash
pytest tests/adapters/test_parity_adapters_vs_cliproxy.py -v -s
```

**Commit:**
```
test(adapters): add parity test for ACP adapter (thegent vs CLIProxy)

Verifies thegent ACP adapter and CLIProxy translator produce identical
transformations for Claude API requests.

@trace FR-ADAPTERS-PARITY-001
```

---

### Work Stream 3: Auth Integrations (Go)

**Dependency:** Work Stream 1 (routing available)
**Target Duration:** ~5 wall-clock hours

Consolidate thegent's OAuth lifecycle management into CLIProxy's auth subsystem.

#### T3.1: Failing Test for OAuth Token Management in CLIProxy

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/auth/oauth_token_manager_test.go`

```go
func TestOAuthTokenManagerRefreshesExpiredToken(t *testing.T) {
    // Mock OAuth provider
    mockProvider := &MockOAuthProvider{
        RefreshTokenFn: func(ctx context.Context, refreshToken string) (string, error) {
            return "new_access_token_xyz", nil
        },
    }

    mgr := NewOAuthTokenManager(mockProvider)

    // Store initial token
    err := mgr.StoreToken(context.Background(), "provider", &Token{
        AccessToken:  "old_token",
        RefreshToken: "refresh_token",
        ExpiresAt:    time.Now().Add(-time.Hour), // Expired
    })
    assert.NoError(t, err)

    // Act: Retrieve token (should auto-refresh)
    token, err := mgr.GetToken(context.Background(), "provider")

    // Assert: Token is refreshed
    assert.NoError(t, err)
    assert.Equal(t, "new_access_token_xyz", token.AccessToken)
}

func TestOAuthTokenManagerStoresAndRetrievesToken(t *testing.T) {
    mgr := NewOAuthTokenManager(nil)

    token := &Token{
        AccessToken:  "access_token",
        RefreshToken: "refresh_token",
        ExpiresAt:    time.Now().Add(time.Hour),
    }

    // Store
    err := mgr.StoreToken(context.Background(), "provider", token)
    assert.NoError(t, err)

    // Retrieve
    retrieved, err := mgr.GetToken(context.Background(), "provider")
    assert.NoError(t, err)
    assert.Equal(t, token.AccessToken, retrieved.AccessToken)
}
```

**Acceptance Criteria:**
- Tests compile and run
- Tests fail (OAuth manager not implemented)
- Error messages are clear

**Verification Command:**
```bash
go test -run TestOAuthTokenManager ./pkg/llmproxy/auth -v
```

**Commit:**
```
test: add failing tests for OAuth token manager in CLIProxy auth

Tests token storage, retrieval, and automatic refresh of expired tokens.

@trace FR-AUTH-001
```

---

#### T3.2: Implement OAuth Token Manager in CLIProxy

**Files:**
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/auth/oauth_token_manager.go`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/auth/oauth_types.go`

**Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/integrations/` (auth-related files)

**Minimal Implementation:**

```go
// oauth_types.go
type Token struct {
    AccessToken  string
    RefreshToken string
    ExpiresAt    time.Time
}

type OAuthProvider interface {
    RefreshToken(ctx context.Context, refreshToken string) (string, error)
}

// oauth_token_manager.go
type OAuthTokenManager struct {
    store    map[string]*Token // provider -> token
    mu       sync.RWMutex
    provider OAuthProvider
}

func NewOAuthTokenManager(provider OAuthProvider) *OAuthTokenManager {
    return &OAuthTokenManager{
        store:    make(map[string]*Token),
        provider: provider,
    }
}

func (m *OAuthTokenManager) StoreToken(ctx context.Context, provider string, token *Token) error {
    m.mu.Lock()
    defer m.mu.Unlock()
    m.store[provider] = token
    return nil
}

func (m *OAuthTokenManager) GetToken(ctx context.Context, provider string) (*Token, error) {
    m.mu.RLock()
    token, exists := m.store[provider]
    m.mu.RUnlock()

    if !exists {
        return nil, fmt.Errorf("token not found for provider: %s", provider)
    }

    // Check if expired
    if time.Now().After(token.ExpiresAt) {
        // Refresh
        if m.provider == nil {
            return nil, fmt.Errorf("token expired and no provider available to refresh")
        }

        newAccessToken, err := m.provider.RefreshToken(ctx, token.RefreshToken)
        if err != nil {
            return nil, err
        }

        token.AccessToken = newAccessToken
        token.ExpiresAt = time.Now().Add(time.Hour)

        m.mu.Lock()
        m.store[provider] = token
        m.mu.Unlock()
    }

    return token, nil
}
```

**Acceptance Criteria:**
- T3.1 tests pass
- Tokens are stored and retrieved correctly
- Expired tokens are automatically refreshed
- Concurrent access is thread-safe (RWMutex)

**Verification Command:**
```bash
go test -run TestOAuthTokenManager ./pkg/llmproxy/auth -v -race
```

**Commit:**
```
feat(auth): add OAuth token manager to CLIProxy

Implements token storage, retrieval, and automatic refresh of expired
tokens. Thread-safe with RWMutex. Supports custom OAuth providers.

@trace FR-AUTH-001 FR-AUTH-002
```

---

#### T3.3: Parity Test for OAuth Token Handling

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/auth/test_parity_oauth_vs_cliproxy.py`

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-AUTH-PARITY-001")
def test_oauth_token_refresh_parity_thegent_vs_cliproxy():
    """Verify thegent and CLIProxy refresh tokens identically."""

    # Mock OAuth provider
    mock_provider = MockOAuthProvider()

    # thegent: OAuth lifecycle
    thegent_oauth = OAuthLifecycle(mock_provider)
    thegent_token = thegent_oauth.refresh_token("old_token", "refresh_token_abc")

    # CLIProxy: Token manager
    cliproxy_resp = httpx.post(
        "http://localhost:8317/v1/auth/oauth/refresh", json={"refresh_token": "refresh_token_abc"}
    ).json()

    # Assert tokens match
    assert thegent_token["access_token"] == cliproxy_resp["access_token"]
    assert thegent_token["expires_in"] == cliproxy_resp["expires_in"]
```

**Acceptance Criteria:**
- Parity test runs and passes
- Token refresh produces identical results in both systems
- Expiration times match (within 1 second tolerance)

**Verification Command:**
```bash
pytest tests/auth/test_parity_oauth_vs_cliproxy.py -v
```

**Commit:**
```
test(auth): add parity test for OAuth token refresh (thegent vs CLIProxy)

Verifies thegent OAuth lifecycle and CLIProxy token manager refresh
tokens identically, including expiration times and access token content.

@trace FR-AUTH-PARITY-001
```

---

### Work Stream 4: Quota & Cost Tracking (Go)

**Dependency:** Work Stream 1 (routing available)
**Target Duration:** ~4 wall-clock hours

Consolidate thegent's quota tracking and cost accounting into CLIProxy's usage subsystem.

#### T4.1: Failing Test for Quota Enforcement

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/usage/quota_enforcer_test.go`

```go
func TestQuotaEnforcerBlocksRequestWhenQuotaExhausted(t *testing.T) {
    quota := &QuotaLimit{
        MaxTokensPerDay: 100000,
        MaxCostPerDay:   10.0,
    }

    enforcer := NewQuotaEnforcer(quota)

    // Simulate usage close to quota
    enforcer.RecordUsage(context.Background(), &Usage{
        TokensUsed: 99000,
        CostUsed:   9.90,
    })

    // Act: Request that would exceed quota
    req := &ChatCompletionRequest{
        Model: "claude-opus-4-6",
        Messages: []Message{{Role: "user", Content: "Hello"}},
    }

    allowed, err := enforcer.CheckQuota(context.Background(), req)

    // Assert: Request is blocked
    assert.NoError(t, err)
    assert.False(t, allowed, "request should be blocked when quota exhausted")
}

func TestQuotaEnforcerAllowsRequestWithinQuota(t *testing.T) {
    quota := &QuotaLimit{
        MaxTokensPerDay: 100000,
        MaxCostPerDay:   10.0,
    }

    enforcer := NewQuotaEnforcer(quota)

    req := &ChatCompletionRequest{
        Model: "claude-opus-4-6",
        Messages: []Message{{Role: "user", Content: "Hello"}},
    }

    allowed, err := enforcer.CheckQuota(context.Background(), req)

    // Assert: Request is allowed
    assert.NoError(t, err)
    assert.True(t, allowed, "request should be allowed within quota")
}
```

**Acceptance Criteria:**
- Tests compile and run
- Tests fail (quota enforcer not implemented)

**Verification Command:**
```bash
go test -run TestQuotaEnforcer ./pkg/llmproxy/usage -v
```

**Commit:**
```
test: add failing tests for quota enforcement in CLIProxy

Tests quota blocking and allowance based on daily token/cost limits.

@trace FR-QUOTA-001
```

---

#### T4.2: Implement Quota Enforcer in CLIProxy

**Files:**
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/usage/quota_enforcer.go`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/usage/quota_types.go`

**Minimal Implementation:**

```go
// quota_types.go
type QuotaLimit struct {
    MaxTokensPerDay float64
    MaxCostPerDay   float64
}

type Usage struct {
    TokensUsed float64
    CostUsed   float64
}

// quota_enforcer.go
type QuotaEnforcer struct {
    quota    *QuotaLimit
    usage    *Usage
    mu       sync.RWMutex
    resetAt  time.Time
}

func NewQuotaEnforcer(quota *QuotaLimit) *QuotaEnforcer {
    return &QuotaEnforcer{
        quota:   quota,
        usage:   &Usage{},
        resetAt: time.Now().Add(24 * time.Hour),
    }
}

func (e *QuotaEnforcer) CheckQuota(ctx context.Context, req *ChatCompletionRequest) (bool, error) {
    e.mu.RLock()
    defer e.mu.RUnlock()

    // Reset if day has passed
    if time.Now().After(e.resetAt) {
        e.mu.RUnlock()
        e.mu.Lock()
        e.usage = &Usage{}
        e.resetAt = time.Now().Add(24 * time.Hour)
        e.mu.Unlock()
        e.mu.RLock()
    }

    // Check if request would exceed quota
    estimatedTokens := estimateTokenCount(req)
    estimatedCost := estimateCost(req)

    if e.usage.TokensUsed+estimatedTokens > e.quota.MaxTokensPerDay {
        return false, nil
    }
    if e.usage.CostUsed+estimatedCost > e.quota.MaxCostPerDay {
        return false, nil
    }

    return true, nil
}

func (e *QuotaEnforcer) RecordUsage(ctx context.Context, usage *Usage) error {
    e.mu.Lock()
    defer e.mu.Unlock()

    e.usage.TokensUsed += usage.TokensUsed
    e.usage.CostUsed += usage.CostUsed

    return nil
}
```

**Acceptance Criteria:**
- T4.1 tests pass
- Quota is enforced correctly
- Daily reset works correctly
- Concurrent access is thread-safe

**Verification Command:**
```bash
go test -run TestQuotaEnforcer ./pkg/llmproxy/usage -v -race
```

**Commit:**
```
feat(quota): add quota enforcer to CLIProxy

Implements daily quota tracking for token count and cost. Blocks requests
that would exceed quota. Resets daily. Thread-safe with RWMutex.

@trace FR-QUOTA-001 FR-QUOTA-002
```

---

#### T4.3: Parity Test for Quota Tracking

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/quota/test_parity_quota_vs_cliproxy.py`

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-QUOTA-PARITY-001")
def test_quota_enforcement_parity_thegent_vs_cliproxy():
    """Verify thegent and CLIProxy enforce quotas identically."""

    quota = {"max_tokens_per_day": 100000, "max_cost_per_day": 10.0}

    # thegent: Quota tracker
    thegent_quota = ConnectorQuota(quota)
    thegent_allowed = thegent_quota.check_quota({"tokens": 50000})

    # CLIProxy: Quota enforcer
    cliproxy_allowed = httpx.post("http://localhost:8317/v1/quota/check", json={"tokens": 50000}).json()["allowed"]

    assert thegent_allowed == cliproxy_allowed
```

**Acceptance Criteria:**
- Parity test runs and passes
- Both systems block at same quota thresholds
- Both systems allow requests within quota

**Verification Command:**
```bash
pytest tests/quota/test_parity_quota_vs_cliproxy.py -v
```

**Commit:**
```
test(quota): add parity test for quota enforcement (thegent vs CLIProxy)

Verifies thegent and CLIProxy enforce token/cost quotas identically,
blocking requests at same thresholds.

@trace FR-QUOTA-PARITY-001
```

---

### Work Stream 5: Thegent Integration & Cleanup (Python)

**Dependency:** All previous work streams complete
**Target Duration:** ~6 wall-clock hours

Update thegent to call CLIProxy instead of LiteLLM, remove old modules, update boundaries.

#### T5.1: Write Failing Test for CLIProxy Integration

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/integration/test_cliproxy_integration_routing.py`

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-CLIPROXY-INTEGRATION-001")
def test_thegent_routes_through_cliproxy_localhost():
    """Verify thegent calls CLIProxy localhost:8317 for routing."""

    # Mock CLIProxy endpoint
    mock_server = MockHTTPServer("http://localhost:8317")

    # Create thegent client configured to use CLIProxy
    client = TheGentClient(
        routing_endpoint="http://localhost:8317/v1/routing/select",
    )

    # Request routing decision
    result = client.route_task(
        complexity="NORMAL",
        max_cost=0.01,
        max_latency_ms=5000,
    )

    # Assert: CLIProxy endpoint was called
    assert mock_server.called
    assert mock_server.last_request.method == "POST"
    assert mock_server.last_request.path == "/v1/routing/select"

    # Assert: Response is valid
    assert result["model_id"] is not None
    assert result["provider"] is not None
```

**Acceptance Criteria:**
- Test compiles and runs
- Test fails (thegent doesn't call CLIProxy yet)

**Verification Command:**
```bash
pytest tests/integration/test_cliproxy_integration_routing.py -v
```

**Commit:**
```
test: add failing test for thegent CLIProxy integration

Verifies thegent routes through CLIProxy localhost:8317 instead of
LiteLLM. Tests request/response flow.

@trace FR-CLIPROXY-INTEGRATION-001
```

---

#### T5.2: Update TheGentClient to Call CLIProxy

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/cliproxy_client.py` (new)

**Minimal Implementation:**

```python
"""CLIProxy client for routing decisions.

Replaces LiteLLM-based routing. All routing decisions go through CLIProxy
localhost:8317 /v1/routing/select endpoint.
"""

import httpx
from typing import Optional


class CLIProxyRoutingClient:
    """Client for CLIProxy routing endpoint."""

    def __init__(self, base_url: str = "http://localhost:8317"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=10.0)

    def select_model(
        self,
        task_complexity: str,
        max_cost_per_call: float,
        max_latency_ms: int,
        min_quality_score: float = 0.7,
    ) -> dict:
        """Select optimal model via CLIProxy Pareto router.

        Args:
            task_complexity: FAST, NORMAL, COMPLEX, or HIGH_COMPLEX
            max_cost_per_call: Maximum cost in USD
            max_latency_ms: Maximum latency in milliseconds
            min_quality_score: Minimum quality threshold (0.0-1.0)

        Returns:
            Dict with model_id, provider, estimated_cost, estimated_latency_ms, quality_score
        """
        resp = self.client.post(
            "/v1/routing/select",
            json={
                "taskComplexity": task_complexity,
                "maxCostPerCall": max_cost_per_call,
                "maxLatencyMs": max_latency_ms,
                "minQualityScore": min_quality_score,
            },
        )
        resp.raise_for_status()
        return resp.json()
```

**Update TaskRouter to use CLIProxyRoutingClient:**

```python
# thegent/routing/task_router.py
class TaskRouter:
    def __init__(self, cliproxy_client: Optional[CLIProxyRoutingClient] = None):
        self.cliproxy_client = cliproxy_client or CLIProxyRoutingClient()

    def route(self, task_metadata: TaskMetadata) -> RouteResult:
        """Route task through CLIProxy instead of local Pareto router."""

        # Classify task
        category = self.classifier.classify(task_metadata)

        # Get constraints from task
        constraints = self.validator.validate(task_metadata)

        # Call CLIProxy for optimal model
        result = self.cliproxy_client.select_model(
            task_complexity=category,
            max_cost_per_call=constraints.max_cost,
            max_latency_ms=constraints.max_latency_ms,
            min_quality_score=constraints.min_quality_score,
        )

        return RouteResult(
            model_id=result["model_id"],
            provider=result["provider"],
            cost=result["estimated_cost"],
            latency_ms=result["estimated_latency_ms"],
        )
```

**Acceptance Criteria:**
- T5.1 test passes
- TaskRouter calls CLIProxy, not LiteLLM
- Response is correctly parsed
- No local Pareto computation

**Verification Command:**
```bash
pytest tests/integration/test_cliproxy_integration_routing.py -v
```

**Commit:**
```
feat(routing): replace LiteLLM with CLIProxy for task routing

Updates TaskRouter to call CLIProxy localhost:8317 /v1/routing/select
instead of LiteLLM for Pareto frontier routing. Adds CLIProxyRoutingClient.

@trace FR-CLIPROXY-INTEGRATION-001 FR-CLIPROXY-INTEGRATION-002
```

---

#### T5.3: Remove Migrated Routing Modules & Update tach.toml

**Files to delete:**
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/pareto_router.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/task_router.py` (keep stub)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/pareto_frontier_calculator.py` (if exists)

**Update `tach.toml`:**

Remove dependency from `thegent.routing` on `thegent.models`:

```toml
[[modules]]
path = "thegent.routing"
depends_on = ["thegent.config"]  # Only depends on config now (CLIProxy URL)
```

**Test:** Run boundary check

```bash
tach check
```

**Acceptance Criteria:**
- Old modules deleted
- tach.toml updated
- `tach check` passes (no boundary violations)
- No import errors in remaining routing module

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
tach check
pytest tests/ -k "not slow" -x
```

**Commit:**
```
refactor(routing): remove migrated Pareto router, update boundaries

Deletes pareto_router.py and related modules now in CLIProxy.
TaskRouter is now a thin wrapper calling CLIProxy /v1/routing/select.

Updates tach.toml to reflect new dependency structure (routing only
depends on config for CLIProxy URL).

@trace FR-CLIPROXY-INTEGRATION-003
```

---

#### T5.4: End-to-End Integration Test (thegent → CLIProxy → Provider)

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/integration/test_e2e_thegent_cliproxy_provider.py`

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requirement("FR-CLIPROXY-E2E-001")
@pytest.mark.requirement("FR-CLIPROXY-E2E-002")
def test_e2e_thegent_routes_and_calls_provider():
    """End-to-end: thegent → CLIProxy → actual LLM provider."""

    # Start CLIProxy (if not running)
    with ProcessManager(
        cmd="/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/bin/cliproxy server",
        port=8317,
        timeout=10,
    ) as _:
        # Create thegent client
        client = TheGentClient(routing_endpoint="http://localhost:8317")

        # Execute task through full stack
        result = client.chat_completion(
            task_metadata={
                "tokens_in": 2500,
                "category": "code_analysis",
            },
            messages=[{"role": "user", "content": "Explain Python async/await"}],
            max_tokens=500,
            max_cost_per_call=0.05,
            max_latency_ms=30000,
        )

        # Assert full flow succeeded
        assert result["id"] is not None
        assert result["choices"][0]["message"]["content"] is not None
        assert result["usage"]["prompt_tokens"] > 0
        assert result["usage"]["completion_tokens"] > 0
```

**Acceptance Criteria:**
- Full request flow succeeds: thegent → CLIProxy → provider
- Response is properly formatted
- Token counts are tracked
- Cost is recorded

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
pytest tests/integration/test_e2e_thegent_cliproxy_provider.py -v -s
```

**Commit:**
```
test(e2e): add end-to-end test for thegent → CLIProxy → provider flow

Verifies full integration: thegent routes task through CLIProxy, which
routes to actual LLM provider. Tests request/response handling, token
tracking, and cost accounting.

@trace FR-CLIPROXY-E2E-001 FR-CLIPROXY-E2E-002
```

---

#### T5.5: Parity Verification Suite (Full System)

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/integration/test_parity_legacy_vs_cliproxy_migration.py`

**Test Strategy:** Compare behavior before (with LiteLLM) and after (with CLIProxy).

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-MIGRATION-PARITY-001")
def test_parity_routing_legacy_vs_cliproxy():
    """Verify thegent routes identically before and after CLIProxy migration."""

    test_cases = [
        {"complexity": "FAST", "max_cost": 0.001},
        {"complexity": "NORMAL", "max_cost": 0.01},
        {"complexity": "COMPLEX", "max_cost": 0.05},
    ]

    for case in test_cases:
        # Legacy: Local Pareto router (from git history or backup)
        legacy_result = legacy_pareto_router.select(case)

        # New: CLIProxy routing
        cliproxy_result = thegent_client.route_task(**case)

        # Assert identical model selection
        assert legacy_result["model_id"] == cliproxy_result["model_id"], f"Model mismatch for {case}"

        # Assert costs within tolerance
        assert abs(legacy_result["cost"] - cliproxy_result["cost"]) < 0.0001
```

**Acceptance Criteria:**
- All parity tests pass
- Models match across all test cases
- Costs/latencies match (within tolerance)
- Quota enforcement is identical

**Verification Command:**
```bash
pytest tests/integration/test_parity_legacy_vs_cliproxy_migration.py -v
```

**Commit:**
```
test(migration): add comprehensive parity test suite for CLIProxy migration

Verifies thegent behavior is identical before and after migrating to
CLIProxy routing. Tests routing selection, cost accounting, quota
enforcement across all complexity tiers.

@trace FR-MIGRATION-PARITY-001 FR-MIGRATION-PARITY-002
```

---

## Cross-Track Integration Tests

### T0.0: Verify All CLIProxy Endpoints Are Accessible

**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/api/endpoints_integration_test.go`

```go
func TestAllRoutingEndpointsRespond(t *testing.T) {
    endpoints := []struct {
        method string
        path   string
    }{
        {"POST", "/v1/routing/select"},
        {"POST", "/v1/auth/oauth/refresh"},
        {"POST", "/v1/quota/check"},
        {"POST", "/v1/translate/acp"},
    }

    for _, ep := range endpoints {
        t.Run(ep.path, func(t *testing.T) {
            resp, err := http.Request(ep.method, fmt.Sprintf("http://localhost:8317%s", ep.path), nil)
            assert.NoError(t, err)
            assert.NotEqual(t, http.StatusNotFound, resp.StatusCode)
        })
    }
}
```

**Verification Command:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus
go test -run TestAllRoutingEndpointsRespond ./pkg/llmproxy/api -v
```

**Commit:**
```
test(integration): verify all CLIProxy Track 1 endpoints are accessible

Smoke test confirming /v1/routing/select, /v1/auth/oauth/refresh,
/v1/quota/check, /v1/translate/acp endpoints respond without 404s.

@trace FR-CLIPROXY-ENDPOINTS-001
```

---

## Summary Table: Tasks, Dependencies, Files

| Task ID | Title | Duration | Depends On | Files | Test | Verification |
|---------|-------|----------|-----------|-------|------|--------------|
| **T1.1** | Pareto test (failing) | 30m | None | `routing_pareto_integration_test.go` | ✓ (fails) | `go test TestPareto...` |
| **T1.2** | Pareto router impl | 2h | T1.1 | `pareto_router.go`, `pareto_types.go` | ✓ (passes) | `go test TestPareto...` |
| **T1.3** | TaskClassifier | 1.5h | T1.2 | `task_classifier.go`, `task_classifier_test.go` | ✓ (passes) | `go test TestTaskClassifier...` |
| **T1.4** | /v1/routing/select endpoint | 1.5h | T1.3 | `routing_handler.go`, `routing_handler_test.go` | ✓ (passes) | `go test TestPOSTRoutingSelect...` |
| **T1.5** | Parity test (routing) | 1h | T1.4 | `test_parity_pareto_router_vs_cliproxy.py` | ✓ (passes) | `pytest test_parity_pareto...` |
| **T2.1** | ACP adapter test (failing) | 30m | T1.4 | `acp_adapter_registry_test.go` | ✓ (fails) | `go test TestACPAdapter...` |
| **T2.2** | ACP adapter impl | 1.5h | T2.1 | `acp_adapter.go`, `acp_request.go`, `acp_response.go` | ✓ (passes) | `go test TestACPAdapter...` |
| **T2.3** | Parity test (adapters) | 1h | T2.2 | `test_parity_adapters_vs_cliproxy.py` | ✓ (passes) | `pytest test_parity_adapters...` |
| **T3.1** | OAuth test (failing) | 30m | T1.4 | `oauth_token_manager_test.go` | ✓ (fails) | `go test TestOAuthTokenManager...` |
| **T3.2** | OAuth manager impl | 1.5h | T3.1 | `oauth_token_manager.go`, `oauth_types.go` | ✓ (passes) | `go test TestOAuthTokenManager... -race` |
| **T3.3** | Parity test (auth) | 1h | T3.2 | `test_parity_oauth_vs_cliproxy.py` | ✓ (passes) | `pytest test_parity_oauth...` |
| **T4.1** | Quota test (failing) | 30m | T1.4 | `quota_enforcer_test.go` | ✓ (fails) | `go test TestQuotaEnforcer...` |
| **T4.2** | Quota enforcer impl | 1.5h | T4.1 | `quota_enforcer.go`, `quota_types.go` | ✓ (passes) | `go test TestQuotaEnforcer... -race` |
| **T4.3** | Parity test (quota) | 1h | T4.2 | `test_parity_quota_vs_cliproxy.py` | ✓ (passes) | `pytest test_parity_quota...` |
| **T5.1** | CLIProxy integration test (failing) | 30m | T1.5+T2.3+T3.3+T4.3 | `test_cliproxy_integration_routing.py` | ✓ (fails) | `pytest test_cliproxy_integration...` |
| **T5.2** | TaskRouter → CLIProxy | 2h | T5.1 | `cliproxy_client.py`, updated `task_router.py` | ✓ (passes) | `pytest test_cliproxy_integration...` |
| **T5.3** | Remove old modules & update tach.toml | 1h | T5.2 | Delete files, update `tach.toml` | ✓ (passes) | `tach check` |
| **T5.4** | E2E test (thegent → CLIProxy → provider) | 1.5h | T5.3 | `test_e2e_thegent_cliproxy_provider.py` | ✓ (passes) | `pytest test_e2e_...` |
| **T5.5** | Full parity suite (legacy vs CLIProxy) | 2h | T5.4 | `test_parity_legacy_vs_cliproxy_migration.py` | ✓ (passes) | `pytest test_parity_legacy...` |
| **T0.0** | Endpoint smoke test | 30m | All (verify) | `endpoints_integration_test.go` | ✓ (passes) | `go test TestAllRouting...` |

---

## Execution Plan: Parallel Tracks

```
Day 1 (8h wall clock):
├─ Work Stream 1 (T1.1–T1.5): Pareto router port [4 subagents, 2-3h each]
│  └─ T1.1 (30m) → T1.2 (2h) → T1.3 (1.5h) → T1.4 (1.5h) → T1.5 (1h)
├─ Work Stream 2 (T2.1–T2.3): Adapters [parallel, 1.5–2h]
│  └─ T2.1 (30m) → T2.2 (1.5h) → T2.3 (1h)
├─ Work Stream 3 (T3.1–T3.3): Auth [parallel, 1.5–2h]
│  └─ T3.1 (30m) → T3.2 (1.5h) → T3.3 (1h)
└─ Work Stream 4 (T4.1–T4.3): Quota [parallel, 1.5–2h]
   └─ T4.1 (30m) → T4.2 (1.5h) → T4.3 (1h)

Day 2 (6h wall clock):
├─ Work Stream 5 (T5.1–T5.5): Integration [sequential, 2–3h]
│  └─ T5.1 (30m) → T5.2 (2h) → T5.3 (1h) → T5.4 (1.5h) → T5.5 (2h)
└─ Verification (T0.0): Smoke test [30m]
```

**Parallelism:** Streams 1–4 run in parallel once Stream 1's routing endpoint is available (after T1.4). Stream 5 is sequential, starting after all parity tests pass.

---

## Quality Gates & Acceptance Criteria

All tasks must pass:
1. **Failing test runs and fails** (TDD requirement)
2. **Implementation makes test pass** (minimal viable change)
3. **Parity test verifies identical behavior** (thegent vs CLIProxy)
4. **No new lint/type/test failures** (`go vet`, `pytest`, type checkers)
5. **Boundary enforcement** (`tach check` passes for Python; `go vet` for Go)
6. **All integration tests pass** (end-to-end flows)

---

## Commits & PR Strategy

**Per-task commits (small, reviewable diffs):**
- Test commits: Failing test + minimal scaffolding
- Implementation commits: Core logic + passing test
- Parity commits: Parity test + verification
- Integration commits: Updated imports + boundary changes
- Cleanup commits: Remove old code

**PR: Single Track 1 PR** collecting all commits in DAG order.

**Pre-merge checks:**
- All tests pass (Go + Python)
- Parity suite 100% pass rate
- `tach check` succeeds
- No quality regressions

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| CLIProxy endpoint timeout | Add 10s client timeout; implement retry with backoff (T1.2) |
| Floating-point cost mismatch | Use parity tolerance (0.1% for cost, 10ms for latency) in tests |
| Concurrent quota access | Use RWMutex with `go test -race` validation (T4.2) |
| Old Pareto code still imported | Run `grep -r "pareto_router"` after deletion (T5.3) |
| LiteLLM still in use | Update all imports to CLIProxyRoutingClient (T5.2) |

---

## Appendix: File Structure Reference

```
CLIProxy (Go):
  pkg/llmproxy/
  ├─ registry/
  │  ├─ pareto_router.go (NEW)
  │  ├─ pareto_types.go (NEW)
  │  ├─ pareto_router_test.go (NEW)
  │  ├─ task_classifier.go (NEW)
  │  └─ task_classifier_test.go (NEW)
  ├─ translator/acp/ (NEW)
  │  ├─ acp_adapter.go
  │  ├─ acp_request.go
  │  ├─ acp_response.go
  │  └─ acp_adapter_registry_test.go
  ├─ auth/
  │  ├─ oauth_token_manager.go (NEW)
  │  ├─ oauth_types.go (NEW)
  │  └─ oauth_token_manager_test.go (NEW)
  ├─ usage/
  │  ├─ quota_enforcer.go (NEW)
  │  ├─ quota_types.go (NEW)
  │  └─ quota_enforcer_test.go (NEW)
  └─ api/
     ├─ routing_handler.go (NEW)
     ├─ routing_handler_test.go (NEW)
     └─ endpoints_integration_test.go (NEW)

thegent (Python):
  src/thegent/
  ├─ routing/
  │  ├─ cliproxy_client.py (NEW)
  │  ├─ task_router.py (UPDATED - now thin wrapper)
  │  └─ pareto_router.py (DELETE in T5.3)
  ├─ adapters/ (NO CHANGES - delegate to CLIProxy)
  └─ integrations/ (NO CHANGES - delegate to CLIProxy)

  tests/
  ├─ routing/
  │  └─ test_parity_pareto_router_vs_cliproxy.py (NEW)
  ├─ adapters/
  │  └─ test_parity_adapters_vs_cliproxy.py (NEW)
  ├─ auth/
  │  └─ test_parity_oauth_vs_cliproxy.py (NEW)
  ├─ quota/
  │  └─ test_parity_quota_vs_cliproxy.py (NEW)
  └─ integration/
     ├─ test_cliproxy_integration_routing.py (NEW)
     ├─ test_e2e_thegent_cliproxy_provider.py (NEW)
     └─ test_parity_legacy_vs_cliproxy_migration.py (NEW)

tach.toml (UPDATED in T5.3)
  - thegent.routing now depends_on = ["thegent.config"]
```

---

## Next Steps After Track 1

Track 2: Migrate remaining thegent integrations (cost tracking, quota lifecycle)
Track 3: Optimize CLIProxy caching + batching for thegent workloads
Track 4: Full hexagonal split validation + production deployment

---

This plan provides **bite-sized, test-driven implementation** with clear parity verification at each stage, enabling safe, incremental migration of ~30K LOC from thegent Python to CLIProxy Go while maintaining behavior equivalence.
