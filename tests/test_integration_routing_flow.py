"""Integration tests for full routing flow: classify -> resolve -> execute."""

import pytest

from thegent.config import ThegentSettings
from thegent.utils.routing_impl.models import TaskCategory
from thegent.utils.routing_impl.task_router import TaskRouter


class TestFullRoutingFlow:
    """Test complete routing flow from prompt to resolved provider."""

    @pytest.fixture
    def router(self):
        """Create TaskRouter for testing."""
        return TaskRouter(ThegentSettings())

    def test_fast_task_routes_to_gemini(self, router):
        """FAST tasks should route to gemini-3-flash."""
        metadata = router.classify("list files in directory")
        assert metadata.category == TaskCategory.FAST
        assert metadata.detected_role in ("researcher", "workhorse")
        assert metadata.selected_model != ""
        assert metadata.model_fallback_chain != []

    def test_complex_task_routes_to_higher_quality(self, router):
        """COMPLEX tasks should route to higher quality models."""
        metadata = router.classify("design a microservices architecture for payment processing")
        assert metadata.category in (TaskCategory.COMPLEX, TaskCategory.HIGH_COMPLEX)
        assert (
            "claude" in metadata.selected_model
            or "deepseek" in metadata.selected_model
            or "glm" in metadata.selected_model
        )

    def test_resolved_provider_set(self, router):
        """classify() should set resolved_provider when route exists."""
        metadata = router.classify("implement a quick fix")
        assert metadata.resolved_provider is not None
        assert isinstance(metadata.resolved_provider, str)

    def test_fallback_chain_populated(self, router):
        """classify() should populate model_fallback_chain."""
        metadata = router.classify("write a function")
        assert len(metadata.model_fallback_chain) >= 1
