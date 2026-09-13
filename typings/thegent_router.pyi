"""Type stubs for thegent_router — native Rust extension (PyO3/maturin).

Optional native router providing Pareto-optimal multi-objective routing.
Falls back to PurePythonRouter when not installed.
"""

class PyParetoRouter:
    @classmethod
    def with_full_config(
        cls,
        low_threshold: float = ...,
        high_threshold: float = ...,
        hysteresis_band: float = ...,
        hysteresis_dwell_s: float = ...,
        hysteresis_max_dwell_s: float = ...,
        hysteresis_override: float = ...,
    ) -> PyParetoRouter: ...
    def route(self, task_description: str) -> object: ...
    def select_agent(self, task_description: str, available_agents: list[object]) -> object: ...
