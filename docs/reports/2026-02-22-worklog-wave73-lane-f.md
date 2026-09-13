# Worklog Wave 73 Lane F

Date: 2026-02-22

## Items

1. **CLIP-BUG-03 — Nullable type arrays rejected with 400**

- **Source:** [CLIProxyAPI#1513](https://github.com/router-for-me/CLIProxyAPI/issues/1513)
- **Recommendation:** adopt
- **Action:** Add a schema normalizer for nullable list types in tool conversion and add golden fixtures for `nullable` array paths.
- **Confidence:** high

2. **CLIP-BUG-04 — Claude to Gemini translation fails on unsupported JSON Schema fields**

- **Source:** [CLIProxyAPI#1424](https://github.com/router-for-me/CLIProxyAPI/issues/1424)
- **Recommendation:** adopt
- **Action:** Filter/strip non-compatible JSON Schema keys (`$id`, `patternProperties`) during Claude→Gemini payload translation and add a regression test.
- **Confidence:** high

3. **CLIP-BUG-05 — `metadata` field injection into `contents[]` breaks Gemini**

- **Source:** [CLIProxyAPI#1477](https://github.com/router-for-me/CLIProxyAPI/issues/1477)
- **Recommendation:** watch
- **Action:** Trace metadata propagation through provider serializers and add a focused test ensuring only provider-compatible metadata is sent.
- **Confidence:** medium

4. **CLIP-BUG-11 — INVALID_ARGUMENT with antigravity Claude Opus-4**

- **Source:** [CLIProxyAPI#1535](https://github.com/router-for-me/CLIProxyAPI/issues/1535)
- **Recommendation:** adopt
- **Action:** Reproduce with captured Antigravity/Opus-4 payloads and patch param translation to preserve required request envelope fields.
- **Confidence:** high

5. **CLIP-BUG-12 — `tool_choice.name` prefix mismatch while `tools[].name` is unprefixed**

- **Source:** [CLIProxyAPI#1530](https://github.com/router-for-me/CLIProxyAPI/issues/1530)
- **Recommendation:** avoid-hype
- **Action:** Apply a minimal fix to align only this naming path and verify behavior with a targeted OAuth request contract test.
- **Confidence:** medium
