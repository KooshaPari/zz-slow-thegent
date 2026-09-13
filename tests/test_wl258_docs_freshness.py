"""Tests for WL-258: Docs Freshness Checker.

Tests the automatic checker for stale sync docs and command reference drift.

# @trace WL-258
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.requirement("WL-258")
class TestDocRecord:
    """Tests for DocRecord dataclass."""

    def test_create_with_defaults(self):
        """# @trace WL-258 — DocRecord can be created with default stale=False."""
        from thegent.integrations.docs_freshness import DocRecord

        now = datetime.now(UTC)
        record = DocRecord(doc_path="docs/test.md", last_updated=now)

        assert record.doc_path == "docs/test.md"
        assert record.last_updated == now
        assert record.stale is False

    def test_create_with_stale_flag(self):
        """# @trace WL-258 — DocRecord can be created with stale=True."""
        from thegent.integrations.docs_freshness import DocRecord

        now = datetime.now(UTC)
        record = DocRecord(doc_path="docs/test.md", last_updated=now, stale=True)

        assert record.stale is True


@pytest.mark.requirement("WL-258")
class TestDocsFreshnessChecker:
    """Tests for DocsFreshnessChecker."""

    def test_init(self):
        """# @trace WL-258 — DocsFreshnessChecker can be initialized."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        assert checker is not None

    def test_register_creates_doc_record(self):
        """# @trace WL-258 — register creates and returns a DocRecord."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        record = checker.register("docs/test.md", now)

        assert record.doc_path == "docs/test.md"
        assert record.last_updated == now
        assert record.stale is False

    def test_register_multiple_docs(self):
        """# @trace WL-258 — register can be called for multiple documents."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        r1 = checker.register("docs/test1.md", now)
        r2 = checker.register("docs/test2.md", now)
        r3 = checker.register("docs/test3.md", now)

        assert r1.doc_path == "docs/test1.md"
        assert r2.doc_path == "docs/test2.md"
        assert r3.doc_path == "docs/test3.md"

    def test_check_staleness_marks_old_docs(self):
        """# @trace WL-258 — check_staleness marks docs older than max_age_days."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        old_time = now - timedelta(days=100)

        checker.register("docs/old.md", old_time)
        stale = checker.check_staleness(max_age_days=90.0)

        assert len(stale) == 1
        assert stale[0].doc_path == "docs/old.md"
        assert stale[0].stale is True

    def test_check_staleness_does_not_mark_recent_docs(self):
        """# @trace WL-258 — check_staleness does not mark recent docs."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        recent_time = now - timedelta(days=30)

        checker.register("docs/recent.md", recent_time)
        stale = checker.check_staleness(max_age_days=90.0)

        assert len(stale) == 0

    def test_check_staleness_returns_all_stale_docs(self):
        """# @trace WL-258 — check_staleness returns all docs exceeding max_age."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        old = now - timedelta(days=100)
        recent = now - timedelta(days=30)

        checker.register("docs/old1.md", old)
        checker.register("docs/old2.md", old)
        checker.register("docs/recent.md", recent)

        stale = checker.check_staleness(max_age_days=90.0)

        assert len(stale) == 2
        assert {s.doc_path for s in stale} == {"docs/old1.md", "docs/old2.md"}

    def test_check_staleness_with_custom_max_age(self):
        """# @trace WL-258 — check_staleness respects custom max_age_days."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        forty_days_old = now - timedelta(days=40)

        checker.register("docs/test.md", forty_days_old)
        stale_30 = checker.check_staleness(max_age_days=30.0)
        stale_60 = checker.check_staleness(max_age_days=60.0)

        assert len(stale_30) == 1  # 40 days > 30 days
        assert len(stale_60) == 0  # 40 days < 60 days

    def test_stale_count_returns_number_of_stale_docs(self):
        """# @trace WL-258 — stale_count returns count of marked-stale docs."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        old = now - timedelta(days=100)

        checker.register("docs/old1.md", old)
        checker.register("docs/old2.md", old)
        checker.register("docs/recent.md", now)

        checker.check_staleness(max_age_days=90.0)
        count = checker.stale_count()

        assert count == 2

    def test_stale_count_zero_when_no_stale_docs(self):
        """# @trace WL-258 — stale_count returns 0 when no stale docs."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)

        checker.register("docs/recent1.md", now)
        checker.register("docs/recent2.md", now)

        checker.check_staleness(max_age_days=90.0)
        count = checker.stale_count()

        assert count == 0

    def test_fresh_count_returns_number_of_fresh_docs(self):
        """# @trace WL-258 — fresh_count returns count of non-stale docs."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        old = now - timedelta(days=100)

        checker.register("docs/old.md", old)
        checker.register("docs/recent1.md", now)
        checker.register("docs/recent2.md", now)

        checker.check_staleness(max_age_days=90.0)
        count = checker.fresh_count()

        assert count == 2

    def test_fresh_count_includes_all_when_no_stale(self):
        """# @trace WL-258 — fresh_count includes all docs when none stale."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)

        checker.register("docs/a.md", now)
        checker.register("docs/b.md", now)
        checker.register("docs/c.md", now)

        checker.check_staleness(max_age_days=90.0)
        count = checker.fresh_count()

        assert count == 3

    def test_stale_and_fresh_count_sum_to_total(self):
        """# @trace WL-258 — stale_count + fresh_count equals total docs."""
        from thegent.integrations.docs_freshness import DocsFreshnessChecker

        checker = DocsFreshnessChecker()
        now = datetime.now(UTC)
        old = now - timedelta(days=100)

        for i in range(5):
            checker.register(f"docs/old{i}.md", old)
        for i in range(3):
            checker.register(f"docs/recent{i}.md", now)

        checker.check_staleness(max_age_days=90.0)
        stale = checker.stale_count()
        fresh = checker.fresh_count()

        assert stale + fresh == 8
        assert stale == 5
        assert fresh == 3
