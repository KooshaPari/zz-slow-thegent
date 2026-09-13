"""Unit tests for required field validation gate.

# @trace WL-211
"""

from __future__ import annotations

import pytest

from thegent.sync.validation import validate_required_fields


@pytest.mark.requirement("WL-211")
def test_validate_required_fields_passes_when_all_present():
    validate_required_fields(required_fields={"f1", "f2"}, available_fields={"f1", "f2", "f3"})


@pytest.mark.requirement("WL-211")
def test_validate_required_fields_raises_for_missing_fields():
    with pytest.raises(ValueError, match="missing required fields: f2"):
        validate_required_fields(required_fields={"f1", "f2"}, available_fields={"f1"})
