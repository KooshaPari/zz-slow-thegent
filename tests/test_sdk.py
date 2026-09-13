"""Tests for thegent.sdk public API facade.

# @trace FR-SDK-102
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# FR-SDK-102: SDK module imports
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SDK-102")
class TestSDKImports:
    """Verify the sdk module is importable and exposes the expected surface."""

    def test_sdk_module_importable(self) -> None:
        import thegent.sdk  # noqa: F401

    def test_sdk_has_version_constant(self) -> None:
        from thegent.sdk import VERSION

        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    def test_sdk_has_get_version_function(self) -> None:
        from thegent.sdk import get_version

        assert callable(get_version)

    def test_sdk_get_version_returns_string(self) -> None:
        from thegent.sdk import get_version

        result = get_version()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sdk_has_all_defined(self) -> None:
        import thegent.sdk

        assert hasattr(thegent.sdk, "__all__")
        assert isinstance(thegent.sdk.__all__, list)
        assert len(thegent.sdk.__all__) > 0

    def test_sdk_all_symbols_importable(self) -> None:
        import thegent.sdk

        for name in thegent.sdk.__all__:
            assert hasattr(thegent.sdk, name), f"__all__ lists {name!r} but it is not defined"


# ---------------------------------------------------------------------------
# FR-SDK-102: Public types
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SDK-102")
class TestSDKPublicTypes:
    """Verify public types are importable and well-formed."""

    def test_sub_agent_request_importable_from_sdk(self) -> None:
        from thegent.sdk import SubAgentRequest

        assert SubAgentRequest is not None

    def test_sub_agent_result_importable_from_sdk(self) -> None:
        from thegent.sdk import SubAgentResult

        assert SubAgentResult is not None

    def test_agent_result_has_output_field(self) -> None:
        from thegent.sdk import AgentResult

        instance = AgentResult(task_id="t1", exit_code=0, stdout="ok", stderr="")
        assert instance.stdout == "ok"

    def test_agent_result_has_exit_code_field(self) -> None:
        from thegent.sdk import AgentResult

        instance = AgentResult(task_id="t1", exit_code=1, stdout="", stderr="err")
        assert instance.exit_code == 1

    def test_run_options_importable_from_sdk(self) -> None:
        from thegent.sdk import RunOptions

        assert RunOptions is not None

    def test_session_state_importable_from_sdk(self) -> None:
        from thegent.sdk import SessionState

        assert SessionState is not None


# ---------------------------------------------------------------------------
# FR-SDK-102: SDK functions
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SDK-102")
class TestSDKFunctions:
    """Verify SDK functions work correctly."""

    def test_list_providers_returns_list(self) -> None:
        from thegent.sdk import list_providers

        result = list_providers()
        assert isinstance(result, list)

    def test_list_providers_returns_strings(self) -> None:
        from thegent.sdk import list_providers

        result = list_providers()
        for item in result:
            assert isinstance(item, str)

    def test_get_version_matches_version_constant(self) -> None:
        from thegent.sdk import VERSION, get_version

        assert get_version() == VERSION

    def test_run_function_importable(self) -> None:
        from thegent.sdk import run

        assert callable(run)
