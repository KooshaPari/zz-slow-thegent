### [WL-6610]

**Title:** Replace simulated neural synthesis output with provider-backed code generation pipeline
**Source Path+Line:** [thegent/src/thegent/agents/synthesis.py:40]
**Acceptance Checklist:**

- [x] Replace `_mock_llm_generation` call path with real provider invocation that accepts prompt and optional formal spec context.
- [x] Capture generation metadata (provider/model/latency/token usage) alongside synthesized source for downstream verification.
- [x] Add tests covering successful generation, provider failure propagation, and deterministic fallback prevention.
      **Notes:** The current synthesis flow still calls a mock generator, so verification runs on synthetic code instead of model-produced output.
      **Evidence:** Updated `ProgramSynthesizer` provider pipeline + metadata in `src/thegent/agents/synthesis.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6610SynthesisProviderPipeline`.

### [WL-6611]

**Title:** Implement real protocol adapters for discovered tools instead of mock adapted output
**Source Path+Line:** [thegent/src/thegent/agents/tool_adapter.py:69]
**Acceptance Checklist:**

- [x] Replace mock `adapted_call` body with protocol-specific execution for `mcp`, `rest`, `python`, and `cli` tool definitions.
- [x] Validate kwargs against declared parameters before execution and return typed error payloads for contract violations.
- [x] Add tests for one successful invocation per supported protocol plus unsupported-protocol failure handling.
      **Notes:** `wrap_tool` currently returns a static success payload and never executes the discovered tool.
      **Evidence:** Implemented protocol dispatch + contract validation in `src/thegent/agents/tool_adapter.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6611ToolAdapterProtocols`.

### [WL-6612]

**Title:** Compute throughput KPI from run telemetry instead of fixed placeholder values
**Source Path+Line:** [thegent/src/thegent/ux/kpis.py:22]
**Acceptance Checklist:**

- [x] Derive `throughput` from concrete session/run artifacts rather than hardcoded constants.
- [x] Keep metric timestamps and existing schema stable while populating live values for reliability/availability when sources exist.
- [x] Add tests proving KPI values change with input telemetry and remain bounded when telemetry is absent.
      **Notes:** The KPI dashboard currently emits placeholder throughput and mostly static health numbers.
      **Evidence:** Added run-registry telemetry KPI computation in `src/thegent/ux/kpis.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6612KpisFromTelemetry`.

### [WL-6613]

**Title:** Replace harness status placeholder with explicit health probe and error classification
**Source Path+Line:** [thegent/src/thegent/sitback_plugins.py:136]
**Acceptance Checklist:**

- [x] Rename and implement the status provider as a concrete harness probe that reports `available`, `unavailable`, and `error` states.
- [x] Distinguish missing dependency, runtime failure, and disabled-by-config outcomes in structured fields.
- [x] Add tests for harness present, harness missing, and probe exception scenarios.
      **Notes:** The current helper is explicitly placeholder-oriented and returns ambiguous fallback states.
      **Evidence:** Replaced placeholder with `_probe_harness_status` classification in `src/thegent/sitback_plugins.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6613HarnessProbeStatus`.

### [WL-6614]

**Title:** Generate module/function-targeted Mojo dispatch scripts instead of generic placeholder main()
**Source Path+Line:** [thegent/src/thegent/infra/mojo_bridge.py:414]
**Acceptance Checklist:**

- [x] Build Mojo script bodies that call the requested `task.module` and `task.function` with decoded args.
- [x] Validate task contract before script generation and surface actionable errors for missing symbols/signature mismatches.
- [x] Add tests for successful dispatch, unknown module/function, and malformed args payloads.
      **Notes:** The default script path still prints raw args and does not invoke the requested kernel function.
      **Evidence:** Added `build_dispatch_script`/`build_python_dispatch_kernel_script` preflight validation in `src/thegent/infra/mojo_bridge.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6614MojoDispatchScripts` and `tests/test_unit_mojo_bridge.py`.

### [WL-6615]

**Title:** Add structured parse-failure accounting for native checkpoint parser exceptions
**Source Path+Line:** [thegent/src/thegent/execution_jsonl_parsers.py:38]
**Acceptance Checklist:**

- [x] Replace silent exception swallow in native parse path with structured diagnostics counters/logging.
- [x] Preserve fallback-to-Python behavior while exposing parse failure reasons to observability surfaces.
- [x] Add tests ensuring native exceptions increment diagnostics and still return correct fallback parse results.
      **Notes:** Native parser failures are currently dropped silently, obscuring parser reliability issues.
      **Evidence:** Added native parse diagnostics counters/logging in `src/thegent/execution_jsonl_parsers.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6615NativeParserDiagnostics` and `tests/test_execution_jsonl_parsers.py`.

### [WL-6616]

**Title:** Harden config load failures with explicit error surfacing instead of empty-config fallback
**Source Path+Line:** [thegent/src/thegent/config/manager.py:34]
**Acceptance Checklist:**

- [x] Replace bare `except` fallback with explicit error classification for invalid JSON vs I/O failures.
- [x] Preserve startup behavior while exposing parse/load failures through logger and/or typed exception pathway.
- [x] Add tests for malformed config, unreadable file, and successful load scenarios.
      **Notes:** Returning `{}` on all errors hides broken user config and makes diagnosis difficult.
      **Evidence:** Added `ConfigLoadError` + classified load diagnostics in `src/thegent/config/manager.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6616ConfigLoadErrorClassification`.

### [WL-6617]

**Title:** Improve shim detection error handling in native Claude binary discovery path
**Source Path+Line:** [thegent/src/thegent/clode_binary_discovery.py:16]
**Acceptance Checklist:**

- [x] Replace silent `OSError` swallow with traceable diagnostics for symlink resolution failures.
- [x] Ensure shim detection still returns deterministic booleans for non-existent paths and permission-restricted links.
- [x] Add tests for direct shim path, non-shim path, broken symlink, and permission error conditions.
      **Notes:** Current behavior suppresses symlink read failures, making native binary resolution failures opaque.
      **Evidence:** Added shim-resolution warning diagnostics in `src/thegent/clode_binary_discovery.py`; covered by `tests/test_wl661x_lane_b.py::TestWL6617ShimDetectionDiagnostics`.

### [WL-6618]

**Title:** Return explicit bottleneck status payload when detector is unavailable
**Source Path+Line:** [thegent/src/thegent/execution.py:463]
**Acceptance Checklist:**

- [x] Replace empty-dict return with stable schema that indicates detector availability and why data is missing.
- [x] Keep existing populated payload contract unchanged when detector is present.
- [x] Add tests for detector-missing and detector-present branches.
      **Notes:** The current empty response is ambiguous for callers that need to distinguish "no bottlenecks" from "no detector configured".
      **Evidence:** Added explicit unavailable payload in `src/thegent/execution.py::ConcurrencyController.get_bottlenecks`; covered by `tests/test_wl661x_lane_b.py::TestWL6618BottleneckStatusPayload`.

### [WL-6619]

**Title:** Add strict provider-definition validation for cliproxy JSON loading path
**Source Path+Line:** [thegent/src/thegent/agents/cliproxy_manager.py:37]
**Acceptance Checklist:**

- [x] Replace generic `{}` fallback with validation errors that identify missing file, invalid JSON, and non-object payloads.
- [x] Keep downstream call sites resilient by returning typed validation results or raising controlled exceptions.
- [x] Add tests for valid definitions, malformed JSON, missing files, and array/scalar JSON payloads.
      **Notes:** `_load_json` currently collapses all load/parse problems into empty dicts, masking configuration defects.
      **Evidence:** Added `ProviderDefinitionsLoadError` + warning-backed fallback in `_get_provider_definitions`; added `TestProviderDefinitionJsonLoading` cases in `tests/test_unit_cliproxy_manager.py`.
