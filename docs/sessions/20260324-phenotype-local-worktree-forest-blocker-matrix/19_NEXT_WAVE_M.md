# 19_NEXT_WAVE_M — next 25 items (Waves 1-8 sequence)

**Follows** `07`–`18`. **Snapshot:** 2026-03-24. **Intent:** Infrastructure & Cloud.

## Slice 1 — Infrastructure as Code (8)

1. **Terraform**: Audit `main.tf` and `provider.tf` in `infrakit`.
2. **Kubernetes**: Verify `helm` chart version consistency.
3. **Container**: Audit `Dockerfile` for multi-stage build size.
4. **Registry**: Verify `ghcr.io` or `docker.io` push permissions.
5. **Networks**: Audit `VPC` or `Security Group` rules.
6. **Storage**: Verify `S3` or `EBS` encryption at rest.
7. **Secrets**: Standardize `Vault` or `Parameter Store`.
8. **Logging**: Audit `CloudWatch` or `ELK` ingestion rules.

## Slice 2 — CI/CD & Automation (8)

9. **Matrix**: Optimize GHA `strategy.matrix` for parallelism.
10. **Cache**: Optimize `pnpm` or `bun` GHA caches.
11. **Self-hosted**: Audit `self-hosted` runner labels.
12. **Tokens**: Verify `GITHUB_TOKEN` least-privilege.
13. **Environments**: Standardize `stage`, `prod`, `qa`.
14. **Deploy**: Verify `blue-green` or `canary` rollout scripts.
15. **Notify**: Standardize `Slack` or `Discord` GHA alerts.
16. **Artifacts**: Verify `upload-artifact` retention policies.

## Slice 3 — Cloud Native & Scalability (8)

17. **Lambda**: Audit `serverless` or `sst` configurations.
18. **DynamoDB**: Verify `TTL` and `PITR` settings.
19. **Redis**: Audit `cluster` or `replication` settings.
20. **CDN**: Verify `CloudFront` or `Cloudflare` caching rules.
21. **DNS**: Audit `Route53` or `Cloudflare` record consistency.
22. **Auth0**: Verify `tenant` and `client` configuration.
23. **API GW**: Audit `throttling` and `usage-plans`.
24. **Observability**: Verify `OpenTelemetry` ingestion.

## Slice 4 — Meta (1)

25. **Task Update**: Record cloud findings in `05_KNOWN_ISSUES.md`.
