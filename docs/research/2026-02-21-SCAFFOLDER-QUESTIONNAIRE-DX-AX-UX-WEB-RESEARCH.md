<DONE>
# Scaffolder Questionnaire DX/AX/UX Web Research

Date: 2026-02-21
Status: Completed
Owner: thegent
Tags: [research, scaffolding, copier, questionnaire, dx, ax, ux]

## Objective

Define a high-signal project initialization questionnaire and instruction template strategy that is:

1. expressive enough for polyglot/project-type differences,
2. strict enough to prevent invalid defaults,
3. lightweight enough for fast setup.

## Primary Sources

1. Copier configuration and question model (`choices`, `multiselect`, `when`, `validator`, defaults):
   https://copier.readthedocs.io/en/stable/configuring/
2. Cookiecutter prompt customization patterns (human-readable prompts):
   https://cookiecutter.readthedocs.io/en/stable/advanced/human_readable_prompts.html
3. Backstage software template parameter modeling (structured parameters, composition):
   https://backstage.io/docs/features/software-templates/writing-templates/
4. CLI design baseline (human-first command/interface design):
   https://clig.dev/
5. GOV.UK guidance for asking for information (progressive disclosure, clarity):
   https://design-system.service.gov.uk/patterns/
6. USWDS form guidance (label/help/error clarity):
   https://designsystem.digital.gov/components/form/
7. Twelve-Factor config principle (config in environment, deploy portability):
   https://12factor.net/config

## Findings Applied

1. Enforce validity at prompt-time: encode constraints in `validator` so incompatible choices fail before generation.
2. Use progressive disclosure: ask core profile questions first, then conditional questions (`when`) to reduce noise.
3. Keep defaults operationally safe: default project shape should be production-credible (`service_api`, `strict`, telemetry present).
4. Generate instruction artifacts from selected profile to avoid re-asking context in downstream tasks.
5. Keep one canonical questionnaire path (Copier) and remove mixed templating conventions.

## Decisions

1. Standardize on Copier-native templating syntax and directory expressions.
2. Add project-shape fields: `project_type`, `runtime_profile`, `governance_mode`, `observability_stack`, `deployment_target`, `interfaces`, `quality_profile`, `questionnaire_summary_hints`.
3. Add validation coupling between fields (for example strict governance cannot pair with fast-iterate quality).
4. Inject questionnaire snapshot and DX/AX/UX contracts into generated project `CLAUDE.md`.

## Validation Evidence

1. `uvx copier --version` -> Copier available.
2. `uvx copier copy --defaults templates/initialize-project <tmpdir>` -> successful render.
3. Rendered output confirms path and template variable expansion for `my-project/CLAUDE.md`.
