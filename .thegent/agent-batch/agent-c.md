# Agent-C Batch Status

## WL-115

- status: blocked
- done: authored implementation-ready benchmark plan slices
- files changed:
  - `docs/plans/WL-115-AGENT-C-BENCH-SLICE-PLAN.md`
- validation commands run:
  - `thegent plan next --format json` (result: `No ready tasks.`)

## WL-116

- status: in-progress
- done: added `--audio` plumbing and transcript-file ingestion slice (`.txt/.md`), surfaced `audio_transcript` in run payload
- files changed:
  - `src/thegent/agents/base.py`
  - `src/thegent/agents/audio_inputs.py`
  - `src/thegent/cli/apps/run.py`
  - `src/thegent/cli/commands/cli.py`
  - `src/thegent/cli/commands/impl.py`
  - `tests/test_wl116_audio_inputs.py`
  - `docs/plans/WL-116-AGENT-C-AUDIO-PASSTHROUGH-PLAN.md`
- validation commands run:
  - `python -m py_compile src/thegent/agents/audio_inputs.py src/thegent/routing/grounding.py src/thegent/doctor.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py` (pass)
  - `pytest -q tests/test_wl116_audio_inputs.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py` (blocked: missing plugin `pytest_asyncio`)

## WL-118

- status: in-progress
- done: added doctor runtime check for local Ollama endpoint reachability and model count reporting
- files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`
  - `docs/plans/WL-118-AGENT-C-OLLAMA-PROVIDER-PLAN.md`
- validation commands run:
  - `python -m py_compile src/thegent/agents/audio_inputs.py src/thegent/routing/grounding.py src/thegent/doctor.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py` (pass)
  - `pytest -q tests/test_wl116_audio_inputs.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py` (blocked: missing plugin `pytest_asyncio`)

## WL-119

- status: in-progress
- done: added `--google-grounding` plumbing, Gemini-only guardrail, and `grounding_sources` extraction slice
- files changed:
  - `src/thegent/agents/base.py`
  - `src/thegent/routing/grounding.py`
  - `src/thegent/cli/apps/run.py`
  - `src/thegent/cli/commands/cli.py`
  - `src/thegent/cli/commands/impl.py`
  - `tests/test_wl119_grounding_sources.py`
  - `docs/plans/WL-119-AGENT-C-GOOGLE-GROUNDING-PLAN.md`
- validation commands run:
  - `python -m py_compile src/thegent/agents/audio_inputs.py src/thegent/routing/grounding.py src/thegent/doctor.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py` (pass)
  - `pytest -q tests/test_wl116_audio_inputs.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py` (blocked: missing plugin `pytest_asyncio`)

## WL-120

- status: blocked
- done: authored phased implementation-ready plan for core boundary + runtime split program
- files changed:
  - `docs/plans/WL-120-AGENT-C-CORE-BOUNDARY-RUNTIME-SPLIT-PLAN.md`
- validation commands run:
  - `python -m py_compile src/thegent/agents/audio_inputs.py src/thegent/routing/grounding.py src/thegent/doctor.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py` (pass)

## do-next loop notes

- `thegent plan do-next --limit 20 --format json` -> command unavailable in current CLI (`plan next` is the replacement).
- `thegent plan next --format json` -> `No ready tasks.`
- `thegent plan work --format json --limit 200` -> import error (`workstream_list_cmd` missing).
