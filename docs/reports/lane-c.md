# Worklog Lane C — Thread Corpus (Wave)

## 1) CLIP-BUG-03 — Nullable type arrays rejected with 400

- **Source URL:** [CLIProxyAPI#1513](https://github.com/router-for-me/CLIProxyAPI/issues/1513)
- **Recommendation:** adopt
- **Next-action:** Add a schema normalizer for nullable list types in tool conversion and add golden fixtures for `nullable` array paths.

## 2) CLIP-BUG-04 — Claude to Gemini translation fails on unsupported JSON Schema fields

- **Source URL:** [CLIProxyAPI#1424](https://github.com/router-for-me/CLIProxyAPI/issues/1424)
- **Recommendation:** adopt
- **Next-action:** Filter/strip non-compatible JSON Schema keys (`$id`, `patternProperties`) during Claude→Gemini payload translation and add a regression test.

## 3) CLIP-BUG-05 — `metadata` field injection into `contents[]` breaks Gemini

- **Source URL:** [CLIProxyAPI#1477](https://github.com/router-for-me/CLIProxyAPI/issues/1477)
- **Recommendation:** watch
- **Next-action:** Trace metadata propagation through provider serializers and add a focused test ensuring only provider-compatible metadata is sent.

## 4) CLIP-BUG-11 — INVALID_ARGUMENT with antigravity Claude Opus-4

- **Source URL:** [CLIProxyAPI#1535](https://github.com/router-for-me/CLIProxyAPI/issues/1535)
- **Recommendation:** adopt
- **Next-action:** Reproduce with captured Antigravity/Opus-4 payloads and patch param translation to preserve required request envelope fields.

## 5) CLIP-BUG-12 — `tool_choice.name` prefix mismatch while `tools[].name` is unprefixed

- **Source URL:** [CLIProxyAPI#1530](https://github.com/router-for-me/CLIProxyAPI/issues/1530)
- **Recommendation:** avoid-hype
- **Next-action:** Apply a minimal fix to align only this naming path and verify behavior with a targeted OAuth request contract test.
