# Canonical invariant prose (credentials, patches, and review hooks)

Use this vocabulary so documentation and agent-facing prose stay **stable under substitution**: CI, Vale, AI-LSP, and human review patch **CredentialRef** and **ModelRef** tokens instead of hand-typing sensitive or volatile strings.

## ZDR and harness policy

When **zero data retention (ZDR)** is enabled on provider harnesses, org policy may **not** require periodic credential rotation for those routes. Docs should say **ZDR applies** rather than implying universal rotation. Non-ZDR routes (third-party SaaS, long-lived tokens) keep their own policy.

## Core tokens (write these in specs and runbooks)

| Token                            | Meaning                                                                        | Resolved by                                            |
| -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------ |
| `CredentialRef::MINIMAX_BYOK`    | MiniMax bring-your-own key used for Anthropic- and OpenAI-compatible endpoints | Factory `custom_models` / env `MINIMAX_API_KEY` / SOPS |
| `CredentialRef::CLIPROXY_DUMMY`  | Placeholder key when CLIProxy authenticates upstream                           | literal `dummy-not-used` where applicable              |
| `ModelRef::MINIMAX_M27_HS`       | Default high-speed MiniMax model id                                            | `minimax-m2.7-highspeed` unless catalog differs        |
| `EndpointRef::MINIMAX_ANTHROPIC` | Anthropic-compatible base URL                                                  | `https://api.minimax.io/anthropic`                     |
| `EndpointRef::MINIMAX_OPENAI`    | OpenAI-compatible base URL                                                     | `https://api.minimax.io/v1`                            |
| `EndpointRef::CLIPROXY_V1`       | Local adapter + proxy                                                          | `http://127.0.0.1:8317/v1`                             |

In **Markdown**, prefer backticked tokens, e.g. `` `CredentialRef::MINIMAX_BYOK` ``, so Vale and search can treat them as proper nouns.

## Avoid ambiguous words in invariant layers

- Prefer **credential material** or **`CredentialRef::*`** over colloquial **“secret”** in architecture specs and governance docs where the goal is a patchable field.
- Prefer **provider key** or **BYOK slot** over **“API key”** when describing Factory: Factory **does not mint** keys; it stores **BYOK** values you supply.

## Vale

Repo vocabulary file: [`docs/reference/vale/Vocab/phenotype/accept.txt`](vale/Vocab/phenotype/accept.txt). Wire it from project `.vale.ini` / `StylesPath`, or copy into your global Vale vocab.

- `CredentialRef`
- `ModelRef`
- `EndpointRef`
- `BYOK`
- `ZDR`
- `CLIProxy`

Map deprecated phrasing with a **substitution** style (optional custom Vale rule): suggest replacing “rotate all secrets” with “review credential policy (ZDR vs retention)” when `ZDR` appears in the same document.

## AI-LSP / structured doc tooling

Treat invariant lines as **LSP symbols** or **code references** where supported:

- Document headings that define `CredentialRef::*` once; link other sections to the symbol.
- For generated docs, run a **patch step** that replaces tokens with values from `manifest.json` (or CI env) so rendered HTML never contains raw credential material unless explicitly a private deploy job.

## FOL-style invariants (lightweight pattern)

When writing formal-ish requirements:

- Use predicates like `HasCredential(MinimaxByok)` instead of “user has a secret”.
- Use `ModelId(x) = ModelRef::MINIMAX_M27_HS` instead of repeating the literal model string in every clause.

## Factory JSON

`repos/.factory/*.json` holds **BYOK** entries for MiniMax. **GLM / Z.ai** entries are removed from the canonical repo copy as unused. Sync your user-level `~/.factory` if you still have stale GLM blocks.
