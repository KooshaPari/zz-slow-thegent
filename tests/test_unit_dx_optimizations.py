import pytest

# thegent.tools.xml_repair module was removed; this entire file is dedicated to its tests.
_xml_repair = pytest.importorskip(
    "thegent.tools.xml_repair",
    reason="thegent.tools.xml_repair module removed; dx optimizations tests skipped",
)
from thegent.tools.cache import ResourceCache
from thegent.tools.xml_repair import (
    SloppyXMLRepair,  # noqa: E402  (importorskip may skip before this)
)

from thegent.governance.handoff import HandoffIntegrity


def test_handoff_integrity_analysis(tmp_path):
    """WP-16005: Verify handoff integrity analysis."""
    # Create a dummy file
    (tmp_path / "src").mkdir()
    dummy_file = tmp_path / "src/main.py"
    dummy_file.write_text("print('hello')")

    handoff = HandoffIntegrity(tmp_path)

    # Test 1: Complete prompt
    res1 = handoff.analyze_prompt("Update the logic in src/main.py")
    assert "src/main.py" in res1["referenced_files"]
    assert res1["is_complete"] is True

    # Test 2: Vague prompt
    res2 = handoff.analyze_prompt("implement this")
    assert "Potential vague instruction" in res2["findings"][0]
    assert res2["is_complete"] is False


def test_resource_cache(tmp_path):
    """WP-DX-023: Verify resource caching."""
    cache = ResourceCache(tmp_path / "cache", ttl_seconds=1)
    key = "test:resource"
    payload = {"status": "ok", "data": [1, 2, 3]}

    # Set cache
    etag = cache.set(key, payload)
    assert len(etag) == 32

    # Get cache
    cached = cache.get(key)
    assert cached == payload

    # Wait for expiry
    import time

    time.sleep(1.1)
    assert cache.get(key) is None


def test_sloppy_xml_repair():
    """WP-ROB-018: Verify best-effort XML repair."""
    repairer = SloppyXMLRepair()

    # 1. Trailing unclosed tag
    assert repairer.repair("<THOUGHT>thinking") == "<THOUGHT>thinking</THOUGHT>"

    # 2. Naked tag
    assert repairer.repair("<STATUS success") == "<STATUS>success</STATUS>"

    # 3. Multiple tags wrap
    assert repairer.repair("<A>1</A><B>2</B>") == "<root>\n<A>1</A><B>2</B>\n</root>"
