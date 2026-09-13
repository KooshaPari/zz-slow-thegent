"""Infrastructure modules for thegent.

This package contains infrastructure utilities including:
- Runtime dispatcher for multi-runtime support
- Performance optimizations
- Error handling
- Progress indicators
- Configuration management
- Multi-runtime diagnostics

All re-exports are lazy to avoid pulling heavy transitive dependencies
(cachetools, orjson, httpx, …) at package-import time.
"""

from __future__ import annotations

import importlib
from typing import Any

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Cache
    "MultiTierCache": ("thegent.infra.cache_v2", "MultiTierCache"),
    "get_cache": ("thegent.infra.cache_v2", "get_cache"),
    # Enhanced errors
    "ConfigurationError": ("thegent.infra.enhanced_errors", "ConfigurationError"),
    "DependencyError": ("thegent.infra.enhanced_errors", "DependencyError"),
    "EnhancedError": ("thegent.infra.enhanced_errors", "EnhancedError"),
    "InfraRuntimeError": ("thegent.infra.enhanced_errors", "InfraRuntimeError"),
    "NetworkError": ("thegent.infra.enhanced_errors", "NetworkError"),
    "create_config_error": ("thegent.infra.enhanced_errors", "create_config_error"),
    "create_dependency_error": (
        "thegent.infra.enhanced_errors",
        "create_dependency_error",
    ),
    "create_network_error": ("thegent.infra.enhanced_errors", "create_network_error"),
    "create_runtime_error": ("thegent.infra.enhanced_errors", "create_runtime_error"),
    "error_report": ("thegent.infra.enhanced_errors", "error_report"),
    "format_error": ("thegent.infra.enhanced_errors", "format_error"),
    "format_error_with_context": (
        "thegent.infra.enhanced_errors",
        "format_error_with_context",
    ),
    # File operations
    "copy_file": ("thegent.infra.fast_file_ops", "copy_file"),
    "copy_tree": ("thegent.infra.fast_file_ops", "copy_tree"),
    # Subprocess
    "run_subprocess_optimized": (
        "thegent.infra.fast_subprocess",
        "run_subprocess_optimized",
    ),
    # YAML
    "yaml_dump": ("thegent.infra.fast_yaml_parser", "yaml_dump"),
    "yaml_load": ("thegent.infra.fast_yaml_parser", "yaml_load"),
    "yaml_loads": ("thegent.infra.fast_yaml_parser", "yaml_loads"),
    # Mojo bridge
    "MojoBridge": ("thegent.infra.mojo_bridge", "MojoBridge"),
    "MojoNotAvailableError": ("thegent.infra.mojo_bridge", "MojoNotAvailableError"),
    "MojoTask": ("thegent.infra.mojo_bridge", "MojoTask"),
    "check_mojo_status": ("thegent.infra.mojo_bridge", "check_mojo_status"),
    "get_bridge": ("thegent.infra.mojo_bridge", "get_bridge"),
    # Progress indicators
    "measure_time": ("thegent.infra.progress", "measure_time"),
    "print_section": ("thegent.infra.progress", "print_section"),
    "print_status": ("thegent.infra.progress", "print_status"),
    "print_step": ("thegent.infra.progress", "print_step"),
    "progress_context": ("thegent.infra.progress", "progress_context"),
    "spinner_context": ("thegent.infra.progress", "spinner_context"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    "ConfigurationError",
    "DependencyError",
    "EnhancedError",
    "InfraRuntimeError",
    "MojoBridge",
    "MojoNotAvailableError",
    "MojoTask",
    "MultiTierCache",
    "NetworkError",
    "check_mojo_status",
    "copy_file",
    "copy_tree",
    "create_config_error",
    "create_dependency_error",
    "create_network_error",
    "create_runtime_error",
    "error_report",
    "format_error",
    "format_error_with_context",
    "get_bridge",
    "get_cache",
    "measure_time",
    "print_section",
    "print_status",
    "print_step",
    "progress_context",
    "run_subprocess_optimized",
    "spinner_context",
    "yaml_dump",
    "yaml_load",
    "yaml_loads",
]
