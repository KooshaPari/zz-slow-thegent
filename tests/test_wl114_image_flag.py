"""Tests for WL-114 --image flag wiring across backends.

# @trace WL-114
"""

from __future__ import annotations

import base64
from pathlib import Path

import orjson as json
import pytest

from thegent.agents.image_inputs import (
    SUPPORTED_FORMATS,
    build_claude_stdin_with_images,
    build_codex_image_args,
    build_image_content_block,
    encode_image_to_base64,
)
from thegent.agents.run_options import CODEX_AGENTS, IMAGE_CAPABLE_AGENTS
from thegent.cli.commands.impl import _normalize_image_paths, _validate_image_capability

# ---------------------------------------------------------------------------
# image_inputs module — encode_image_to_base64
# ---------------------------------------------------------------------------


def test_encode_image_to_base64_roundtrips(tmp_path: Path) -> None:
    """encode_image_to_base64 produces decodable base64 of exact file bytes.

    # @trace WL-114
    """
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 24)
    encoded = encode_image_to_base64(img)
    assert base64.standard_b64decode(encoded) == img.read_bytes()


def test_encode_image_to_base64_ascii_safe(tmp_path: Path) -> None:
    """Encoded string contains only ASCII characters.

    # @trace WL-114
    """
    img = tmp_path / "test.png"
    img.write_bytes(bytes(range(256)))
    encoded = encode_image_to_base64(img)
    encoded.encode("ascii")  # must not raise


# ---------------------------------------------------------------------------
# image_inputs module — build_image_content_block
# ---------------------------------------------------------------------------


def test_build_image_content_block_structure(tmp_path: Path) -> None:
    """Content block has required Anthropic shape.

    # @trace WL-114
    """
    img = tmp_path / "shot.png"
    img.write_bytes(b"PNG")
    block = build_image_content_block(img)
    assert block["type"] == "image"
    assert block["source"]["type"] == "base64"
    assert block["source"]["media_type"] == "image/png"
    assert block["source"]["data"] == base64.standard_b64encode(b"PNG").decode("ascii")


def test_build_image_content_block_jpeg(tmp_path: Path) -> None:
    """JPEG files get correct media_type.

    # @trace WL-114
    """
    img = tmp_path / "photo.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    block = build_image_content_block(img)
    assert block["source"]["media_type"] == "image/jpeg"


def test_build_image_content_block_webp(tmp_path: Path) -> None:
    """WEBP files get correct media_type.

    # @trace WL-114
    """
    img = tmp_path / "anim.webp"
    img.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
    block = build_image_content_block(img)
    assert block["source"]["media_type"] == "image/webp"


# ---------------------------------------------------------------------------
# image_inputs module — build_codex_image_args
# ---------------------------------------------------------------------------


def test_build_codex_image_args_empty() -> None:
    """Empty paths list returns empty args.

    # @trace WL-114
    """
    assert build_codex_image_args([]) == []


def test_build_codex_image_args_single() -> None:
    """Single path produces one --image pair.

    # @trace WL-114
    """
    args = build_codex_image_args(["/tmp/a.png"])
    assert args == ["--image", "/tmp/a.png"]


def test_build_codex_image_args_multiple() -> None:
    """Multiple paths produce correctly ordered --image pairs.

    # @trace WL-114
    """
    args = build_codex_image_args(["/tmp/a.png", "/tmp/b.jpg"])
    assert args == ["--image", "/tmp/a.png", "--image", "/tmp/b.jpg"]


def test_build_codex_image_args_trims_whitespace() -> None:
    args = build_codex_image_args(["  /tmp/a.png  "])
    assert args == ["--image", "/tmp/a.png"]


def test_build_codex_image_args_rejects_empty_or_non_string_path() -> None:
    with pytest.raises(ValueError, match="must be non-empty strings"):
        build_codex_image_args(["/tmp/a.png", "   "])
    with pytest.raises(ValueError, match="must be non-empty strings"):
        build_codex_image_args(["/tmp/a.png", 123])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# image_inputs module — build_claude_stdin_with_images
# ---------------------------------------------------------------------------


def test_build_claude_stdin_with_images_valid_json(tmp_path: Path) -> None:
    """Output is valid JSON terminated with newline.

    # @trace WL-114
    """
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    payload = build_claude_stdin_with_images("describe this", [str(img)])
    assert payload.endswith("\n")
    parsed = json.loads(payload.strip())
    assert isinstance(parsed, dict)


def test_build_claude_stdin_with_images_structure(tmp_path: Path) -> None:
    """JSONL payload has correct Anthropic stream-json message shape.

    # @trace WL-114
    """
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    payload = build_claude_stdin_with_images("describe", [str(img)])
    msg = json.loads(payload.strip())
    assert msg["type"] == "user"
    assert msg["message"]["role"] == "user"
    content = msg["message"]["content"]
    assert content[-1]["type"] == "text"
    assert content[-1]["text"] == "describe"
    # Image block comes before text
    assert content[0]["type"] == "image"


def test_build_claude_stdin_with_images_multiple(tmp_path: Path) -> None:
    """Multiple images all appear in content before the text block.

    # @trace WL-114
    """
    img1 = tmp_path / "a.png"
    img2 = tmp_path / "b.png"
    img1.write_bytes(b"AA")
    img2.write_bytes(b"BB")
    payload = build_claude_stdin_with_images("compare", [str(img1), str(img2)])
    msg = json.loads(payload.strip())
    content = msg["message"]["content"]
    image_blocks = [c for c in content if c["type"] == "image"]
    assert len(image_blocks) == 2
    text_blocks = [c for c in content if c["type"] == "text"]
    assert len(text_blocks) == 1


# ---------------------------------------------------------------------------
# run_options — IMAGE_CAPABLE_AGENTS
# ---------------------------------------------------------------------------


def test_image_capable_agents_contains_codex() -> None:
    """codex is in IMAGE_CAPABLE_AGENTS.

    # @trace WL-114
    """
    assert "codex" in IMAGE_CAPABLE_AGENTS


def test_image_capable_agents_contains_claude() -> None:
    """claude is in IMAGE_CAPABLE_AGENTS for Claude Code CLI path.

    # @trace WL-114
    """
    assert "claude" in IMAGE_CAPABLE_AGENTS


def test_image_capable_agents_superset_of_codex_agents() -> None:
    """All CODEX_AGENTS are also IMAGE_CAPABLE_AGENTS.

    # @trace WL-114
    """
    assert CODEX_AGENTS.issubset(IMAGE_CAPABLE_AGENTS)


def test_cursor_agent_not_image_capable() -> None:
    """cursor-agent is not image capable.

    # @trace WL-114
    """
    assert "cursor-agent" not in IMAGE_CAPABLE_AGENTS


# ---------------------------------------------------------------------------
# validate_image_capability uses IMAGE_CAPABLE_AGENTS
# ---------------------------------------------------------------------------


def test_validate_image_capability_rejects_non_image_agent() -> None:
    """Unknown agent names not in IMAGE_CAPABLE_AGENTS raise loudly.

    # @trace WL-114
    """
    with pytest.raises(ValueError, match="not supported for agent"):
        _validate_image_capability("not-a-real-agent", "gpt-5-codex")


def test_validate_image_capability_accepts_claude_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """claude is now accepted by validate_image_capability.

    # @trace WL-114
    """
    monkeypatch.setattr("thegent.cli.commands.impl._model_supports_vision", lambda _m: True)
    # Must not raise
    _validate_image_capability("claude", "claude-opus-4-6")


# ---------------------------------------------------------------------------
# DirectAgentRunner._build_cmd — claude branch
# ---------------------------------------------------------------------------


def test_direct_agent_runner_build_cmd_claude_adds_input_format_when_images() -> None:
    """_build_cmd for claude includes --input-format stream-json when image_paths given.

    # @trace WL-114
    """
    from thegent.agents.direct_agents import DirectAgentRunner

    runner = DirectAgentRunner("claude")
    cmd = runner._build_cmd(
        cwd=None,
        use_stream=True,
        model="claude-opus-4-6",
        mode="read-only",
        image_paths=["/tmp/a.png"],
    )
    assert "--input-format" in cmd
    idx = cmd.index("--input-format")
    assert cmd[idx + 1] == "stream-json"


def test_direct_agent_runner_build_cmd_claude_no_input_format_without_images() -> None:
    """_build_cmd for claude does NOT add --input-format stream-json without images.

    # @trace WL-114
    """
    from thegent.agents.direct_agents import DirectAgentRunner

    runner = DirectAgentRunner("claude")
    cmd = runner._build_cmd(
        cwd=None,
        use_stream=True,
        model="claude-opus-4-6",
        mode="read-only",
        image_paths=None,
    )
    assert "--input-format" not in cmd


# ---------------------------------------------------------------------------
# DirectAgentRunner._build_cmd — codex branch (direct_agents)
# ---------------------------------------------------------------------------


def test_direct_agent_runner_build_cmd_codex_passes_image_args() -> None:
    """_build_cmd for codex emits --image <path> args.

    # @trace WL-114
    """
    from thegent.agents.direct_agents import DirectAgentRunner

    runner = DirectAgentRunner("codex")
    cmd = runner._build_cmd(
        cwd=None,
        use_stream=True,
        model="gpt-5-codex",
        mode="read-only",
        image_paths=["/tmp/img.png", "/tmp/img2.jpg"],
    )
    # Both images must appear as --image pairs
    assert cmd.count("--image") == 2
    idx1 = cmd.index("--image")
    assert cmd[idx1 + 1] == "/tmp/img.png"


# ---------------------------------------------------------------------------
# SUPPORTED_FORMATS constant
# ---------------------------------------------------------------------------


def test_supported_formats_includes_standard_types() -> None:
    """SUPPORTED_FORMATS includes png, jpg, jpeg, webp, gif.

    # @trace WL-114
    """
    assert ".png" in SUPPORTED_FORMATS
    assert ".jpg" in SUPPORTED_FORMATS
    assert ".jpeg" in SUPPORTED_FORMATS
    assert ".webp" in SUPPORTED_FORMATS
    assert ".gif" in SUPPORTED_FORMATS


# ---------------------------------------------------------------------------
# normalize_image_paths — integration with image_inputs
# ---------------------------------------------------------------------------


def test_normalize_image_paths_resolves_local_png(tmp_path: Path) -> None:
    """_normalize_image_paths resolves a local PNG path to absolute form.

    # @trace WL-114
    """
    img = tmp_path / "test.png"
    img.write_bytes(b"PNG")
    result = _normalize_image_paths([str(img)])
    assert result == [str(img.resolve())]


def test_normalize_image_paths_rejects_pdf(tmp_path: Path) -> None:
    """_normalize_image_paths rejects unsupported PDF extension.

    # @trace WL-114
    """
    doc = tmp_path / "notes.pdf"
    doc.write_bytes(b"%PDF")
    with pytest.raises(ValueError, match="supported extension"):
        _normalize_image_paths([str(doc)])
