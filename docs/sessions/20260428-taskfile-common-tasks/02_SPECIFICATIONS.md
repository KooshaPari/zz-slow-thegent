# Specifications

The root task runner should provide:

- `build`: build every detected project surface.
- `test`: run the test commands for every detected project surface.
- `lint`: run the lint commands for every detected project surface.
- `clean`: remove generated caches and build artifacts.

Behavioral constraints:

- If a surface is missing, skip it silently.
- If no supported surface is found, fail with a clear error.
- Preserve existing repo-specific tasks below the common task surface.
