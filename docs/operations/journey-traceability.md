# Journey Traceability

`thegent` is a governance and bootstrap hub, so user-facing flows should carry
journey evidence just like product repos do.

## What to capture

- keyframes for the important state changes in a flow
- a recording for the full end-to-end interaction
- a stable manifest or artifact path for the journey
- links back to the spec, workstream, or operational task

## Shared Phenotype standard

The canonical org-wide standard lives in:

- [phenotype-infra journey-traceability standard](https://github.com/kooshapari/phenotype-infra/blob/main/docs/governance/journey-traceability-standard.md)

## thegent-specific use

Capture journeys for:

- bootstrap and install flows
- governance and policy gates
- agent orchestration and dispatch flows
- docs and template generation paths

## Rule of thumb

If a flow is important enough to document, it is important enough to capture
with a keyframe gallery and a replayable recording.

---

## Journey Manifest Schema

All journey manifests follow this schema:

```yaml
journey:
  id: string (unique identifier)
  title: string
  description: string
  version: semver
  repository: owner/repo
  branch: string
  created: ISO8601 timestamp
  updated: ISO8601 timestamp
  owner: GitHub handle
  tags: [string]

flow:
  name: string
  category: bootstrap|governance|orchestration|generation
  steps:
    - id: step-001
      name: string
      description: string
      keyframes: [path]
      assertions: [assertion]
      annotation_required: boolean

assets:
  keyframes: [path]
  recording: path (placeholder)
  screenshots: [path]
  video: path (placeholder)

ci_gate:
  enabled: boolean
  workflow: path
  assertion_mode: strict|lenient
  blocking: boolean

metadata:
  spec_reference: URL
  work_package: string
  evidence_ledger: URL
```

## Annotations

Each journey step annotation must include:

- **Step ID**: Unique identifier matching manifest
- **Timestamp**: When the annotation was created
- **Actor**: GitHub handle or system identity
- **Evidence type**: screenshot|video|log|artifact
- **Content**: Link to or embedded evidence
- **Assertions**: Verification results for this step
- **Agreement**: Sign-off status and approvers

### Annotation Requirements

| Evidence Type | Required Fields                     | Format   |
| ------------- | ----------------------------------- | -------- |
| screenshot    | timestamp, actor, step_id, path     | PNG/WebP |
| video         | timestamp, actor, flow_id, duration | MP4/WebM |
| log           | timestamp, actor, step_id, level    | JSONL    |
| artifact      | timestamp, actor, step_id, type     | varies   |

## Assertions

Assertions validate journey completion:

```yaml
assertions:
  - type: screenshot_present
    step_id: step-001
    required: true
  - type: no_error_logs
    step_id: step-002
    required: true
  - type: keyframe_sequence
    steps: [step-001, step-002, step-003]
    required: true
  - type: ci_passed
    workflow: journey-gate.yml
    required: true
```

### Assertion Types

| Type                 | Description                    | Mode    |
| -------------------- | ------------------------------ | ------- |
| `screenshot_present` | SS exists for step             | strict  |
| `no_error_logs`      | Zero ERROR entries in logs     | strict  |
| `keyframe_sequence`  | Ordered keyframe chain         | strict  |
| `ci_passed`          | Journey gate workflow succeeds | strict  |
| `video_duration`     | Recording meets minimum length | lenient |
| `artifact_complete`  | All artifacts linked           | lenient |

## Agreement

Journeys require explicit sign-off:

```yaml
agreement:
  status: draft|pending_review|approved|rejected
  reviewers:
    - handle: string
      role: owner|reviewer|approver
      status: pending|approved|rejected
      timestamp: ISO8601
  blockers: [string]
  notes: string
```

## Verification Modes

| Mode      | Behavior                                            |
| --------- | --------------------------------------------------- |
| `strict`  | All required assertions must pass; blocking failure |
| `lenient` | Failures logged but don't block; advisory only      |
| `gate`    | Full CI gate; blocks merge until all pass           |

## Asset Layout

```
journeys/
├── manifests/
│   ├── bootstrap-flow.journey.yaml
│   ├── plugin-onboarding.journey.yaml
│   ├── agent-dispatch.journey.yaml
│   ├── governance-gate.journey.yaml
│   └── template-generation.journey.yaml
├── keyframes/
│   ├── bootstrap-flow/
│   │   ├── step-001-init.png
│   │   ├── step-002-config.png
│   │   └── step-003-ready.png
│   └── ...
├── recordings/
│   ├── bootstrap-flow.mp4
│   └── ...
└── assertions/
    ├── bootstrap-flow.jsonl
    └── ...
```

## CI Gate

The journey-gate.yml workflow validates manifests:

```yaml
name: Journey Gate

on:
  push:
    branches: [feat/*]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate manifests
        run: |
          for manifest in journeys/manifests/*.yaml; do
            # Validate schema, assertions, keyframes
          done
      - name: Generate report
        run: |
          # Generate JSON report
      - name: Post comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            // Post results as PR comment
```

## Screenshot & Video Placeholder Policy

| Asset                     | Status      | Location                                            | Notes        |
| ------------------------- | ----------- | --------------------------------------------------- | ------------ |
| Bootstrap Flow SS         | PLACEHOLDER | `docs/assets/journeys/placeholder.png`              | TODO: Record |
| Bootstrap Flow Video      | PLACEHOLDER | `cli-journeys/recordings/bootstrap-placeholder.mp4` | TODO: Record |
| Plugin Onboarding SS      | PLACEHOLDER | `docs/assets/journeys/placeholder.png`              | TODO: Record |
| Plugin Onboarding Video   | PLACEHOLDER | `cli-journeys/recordings/plugin-placeholder.mp4`    | TODO: Record |
| Agent Dispatch SS         | PLACEHOLDER | `docs/assets/journeys/placeholder.png`              | TODO: Record |
| Agent Dispatch Video      | PLACEHOLDER | `cli-journeys/recordings/dispatch-placeholder.mp4`  | TODO: Record |
| Governance Gate SS        | PLACEHOLDER | `docs/assets/journeys/placeholder.png`              | TODO: Record |
| Governance Gate Video     | PLACEHOLDER | `cli-journeys/recordings/gate-placeholder.mp4`      | TODO: Record |
| Template Generation SS    | PLACEHOLDER | `docs/assets/journeys/placeholder.png`              | TODO: Record |
| Template Generation Video | PLACEHOLDER | `cli-journeys/recordings/template-placeholder.mp4`  | TODO: Record |

## Video Requirements

| Journey             | Min Duration | Max Duration | Format | Codec |
| ------------------- | ------------ | ------------ | ------ | ----- |
| bootstrap-flow      | 30s          | 120s         | MP4    | h264  |
| plugin-onboarding   | 60s          | 180s         | MP4    | h264  |
| agent-dispatch      | 30s          | 120s         | MP4    | h264  |
| governance-gate     | 30s          | 90s          | MP4    | h264  |
| template-generation | 30s          | 120s         | MP4    | h264  |

Videos must:

- Include timestamp overlay (bottom-right)
- Show full step sequence without cuts
- Have clear audio narration (optional)
- Be under 50MB for storage efficiency
