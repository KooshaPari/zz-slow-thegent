### [WL-5200] cli test_wl136_tooling_routing:81 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/cli/test_wl136_tooling_routing.py:81]
Replace this import-error skip with deterministic setup so CLI import validation always runs in CI.

### [WL-5201] cli test_wl136_tooling_routing:96 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/cli/test_wl136_tooling_routing.py:96]
Remove this import-error skip path by stabilizing module preconditions in the test fixture.

### [WL-5202] cli test_wl136_tooling_routing:124 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/cli/test_wl136_tooling_routing.py:124]
Replace the missing-server skip with a fixture-backed server path so this assertion is deterministic.

### [WL-5203] e2e cli_runner_compat:109 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/e2e/cli_runner_compat.py:109]
Convert command-surface drift skip behavior into an explicit failing assertion with actionable diff output.

### [WL-5204] infra test_fast_websocket:64 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:64]
Eliminate dependency skip for websocket-client by injecting a deterministic transport test double.

### [WL-5205] infra test_fast_websocket:94 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:94]
Replace websockets-library availability skip with controlled fixture wiring so fallback behavior is asserted.

### [WL-5206] infra test_fast_websocket:111 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:111]
Remove this environment-branch skip by parameterizing availability states and asserting both branches.

### [WL-5207] infra test_fast_websocket:114 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:114]
Replace fallback dependency skip with a deterministic adapter mock that covers the fallback path in CI.

### [WL-5208] infra test_fast_websocket:155 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:155]
Refactor this availability skip into an explicit fixture matrix that exercises websocket branches predictably.

### [WL-5209] infra test_fast_websocket:211 follow-up

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/tests/infra/test_fast_websocket.py:211]
Drop this websockets availability skip by using a stable protocol stub and asserting timeout/error semantics.
