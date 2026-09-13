from __future__ import annotations

import importlib.util
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import orjson as json
import pytest

import thegent.execution_jsonl_parsers as jsonl_parsers
from thegent.agents.synthesis import GenerationResponse, ProgramSynthesizer
from thegent.agents.tool_adapter import ToolAdapter, ToolDefinition
from thegent.clode_binary_discovery import is_thegent_shim
from thegent.config import ThegentSettings
from thegent.execution import ConcurrencyController
from thegent.infra.mojo_bridge import MojoTask, build_dispatch_script
from thegent.sitback_plugins import _probe_harness_status
from thegent.ux.kpis import KPIDashboard

_CONFIG_MANAGER_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "thegent" / "config" / "manager.py"
)
_config_manager_spec = importlib.util.spec_from_file_location(
    "thegent_config_manager_module", _CONFIG_MANAGER_PATH
)
assert _config_manager_spec is not None and _config_manager_spec.loader is not None
_config_manager_module = importlib.util.module_from_spec(_config_manager_spec)
_config_manager_spec.loader.exec_module(_config_manager_module)
ConfigManager = _config_manager_module.ConfigManager


@pytest.mark.unit
class TestWL6610SynthesisProviderPipeline:
    def test_synthesize_uses_provider_and_captures_metadata(self) -> None:
        calls: list[tuple[str, str | None]] = []

        class _Provider:
            def generate_code(
                self, prompt: str, formal_spec: str | None = None
            ) -> GenerationResponse:
                calls.append((prompt, formal_spec))
                return GenerationResponse(
                    source_code="def run_task():\n    return 'ok'\n",
                    provider="cliproxy",
                    model="glm-5",
                    tokens_in=12,
                    tokens_out=34,
                )

        result = ProgramSynthesizer(run_id="wl6610", provider=_Provider()).synthesize(
            "write task",
            formal_spec="must terminate",
        )

        assert calls == [("write task", "must terminate")]
        assert result.source_code.startswith("def run_task")
        assert result.generation_metadata["provider"] == "cliproxy"
        assert result.generation_metadata["model"] == "glm-5"
        assert result.generation_metadata["tokens_in"] == 12
        assert result.generation_metadata["tokens_out"] == 34
        assert float(result.generation_metadata["latency_ms"]) >= 0.0

    def test_provider_failure_is_not_swallowed(self) -> None:
        class _BrokenProvider:
            def generate_code(
                self, prompt: str, formal_spec: str | None = None
            ) -> GenerationResponse:
                raise RuntimeError("provider_down")

        with pytest.raises(RuntimeError, match="provider_down"):
            ProgramSynthesizer(
                run_id="wl6610-broken", provider=_BrokenProvider()
            ).synthesize("prompt")

    def test_no_deterministic_fallback_provider_exists(self) -> None:
        with pytest.raises(RuntimeError, match="No synthesis provider configured"):
            ProgramSynthesizer(run_id="wl6610-default").synthesize("prompt")


@pytest.mark.unit
class TestWL6611ToolAdapterProtocols:
    @pytest.mark.asyncio
    async def test_protocol_success_for_mcp_rest_python_and_cli(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = ToolAdapter(agent_id="wl6611")
        adapter.discovered_tools["mcp_tool"] = ToolDefinition(
            tool_id="mcp_tool",
            description="mcp",
            parameters={"query": "string"},
            protocol="mcp",
            target="server:tool",
        )
        adapter.discovered_tools["rest_tool"] = ToolDefinition(
            tool_id="rest_tool",
            description="rest",
            parameters={"value": "number"},
            protocol="rest",
            endpoint="https://example.invalid/v1",
        )
        adapter.discovered_tools["python_tool"] = ToolDefinition(
            tool_id="python_tool",
            description="python",
            parameters={"obj": "any"},
            protocol="python",
            target="json:dumps",
        )
        adapter.discovered_tools["cli_tool"] = ToolDefinition(
            tool_id="cli_tool",
            description="cli",
            parameters={},
            protocol="cli",
            command="echo lane-b",
        )

        async def _rest(
            _tool: ToolDefinition, kwargs: dict[str, object]
        ) -> dict[str, object]:
            return {"status": "success", "protocol": "rest", "data": kwargs}

        monkeypatch.setattr(ToolAdapter, "_execute_rest", staticmethod(_rest))

        mcp = await adapter.wrap_tool("mcp_tool")(query="q")
        rest = await adapter.wrap_tool("rest_tool")(value=7)
        py = await adapter.wrap_tool("python_tool")(obj={"k": "v"})
        cli = await adapter.wrap_tool("cli_tool")()

        assert mcp["protocol"] == "mcp"
        assert rest["protocol"] == "rest"
        assert py["protocol"] == "python"
        assert "k" in py["data"]
        assert cli["protocol"] == "cli"
        assert "lane-b" in cli["data"]

    @pytest.mark.asyncio
    async def test_contract_violation_returns_typed_error(self) -> None:
        adapter = ToolAdapter(agent_id="wl6611-contract")
        adapter.discovered_tools["contract_tool"] = ToolDefinition(
            tool_id="contract_tool",
            description="contract",
            parameters={"expected": "string"},
            protocol="mcp",
            target="server:tool",
        )
        result = await adapter.wrap_tool("contract_tool")(unexpected="value")
        assert result["status"] == "error"
        assert result["error"]["type"] == "contract_violation"
        assert result["error"]["missing"] == ["expected"]
        assert result["error"]["unexpected"] == ["unexpected"]

    @pytest.mark.asyncio
    async def test_unsupported_protocol_raises(self) -> None:
        adapter = ToolAdapter(agent_id="wl6611-unsupported")
        adapter.discovered_tools["bad"] = ToolDefinition(
            tool_id="bad",
            description="bad",
            parameters={},
            protocol="grpc",
        )
        with pytest.raises(ValueError, match="Unsupported protocol"):
            await adapter.wrap_tool("bad")()


@pytest.mark.unit
class TestWL6612KpisFromTelemetry:
    def test_throughput_changes_with_run_registry_telemetry(
        self, tmp_path: Path
    ) -> None:
        now = datetime.now(UTC)
        rows = [
            {"event": "start", "ts": now.isoformat(), "run_id": "r1"},
            {
                "event": "end",
                "ts": now.isoformat(),
                "run_id": "r1",
                "status": "completed",
            },
            {"event": "start", "ts": now.isoformat(), "run_id": "r2"},
            {"event": "end", "ts": now.isoformat(), "run_id": "r2", "status": "failed"},
        ]
        (tmp_path / "run_registry.jsonl").write_text(
            "\n".join(json.dumps(r).decode() for r in rows), encoding="utf-8"
        )

        settings = ThegentSettings(session_dir=tmp_path)
        metrics = KPIDashboard(settings).get_metrics()
        assert metrics["throughput"] == 1.0
        assert 0.0 <= metrics["reliability"] <= 1.0
        assert 0.0 <= metrics["availability"] <= 1.0
        assert "timestamp" in metrics

    def test_metrics_remain_bounded_when_telemetry_absent(self, tmp_path: Path) -> None:
        settings = ThegentSettings(session_dir=tmp_path)
        metrics = KPIDashboard(settings).get_metrics()
        assert metrics["throughput"] == 0.0
        assert 0.0 <= metrics["reliability"] <= 1.0
        assert 0.0 <= metrics["availability"] <= 1.0


@pytest.mark.unit
class TestWL6613HarnessProbeStatus:
    def test_probe_reports_disabled_by_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "thegent.config.ThegentSettings",
            lambda: types.SimpleNamespace(sitback_harness=False),
        )
        status = _probe_harness_status()
        assert status["status"] == "unavailable"
        assert status["reason"] == "disabled_by_config"

    def test_probe_reports_missing_dependency(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "thegent.config.ThegentSettings",
            lambda: types.SimpleNamespace(sitback_harness=True),
        )
        missing_attr_module = types.ModuleType("thegent.skills.terminal")
        monkeypatch.setitem(sys.modules, "thegent.skills.terminal", missing_attr_module)
        status = _probe_harness_status()
        assert status["status"] == "unavailable"
        assert status["reason"] == "dependency_missing"

    def test_probe_reports_runtime_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "thegent.config.ThegentSettings",
            lambda: types.SimpleNamespace(sitback_harness=True),
        )
        fake_terminal = types.ModuleType("thegent.skills.terminal")

        def _raise() -> str:
            raise RuntimeError("boom")

        fake_terminal.heliosShield_status = _raise  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "thegent.skills.terminal", fake_terminal)
        status = _probe_harness_status()
        assert status["status"] == "error"
        assert status["reason"] == "runtime_failure"


@pytest.mark.unit
class TestWL6614MojoDispatchScripts:
    def test_builds_module_function_targeted_dispatch_script(self) -> None:
        script = build_dispatch_script(
            MojoTask(
                task_id="wl6614-ok", module="json", function="loads", args={"s": "{}"}
            ),
        )
        assert "json" in script
        assert "loads" in script

    def test_unknown_module_and_function_raise_actionable_errors(self) -> None:
        with pytest.raises(ValueError, match="Unknown module"):
            build_dispatch_script(
                MojoTask(
                    task_id="wl6614-missing-module",
                    module="missing_mod_zzz",
                    function="run",
                    args={},
                )
            )
        with pytest.raises(ValueError, match="Unknown function"):
            build_dispatch_script(
                MojoTask(
                    task_id="wl6614-missing-fn",
                    module="json",
                    function="missing_fn",
                    args={},
                )
            )

    def test_malformed_args_payload_raises(self) -> None:
        with pytest.raises(ValueError, match="Malformed args payload"):
            build_dispatch_script(
                MojoTask(
                    task_id="wl6614-bad-args", module="json", function="loads", args=[]
                )
            )  # type: ignore[arg-type]


@pytest.mark.unit
class TestWL6615NativeParserDiagnostics:
    def test_native_parse_failure_increments_diagnostics_and_falls_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _Native:
            @staticmethod
            def parse_checkpoint_by_id(
                line: str, checkpoint_id: str
            ) -> dict[str, object] | None:
                raise RuntimeError("native exploded")

        jsonl_parsers.reset_native_parse_diagnostics()
        monkeypatch.setattr(jsonl_parsers, "_get_native_parser", lambda: _Native())
        parsed = jsonl_parsers.parse_checkpoint_by_id(
            '{"checkpoint_id":"cp","status":"ok"}', "cp"
        )
        diag = jsonl_parsers.get_native_parse_diagnostics()

        assert parsed == {"checkpoint_id": "cp", "status": "ok"}
        assert diag["total_failures"] == 1
        assert diag["by_parser"]["parse_checkpoint_by_id"] == 1
        assert diag["last_error_type"] == "RuntimeError"


@pytest.mark.unit
class TestWL6616ConfigLoadErrorClassification:
    def test_successful_load(self, tmp_path: Path) -> None:
        config = tmp_path / "config.json"
        config.write_text('{"foo":"bar"}', encoding="utf-8")
        manager = ConfigManager(config)
        assert manager.config["foo"] == "bar"
        assert manager.last_load_error is None

    def test_malformed_json_sets_invalid_json_error(self, tmp_path: Path) -> None:
        config = tmp_path / "config.json"
        config.write_text("{not-json", encoding="utf-8")
        manager = ConfigManager(config)
        assert manager.config == {}
        assert manager.last_load_error is not None
        assert manager.last_load_error.reason == "invalid_json"

    def test_unreadable_path_sets_read_error(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config.json"
        config_dir.mkdir()
        manager = ConfigManager(config_dir)
        assert manager.config == {}
        assert manager.last_load_error is not None
        assert manager.last_load_error.reason == "read_error"


@pytest.mark.unit
class TestWL6617ShimDetectionDiagnostics:
    def test_direct_shim_and_non_shim(self, tmp_path: Path) -> None:
        assert is_thegent_shim(str(tmp_path / "thegent-shims-claude")) is True
        assert is_thegent_shim(str(tmp_path / "claude")) is False

    def test_broken_symlink_returns_false(self, tmp_path: Path) -> None:
        link = tmp_path / "claude-link"
        link.symlink_to(tmp_path / "missing-target")
        assert is_thegent_shim(str(link)) is False

    def test_permission_error_returns_false_and_logs(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level("WARNING")
        monkeypatch.setattr(Path, "is_symlink", lambda self: True)
        monkeypatch.setattr(
            Path,
            "readlink",
            lambda self: (_ for _ in ()).throw(PermissionError("denied")),
        )
        assert is_thegent_shim("/tmp/claude") is False
        assert any("shim_resolution_failed" in r.message for r in caplog.records)


@pytest.mark.unit
class TestWL6618BottleneckStatusPayload:
    def test_returns_explicit_payload_when_detector_missing(
        self, tmp_path: Path
    ) -> None:
        controller = ConcurrencyController(tmp_path)
        controller.bottleneck_detector = None
        payload = controller.get_bottlenecks()
        assert payload["detector_available"] is False
        assert payload["reason"] == "bottleneck_detector_unavailable"

    def test_detector_present_payload_contract_unchanged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        controller = ConcurrencyController(tmp_path)

        class _Detector:
            @staticmethod
            def identify_slow_points() -> list[dict[str, str]]:
                return [{"component": "cpu"}]

            @staticmethod
            def detect_resource_contention(
                snapshot: dict[str, object], harness_cards: dict[str, object]
            ) -> list[dict[str, str]]:
                return [{"resource": "memory"}]

        controller.bottleneck_detector = _Detector()
        controller.harness_cards = {}
        monkeypatch.setattr(
            "thegent.orchestration.resource.resource_management.sample_extended_resources",
            dict,
        )
        payload = controller.get_bottlenecks()
        assert set(payload.keys()) == {"slow_points", "resource_contention"}
        assert payload["slow_points"] == [{"component": "cpu"}]
        assert payload["resource_contention"] == [{"resource": "memory"}]


# noqa: PT018
