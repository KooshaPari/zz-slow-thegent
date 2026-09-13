# G2 chokepoint audit — thegent (2026-06-17)

**Wave:** G2  
**Chokepoint ID:** `thegent`  
**Blocks sources:** AuthKit, BytePort  
**Repoint targets:** Authvault, phenotype-tooling

## Manifest audit

Scanned all `Cargo.toml` and `pyproject.toml` files under `archive-migration/thegent-fresh`.

| Pattern           | Matches |
| ----------------- | ------- |
| HexaKit           | none    |
| AuthKit           | none    |
| Traceon           | none    |
| stashly / Stashly | none    |

## Findings

- Root `pyproject.toml` depends on `phenotype-py-utils` (git) — already canonical tooling, not a G2 block.
- No Rust workspace manifests reference AuthKit or BytePort git deps.
- **Status:** verified-clean — no manifest repoint required in this lane.

## Follow-up

If AuthKit/BytePort surface via generated imports or submodule paths later, repoint to
Authvault / phenotype-tooling per [DOMAIN_ROLES](https://github.com/KooshaPari/phenotype-registry/blob/main/docs/rationalization/DOMAIN_ROLES.md).
