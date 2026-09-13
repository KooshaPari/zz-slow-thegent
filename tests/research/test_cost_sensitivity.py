
from thegent.research.cost_sensitivity import CostSensitivityFramework


def test_cost_sensitivity_framework():
    framework = CostSensitivityFramework(
        baseline_config={"policy_depth": 1},
        experiment_a_config={"policy_depth": 2},
        experiment_b_config={"policy_depth": 5},
    )

    def dummy_action():
        return "done"

    framework.run_experiment("baseline", dummy_action)
    framework.run_experiment("experiment_a", dummy_action)
    framework.run_experiment("experiment_b", dummy_action)

    results = framework.analyze()

    assert "baseline" in results
    assert "experiment_a" in results
    assert "experiment_b" in results

    # Latency should follow policy depth
    assert results["experiment_b"]["avg_latency_ms"] > results["baseline"]["avg_latency_ms"]
    assert results["baseline"]["avg_cost"] == 0.05
    assert results["experiment_b"]["avg_cost"] == 0.03
