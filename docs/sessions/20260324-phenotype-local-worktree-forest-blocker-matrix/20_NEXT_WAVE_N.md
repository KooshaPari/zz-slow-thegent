# 20_NEXT_WAVE_N — next 25 items (Waves 1-8 sequence)

**Follows** `07`–`19`. **Snapshot:** 2026-03-24. **Intent:** AI & Data.

## Slice 1 — AI Engineering & Prompting (8)

1. **Prompts**: Audit `.prompt` or `.txt` templates.
2. **Context**: Verify `window-size` and `token-count` limits.
3. **Provider**: Standardize `Anthropic`, `OpenAI`, `Google` APIs.
4. **Retry**: Verify `exponential-backoff` for rate limits.
5. **Fallbacks**: Implement `Claude -> GPT` or `Haiku -> Opus` failover.
6. **Hallucination**: Audit `temperature` and `top_p` settings.
7. **Embeddings**: Verify `vector-store` (Pinecone/Milvus) indexing.
8. **Evaluation**: Create a `prompt-eval` or `benchmark` suite.

## Slice 2 — Data Engineering & Storage (8)

9. **SQL**: Audit `migrations/` in `contracts` or `thegent`.
10. **ORM**: Verify `drizzle` or `prisma` schema consistency.
11. **Cache**: Optimize `redis` or `valkey` key eviction.
12. **Streams**: Audit `kafka` or `rabbitmq` message TTL.
13. **Parquet**: Verify `data-lake` or `warehouse` file formats.
14. **Ingestion**: Audit `ETL` or `ELT` job success rates.
15. **Integrity**: Verify `checksum` or `hash` for all stored data.
16. **Backup**: Test `SQL` dump and restore procedure.

## Slice 3 — Model Performance & Costs (8)

17. **Latency**: Audit P50/P95 for all AI inference calls.
18. **Cost**: Implement `token-usage` and `billing` alerts.
19. **Metrics**: Standardize `langsmith` or `wandb` tracking.
20. **Tuning**: Audit `fine-tuning` dataset preparation.
21. **Quantization**: Verify `gguf` or `mlx` model performance.
22. **Parallelism**: Audit `async` prompt execution pools.
23. **Throttle**: Implement `client-side` rate limiting.
24. **Safety**: Verify `moderation-api` or `filter` usage.

## Slice 4 — Meta (1)

25. **Task Update**: Record AI findings in `05_KNOWN_ISSUES.md`.
