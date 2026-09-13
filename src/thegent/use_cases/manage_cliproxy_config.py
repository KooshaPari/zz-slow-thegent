"""Provider definitions, login config, and cliproxy config injection.

L1 Architecture: extracted from ``thegent.agents.cliproxy_manager`` (1132L)
into a focused use_case module so the agents shim stays below the file-size
and complexity budgets.

Public surface (re-exported from the legacy shim):
- ``ProviderDefinitionsLoadError`` — typed JSON load error
- ``_load_json``, ``_get_provider_definitions``, ``_get_claude_aliases``
- ``_build_provider_login_config``, ``PROVIDER_LOGIN_CONFIG``
- ``_get_factory_api_key`` — looks up API keys in ``~/.factory/``
- ``_has_provider_credentials``, ``_has_oauth_credentials`` — preflight checks
- ``_inject_api_key_into_cliproxy``, ``_inject_cursor_into_cliproxy``,
  ``_inject_kiro_into_cliproxy`` — config writers
- ``_patch_provider_aliases`` + per-provider helpers + ``_PROVIDER_PATCHERS``
  dispatch table + ``_resolve_claude_aliases`` (WP-Y16 alias compat)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import orjson as json

from thegent.config.settings import ThegentSettings

_LOG = logging.getLogger(__name__)

_CLIPROXY_DATA_DIR = Path(__file__).parent.parent / "agents" / "cliproxy_data"

_KIRO_TOKEN_PATH = Path("~/.kiro/kiro-auth-token.json")


# ---------------------------------------------------------------------------
# Provider definitions JSON (internal data dir)
# ---------------------------------------------------------------------------


class ProviderDefinitionsLoadError(ValueError):
    """Typed validation error for provider definition JSON loading."""

    def __init__(
        self,
        name: str,
        reason: str,
        *,
        path: Path,
        cause: Exception | None = None,
    ) -> None:
        self.name = name
        self.reason = reason
        self.path = path
        self.cause = cause
        message = f"{name}: {reason} ({path})"
        super().__init__(message)


def _load_json(name: str) -> dict[str, Any]:
    """Load and validate JSON object from cliproxy_data."""
    path = _CLIPROXY_DATA_DIR / name
    if not path.exists():
        raise ProviderDefinitionsLoadError(name, "missing_file", path=path)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProviderDefinitionsLoadError(
            name, "invalid_json", path=path, cause=exc
        ) from exc
    except OSError as exc:
        raise ProviderDefinitionsLoadError(
            name, "read_error", path=path, cause=exc
        ) from exc

    if not isinstance(data, dict):
        raise ProviderDefinitionsLoadError(name, "invalid_shape", path=path)
    return data


def _get_provider_definitions() -> dict[str, Any]:
    """Load provider definitions from internal JSON (cached by caller)."""
    try:
        return _load_json("provider_definitions.json")
    except ProviderDefinitionsLoadError as exc:
        _LOG.warning(
            "provider_definitions_load_failed",
            extra={
                "file": exc.name,
                "reason": exc.reason,
                "path": str(exc.path),
                "cause": str(exc.cause) if exc.cause else "",
            },
        )
        return {}


def _get_claude_aliases(model: str) -> list[dict[str, str]]:
    """Standard Claude aliases for a given underlying model."""
    common = [
        "sonnet",
        "haiku",
        "opus",
        "claude-sonnet-4.5",
        "claude-haiku-4.5",
        "claude-opus-4.6",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "composer-1.5",
        "composer-1.5-high",
        "composer-1.5-spark",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ]
    out = [{"name": model, "alias": model}]
    for a in common:
        out.append({"name": model, "alias": a})
    return out


# ---------------------------------------------------------------------------
# Login config build
# ---------------------------------------------------------------------------


def _build_provider_login_config() -> dict[str, dict[str, Any]]:
    """Build ``PROVIDER_LOGIN_CONFIG`` from internal ``provider_definitions.json``."""
    defs_ = _get_provider_definitions()
    out: dict[str, dict[str, Any]] = {}
    for name, cfg in defs_.items():
        if not isinstance(cfg, dict) or "login" not in cfg:
            continue
        login = cfg.get("login", {})
        base_url = cfg.get("base_url", "")
        if cfg.get("base_url_env"):
            base_url = os.environ.get(cfg["base_url_env"], base_url)
        out[name] = {
            "url": login.get("url", ""),
            "base_url": base_url,
            "display_name": login.get("display_name", name),
            "model": cfg.get("model", name),
            "instructions": login.get("instructions", []),
        }
    return out


PROVIDER_LOGIN_CONFIG: dict[str, dict[str, Any]] = _build_provider_login_config()


# ---------------------------------------------------------------------------
# Factory config API-key lookup
# ---------------------------------------------------------------------------


_FACTORY_PROVIDER_PATTERNS: dict[str, tuple[list[str], list[str]]] = {
    "minimax": (["minimax"], ["minimax"]),
    "nim": (["nvidia"], ["nvidia", "nim"]),
    "openrouter": (["openrouter"], ["openrouter"]),
    "zen": (["opencode"], ["opencode", "zen"]),
    "qwen": (["dashscope", "aliyuncs"], ["qwen"]),
    "roo": (["roo.ai"], ["roo"]),
    "kimi": (["moonshot.cn"], ["kimi"]),
}

_DUMMY_KEYS = frozenset({"dummy-not-used", "dummy", ""})


def _matches_factory_entry(
    entry: Any,
    base_patterns: list[str],
    model_patterns: list[str],
    api_key: str,
) -> bool:
    """Return True when ``entry`` is a live provider row matching the patterns."""
    base_url = (entry.get("base_url") or "").lower()
    model = (entry.get("model") or "").lower()
    if not any(p in base_url for p in base_patterns) and not any(
        p in model for p in model_patterns
    ):
        return False
    if entry.get("enabled", True) is False:
        return False
    return entry.get("api_key") or entry.get(api_key)


def _extract_factory_api_key(
    data: Any,
    base_patterns: list[str],
    model_patterns: list[str],
) -> str | None:
    """Scan ``data`` for the first live API key matching the patterns."""
    if not isinstance(data, dict):
        return None
    providers = data.get("providers", data)
    if not isinstance(providers, list):
        return None
    for entry in providers:
        if not isinstance(entry, dict):
            continue
        for api_key in ("api_key", "apiKey", "key"):
            if not _matches_factory_entry(
                entry, base_patterns, model_patterns, api_key
            ):
                continue
            raw = entry.get(api_key)
            if (
                isinstance(raw, str)
                and raw.strip()
                and raw.strip().lower() not in _DUMMY_KEYS
            ):
                return raw.strip()
    return None


def _factory_api_key_at_path(path: Path, provider: str) -> str | None:
    """Return the API key from ``path`` for ``provider`` or ``None``."""
    patterns = _FACTORY_PROVIDER_PATTERNS.get(provider.lower())
    if patterns is None:
        return None
    base_patterns, model_patterns = patterns
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return _extract_factory_api_key(data, base_patterns, model_patterns)


def _get_factory_api_key(provider: str) -> tuple[str | None, str]:
    """Look up API key in ``~/.factory/config.json`` and ``~/.factory/settings.json``."""
    candidates = (
        Path.home() / ".factory" / "config.json",
        Path.home() / ".factory" / "settings.json",
    )
    for path in candidates:
        if not path.exists():
            continue
        api_key = _factory_api_key_at_path(path, provider)
        if api_key:
            return api_key, str(path)
    return None, ""


# ---------------------------------------------------------------------------
# Credential preflight checks
# ---------------------------------------------------------------------------


def _has_provider_credentials(config: dict[str, Any], provider: str) -> bool:
    """Check if provider already has credentials in cliproxy config."""
    compat = config.get("openai-compatibility")
    if not isinstance(compat, list):
        return False
    for entry in compat:
        if not isinstance(entry, dict):
            continue
        if entry.get("name", "").lower() != provider.lower():
            continue
        keys = entry.get("api-key-entries") or entry.get("api-key")
        if keys and isinstance(keys, list) and keys:
            return any(
                (k.get("api-key") or "").strip() for k in keys if isinstance(k, dict)
            )
        if isinstance(keys, str) and keys.strip():
            return True
    return False


_OAUTH_AUTH_PREFIXES: dict[str, list[str]] = {
    "claude": ["claude-"],
    "codex": ["codex-"],
    "gemini": ["gemini-"],
    "antigravity": ["antigravity-"],
    "copilot": ["github-", "copilot-"],
    "kilo": ["kilo-"],
    "glm": ["iflow-"],
    "iflow": ["iflow-"],
    "kiro": ["kiro-"],
    "roo": ["roo-"],
    "qwen": ["qwen-"],
    "kimi": ["kimi-"],
}


def _kiro_token_path() -> Path:
    """Return the expanded ``~/.kiro/kiro-auth-token.json`` path."""
    return _KIRO_TOKEN_PATH.expanduser().resolve()


def _scan_auth_dir_for_oauth(
    auth_dir: Path,
    prefixes: list[str],
    provider_lower: str,
) -> bool:
    """Return True when ``auth_dir`` contains a matching OAuth credential file."""
    for f in auth_dir.iterdir():
        if not f.is_file() or f.suffix != ".json":
            continue
        name = f.name
        for prefix in prefixes:
            if name.startswith(prefix):
                return True
        if provider_lower == "gemini" and "@" in name and name.endswith(".json"):
            return True
    return False


def _has_oauth_credentials(settings: ThegentSettings, provider: str) -> bool:
    """Preflight: check if OAuth provider already has credentials in auth dir."""
    provider_lower = provider.lower()
    prefixes = _OAUTH_AUTH_PREFIXES.get(provider_lower)
    if not prefixes:
        return False
    if provider_lower == "kiro" and _kiro_token_path().exists():
        return True
    auth_dir = settings.cliproxy_auth_dir.expanduser().resolve()
    if not auth_dir.exists():
        return False
    return _scan_auth_dir_for_oauth(auth_dir, prefixes, provider_lower)


# ---------------------------------------------------------------------------
# Config writers (login flow side-effects on cliproxy config)
# ---------------------------------------------------------------------------


OAUTH_ONLY_PROVIDERS = frozenset({"claude", "codex"})


def _build_alias_list(
    provider: str, model: str, defs_: dict[str, Any]
) -> list[dict[str, str]]:
    """Return the canonical alias list for ``provider`` at ``model``."""
    provider_def = defs_.get(provider) if isinstance(defs_.get(provider), dict) else {}
    extra_aliases = provider_def.get(
        "extra_aliases",
        ["glm-5"] if provider in ("glm", "kilo") else [],
    )

    if provider.lower() == "minimax" and "MiniMax" in model:
        models = [
            {"name": "MiniMax-M2.5", "alias": "MiniMax-M2.5"},
            {"name": "MiniMax-M2.5", "alias": "minimax-m2.5"},
        ]
    elif provider.lower() in ("glm", "kilo") and (
        "GLM" in model or "glm" in model.lower()
    ):
        models = [
            {"name": model, "alias": model},
            {"name": model, "alias": model.lower()},
        ]
    else:
        models = [*_get_claude_aliases(model)]
    for alias in extra_aliases:
        models.append({"name": model, "alias": alias})
    return models


def _replace_provider_in_compat(
    compat: list[Any], provider: str
) -> list[dict[str, Any]]:
    """Strip any prior entries for ``provider``; return the surviving dicts."""
    return [
        c
        for c in compat
        if isinstance(c, dict) and c.get("name", "").lower() != provider.lower()
    ]


def _inject_api_key_into_cliproxy(
    config: dict[str, Any],
    provider: str,
    api_key: str,
    cfg: dict[str, Any],
) -> None:
    """Add or update ``openai-compatibility`` entry with the given API key.

    Claude and Codex are OAuth-only; no-op for them.
    """
    if provider.lower() in OAUTH_ONLY_PROVIDERS:
        return
    compat = config.get("openai-compatibility")
    if not isinstance(compat, list):
        compat = []
        config["openai-compatibility"] = compat

    compat[:] = _replace_provider_in_compat(compat, provider)

    base_url = cfg.get("base_url", "").rstrip("/")
    model = cfg.get("model", cfg.get("display_name", provider))
    entries = [{"api-key": api_key}]

    defs_ = _get_provider_definitions()
    models = _build_alias_list(provider, model, defs_)

    compat.append(
        {
            "name": provider,
            "base-url": base_url,
            "api-key-entries": entries,
            "models": models,
        }
    )


def _write_cursor_token(token: str, auth_dir: Path) -> Path | None:
    """Persist ``token`` to ``auth_dir/cursor-session-token.txt`` (mode 600)."""
    try:
        auth_dir.mkdir(parents=True, exist_ok=True)
        token_file = auth_dir / "cursor-session-token.txt"
        token_file.write_text(token, encoding="utf-8")
        token_file.chmod(0o600)
    except OSError:
        return None
    return token_file


def _build_cursor_entry(token: str, settings: ThegentSettings) -> dict[str, Any] | None:
    """Return the cursor config entry, or ``None`` when prerequisites are absent."""
    url = settings.cursor_api_url
    if not url or not token:
        return None
    cursor_api_url = url.rstrip("/") or "http://127.0.0.1:3000"
    entry: dict[str, Any] = {"cursor-api-url": cursor_api_url}
    if token.startswith("sk-"):
        auth_dir = settings.cliproxy_auth_dir.expanduser().resolve()
        token_file = _write_cursor_token(token, auth_dir)
        if token_file is None:
            return None
        entry["token-file"] = str(token_file)
    else:
        entry["auth-token"] = token
    return entry


def _inject_cursor_into_cliproxy(
    config: dict[str, Any], settings: ThegentSettings
) -> None:
    """Inject cursor block when ``THGENT_CURSOR_API_URL`` and token are set."""
    if config.get("cursor"):
        return
    # WL153: cursor_api_token is now SecretStr — use the canonical
    # secret_value() accessor to obtain the raw string for the
    # cli-proxy config injection.
    token = (settings.secret_value("cursor_api_token") or "").strip()
    entry = _build_cursor_entry(token, settings)
    if entry is None:
        return
    config["cursor"] = [entry]


def _inject_kiro_into_cliproxy(
    config: dict[str, Any], settings: ThegentSettings
) -> None:
    """Inject kiro block when ``~/.kiro/kiro-auth-token.json`` exists."""
    if config.get("kiro"):
        return
    token_path = _kiro_token_path()
    if not token_path.exists():
        return
    config["kiro"] = [{"token-file": str(token_path)}]


# ---------------------------------------------------------------------------
# WP-Y16 alias compatibility patchers
# ---------------------------------------------------------------------------


def _patch_minimax_provider(p: dict[str, Any]) -> None:
    """Apply the WP-Y16 minimax→minimax alias compatibility shim."""
    base = (p.get("base-url") or "").strip()
    if "api.minimax.chat" in base:
        p["base-url"] = base.replace("api.minimax.chat", "api.minimax.io")
    models_list = p.get("models", [])
    if not any(m.get("name") == "MiniMax-M2.5" for m in models_list):
        models_list.append({"name": "MiniMax-M2.5", "alias": "MiniMax-M2.5"})
        models_list.append({"name": "MiniMax-M2.5", "alias": "minimax-m2.5"})
        p["models"] = models_list


def _patch_glm_provider(p: dict[str, Any]) -> None:
    """Ensure the GLM-5 alias pair is registered for WP-Y16 compatibility."""
    models_list = p.get("models", [])
    if not any(
        m.get("name") == "GLM-5" or m.get("alias") == "glm-5" for m in models_list
    ):
        models_list.append({"name": "GLM-5", "alias": "GLM-5"})
        models_list.append({"name": "GLM-5", "alias": "glm-5"})
        models_list.append({"name": "GLM-5", "alias": "z-ai/glm-5"})
        p["models"] = models_list


def _patch_kilo_provider(p: dict[str, Any]) -> None:
    """Register the kilo-default alias for WP-Y16 compatibility."""
    models_list = p.get("models", [])
    if not any(m.get("alias") == "kilo-default" for m in models_list):
        model_name = p.get("model") or "kilo-default"
        models_list.append({"name": model_name, "alias": "kilo-default"})
        p["models"] = models_list


def _patch_roo_provider(p: dict[str, Any]) -> None:
    """Register the roo-default alias for WP-Y16 compatibility."""
    models_list = p.get("models", [])
    if not any(m.get("alias") == "roo-default" for m in models_list):
        model_name = p.get("model") or "roo-default"
        models_list.append({"name": model_name, "alias": "roo-default"})
        p["models"] = models_list


_PROVIDER_PATCHERS: dict[str, Callable[[dict[str, Any]], None]] = {
    "minimax": _patch_minimax_provider,
    "glm": _patch_glm_provider,
    "kilo": _patch_kilo_provider,
    "roo": _patch_roo_provider,
}


def _resolve_claude_aliases(p: dict[str, Any], name: str) -> None:
    """Populate ``models`` from ``model`` for Claude-compatible providers."""
    model = p.get("model")
    if not model and p.get("models"):
        model = p["models"][0].get("name")
    if not model:
        return
    if name == "minimax" and "MiniMax" in model and not p.get("models"):
        p["models"] = [
            {"name": "MiniMax-M2.5", "alias": "MiniMax-M2.5"},
            {"name": "MiniMax-M2.5", "alias": "minimax-m2.5"},
        ]
    elif (
        name in ("glm", "kilo")
        and ("GLM" in model or "glm" in model.lower())
        and not p.get("models")
    ):
        p["models"] = [
            {"name": model, "alias": model},
            {"name": model, "alias": model.lower()},
        ]
    elif name not in _PROVIDER_PATCHERS:
        p["models"] = _get_claude_aliases(model)


def _patch_provider_aliases(config: dict[str, Any]) -> None:
    """Ensure WP-Y16 alias compatibility for existing provider entries.

    No-ops when ``openai-compatibility`` is absent or non-list.
    """
    providers = config.get("openai-compatibility")
    if not isinstance(providers, list):
        return

    for p in providers:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").lower()
        patcher = _PROVIDER_PATCHERS.get(name)
        if patcher is not None:
            patcher(p)
        _resolve_claude_aliases(p, name)


# ---------------------------------------------------------------------------
# Config file IO
# ---------------------------------------------------------------------------


def _ensure_config(settings: ThegentSettings) -> Path:
    """Ensure cliproxy config exists; create minimal YAML if missing.

    Default ``auth-dir`` is ``~/.cache/thegent/cliproxy/auth`` (matches the
    runtime module's data-dir layout) so that the proxy and the config
    always agree on where to find oauth tokens.
    """
    auth_dir_default = Path.home() / ".cache" / "thegent" / "cliproxy" / "auth"
    config_path = settings.cliproxy_config_path.expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    auth_dir = (
        (
            settings.cliproxy_auth_dir
            if hasattr(settings, "cliproxy_auth_dir")
            else auth_dir_default
        )
        .expanduser()
        .resolve()
    )
    auth_dir.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        try:
            raw = _yaml_load(config_path)
            config: dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}
        except Exception:
            config = {}
    else:
        config = {}

    config.setdefault("port", settings.cliproxy_port)
    config.setdefault("auth-dir", str(auth_dir))
    _patch_provider_aliases(config)
    _inject_cursor_into_cliproxy(config, settings)
    _inject_kiro_into_cliproxy(config, settings)

    config_path.write_text(_yaml_dumps(config))
    return config_path


# ---------------------------------------------------------------------------
# Lazy YAML helpers (avoid top-level yaml dep to keep this module importable
# in environments where PyYAML is missing — e.g. minimal CI containers).
# ---------------------------------------------------------------------------


def _yaml_load(path: Path) -> Any:
    import yaml  # type: ignore[import-not-found]

    return yaml.safe_load(path.read_text())


def _yaml_dumps(data: Any) -> str:
    import yaml  # type: ignore[import-not-found]

    return yaml.safe_dump(data, sort_keys=False)
