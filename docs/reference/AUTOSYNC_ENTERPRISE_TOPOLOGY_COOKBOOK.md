# Autosync Enterprise Topology Cookbook

## Purpose

Reference deployment patterns for autosync in enterprise environments.

## Topology A: Single Team, Single Project

- Use case: initial adoption, low complexity.
- Components: one local workstream, one GitHub project, one Linear team.
- Notes: fastest path; minimal conflict surface.

## Topology B: Multi-Team Shared Platform

- Use case: multiple feature teams sharing governance baseline.
- Components: per-team project registry entries + shared policy pack.
- Notes: enforce ownership metadata and per-team auth boundaries.

## Topology C: Hub-and-Spoke Program

- Use case: central platform team with many product teams.
- Components: central governance controls + team-level connector mappings.
- Notes: require strict conflict TTL/escalation and incident snapshots.

## Topology D: Regulated Environment

- Use case: compliance-heavy workflows.
- Components: immutable cycle manifests, artifact redaction, audit log retention.
- Notes: prioritize reproducibility and restore verification over throughput.

## Topology E: Staged Rollout (Recommended Default)

- Use case: safe enterprise onboarding.
- Components: observe-only/shadow mode -> limited write mode -> full mode.
- Notes: advance stages only when reliability and conflict metrics are stable.

## Pattern Selection Guide

- Choose A for pilot.
- Move to E for structured expansion.
- Use B or C depending on team autonomy model.
- Use D when compliance or legal requirements dominate.
