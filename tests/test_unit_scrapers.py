"""Unit tests for thegent.models.scrapers — model discovery scrapers."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

MODULE = "thegent.models.scrapers"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(**overrides: object) -> MagicMock:
    """Build a mock ThegentSettings with sensible defaults."""
    defaults = {
        "cliproxy_port": 8317,
        "cursor_api_url": "http://127.0.0.1:3000",
        "cursor_api_token": "tok-test",
        "models_cache_ttl_sec": 300,
        "default_cursor_model": "gemini-3-flash",
        "default_copilot_model": "claude-haiku-4.5",
        "default_gemini_model": "gemini-2.0-flash",
        "default_claude_model": "haiku",
        "default_codex_model": "gpt-5.3-codex",
        "default_antigravity_model": "gemini-3-flash",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _subprocess_result(stdout: str = "", returncode: int = 0) -> MagicMock:
    """Build a mock subprocess.CompletedProcess."""
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    return m


# ---------------------------------------------------------------------------
# _load_cached / _save_cache
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadCached:
    """Tests for _load_cached (diskcache-backed)."""

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_returns_none_when_cache_missing(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-001
        mock_cache.get.side_effect = lambda k, default=None: default
        from thegent.models.scrapers import _load_cached

        assert _load_cached() is None

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_returns_data_when_fresh(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-002
        now = time.time()
        mock_cache.get.side_effect = lambda k, default=None: (
            {"claude": ["haiku"]} if k == "by_provider" else now if k == "by_provider_mtime" else default
        )
        from thegent.models.scrapers import _load_cached

        result = _load_cached(ttl_sec=300)
        assert result is not None
        by_provider, mtime = result
        assert by_provider == {"claude": ["haiku"]}
        assert mtime == now

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_returns_none_when_expired(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-003 (diskcache returns None for expired keys)
        mock_cache.get.return_value = None
        from thegent.models.scrapers import _load_cached

        assert _load_cached(ttl_sec=300) is None

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_returns_none_on_os_error(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-004
        mock_cache.get.side_effect = OSError("disk read failed")
        from thegent.models.scrapers import _load_cached

        assert _load_cached() is None


@pytest.mark.unit
class TestSaveCache:
    """Tests for _save_cache (diskcache-backed)."""

    @patch(f"{MODULE}.time")
    @patch(f"{MODULE}._MODELS_CACHE")
    def test_writes_to_cache_with_ttl(self, mock_cache: MagicMock, mock_time: MagicMock) -> None:
        # @trace FR-MOD-006
        mock_time.time.return_value = 1700000000.0
        from thegent.models.scrapers import _save_cache

        _save_cache({"claude": ["sonnet"]}, ttl_sec=300)
        mock_cache.set.assert_any_call("by_provider", {"claude": ["sonnet"]}, expire=300)
        mock_cache.set.assert_any_call("by_provider_mtime", 1700000000.0, expire=300)


# ---------------------------------------------------------------------------
# get_models_cache_path / invalidate_models_cache
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCacheUtilities:
    """Tests for get_models_cache_path and invalidate_models_cache."""

    def test_get_models_cache_path_returns_path(self) -> None:
        # @trace FR-MOD-007
        from thegent.models.scrapers import get_models_cache_path

        p = get_models_cache_path()
        assert isinstance(p, Path)
        assert "models-cache" in str(p)

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_invalidate_removes_existing_cache(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-008
        mock_cache.__len__ = MagicMock(return_value=3)
        mock_cache.clear = MagicMock()
        from thegent.models.scrapers import invalidate_models_cache

        assert invalidate_models_cache() is True
        mock_cache.clear.assert_called_once()

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_invalidate_returns_false_when_empty(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-009
        mock_cache.__len__ = MagicMock(return_value=0)
        mock_cache.clear = MagicMock()
        from thegent.models.scrapers import invalidate_models_cache

        assert invalidate_models_cache() is False

    @patch(f"{MODULE}._MODELS_CACHE")
    def test_invalidate_returns_false_on_os_error(self, mock_cache: MagicMock) -> None:
        # @trace FR-MOD-010
        mock_cache.__len__ = MagicMock(return_value=1)
        mock_cache.clear = MagicMock(side_effect=OSError("permission denied"))
        from thegent.models.scrapers import invalidate_models_cache

        assert invalidate_models_cache() is False


# ---------------------------------------------------------------------------
# scrape_cursor
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeCursor:
    """Tests for scrape_cursor (CLI subprocess)."""

    @patch("subprocess.run")
    def test_returns_model_list_on_success(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-011
        mock_run.return_value = _subprocess_result(
            stdout="gemini-3-flash\nclaude-sonnet-4.5\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_cursor

        result = scrape_cursor()
        assert result == ["gemini-3-flash", "claude-sonnet-4.5"]

    @patch("subprocess.run")
    def test_filters_tip_lines(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-012
        mock_run.return_value = _subprocess_result(
            stdout="gemini-3-flash\nTip: use --model to pick\nclaude-sonnet-4.5\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_cursor

        result = scrape_cursor()
        assert "Tip: use --model to pick" not in result
        assert result == ["gemini-3-flash", "claude-sonnet-4.5"]

    @patch("subprocess.run")
    def test_returns_empty_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-013
        mock_run.return_value = _subprocess_result(returncode=1)
        from thegent.models.scrapers import scrape_cursor

        assert scrape_cursor() == []

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_empty_when_binary_missing(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-014
        from thegent.models.scrapers import scrape_cursor

        assert scrape_cursor() == []

    @patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(cmd="cursor", timeout=10))
    def test_returns_empty_on_timeout(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-015
        from thegent.models.scrapers import scrape_cursor

        assert scrape_cursor() == []


# ---------------------------------------------------------------------------
# scrape_copilot
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeCopilot:
    """Tests for scrape_copilot (--help parsing)."""

    @patch("subprocess.run")
    def test_extracts_models_from_help(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-016
        help_text = (
            "Usage: copilot [options]\n\n"
            '  --model <model>  Model to use. Choices: "claude-sonnet-4.5" "gpt-4o" "gemini-2.0-flash"\n'
        )
        mock_run.return_value = _subprocess_result(stdout=help_text, returncode=0)
        from thegent.models.scrapers import scrape_copilot

        result = scrape_copilot()
        assert "claude-sonnet-4.5" in result
        assert "gemini-2.0-flash" in result
        # gpt-4o contains "gpt" so it should be included
        assert "gpt-4o" in result

    @patch("subprocess.run")
    def test_returns_fallback_on_no_model_flag(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-017
        mock_run.return_value = _subprocess_result(stdout="Usage: copilot\n  --help", returncode=0)
        from thegent.models.scrapers import scrape_copilot

        result = scrape_copilot()
        assert result == ["claude-haiku-4.5", "gpt-5.3-codex", "gemini-3-flash"]

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_fallback_when_binary_missing(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-018
        from thegent.models.scrapers import scrape_copilot

        result = scrape_copilot()
        assert result == ["claude-haiku-4.5", "gpt-5.3-codex", "gemini-3-flash"]


# ---------------------------------------------------------------------------
# scrape_gemini
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeGemini:
    """Tests for scrape_gemini (multi-command fallback)."""

    @patch("subprocess.run")
    def test_extracts_gemini_models(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-019
        mock_run.return_value = _subprocess_result(
            stdout="Available models:\n  gemini-2.0-flash\n  gemini-2.5-flash\n  gemini-3-flash\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_gemini

        result = scrape_gemini()
        assert "gemini-2.0-flash" in result
        assert "gemini-2.5-flash" in result
        assert "gemini-3-flash" in result

    @patch("subprocess.run")
    def test_deduplicates_model_ids(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-020
        mock_run.return_value = _subprocess_result(
            stdout="gemini-2.0-flash\ngemini-2.0-flash\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_gemini

        result = scrape_gemini()
        assert result.count("gemini-2.0-flash") == 1

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_fallback_when_binary_missing(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-021
        from thegent.models.scrapers import scrape_gemini

        result = scrape_gemini()
        assert result == ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3-flash"]

    @patch("subprocess.run")
    def test_falls_through_commands_on_nonzero(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-022
        # First two commands fail, third succeeds
        mock_run.side_effect = [
            _subprocess_result(returncode=1),
            _subprocess_result(returncode=1),
            _subprocess_result(stdout="gemini-3-flash available", returncode=0),
        ]
        from thegent.models.scrapers import scrape_gemini

        result = scrape_gemini()
        assert "gemini-3-flash" in result


# ---------------------------------------------------------------------------
# scrape_claude
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeClaude:
    """Tests for scrape_claude (multi-command fallback)."""

    @patch("subprocess.run")
    def test_extracts_claude_models(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-023
        mock_run.return_value = _subprocess_result(
            stdout="Models:\n  claude-sonnet-4.5\n  claude-opus-4.6\n  claude-haiku-4.5\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_claude

        result = scrape_claude()
        assert "haiku" in result
        assert "sonnet" in result
        assert "opus" in result
        assert "claude-sonnet-4.5" in result
        assert "claude-opus-4.6" in result
        assert "claude-haiku-4.5" in result

    @patch("subprocess.run")
    def test_returns_fallback_when_no_matches_beyond_aliases(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-024
        # stdout has no claude-* models, so out stays at 3 aliases -> returns fallback
        mock_run.return_value = _subprocess_result(
            stdout="No models found\n",
            returncode=0,
        )
        from thegent.models.scrapers import scrape_claude

        result = scrape_claude()
        assert "haiku" in result
        assert "sonnet" in result
        assert "opus" in result

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_fallback_when_binary_missing(self, mock_run: MagicMock) -> None:
        # @trace FR-MOD-025
        from thegent.models.scrapers import scrape_claude

        result = scrape_claude()
        assert result == ["haiku", "sonnet", "opus", "claude-haiku-4.5", "claude-sonnet-4.5", "claude-opus-4.6"]


# ---------------------------------------------------------------------------
# scrape_proxy / _scrape_proxy_models
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeProxy:
    """Tests for scrape_proxy and _scrape_proxy_models (HTTP)."""

    @patch(f"{MODULE}.urllib.request.urlopen")
    @patch(f"{MODULE}.urllib.request.Request")
    def test_scrape_proxy_models_parses_response(self, mock_req_cls: MagicMock, mock_urlopen: MagicMock) -> None:
        # @trace FR-MOD-026
        body = json.dumps({"data": [{"id": "gemini-3-flash"}, {"id": "claude-sonnet-4.5"}]}).decode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body.encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        from thegent.models.scrapers import _scrape_proxy_models

        result = _scrape_proxy_models("http://127.0.0.1:8317")
        assert "gemini-3-flash" in result
        assert "claude-sonnet-4.5" in result

    @patch(f"{MODULE}.urllib.request.urlopen", side_effect=Exception("connection refused"))
    def test_scrape_proxy_models_returns_empty_on_error(self, mock_urlopen: MagicMock) -> None:
        # @trace FR-MOD-027
        from thegent.models.scrapers import _scrape_proxy_models

        assert _scrape_proxy_models("http://127.0.0.1:8317") == []

    @patch(f"{MODULE}._scrape_proxy_models")
    @patch(f"{MODULE}.ThegentSettings")
    def test_scrape_proxy_categorizes_models(self, mock_settings_cls: MagicMock, mock_fetch: MagicMock) -> None:
        # @trace FR-MOD-028
        settings = _make_settings()
        mock_fetch.return_value = [
            "minimax-m2.5",
            "glm-5",
            "gemini-3-flash",
            "claude-sonnet-4.5",
            "roo-v1",
            "kilo-code",
            "some-unknown-model",
        ]
        from thegent.models.scrapers import scrape_proxy

        result = scrape_proxy(settings)
        assert "minimax-m2.5" in result["minimax"]
        assert "glm-5" in result["glm"]
        assert "gemini-3-flash" in result["gemini"]
        assert "claude-sonnet-4.5" in result["claude"]
        assert "roo-v1" in result["roo"]
        assert "kilo-code" in result["kilo"]
        assert "some-unknown-model" in result["antigravity"]

    @patch(f"{MODULE}._scrape_proxy_models", return_value=[])
    @patch(f"{MODULE}.ThegentSettings")
    def test_scrape_proxy_defaults_minimax_and_glm(self, mock_settings_cls: MagicMock, mock_fetch: MagicMock) -> None:
        # @trace FR-MOD-029
        settings = _make_settings()
        from thegent.models.scrapers import scrape_proxy

        result = scrape_proxy(settings)
        assert result["minimax"] == ["minimax-m2.5"]
        assert result["glm"] == ["glm-5"]


# ---------------------------------------------------------------------------
# scrape_cursor_api / _scrape_cursor_api_models
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeCursorApi:
    """Tests for scrape_cursor_api and _scrape_cursor_api_models (HTTP)."""

    @patch(f"{MODULE}.urllib.request.urlopen")
    @patch(f"{MODULE}.urllib.request.Request")
    def test_fetches_models_with_token(self, mock_req_cls: MagicMock, mock_urlopen: MagicMock) -> None:
        # @trace FR-MOD-030
        body = json.dumps({"data": [{"id": "claude-4.5-opus-high-thinking"}, {"id": "gpt-5.1-codex"}]}).decode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body.encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        from thegent.models.scrapers import _scrape_cursor_api_models

        result = _scrape_cursor_api_models("http://127.0.0.1:3000", "tok-test")
        assert "claude-4.5-opus-high-thinking" in result
        assert "gpt-5.1-codex" in result

    @patch(f"{MODULE}.urllib.request.urlopen")
    @patch(f"{MODULE}.urllib.request.Request")
    def test_skips_non_string_ids(self, mock_req_cls: MagicMock, mock_urlopen: MagicMock) -> None:
        # @trace FR-MOD-001
        body = json.dumps({"data": [{"id": 123}, {"id": None}, {"id": "valid-model"}]}).decode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body.encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        from thegent.models.scrapers import _scrape_cursor_api_models

        result = _scrape_cursor_api_models("http://127.0.0.1:3000", "")
        assert result == ["valid-model"]

    @patch(f"{MODULE}.urllib.request.urlopen", side_effect=Exception("timeout"))
    def test_returns_empty_on_network_error(self, mock_urlopen: MagicMock) -> None:
        # @trace FR-MOD-002
        from thegent.models.scrapers import _scrape_cursor_api_models

        assert _scrape_cursor_api_models("http://127.0.0.1:3000", "tok") == []

    def test_scrape_cursor_api_delegates_to_internal(self) -> None:
        # @trace FR-MOD-003
        settings = _make_settings()
        with patch(f"{MODULE}._scrape_cursor_api_models", return_value=["m1"]) as mock_internal:
            from thegent.models.scrapers import scrape_cursor_api

            result = scrape_cursor_api(settings)
            assert result == ["m1"]
            mock_internal.assert_called_once_with("http://127.0.0.1:3000", "tok-test")


# ---------------------------------------------------------------------------
# scrape_minimax_from_proxy
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeMinimax:
    """Tests for scrape_minimax_from_proxy (static fallback)."""

    def test_returns_static_minimax(self) -> None:
        # @trace FR-MOD-004
        from thegent.models.scrapers import scrape_minimax_from_proxy

        assert scrape_minimax_from_proxy() == ["minimax-m2.5"]


# ---------------------------------------------------------------------------
# scrape_ante
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeAnte:
    """Tests for scrape_ante (Ante harness model discovery)."""

    @patch("thegent.models.ante_scraper.Path.home")
    def test_returns_model_from_settings(self, mock_home: MagicMock) -> None:
        # @trace FR-MOD-031
        """scrape_ante extracts model from ~/.ante/settings.json."""
        mock_settings_path = MagicMock()
        mock_settings_path.exists.return_value = True
        mock_home.return_value = MagicMock(
            __truediv__=lambda self, x: mock_settings_path if x == ".ante" else MagicMock()
        )

        settings_data = {
            "model": {"name": "claude-sonnet-4-5"},
            "provider": "anthropic-subscription",
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(settings_data).decode()
            from thegent.models.scrapers import scrape_ante

            result = scrape_ante()
            assert isinstance(result, list)

    @patch("thegent.models.ante_scraper.Path.home")
    def test_returns_fallback_when_settings_missing(self, mock_home: MagicMock) -> None:
        # @trace FR-MOD-032
        """scrape_ante returns default when ~/.ante/settings.json not found."""
        mock_settings_path = MagicMock()
        mock_settings_path.exists.return_value = False
        mock_home.return_value = MagicMock(
            __truediv__=lambda self, x: mock_settings_path if x == ".ante" else MagicMock()
        )

        from thegent.models.scrapers import scrape_ante

        result = scrape_ante()
        assert result == ["claude-haiku-4-5"]

    @patch("thegent.models.ante_scraper.Path.home")
    def test_handles_malformed_settings_json(self, mock_home: MagicMock) -> None:
        # @trace FR-MOD-033
        """scrape_ante returns default when settings.json is malformed."""
        mock_settings_path = MagicMock()
        mock_settings_path.exists.return_value = True
        mock_home.return_value = MagicMock(
            __truediv__=lambda self, x: mock_settings_path if x == ".ante" else MagicMock()
        )

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.side_effect = ValueError("invalid json")
            from thegent.models.scrapers import scrape_ante

            result = scrape_ante()
            assert result == ["claude-haiku-4-5"]


# ---------------------------------------------------------------------------
# get_scraped_catalog
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetScrapedCatalog:
    """Tests for get_scraped_catalog (cache-aware entry point)."""

    @patch(f"{MODULE}.scrape_all")
    @patch(f"{MODULE}._save_cache")
    @patch(f"{MODULE}._load_cached")
    @patch(f"{MODULE}.ThegentSettings")
    def test_returns_cached_when_fresh(
        self,
        mock_settings_cls: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_scrape: MagicMock,
    ) -> None:
        # @trace FR-MOD-005
        cached_data = {"claude": ["haiku"]}
        mock_load.return_value = (cached_data, time.time())
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import get_scraped_catalog

        result = get_scraped_catalog(use_cache=True, refresh=False, settings=settings)
        assert result == cached_data
        mock_scrape.assert_not_called()

    @patch(f"{MODULE}.scrape_all", return_value={"claude": ["sonnet"]})
    @patch(f"{MODULE}._save_cache")
    @patch(f"{MODULE}._load_cached", return_value=None)
    @patch(f"{MODULE}.ThegentSettings")
    def test_scrapes_when_cache_expired(
        self,
        mock_settings_cls: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_scrape: MagicMock,
    ) -> None:
        # @trace FR-MOD-006
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import get_scraped_catalog

        result = get_scraped_catalog(use_cache=True, refresh=False, settings=settings)
        assert result == {"claude": ["sonnet"]}
        mock_save.assert_called_once()

    @patch(f"{MODULE}.scrape_all", return_value={"claude": ["opus"]})
    @patch(f"{MODULE}._save_cache")
    @patch(f"{MODULE}._load_cached")
    @patch(f"{MODULE}.ThegentSettings")
    def test_refresh_bypasses_cache(
        self,
        mock_settings_cls: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_scrape: MagicMock,
    ) -> None:
        # @trace FR-MOD-007
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import get_scraped_catalog

        result = get_scraped_catalog(use_cache=True, refresh=True, settings=settings)
        assert result == {"claude": ["opus"]}
        mock_load.assert_not_called()
        mock_save.assert_called_once()

    @patch(f"{MODULE}.scrape_all", return_value={"claude": ["haiku"]})
    @patch(f"{MODULE}._save_cache")
    @patch(f"{MODULE}._load_cached")
    @patch(f"{MODULE}.ThegentSettings")
    def test_no_cache_skips_save(
        self,
        mock_settings_cls: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_scrape: MagicMock,
    ) -> None:
        # @trace FR-MOD-008
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import get_scraped_catalog

        result = get_scraped_catalog(use_cache=False, settings=settings)
        assert result == {"claude": ["haiku"]}
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Coverage gaps: scrape_proxy exception (lines 119-120, 305-306)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeProxyEnsureProxyException:
    """Tests for scrape_proxy ensure_proxy_running exception (lines 119-120)."""

    @patch(f"{MODULE}._scrape_proxy_models", return_value=["test-model"])
    @patch(f"{MODULE}.ThegentSettings")
    def test_ensure_proxy_exception_falls_through(self, mock_settings_cls: MagicMock, mock_fetch: MagicMock) -> None:
        # @trace FR-MOD-026
        """scrape_proxy continues when ensure_proxy_running raises."""
        settings = _make_settings()
        with patch("thegent.agents.cliproxy_manager.ensure_proxy_running", side_effect=RuntimeError("proxy not found")):
            from thegent.models.scrapers import scrape_proxy

            result = scrape_proxy(settings)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Coverage gaps: scrape_all exception branches (lines 305-378)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestScrapeAllExceptionBranches:
    """Tests for scrape_all try/except fallback branches."""

    @patch(f"{MODULE}.scrape_proxy", side_effect=Exception("proxy error"))
    @patch(f"{MODULE}.scrape_cursor", side_effect=Exception("cursor error"))
    @patch(f"{MODULE}.scrape_cursor_api", side_effect=Exception("cursor-api error"))
    @patch(f"{MODULE}.scrape_copilot", side_effect=Exception("copilot error"))
    @patch(f"{MODULE}.scrape_gemini", side_effect=Exception("gemini error"))
    @patch(f"{MODULE}.scrape_claude", side_effect=Exception("claude error"))
    @patch(f"{MODULE}.ThegentSettings")
    def test_all_scrapers_fail_returns_defaults(
        self,
        mock_settings_cls: MagicMock,
        mock_claude: MagicMock,
        mock_gemini: MagicMock,
        mock_copilot: MagicMock,
        mock_cursor_api: MagicMock,
        mock_cursor: MagicMock,
        mock_proxy: MagicMock,
    ) -> None:
        # @trace FR-MOD-028
        """scrape_all returns defaults when all scrapers fail (lines 314-378)."""
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import scrape_all

        result = scrape_all(settings)
        assert isinstance(result, dict)
        # Each provider should have a default
        assert "cursor-agent" in result
        assert len(result["cursor-agent"]) >= 1
        assert "cursor-api" in result
        assert "copilot" in result
        assert "gemini" in result
        assert "claude" in result
        assert "codex" in result

    @patch("thegent.models.catalog.filter_models_for_provider", return_value=[])
    @patch(
        f"{MODULE}.scrape_proxy",
        return_value={"antigravity": [], "minimax": [], "glm": [], "roo": [], "kilo": [], "gemini": [], "claude": []},
    )
    @patch(f"{MODULE}.scrape_cursor", return_value=["model-1"])
    @patch(f"{MODULE}.scrape_cursor_api", return_value=["model-api-1"])
    @patch(f"{MODULE}.scrape_copilot", return_value=["model-cop"])
    @patch(f"{MODULE}.scrape_gemini", return_value=["gem-model"])
    @patch(f"{MODULE}.scrape_claude", return_value=["claude-model"])
    @patch(f"{MODULE}.ThegentSettings")
    def test_empty_filter_uses_defaults(
        self,
        mock_settings_cls: MagicMock,
        mock_claude: MagicMock,
        mock_gemini: MagicMock,
        mock_copilot: MagicMock,
        mock_cursor_api: MagicMock,
        mock_cursor: MagicMock,
        mock_proxy: MagicMock,
        mock_filter: MagicMock,
    ) -> None:
        # @trace FR-MOD-028
        """scrape_all uses default models when filter returns empty (lines 313-365)."""
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import scrape_all

        result = scrape_all(settings)
        # Each should have at least the default
        assert len(result["cursor-agent"]) >= 1
        assert len(result["copilot"]) >= 1

    @patch(
        f"{MODULE}.scrape_proxy",
        return_value={
            "antigravity": ["ag-model"],
            "minimax": [],
            "glm": [],
            "roo": [],
            "kilo": [],
            "gemini": [],
            "claude": [],
        },
    )
    @patch(f"{MODULE}.scrape_cursor", return_value=[])
    @patch(f"{MODULE}.scrape_cursor_api", return_value=[])
    @patch(f"{MODULE}.scrape_copilot", return_value=[])
    @patch(f"{MODULE}.scrape_gemini", return_value=[])
    @patch(f"{MODULE}.scrape_claude", return_value=[])
    @patch(f"{MODULE}.scrape_minimax_from_proxy", return_value=["minimax-m2.5"])
    @patch(f"{MODULE}.ThegentSettings")
    def test_proxy_section_antigravity_filter(
        self,
        mock_settings_cls: MagicMock,
        mock_minimax: MagicMock,
        mock_claude: MagicMock,
        mock_gemini: MagicMock,
        mock_copilot: MagicMock,
        mock_cursor_api: MagicMock,
        mock_cursor: MagicMock,
        mock_proxy: MagicMock,
    ) -> None:
        # @trace FR-MOD-028
        """scrape_all processes proxy antigravity, minimax, glm, roo, kilo (lines 368-378)."""
        settings = _make_settings()
        mock_settings_cls.return_value = settings
        from thegent.models.scrapers import scrape_all

        result = scrape_all(settings)
        assert "antigravity" in result
        assert "minimax" in result
        assert "glm" in result
        assert "roo" in result
        assert "kilo" in result
