"""Tests for WL-260: Default Enablement Migration Plan.

Verifies phase tracking, advancement, and filtering of feature enablement plans.

# @trace WL-260
"""

from __future__ import annotations

import pytest


@pytest.mark.requirement("WL-260")
class TestDefaultEnablementMigrator:
    """WL-260: Feature enablement migration plan management."""

    def test_register_creates_plan_in_plan_phase(self):
        """# @trace WL-260 — register() creates feature in PLAN phase."""
        from thegent.integrations.enablement_migration import (
            DefaultEnablementMigrator,
            MigrationPhase,
        )

        migrator = DefaultEnablementMigrator()
        plan = migrator.register("feature_1")

        assert plan.feature_id == "feature_1"
        assert plan.phase == MigrationPhase.PLAN

    def test_register_duplicate_raises_error(self):
        """# @trace WL-260 — register() raises ValueError for duplicate feature."""
        from thegent.integrations.enablement_migration import DefaultEnablementMigrator

        migrator = DefaultEnablementMigrator()
        migrator.register("feature_1")

        with pytest.raises(ValueError, match="already registered"):
            migrator.register("feature_1")

    def test_advance_moves_to_next_phase(self):
        """# @trace WL-260 — advance() moves feature through phases sequentially."""
        from thegent.integrations.enablement_migration import (
            DefaultEnablementMigrator,
            MigrationPhase,
        )

        migrator = DefaultEnablementMigrator()
        migrator.register("feature_1")

        # PLAN -> PILOT
        plan = migrator.advance("feature_1")
        assert plan.phase == MigrationPhase.PILOT

        # PILOT -> ROLLOUT
        plan = migrator.advance("feature_1")
        assert plan.phase == MigrationPhase.ROLLOUT

        # ROLLOUT -> COMPLETE
        plan = migrator.advance("feature_1")
        assert plan.phase == MigrationPhase.COMPLETE

    def test_advance_nonexistent_feature_raises_keyerror(self):
        """# @trace WL-260 — advance() raises KeyError for missing feature."""
        from thegent.integrations.enablement_migration import DefaultEnablementMigrator

        migrator = DefaultEnablementMigrator()

        with pytest.raises(KeyError, match="not found"):
            migrator.advance("missing")

    def test_advance_from_complete_raises_error(self):
        """# @trace WL-260 — advance() raises ValueError when feature already COMPLETE."""
        from thegent.integrations.enablement_migration import DefaultEnablementMigrator

        migrator = DefaultEnablementMigrator()
        migrator.register("feature_1")
        migrator.advance("feature_1")
        migrator.advance("feature_1")
        migrator.advance("feature_1")

        with pytest.raises(ValueError, match="already in complete phase"):
            migrator.advance("feature_1")

    def test_get_returns_plan(self):
        """# @trace WL-260 — get() returns registered EnablementMigrationPlan."""
        from thegent.integrations.enablement_migration import DefaultEnablementMigrator

        migrator = DefaultEnablementMigrator()
        migrator.register("feature_1")

        plan = migrator.get("feature_1")

        assert plan.feature_id == "feature_1"

    def test_get_nonexistent_raises_keyerror(self):
        """# @trace WL-260 — get() raises KeyError for missing feature."""
        from thegent.integrations.enablement_migration import DefaultEnablementMigrator

        migrator = DefaultEnablementMigrator()

        with pytest.raises(KeyError, match="not found"):
            migrator.get("missing")

    def test_by_phase_filters_correctly(self):
        """# @trace WL-260 — by_phase() returns only features in specified phase."""
        from thegent.integrations.enablement_migration import (
            DefaultEnablementMigrator,
            MigrationPhase,
        )

        migrator = DefaultEnablementMigrator()
        migrator.register("feat_a")
        migrator.register("feat_b")
        migrator.register("feat_c")

        migrator.advance("feat_a")  # PLAN -> PILOT
        migrator.advance("feat_b")  # PLAN -> PILOT
        migrator.advance("feat_b")  # PILOT -> ROLLOUT

        plan_phase = migrator.by_phase(MigrationPhase.PLAN)
        pilot_phase = migrator.by_phase(MigrationPhase.PILOT)
        rollout_phase = migrator.by_phase(MigrationPhase.ROLLOUT)

        assert len(plan_phase) == 1
        assert plan_phase[0].feature_id == "feat_c"

        assert len(pilot_phase) == 1
        assert pilot_phase[0].feature_id == "feat_a"

        assert len(rollout_phase) == 1
        assert rollout_phase[0].feature_id == "feat_b"

    def test_by_phase_returns_sorted_list(self):
        """# @trace WL-260 — by_phase() returns results sorted by feature_id."""
        from thegent.integrations.enablement_migration import (
            DefaultEnablementMigrator,
            MigrationPhase,
        )

        migrator = DefaultEnablementMigrator()
        migrator.register("zebra")
        migrator.register("alpha")
        migrator.register("beta")

        results = migrator.by_phase(MigrationPhase.PLAN)
        feature_ids = [p.feature_id for p in results]

        assert feature_ids == ["alpha", "beta", "zebra"]

    def test_by_phase_empty(self):
        """# @trace WL-260 — by_phase() returns empty list when no features in phase."""
        from thegent.integrations.enablement_migration import (
            DefaultEnablementMigrator,
            MigrationPhase,
        )

        migrator = DefaultEnablementMigrator()
        migrator.register("feat_a")
        migrator.advance("feat_a")

        plan_phase = migrator.by_phase(MigrationPhase.PLAN)

        assert plan_phase == []

    def test_migration_phase_enum_values(self):
        """# @trace WL-260 — MigrationPhase enum has all expected values."""
        from thegent.integrations.enablement_migration import MigrationPhase

        phases = {p.value for p in MigrationPhase}

        assert phases == {"plan", "pilot", "rollout", "complete"}
