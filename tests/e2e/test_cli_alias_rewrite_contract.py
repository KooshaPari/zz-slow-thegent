from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import typer

from tests.e2e.cli_runner_compat import _ALIAS_REWRITE_PREFIXES
from tests.e2e.command_surface import command_path_exists

_ALLOWED_CANONICAL_PREFIXES: set[tuple[str, ...]] = {
    ("run", "logs"),
    ("run", "status"),
    ("run", "wait"),
    ("run", "stop"),
    ("run", "inspect"),
    ("run", "history"),
    ("run", "ps"),
    ("plan", "rollback"),
}

_DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES: set[tuple[str, ...]] = {
    ("run", "inspect"),
    ("run", "status"),
    ("run", "wait"),
}

_REQUIRED_LEGACY_ROOTS: set[str] = {
    "logs",
    "status",
    "wait",
    "stop",
    "inspect",
    "history",
    "ps",
    "orchestrate",
    "observe",
    "recover",
}


def test_canonical_target_set_has_no_unapproved_entries_and_is_non_empty() -> None:
    canonical_targets = {new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES}
    assert canonical_targets
    assert canonical_targets <= _ALLOWED_CANONICAL_PREFIXES


def test_allowed_canonical_prefixes_are_covered_except_deliberately_unsupported() -> None:
    assert _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES <= _ALLOWED_CANONICAL_PREFIXES

    canonical_targets = {new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES}
    expected_covered_prefixes = _ALLOWED_CANONICAL_PREFIXES - _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES
    assert canonical_targets >= expected_covered_prefixes


def test_root_second_token_sets_are_exact() -> None:
    expected_by_root: dict[str, set[str]] = {
        "orchestrate": {"status", "logs", "wait", "stop", "inspect"},
        "observe": {"status", "logs", "wait", "stop", "inspect"},
        "recover": {"stop", "rollback"},
    }

    for root, expected_second_tokens in expected_by_root.items():
        actual_second_tokens = {
            old_prefix[1] for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if len(old_prefix) >= 2 and old_prefix[0] == root
        }
        assert actual_second_tokens == expected_second_tokens


def _is_non_empty_string_tuple(value: object) -> bool:
    return isinstance(value, tuple) and bool(value) and all(isinstance(part, str) and bool(part) for part in value)


def _is_lowercase_space_free_token(value: str) -> bool:
    return value == value.lower() and not any(ch.isspace() for ch in value)


def _build_minimal_canonical_path_app() -> typer.Typer:
    app = typer.Typer()
    run_app = typer.Typer()
    plan_app = typer.Typer()

    app.add_typer(run_app, name="run")
    app.add_typer(plan_app, name="plan")

    @run_app.command("logs")
    def run_logs() -> None:
        return None

    @run_app.command("status")
    def run_status() -> None:
        return None

    @run_app.command("wait")
    def run_wait() -> None:
        return None

    @run_app.command("stop")
    def run_stop() -> None:
        return None

    @run_app.command("inspect")
    def run_inspect() -> None:
        return None

    @run_app.command("history")
    def run_history() -> None:
        return None

    @run_app.command("ps")
    def run_ps() -> None:
        return None

    @plan_app.command("rollback")
    def plan_rollback() -> None:
        return None

    return app


def test_alias_rewrite_new_prefixes_are_command_path_valid() -> None:
    app = _build_minimal_canonical_path_app()
    canonical_new_prefixes = {new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES}
    assert canonical_new_prefixes == _ALLOWED_CANONICAL_PREFIXES

    for new_prefix in sorted(canonical_new_prefixes):
        assert command_path_exists(app, list(new_prefix)), (
            f"Canonical alias rewrite target must resolve on minimal Typer fixture: {new_prefix!r}"
        )


def test_orchestrate_and_observe_cover_same_second_tokens() -> None:
    orchestrate_second_tokens = {
        old_prefix[1]
        for old_prefix, _ in _ALIAS_REWRITE_PREFIXES
        if len(old_prefix) >= 2 and old_prefix[0] == "orchestrate"
    }
    observe_second_tokens = {
        old_prefix[1]
        for old_prefix, _ in _ALIAS_REWRITE_PREFIXES
        if len(old_prefix) >= 2 and old_prefix[0] == "observe"
    }

    assert orchestrate_second_tokens
    assert observe_second_tokens
    assert orchestrate_second_tokens == observe_second_tokens


def test_recover_old_prefixes_are_explicit_subcommand_aliases() -> None:
    recover_old_prefixes = [old_prefix for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if old_prefix[0] == "recover"]
    assert recover_old_prefixes
    assert all(len(old_prefix) == 2 for old_prefix in recover_old_prefixes)


def test_orchestrate_and_observe_old_prefixes_are_explicit_subcommand_aliases() -> None:
    for root in ("orchestrate", "observe"):
        old_prefixes = [old_prefix for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if old_prefix[0] == root]
        assert old_prefixes
        assert all(len(old_prefix) == 2 for old_prefix in old_prefixes)


def test_single_token_roots_are_exactly_legacy_run_alias_roots() -> None:
    single_token_roots = {old_prefix[0] for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if len(old_prefix) == 1}
    multi_token_roots = {old_prefix[0] for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if len(old_prefix) >= 2}
    assert single_token_roots == (_REQUIRED_LEGACY_ROOTS - multi_token_roots)


def test_multi_token_roots_are_length_two_only() -> None:
    multi_token_roots = {old_prefix[0] for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if len(old_prefix) >= 2}
    assert multi_token_roots

    for root in multi_token_roots:
        prefix_lengths_for_root = {
            len(old_prefix) for old_prefix, _ in _ALIAS_REWRITE_PREFIXES if old_prefix[0] == root
        }
        assert prefix_lengths_for_root == {2}, (
            "Multi-token legacy roots must appear only as 2-token prefixes: "
            f"{root!r} -> {sorted(prefix_lengths_for_root)!r}"
        )

    assert not any(len(old_prefix) > 2 for old_prefix, _ in _ALIAS_REWRITE_PREFIXES)


def test_each_allowed_canonical_prefix_has_a_legacy_source_mapping() -> None:
    canonical_target_counts = Counter(new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES)
    missing_targets = sorted(target for target in _ALLOWED_CANONICAL_PREFIXES if canonical_target_counts[target] < 1)
    assert not missing_targets, (
        f"Every allowed canonical prefix must have at least one legacy source mapping; missing: {missing_targets!r}"
    )


def test_alias_rewrite_prefix_contract() -> None:
    old_prefixes: list[tuple[str, ...]] = []
    new_prefixes: list[tuple[str, ...]] = []
    old_roots: set[str] = set()

    for mapping in _ALIAS_REWRITE_PREFIXES:
        assert isinstance(mapping, tuple)
        assert len(mapping) == 2
        old_prefix, new_prefix = mapping

        assert _is_non_empty_string_tuple(old_prefix)
        assert _is_non_empty_string_tuple(new_prefix)

        # New prefixes must keep the command path shape consumed by
        # command-surface checks (Sequence[str]).
        path: Sequence[str] = new_prefix
        assert tuple(path) == new_prefix

        assert old_prefix != new_prefix, f"Alias rewrite must change command prefix: {old_prefix!r} -> {new_prefix!r}"
        assert new_prefix in _ALLOWED_CANONICAL_PREFIXES, (
            f"New prefix must be one of policy-approved canonical targets: {new_prefix!r}"
        )

        for prefix in (old_prefix, new_prefix):
            for token in prefix:
                assert _is_lowercase_space_free_token(token), (
                    f"Prefix token must be lowercase and space-free: {token!r}"
                )

        old_prefixes.append(old_prefix)
        new_prefixes.append(new_prefix)
        old_roots.add(old_prefix[0])

    assert len(old_prefixes) == len(set(old_prefixes))
    assert old_roots >= _REQUIRED_LEGACY_ROOTS, (
        f"Missing required legacy alias roots: {sorted(_REQUIRED_LEGACY_ROOTS - old_roots)!r}"
    )

    # Multiple aliases may intentionally point to the same canonical target.
    # Ensure no mapping is duplicated exactly.
    prefix_pairs = list(zip(old_prefixes, new_prefixes, strict=False))
    assert len(prefix_pairs) == len(set(prefix_pairs))

    canonical_cardinality = Counter(new_prefixes)
    assert canonical_cardinality[("run", "logs")] >= 3, (
        "Canonical target ('run', 'logs') must have at least 3 aliases (logs/orchestrate logs/observe logs)"
    )
    assert canonical_cardinality[("run", "stop")] >= 4, (
        "Canonical target ('run', 'stop') must have at least 4 aliases "
        "(stop/orchestrate stop/observe stop/recover stop)"
    )
    assert canonical_cardinality[("plan", "rollback")] == 1, (
        "Canonical target ('plan', 'rollback') must have exactly 1 alias (recover rollback)"
    )

    # If one old prefix is a prefix of another, longer prefix must appear first
    # so matching cannot be shadowed by a shorter entry.
    for i, left in enumerate(old_prefixes):
        for j, right in enumerate(old_prefixes):
            if i == j or len(left) >= len(right):
                continue
            if right[: len(left)] == left:
                assert i > j, (
                    f"Alias rewrite ordering shadow detected: shorter prefix {left!r} appears before longer {right!r}"
                )
