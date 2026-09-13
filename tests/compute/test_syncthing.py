"""Unit tests for SyncthingManager and related classes.

@trace FR-COMPUTE-001
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from thegent.compute.syncthing import (
    SyncthingConfig,
    SyncthingDevice,
    SyncthingError,
    SyncthingFolder,
    SyncthingManager,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(
    status_code: int = 200,
    json_body: Any = None,
    content: bytes = b"",
) -> MagicMock:
    """Build a mock ``httpx.Response``."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = (json_body is not None and b"x") or content
    if json_body is not None:
        resp.json.return_value = json_body
        resp.content = b"x"
    else:
        resp.json.side_effect = ValueError("no body")
        resp.content = b""

    if status_code >= 400:
        resp.text = f"HTTP {status_code}"
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _make_manager(api_key: str = "test-key", base_url: str = "http://localhost:8384") -> SyncthingManager:
    cfg = SyncthingConfig(
        THGENT_SYNCTHING_API_KEY=api_key,
        THGENT_SYNCTHING_URL=base_url,
    )
    return SyncthingManager(config=cfg)


# ---------------------------------------------------------------------------
# SyncthingConfig tests
# ---------------------------------------------------------------------------


class TestSyncthingConfig:
    """Tests for SyncthingConfig Pydantic settings model."""

    def test_defaults(self) -> None:
        """Default base_url and None api_key when env vars absent."""
        # Pass empty values to avoid picking up real env vars in CI
        cfg = SyncthingConfig(THGENT_SYNCTHING_URL="http://localhost:8384")
        assert cfg.base_url == "http://localhost:8384"
        assert cfg.api_key is None

    def test_custom_values(self) -> None:
        """Custom values are stored correctly."""
        cfg = SyncthingConfig(
            THGENT_SYNCTHING_API_KEY="secret",
            THGENT_SYNCTHING_URL="http://remote:8384",
        )
        assert cfg.api_key == "secret"
        assert cfg.base_url == "http://remote:8384"

    def test_api_key_none_allowed(self) -> None:
        """api_key is optional and can be None."""
        cfg = SyncthingConfig(THGENT_SYNCTHING_URL="http://localhost:8384")
        assert cfg.api_key is None


# ---------------------------------------------------------------------------
# SyncthingDevice / SyncthingFolder dataclasses
# ---------------------------------------------------------------------------


class TestSyncthingDevice:
    """Tests for SyncthingDevice dataclass."""

    def test_fields(self) -> None:
        dev = SyncthingDevice(device_id="AAAAAA-BBBBBB", name="my-mac", is_connected=True)
        assert dev.device_id == "AAAAAA-BBBBBB"
        assert dev.name == "my-mac"
        assert dev.is_connected is True

    def test_disconnected(self) -> None:
        dev = SyncthingDevice(device_id="X", name="offline", is_connected=False)
        assert dev.is_connected is False


class TestSyncthingFolder:
    """Tests for SyncthingFolder dataclass."""

    def test_fields(self) -> None:
        folder = SyncthingFolder(
            folder_id="workspace-1",
            path="/home/user/workspace",
            label="My Workspace",
            devices=["DEV1", "DEV2"],
        )
        assert folder.folder_id == "workspace-1"
        assert folder.path == "/home/user/workspace"
        assert folder.label == "My Workspace"
        assert folder.devices == ["DEV1", "DEV2"]

    def test_default_devices(self) -> None:
        folder = SyncthingFolder(folder_id="f", path="/tmp", label="L")
        assert folder.devices == []


# ---------------------------------------------------------------------------
# SyncthingManager — is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for SyncthingManager.is_available."""

    @pytest.mark.asyncio
    async def test_returns_true_when_status_ok(self) -> None:
        manager = _make_manager()
        resp = _make_response(json_body={"status": "OK"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.is_available()

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_http_error(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=500, json_body={"error": "internal"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.is_available()

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_connection_error(self) -> None:
        manager = _make_manager()
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.is_available()

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_status_not_ok(self) -> None:
        manager = _make_manager()
        resp = _make_response(json_body={"status": "degraded"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.is_available()

        assert result is False


# ---------------------------------------------------------------------------
# SyncthingManager — get_devices
# ---------------------------------------------------------------------------


class TestGetDevices:
    """Tests for SyncthingManager.get_devices."""

    @pytest.mark.asyncio
    async def test_parses_device_list(self) -> None:
        manager = _make_manager()
        raw = [
            {"deviceID": "DEV1-XXX", "name": "laptop", "paused": False},
            {"deviceID": "DEV2-YYY", "name": "desktop", "paused": True},
        ]
        resp = _make_response(json_body=raw)
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            devices = await manager.get_devices()

        assert len(devices) == 2
        assert devices[0].device_id == "DEV1-XXX"
        assert devices[0].name == "laptop"
        assert devices[0].is_connected is True
        assert devices[1].device_id == "DEV2-YYY"
        assert devices[1].is_connected is False

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        manager = _make_manager()
        resp = _make_response(json_body=[])
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            devices = await manager.get_devices()

        assert devices == []

    @pytest.mark.asyncio
    async def test_uses_device_id_as_name_when_name_missing(self) -> None:
        manager = _make_manager()
        raw = [{"deviceID": "ANON-ID", "name": "", "paused": False}]
        resp = _make_response(json_body=raw)
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            devices = await manager.get_devices()

        assert devices[0].name == "ANON-ID"

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_http_failure(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=403, json_body={"error": "forbidden"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="403"):
                await manager.get_devices()

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_connection_failure(self) -> None:
        manager = _make_manager()
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="connection error"):
                await manager.get_devices()


# ---------------------------------------------------------------------------
# SyncthingManager — get_folders
# ---------------------------------------------------------------------------


class TestGetFolders:
    """Tests for SyncthingManager.get_folders."""

    @pytest.mark.asyncio
    async def test_parses_folder_list(self) -> None:
        manager = _make_manager()
        raw = [
            {
                "id": "workspace-1",
                "path": "/home/user/workspace",
                "label": "Workspace",
                "devices": [{"deviceID": "DEV1"}, {"deviceID": "DEV2"}],
            }
        ]
        resp = _make_response(json_body=raw)
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            folders = await manager.get_folders()

        assert len(folders) == 1
        f = folders[0]
        assert f.folder_id == "workspace-1"
        assert f.path == "/home/user/workspace"
        assert f.label == "Workspace"
        assert f.devices == ["DEV1", "DEV2"]

    @pytest.mark.asyncio
    async def test_empty_folder_list(self) -> None:
        manager = _make_manager()
        resp = _make_response(json_body=[])
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            folders = await manager.get_folders()

        assert folders == []

    @pytest.mark.asyncio
    async def test_uses_id_as_label_when_label_missing(self) -> None:
        manager = _make_manager()
        raw = [{"id": "my-folder", "path": "/tmp/x", "label": "", "devices": []}]
        resp = _make_response(json_body=raw)
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            folders = await manager.get_folders()

        assert folders[0].label == "my-folder"

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_api_error(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=401, json_body={"error": "unauthorized"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="401"):
                await manager.get_folders()


# ---------------------------------------------------------------------------
# SyncthingManager — add_folder
# ---------------------------------------------------------------------------


class TestAddFolder:
    """Tests for SyncthingManager.add_folder."""

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=200, json_body=None)
        client_mock = AsyncMock()
        client_mock.post = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.add_folder(
                folder_id="ws-new",
                path="/data/workspace",
                label="New Workspace",
                device_ids=["DEV1", "DEV2"],
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_sends_correct_payload(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=200, json_body=None)
        client_mock = AsyncMock()
        client_mock.post = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            await manager.add_folder(
                folder_id="ws-abc",
                path="/some/path",
                label="My Folder",
                device_ids=["D1", "D2", "D3"],
            )

        call_kwargs = client_mock.post.call_args
        sent_json = call_kwargs.kwargs["json"]
        assert sent_json["id"] == "ws-abc"
        assert sent_json["path"] == "/some/path"
        assert sent_json["label"] == "My Folder"
        assert {"deviceID": "D1"} in sent_json["devices"]
        assert {"deviceID": "D2"} in sent_json["devices"]
        assert {"deviceID": "D3"} in sent_json["devices"]

    @pytest.mark.asyncio
    async def test_empty_device_list_allowed(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=200, json_body=None)
        client_mock = AsyncMock()
        client_mock.post = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.add_folder("f", "/p", "L", [])

        assert result is True

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_failure(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=400, json_body={"error": "bad request"})
        client_mock = AsyncMock()
        client_mock.post = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="400"):
                await manager.add_folder("f", "/p", "L", [])


# ---------------------------------------------------------------------------
# SyncthingManager — sync_status
# ---------------------------------------------------------------------------


class TestSyncStatus:
    """Tests for SyncthingManager.sync_status."""

    @pytest.mark.asyncio
    async def test_returns_status_dict(self) -> None:
        manager = _make_manager()
        status_data = {
            "state": "idle",
            "needBytes": 0,
            "inSyncFiles": 42,
        }
        resp = _make_response(json_body=status_data)
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            result = await manager.sync_status("workspace-1")

        assert result["state"] == "idle"
        assert result["inSyncFiles"] == 42

    @pytest.mark.asyncio
    async def test_passes_folder_id_as_query_param(self) -> None:
        manager = _make_manager()
        resp = _make_response(json_body={"state": "syncing"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            await manager.sync_status("my-folder-id")

        call_args = client_mock.get.call_args
        assert call_args.kwargs.get("params") == {"folder": "my-folder-id"}

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_api_error(self) -> None:
        manager = _make_manager()
        resp = _make_response(status_code=404, json_body={"error": "not found"})
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=resp)
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="404"):
                await manager.sync_status("nonexistent-folder")

    @pytest.mark.asyncio
    async def test_raises_syncthing_error_on_connection_error(self) -> None:
        manager = _make_manager()
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(side_effect=httpx.ConnectError("down"))
        client_mock.is_closed = False

        with patch.object(manager, "_get_client", return_value=client_mock):
            with pytest.raises(SyncthingError, match="connection error"):
                await manager.sync_status("ws")


# ---------------------------------------------------------------------------
# SyncthingManager — lifecycle / context manager
# ---------------------------------------------------------------------------


class TestSyncthingManagerLifecycle:
    """Tests for client creation and close behaviour."""

    @pytest.mark.asyncio
    async def test_close_releases_client(self) -> None:
        manager = _make_manager()
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False
        manager._client = mock_client

        await manager.close()

        mock_client.aclose.assert_called_once()
        assert manager._client is None

    @pytest.mark.asyncio
    async def test_close_when_no_client_is_noop(self) -> None:
        manager = _make_manager()
        # Should not raise
        await manager.close()

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_on_exit(self) -> None:
        manager = _make_manager()
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False
        manager._client = mock_client

        async with manager:
            pass

        mock_client.aclose.assert_called_once()

    def test_get_client_sets_api_key_header(self) -> None:
        manager = _make_manager(api_key="my-secret")
        client = manager._get_client()
        assert "X-API-Key" in client.headers
        assert client.headers["X-API-Key"] == "my-secret"

    def test_get_client_no_api_key_header_when_none(self) -> None:
        cfg = SyncthingConfig(THGENT_SYNCTHING_URL="http://localhost:8384")
        manager = SyncthingManager(config=cfg)
        client = manager._get_client()
        assert "X-API-Key" not in client.headers

    @pytest.mark.asyncio
    async def test_default_config_used_when_none_provided(self) -> None:
        """SyncthingManager creates its own config if none supplied."""
        with patch("thegent.compute.syncthing.SyncthingConfig") as mock_cfg_cls:
            mock_cfg = MagicMock()
            mock_cfg.api_key = None
            mock_cfg.base_url = "http://localhost:8384"
            mock_cfg_cls.return_value = mock_cfg
            manager = SyncthingManager()
            assert manager._config is mock_cfg
