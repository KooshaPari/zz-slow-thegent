# External signals: ZDR, mesh VPN, secrets CI (2025–2026)

Curated **primary sources** for patterns aligned with Phenotype harness docs (ZDR posture, Tailscale/headscale, SOPS/age, GitHub OIDC → Vault, prose linting). DuckDuckGo HTML was **blocked** from this automation environment (anti-bot page); no reliance on unverifiable SEO snippets.

## Zero data retention (ZDR) — vendor-grounded

OpenAI documents **Zero Data Retention** and **Modified Abuse Monitoring** as **contractual / org-level** controls: eligible customers exclude customer content from abuse-monitoring logs; ZDR also forces `store` treated as `false` for `/v1/responses` and `/v1/chat/completions` even if a client sets `true`. Many endpoints remain **ZDR-ineligible** because they persist application state (Assistants, Threads, vector stores, some video paths, etc.). **Data residency** outside the US is tied to abuse-monitoring / ZDR amendments in their docs.

- Source: [OpenAI Platform — Data controls / Zero Data Retention](https://platform.openai.com/docs/guides/your-data)

**Factoring for your stack:** “We have ZDR on harnesses” is **provider-specific**. It justifies **not** treating OpenAI-route keys like generic long-lived SaaS passwords _when_ the org is actually on an approved ZDR/MAM project. It does **not** automatically apply to MiniMax, Anthropic, or self-hosted CLIProxy; each route needs its **own** DPA / dashboard / policy citation.

## Mesh VPN — implementation reality (2026)

**Tailscale** (hosted control plane): Official quickstart doc **last validated Jan 5, 2026** on their site. Covers tailnet creation, MagicDNS, ACLs/grants, subnet routers, exit nodes, SSH, logging. This is the low-ops default for AZ↔LA style use.

- Source: [Tailscale quickstart](https://tailscale.com/kb/1017/install-linux/) (see page header “Last validated”)

**headscale** (self-hosted control plane, WireGuard-compatible with Tailscale clients): Active OSS implementation; typical for “no Tailscale SaaS” requirements. Operational cost is yours (VM, upgrades, backups).

- Source: [headscale on GitHub](https://github.com/juanfont/headscale)

## Git-encrypted and CI secrets — implementations

**Mozilla SOPS** (encrypt YAML/JSON/ENV/INI; keys via age, PGP, KMS, Azure KV, **Vault Transit**, etc.): Official README describes **age as recommended over PGP**, `.sops.yaml` creation rules, stdin/stdout for pipelines, and **HashiCorp Vault transit** integration for encryption-at-rest of file keys.

- Source: [SOPS README (raw)](https://raw.githubusercontent.com/getsops/sops/master/README.rst)

**GitHub Actions OIDC**: GitHub’s own docs describe exchanging **short-lived** tokens with cloud providers (explicitly naming **HashiCorp Vault** among others), avoiding duplicated long-lived cloud secrets in `GITHUB_SECRET`.

- Source: [GitHub Docs — OpenID Connect](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

**Vault JWT/OIDC auth**: HashiCorp documents JWT verification (JWKS, discovery, bound claims, audiences). **Vault 1.17+**: if JWT has `aud`, role `bound_audiences` must match — relevant when wiring GitHub’s OIDC JWT.

- Source: [Vault — JWT/OIDC authentication](https://developer.hashicorp.com/vault/docs/auth/jwt)

## Prose / invariants (Vale, LSP-adjacent)

See the focused note (repo wiring + citations): [`LANGUAGE_INVARIANTS_AND_VALE_2026-03.md`](LANGUAGE_INVARIANTS_AND_VALE_2026-03.md).

**Vale 3** vocabularies: [Vocabularies](https://vale.sh/docs/topics/vocab/) under `StylesPath/config/vocabularies/`.

**Factoring:** Treat `CredentialRef::*` / `ModelRef::*` as **stable symbols**; render-time or CI **patch** steps substitute environment-specific values — same pattern as OpenAPI code generators and Helm `values.yaml`, not novel.

## Cross-check summary

| Claim                                                              | Independent lines               |
| ------------------------------------------------------------------ | ------------------------------- |
| ZDR reduces retained **customer content** in OpenAI API abuse logs | OpenAI data-controls doc        |
| OIDC reduces long-lived **GitHub↔cloud** secrets                  | GitHub OIDC doc + Vault JWT doc |
| SOPS+age is a **standard** git-friendly encrypted-file workflow    | SOPS upstream README            |
| Tailscale **mesh** is actively maintained (2026 validation stamp)  | Tailscale KB page metadata      |

## Gaps (honest)

- **MiniMax-specific** retention / ZDR-equivalent: use **their** current legal + console docs, not OpenAI’s.
- **Blog opinion** pieces omitted unless they cite primary sources; prefer vendor and project READMEs above.
