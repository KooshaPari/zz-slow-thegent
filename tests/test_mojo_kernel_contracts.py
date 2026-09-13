from __future__ import annotations

from pathlib import Path

import orjson as json

CONTRACT_PATH = Path("contracts/runtime/mojo_kernel_contract_v1.json")
HARNESS_DEF_PATH = Path("benchmarks/mojo_score_rank_v1_harness.json")
FIXTURE_SPEC_PATH = Path("benchmarks/mojo_score_rank_v1_fixture_spec.json")


def test_contract_has_expected_harness_and_fixture_refs() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    benchmark_contract = contract["benchmark_contract"]

    assert benchmark_contract["harness_id"] == "mojo-kernel-bench-v1"
    assert benchmark_contract["harness_definition_ref"] == str(HARNESS_DEF_PATH)
    assert benchmark_contract["fixture_spec_ref"] == str(FIXTURE_SPEC_PATH)
    assert benchmark_contract["datasets"] == ["small-128", "medium-1024", "large-8192"]
    assert benchmark_contract["correctness_hooks"] == [
        "fixture_expected_output_parity",
        "rank_order_exact",
        "score_absolute_error_max",
    ]


def test_contract_schemas_include_required_fields() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    input_schema = contract["schemas"]["score_rank_input"]
    output_schema = contract["schemas"]["score_rank_output"]

    assert set(input_schema["required"]) == {"request_id", "candidates", "weights"}
    assert set(output_schema["required"]) == {"request_id", "ranked"}
    assert set(input_schema["properties"]["weights"]["required"]) == {"cost", "latency", "quality"}
    assert set(input_schema["properties"]["candidates"]["items"]["required"]) == {"id", "cost", "latency", "quality"}
    assert set(output_schema["properties"]["ranked"]["items"]["required"]) == {"id", "score", "rank"}


def test_harness_definition_matches_fixture_spec_and_contract() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    harness = json.loads(HARNESS_DEF_PATH.read_text(encoding="utf-8"))
    fixture_spec = json.loads(FIXTURE_SPEC_PATH.read_text(encoding="utf-8"))

    assert harness["harness_id"] == contract["benchmark_contract"]["harness_id"]
    assert harness["contract_ref"] == str(CONTRACT_PATH)
    assert harness["fixture_spec_ref"] == str(FIXTURE_SPEC_PATH)
    assert set(fixture_spec["dataset_sizes"].keys()) == set(contract["benchmark_contract"]["datasets"])


def test_contract_promotion_gate_fields_are_present() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    gate = contract["benchmark_contract"]["promotion_gate"]

    assert set(gate) == {
        "p95_speedup_vs_python_min",
        "p99_regression_max_pct",
        "correctness_failures_allowed",
    }
    assert gate["p95_speedup_vs_python_min"] > 0
    assert gate["p99_regression_max_pct"] >= 0
    assert gate["correctness_failures_allowed"] == 0
