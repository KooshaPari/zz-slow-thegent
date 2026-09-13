"""Tests for WL-223: Actor/Impersonation Guardrails.

Verifies actor policy registration, target access control, and impersonation permissions.

# @trace WL-223
"""

from __future__ import annotations

import pytest


@pytest.mark.requirement("WL-223")
class TestActorImpersonationGuardrails:
    """WL-223: Actor and impersonation guardrails for identity control."""

    def test_register_creates_policy(self):
        """# @trace WL-223 — register() creates an actor policy."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        policy = guardrails.register("actor_1", ["target_1", "target_2"])

        assert policy.actor_id == "actor_1"
        assert policy.allowed_targets == ["target_1", "target_2"]
        assert policy.can_impersonate is False

    def test_register_with_impersonate_true(self):
        """# @trace WL-223 — register() respects can_impersonate parameter."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        policy = guardrails.register("actor_1", ["target_1"], can_impersonate=True)

        assert policy.can_impersonate is True

    def test_register_duplicate_raises_error(self):
        """# @trace WL-223 — register() raises ValueError for duplicate actor."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", ["target_1"])

        with pytest.raises(ValueError, match="already registered"):
            guardrails.register("actor_1", ["target_2"])

    def test_can_act_as_returns_true_for_allowed_target(self):
        """# @trace WL-223 — can_act_as() returns True if target is allowed."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", ["target_1", "target_2"])

        assert guardrails.can_act_as("actor_1", "target_1") is True
        assert guardrails.can_act_as("actor_1", "target_2") is True

    def test_can_act_as_returns_false_for_disallowed_target(self):
        """# @trace WL-223 — can_act_as() returns False if target is not allowed."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", ["target_1"])

        assert guardrails.can_act_as("actor_1", "target_2") is False

    def test_can_act_as_returns_false_for_unknown_actor(self):
        """# @trace WL-223 — can_act_as() returns False if actor not registered."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()

        assert guardrails.can_act_as("unknown", "target_1") is False

    def test_can_act_as_with_empty_allowed_targets(self):
        """# @trace WL-223 — can_act_as() returns False when actor has no targets."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", [])

        assert guardrails.can_act_as("actor_1", "target_1") is False

    def test_is_allowed_impersonation_returns_true(self):
        """# @trace WL-223 — is_allowed_impersonation() returns True when enabled."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", [], can_impersonate=True)

        assert guardrails.is_allowed_impersonation("actor_1") is True

    def test_is_allowed_impersonation_returns_false(self):
        """# @trace WL-223 — is_allowed_impersonation() returns False when disabled."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", [], can_impersonate=False)

        assert guardrails.is_allowed_impersonation("actor_1") is False

    def test_is_allowed_impersonation_returns_false_for_unknown_actor(self):
        """# @trace WL-223 — is_allowed_impersonation() returns False for unknown actor."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()

        assert guardrails.is_allowed_impersonation("unknown") is False

    def test_get_returns_policy(self):
        """# @trace WL-223 — get() returns the registered policy."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", ["target_1"], can_impersonate=True)

        policy = guardrails.get("actor_1")

        assert policy.actor_id == "actor_1"
        assert policy.allowed_targets == ["target_1"]
        assert policy.can_impersonate is True

    def test_get_nonexistent_raises_keyerror(self):
        """# @trace WL-223 — get() raises KeyError for unknown actor."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()

        with pytest.raises(KeyError, match="not found"):
            guardrails.get("unknown")

    def test_multiple_actors_independent_policies(self):
        """# @trace WL-223 — multiple actors have independent policies."""
        from thegent.integrations.actor_guardrails import ActorImpersonationGuardrails

        guardrails = ActorImpersonationGuardrails()
        guardrails.register("actor_1", ["target_1"], can_impersonate=True)
        guardrails.register("actor_2", ["target_2"], can_impersonate=False)

        assert guardrails.can_act_as("actor_1", "target_1") is True
        assert guardrails.can_act_as("actor_1", "target_2") is False

        assert guardrails.can_act_as("actor_2", "target_2") is True
        assert guardrails.can_act_as("actor_2", "target_1") is False

        assert guardrails.is_allowed_impersonation("actor_1") is True
        assert guardrails.is_allowed_impersonation("actor_2") is False

    def test_actor_policy_dataclass_structure(self):
        """# @trace WL-223 — ActorPolicy has required fields."""
        from thegent.integrations.actor_guardrails import ActorPolicy

        policy = ActorPolicy(actor_id="test", allowed_targets=["t1"], can_impersonate=True)

        assert policy.actor_id == "test"
        assert policy.allowed_targets == ["t1"]
        assert policy.can_impersonate is True

    def test_actor_policy_default_can_impersonate(self):
        """# @trace WL-223 — ActorPolicy defaults can_impersonate to False."""
        from thegent.integrations.actor_guardrails import ActorPolicy

        policy = ActorPolicy(actor_id="test", allowed_targets=["t1"])

        assert policy.can_impersonate is False
