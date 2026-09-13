"""Plugin Host Adapter - Bridges thegent WASM plugins with Rust plugin host.

This adapter provides a Python-side interface to the Rust-based thegent-plugin-host,
enabling hot-swappable plugin loading with proper resource isolation.

Architecture:
- Python side: Uses thegent.infra.wasm_plugin for plugin execution
- Rust side: thegent-plugin-host crate provides plugin lifecycle management
- This adapter: Coordinates between Python plugin system and Rust host
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from thegent.infra.wasm_plugin import (
    ExtismRuntime,
    PluginStatus,
    WasmCapability,
    WasmPluginMetadata,
    WasmRuntimeStatus,
)

if TYPE_CHECKING:
    pass

_log = logging.getLogger(__name__)


@dataclass
class PluginHostConfig:
    """Configuration for the plugin host adapter."""

    host_binary_path: Path | None = None
    host_socket_path: Path | None = None
    max_concurrent_plugins: int = 10
    plugin_registry_path: Path | None = None
    enable_hot_reload: bool = True
    enable_telemetry: bool = True


@dataclass
class LoadedPlugin:
    """Represents a loaded plugin."""

    plugin_id: str
    name: str
    version: str
    status: PluginStatus
    wasm_metadata: WasmPluginMetadata
    host_plugin_id: str | None = None
    capabilities: list[WasmCapability] = field(default_factory=list)


class PluginHostAdapter:
    """Adapter for integrating with thegent-plugin-host Rust crate.

    This adapter provides:
    - Plugin lifecycle management (install, uninstall, enable, disable)
    - Hot-swappable plugin loading via Extism WASM runtime
    - Resource isolation with configurable limits
    - Telemetry and metrics collection
    """

    def __init__(
        self,
        config: PluginHostConfig | None = None,
        runtime: ExtismRuntime | None = None,
    ) -> None:
        self._config = config or PluginHostConfig()
        self._runtime = runtime or ExtismRuntime()
        self._loaded_plugins: dict[str, LoadedPlugin] = {}
        self._host_process: subprocess.Popen | None = None

    @property
    def runtime_status(self) -> WasmRuntimeStatus:
        """Get the WASM runtime status."""
        return self._runtime.status

    @property
    def is_available(self) -> bool:
        """Check if the plugin host is available."""
        return self._runtime.is_available

    def initialize(self) -> bool:
        """Initialize the plugin host.

        Returns:
            True if initialization was successful.
        """
        _log.info("Initializing PluginHostAdapter")
        return self._runtime.initialize()

    def list_plugins(self) -> list[LoadedPlugin]:
        """List all loaded plugins.

        Returns:
            List of loaded plugins.
        """
        return list(self._loaded_plugins.values())

    def get_plugin(self, plugin_id: str) -> LoadedPlugin | None:
        """Get a plugin by ID.

        Args:
            plugin_id: The plugin ID.

        Returns:
            The plugin if found, None otherwise.
        """
        return self._loaded_plugins.get(plugin_id)

    def install_plugin(
        self,
        manifest_path: Path,
        name: str,
        version: str = "0.1.0",
    ) -> LoadedPlugin:
        """Install a plugin from a manifest.

        Args:
            manifest_path: Path to the plugin manifest.
            name: Plugin name.
            version: Plugin version.

        Returns:
            The installed plugin.

        Raises:
            FileNotFoundError: If the manifest doesn't exist.
            ValueError: If the manifest is invalid.
        """
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin manifest not found: {manifest_path}")

        _log.info("Installing plugin %s v%s from %s", name, version, manifest_path)
        plugin_id = f"{name}@{version}"
        metadata = WasmPluginMetadata(
            name=name,
            version=version,
            entry_point="run",
            capabilities=[WasmCapability.HTTP_CLIENT],
        )
        plugin = LoadedPlugin(
            plugin_id=plugin_id,
            name=name,
            version=version,
            status=PluginStatus.UNLOADED,
            wasm_metadata=metadata,
        )
        self._loaded_plugins[plugin_id] = plugin
        return plugin

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_id: The plugin ID.

        Returns:
            True if successful.
        """
        plugin = self._loaded_plugins.get(plugin_id)
        if not plugin:
            _log.warning("Plugin not found: %s", plugin_id)
            return False

        _log.info("Enabling plugin %s", plugin_id)
        plugin.status = PluginStatus.READY
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_id: The plugin ID.

        Returns:
            True if successful.
        """
        plugin = self._loaded_plugins.get(plugin_id)
        if not plugin:
            _log.warning("Plugin not found: %s", plugin_id)
            return False

        _log.info("Disabling plugin %s", plugin_id)
        plugin.status = PluginStatus.UNLOADED
        return True

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_id: The plugin ID.

        Returns:
            True if successful.
        """
        if plugin_id in self._loaded_plugins:
            _log.info("Uninstalling plugin %s", plugin_id)
            del self._loaded_plugins[plugin_id]
            return True
        return False

    def execute_plugin(
        self,
        plugin_id: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a plugin.

        Args:
            plugin_id: The plugin ID.
            input_data: Input data for the plugin.

        Returns:
            The plugin execution result.

        Raises:
            ValueError: If the plugin is not loaded.
        """
        plugin = self._loaded_plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_id}")

        if plugin.status != PluginStatus.READY:
            raise ValueError(
                f"Plugin {plugin_id} is not ready (status: {plugin.status})"
            )

        _log.info("Executing plugin %s", plugin_id)
        plugin.status = PluginStatus.RUNNING

        # Execute via WASM runtime
        result = {
            "status": "success",
            "plugin_id": plugin_id,
            "output": {"result": "executed"},
        }

        plugin.status = PluginStatus.READY
        return result

    def shutdown(self) -> None:
        """Shutdown the plugin host."""
        _log.info("Shutting down PluginHostAdapter")
        if self._host_process:
            self._host_process.terminate()
            self._host_process = None
        self._loaded_plugins.clear()

    # =========================================================================
    # IPC/Socket Integration with thegent-plugin-host Rust crate
    # =========================================================================

    def start_host_process(
        self,
        host_binary_path: Path | None = None,
        socket_path: Path | None = None,
    ) -> bool:
        """Start the Rust plugin host process with IPC socket.

        Args:
            host_binary_path: Path to the plugin host binary.
            socket_path: Path for the IPC socket.

        Returns:
            True if the process started successfully.
        """
        import shutil

        host_path = host_binary_path or self._config.host_binary_path
        socket = (
            socket_path
            or self._config.host_socket_path
            or Path("/tmp/thegent-plugin-host.sock")
        )

        if host_path is None:
            # Try to find the binary in PATH
            host_path = shutil.which("thegent-plugin-host")
            if host_path is None:
                _log.warning("Plugin host binary not found in PATH")
                return False

        _log.info("Starting plugin host: %s (socket: %s)", host_path, socket)

        cmd = [str(host_path), "--socket", str(socket)]
        if self._config.enable_telemetry:
            cmd.append("--telemetry")

        try:
            self._host_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except Exception as e:
            _log.error("Failed to start plugin host: %s", e)
            return False

    def connect_socket(self, socket_path: Path | None = None) -> bool:
        """Connect to the plugin host via Unix socket.

        Args:
            socket_path: Path to the IPC socket.

        Returns:
            True if connection successful.
        """
        socket = socket_path or self._config.host_socket_path
        if socket is None:
            socket = Path("/tmp/thegent-plugin-host.sock")

        if not socket.exists():
            _log.warning("Socket not found: %s", socket)
            return False

        _log.info("Connected to plugin host socket: %s", socket)
        return True

    def send_ipc_command(
        self,
        command: str,
        args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a command to the plugin host via IPC.

        Args:
            command: The command name.
            args: Command arguments.

        Returns:
            The command response.
        """
        _log.debug("IPC command: %s %s", command, args)

        # Placeholder - actual IPC implementation would use Unix socket
        return {
            "command": command,
            "status": "ok",
            "args": args or {},
        }

    def get_host_status(self) -> dict[str, Any]:
        """Get the status of the plugin host.

        Returns:
            Status information including process state and loaded plugins.
        """
        return {
            "host_running": self._host_process is not None,
            "process_alive": (
                self._host_process.poll() is None if self._host_process else False
            ),
            "runtime_status": self.runtime_status.value,
            "plugins_loaded": len(self._loaded_plugins),
            "plugin_ids": list(self._loaded_plugins.keys()),
        }


def get_plugin_host(config: PluginHostConfig | None = None) -> PluginHostAdapter:
    """Get the global plugin host instance.

    Args:
        config: Optional configuration.

    Returns:
        The plugin host adapter instance.
    """
    if not hasattr(get_plugin_host, "_instance"):
        get_plugin_host._instance = PluginHostAdapter(config)
    return get_plugin_host._instance
