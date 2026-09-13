"""Tests for GW-59: Traffic mirroring.

# @trace FR-AROUTE-059
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.mirror import MirrorConfig, MirrorResult, should_mirror


@pytest.mark.requirement("FR-AROUTE-059")
class TestShouldMirror:
    def test_should_mirror_enabled(self) -> None:
        config = MirrorConfig(enabled=True, target_url="http://secondary:8080", sample_rate=1.0)
        # With sample_rate=1.0, random.random() < 1.0 is always True
        assert should_mirror(config) is True

    def test_should_mirror_disabled(self) -> None:
        config = MirrorConfig(enabled=False, target_url="http://secondary:8080", sample_rate=1.0)
        assert should_mirror(config) is False

    def test_should_mirror_empty_url(self) -> None:
        config = MirrorConfig(enabled=True, target_url="", sample_rate=1.0)
        assert should_mirror(config) is False

    def test_should_mirror_sample_rate_zero(self) -> None:
        config = MirrorConfig(enabled=True, target_url="http://secondary:8080", sample_rate=0.0)
        # random.random() >= 0.0 is always True, so 0.0 never mirrors
        assert should_mirror(config) is False

    def test_should_mirror_sample_rate_partial(self) -> None:
        config = MirrorConfig(enabled=True, target_url="http://secondary:8080", sample_rate=0.5)
        # Deterministic via monkeypatching not needed here — just verify it returns bool
        result = should_mirror(config)
        assert isinstance(result, bool)

    def test_should_not_mirror_when_disabled_and_empty_url(self) -> None:
        config = MirrorConfig(enabled=False, target_url="", sample_rate=1.0)
        assert should_mirror(config) is False


@pytest.mark.requirement("FR-AROUTE-059")
class TestMirrorResult:
    def test_mirror_result_fields_mirrored(self) -> None:
        result = MirrorResult(mirrored=True)
        assert result.mirrored is True
        assert result.error == ""

    def test_mirror_result_fields_failed(self) -> None:
        result = MirrorResult(mirrored=False, error="connection refused")
        assert result.mirrored is False
        assert result.error == "connection refused"

    def test_mirror_result_default_error_empty(self) -> None:
        result = MirrorResult(mirrored=True)
        assert result.error == ""


@pytest.mark.requirement("FR-AROUTE-059")
class TestMirrorConfig:
    def test_mirror_config_defaults(self) -> None:
        config = MirrorConfig()
        assert config.enabled is False
        assert config.target_url == ""
        assert config.sample_rate == 1.0
        assert config.timeout_sec == 5.0

    def test_mirror_config_custom(self) -> None:
        config = MirrorConfig(
            enabled=True,
            target_url="http://shadow:9000",
            sample_rate=0.1,
            timeout_sec=2.5,
        )
        assert config.enabled is True
        assert config.target_url == "http://shadow:9000"
        assert config.sample_rate == 0.1
        assert config.timeout_sec == 2.5
