# Research

Repo surface detection:

- `pyproject.toml` identifies the Python workspace.
- `package.json` identifies the Bun/VitePress docs surface.
- `crates/Cargo.toml` identifies the Rust workspace.

Existing task patterns in the repo already map those surfaces to:

- `uv build`, `uv run pytest`, `uv run ruff check`
- `bun run docs:build`, `bun run docs:validate`, `bun run docs:links`
- `cargo build --workspace`, `cargo test --workspace`, `cargo fmt --check`, `cargo clippy`

Decision:

- Keep the task names common and stable.
- Detect the supported surfaces from the manifests instead of hardcoding a single language.
