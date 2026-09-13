<DONE>
# Context & Memory Management Strategies Research

Research gathered: 2026-02-21
Comprehensive taxonomy based on cognitive science + production systems.

---

## 1. Memory Taxonomy (Cognitive Science Mapping)

Based on research from Oracle, Redis, MongoDB, Tacnode, and academic papers:

### 1.1 Short-Term / Working Memory

| Type               | Description                 | Storage            | thegent Equivalent      |
| ------------------ | --------------------------- | ------------------ | ----------------------- |
| **Working Memory** | Active manipulation of info | RAM/context window | Current session context |
| **Semantic Cache** | Recent query-response pairs | Fast cache         | `PromptQueueManager`    |
| **Shared Memory**  | Multi-agent workspace       | Temp storage       | Orchestration state     |

### 1.2 Long-Term Memory

| Type                  | Description                             | Storage        | thegent Equivalent    |
| --------------------- | --------------------------------------- | -------------- | --------------------- |
| **Episodic Memory**   | Time-stamped experiences, conversations | SQLite + FTS   | `UnifiedSessionIndex` |
| **Semantic Memory**   | Facts, knowledge, preferences           | Vector DB + KG | Future: embeddings    |
| **Procedural Memory** | Skills, workflows, how-to               | Structured DB  | `skills/`, hooks      |
| **State Memory**      | Current conditions, authoritative data  | Mutable state  | `run_registry.jsonl`  |

---

## 2. Key Architectural Patterns

### 2.1 Three-Layer Production Architecture (Tacnode)

```
┌─────────────────────────────────────────────────┐
│           STATE MEMORY (Mutable)              │
│  Current conditions, authoritative data       │
│  - run_registry.jsonl                     │
│  - ConcurrencyController state              │
├─────────────────────────────────────────────────┤
│        EPISODIC MEMORY (Immutable)         │
│  Time-stamped interactions                 │
│  - SessionIndex (SQLite)                 │
│  - governance_events.jsonl                 │
├─────────────────────────────────────────────────┤
│       SEMANTIC MEMORY (Learned)            │
│  Patterns, embeddings, knowledge          │
│  - Future: vector store                  │
│  - EvidenceStore (hash-chain)            │
└─────────────────────────────────────────────────┘
```

### 2.2 ENGRAM Pattern (arxiv 2511.12960)

- **Single router + retriever** for all memory types
- Converts interactions → structured records
- Set operations for retrieval
- **Performance**: ~1% tokens vs full context, SOTA on LoCoMo

### 2.3 MAPLE Architecture (arxiv 2602.13258)

Three sub-agents, independently optimized:

1. **Memory sub-agent**: Storage/retrieval
2. **Learning sub-agent**: Async insight extraction
3. **Personalization sub-agent**: Real-time adaptation

- **Result**: 14.6% personalization improvement

### 2.4 MemoriesDB (PostgreSQL + pgvector)

- Temporal-semantic-relational graph
- Mememory = vertex with timestamp + embedding
- Supports temporal queries + graph traversal

### 2.5 AgentFold (arxiv 2510.24699)

- **Proactive context folding** - not reactive
- Multi-scale condensation: granular → abstract
- Inspired by human cognitive processes

---

## 3. Retrieval Strategies

### 3.1 Hybrid Search (BM25 + Semantic)

| Phase | Method               | Purpose                          |
| ----- | -------------------- | -------------------------------- |
| 1     | BM25 FTS5            | Keyword precision, exact matches |
| 2     | Semantic embedding   | Contextual similarity            |
| 3     | Cross-encoder rerank | Final top-k precision            |

### 3.2 Two-Stage Retrieval

- **Stage 1**: Broad recall (20-100 candidates)
- **Stage 2**: Rerank to top-k

### 3.3 Strategic Context Ordering

- Place most relevant at start AND end
- Mitigates "lost in middle" problem

### 3.4 Query Decomposition (Damocles)

- Decompose prompt into 1-4 facets
- Run separate BM25 query per facet
- Deduplicate + merge results

---

## 4. Chunking Strategies

| Strategy           | Method                            | Best For              |
| ------------------ | --------------------------------- | --------------------- |
| **Recursive**      | Split by chars, then semantically | General text          |
| **Semantic**       | LLM identifies breakpoints        | Code, structured docs |
| **Page-level**     | Whole pages                       | Reference docs        |
| **Sentence**       | Per-sentence                      | Fine-grained          |
| **Function/Class** | Code boundaries                   | Code retrieval        |

**Recommended for code**: Semantic chunking on function/class boundaries

---

## 5. thegent Current State vs. Gap Analysis

| Memory Type | Current Implementation         | Gap                  |
| ----------- | ------------------------------ | -------------------- |
| Working     | `run_context`, context window  | ✅                   |
| Episodic    | `UnifiedSessionIndex` (SQLite) | Need BM25 FTS5       |
| Semantic    | `EvidenceStore` (hash-chain)   | Need vector store    |
| Procedural  | `skills/`, hooks               | ✅                   |
| State       | `run_registry.jsonl`           | Need semantic search |

---

## 6. Implementation Roadmap

### Phase 1: Enhanced Episodic (P1)

- [ ] Add BM25 FTS5 to `UnifiedSessionIndex`
- [ ] Query decomposition for multi-topic prompts
- [ ] Context budget injection (4k tokens)

### Phase 2: Semantic Layer (P2)

- [ ] Add embeddings for session summaries
- [ ] Hybrid search (BM25 + semantic)
- [ ] Reranking pipeline

### Phase 3: Procedural Memory (P3)

- [ ] Skill/hook memory system
- [ ] Learn from successful patterns

### Phase 4: State Memory (P4)

- [ ] Real-time state injection
- [ ] Multi-agent shared memory

---

## 7. Key Sources

- Oracle: "Agent Memory: Why Your AI Has Amnesia"
- Redis: "AI Agent Architecture: Build Systems That Work in 2026"
- Tacnode: "AI Agent Memory Architecture: The Three Layers"
- MongoDB: "What Is Agent Memory?"
- arxiv: ENGRAM (2511.12960), AgentFold (2510.24699), MemoriesDB (2511.06179), MAPLE (2602.13258)
- Reddit: Damocles VS Code extension (BM25 + SQLite pattern)
- Firecrawl/Weaviate: 2025 RAG chunking guides
- Factory.ai: "Evaluating Context Compression for AI Agents"
- Medium: "Context Engineering: 6 Techniques That Actually Matter"
- OneUptime: "How to Build Context Compression"
- Redis: "LLM Token Optimization"
- JetBrains: "Cutting Through the Noise: Smarter Context Management"
- arxiv: Semantic-Anchor Compression (2510.08907), GistPool, Activation Beacon
- arxiv: Dr.LLM (2510.12773), DTRNet (2509.00925), SEAL (2501.15225)
- NeurIPS 2025: Gated Attention

---

## 14. Harness-Specific Patterns

### 14.1 Claude Code Patterns

| Technique              | Command   | Description                                  |
| ---------------------- | --------- | -------------------------------------------- |
| **CLAUDE.md**          | N/A       | Persistent project context file at repo root |
| **/compact**           | Slash cmd | Compress conversation, keep key info         |
| **/clear**             | Slash cmd | Reset conversation history                   |
| **Status bar**         | N/A       | Token % indicator                            |
| **Auto-compact**       | N/A       | Triggered at 80% capacity                    |
| **Subagents**          | Slash cmd | Isolated context windows                     |
| **MCP isolation**      | Slash cmd | Separate agents per MCP tool                 |
| **CLAUDE.md sections** | File      | PROJECT, CODEBASE, APPROACH, STATUS          |

**Key learnings:**

- 200K token limit, compaction loses detail
- CLAUDE.md persists across sessions
- 80/20 rule: don't use last 20% for complex tasks
- `.claudeignore` for file exclusion

### 14.2 Codex CLI Patterns

| Technique                  | Command  | Description             |
| -------------------------- | -------- | ----------------------- |
| **AGENTS.md**              | N/A      | Global prompt config    |
| **codex resume**           | CLI      | Resume previous session |
| **--profile**              | Flag     | Switch config profiles  |
| **model_reasoning_effort** | Config   | Adjust depth            |
| **shell shortcuts**        | Shell rc | Aliases for flags       |
| **exec mode**              | N/A      | Non-interactive batch   |

**Key learnings:**

- `~/.codex/config.toml` for defaults
- Session persistence via cloud
- Reasoning depth affects context

### 14.3 OpenCode Patterns

| Technique           | Command | Description                                 |
| ------------------- | ------- | ------------------------------------------- |
| **--continue/-c**   | CLI     | Resume last session                         |
| **--session/-s**    | CLI     | Resume specific session                     |
| **--fork**          | CLI     | Fork session                                |
| **Agent modes**     | Config  | COLLABORATE, HANDOFF, COMPRESS, PARALLELIZE |
| **tmux-resurrect**  | Plugin  | Save/restore sessions                       |
| **Dynamic pruning** | Plugin  | Auto-context optimization                   |

**Key learnings:**

- Multiple provider support (75+)
- Event-driven session architecture
- Remote backend via `attach`

---

## 15. Common Patterns Across Harnesses

### 15.1 Persistent Context Files

| Harness     | File        | Scope        |
| ----------- | ----------- | ------------ |
| Claude Code | `CLAUDE.md` | Project      |
| Codex       | `AGENTS.md` | Global       |
| OpenCode    | N/A         | Config-based |

### 15.2 Session Commands

| Operation | Claude     | Codex          | OpenCode    |
| --------- | ---------- | -------------- | ----------- |
| Resume    | `/resume`  | `codex resume` | `-c`        |
| Clear     | `/clear`   | N/A            | New session |
| Compact   | `/compact` | N/A            | Auto        |
| Fork      | N/A        | N/A            | `--fork`    |

### 15.3 Best Practices

1. **Front-load critical info** - Put important context at start
2. **Use dedicated files** - CLAUDE.md, AGENTS.md for persistence
3. **Monitor token %** - Stop at 70-80% before auto-compact
4. **Split sessions** - Separate contexts for separate tasks
5. **Manual checkpoints** - Save progress before compact
6. **File references** - Use `@file` instead of full content

---

## 16. thegent Integration Opportunities

| Pattern                 | Harness        | Implementation                    |
| ----------------------- | -------------- | --------------------------------- |
| Persistent context file | All            | `CLAUDE.md` / `AGENTS.md` pattern |
| Session resume          | Codex/OpenCode | `session resume` command          |
| Compact/compress        | Claude         | `/compact` equivalent             |
| Token monitoring        | OpenCode       | Real-time tracking                |
| Subagent isolation      | Claude         | MCP-based isolation               |
| Dynamic pruning         | OpenCode       | Plugin integration                |

---

## 8. Compression Techniques

### 8.1 Extraction-Based

| Technique               | Description                | Ratio        | Quality |
| ----------------------- | -------------------------- | ------------ | ------- |
| **Relevance Filtering** | Keep only pertinent info   | 50-80%       | High    |
| **Redundancy Removal**  | Dedupe repeated content    | Variable     | High    |
| **Sentence Pruning**    | Remove low-value sentences | 30-50%       | Medium  |
| **Truncation**          | Cut at token limit         | Configurable | Low     |

### 8.2 Summarization-Based

| Technique                     | Description             | Ratio     | Quality   |
| ----------------------------- | ----------------------- | --------- | --------- |
| **Extractive Summarization**  | Key sentences only      | 50-70%    | High      |
| **Abstractive Summarization** | LLM rewrite             | 60-90%    | High      |
| **Structured Summarization**  | Entity-relation format  | 40-60%    | Very High |
| **Gisting**                   | Compress to gist tokens | Up to 10x | Medium    |

### 8.3 Advanced Compression

| Technique                             | Description                        | Benefit            |
| ------------------------------------- | ---------------------------------- | ------------------ |
| **Semantic-Anchor Compression (SAC)** | Select anchor tokens, aggregate KV | No training needed |
| **Activation Beacon**                 | Compress activations per layer     | 8x KV reduction    |
| **GistPool**                          | Learnable pooling for long context | Better long-range  |
| **Token Pruning**                     | Remove low-importance tokens       | 2-4x speedup       |

### 8.4 Factory.ai Probe Evaluation

Structured summarization outperforms generic methods. Probes measure:

- **Recall**: Factual retention (errors, outputs)
- **Artifact**: File tracking (modified files)
- **Continuation**: Task planning (next steps)
- **Decision**: Reasoning chain retention

---

## 9. Attention-Based Optimization

### 9.1 Dynamic Routing

| Technique                  | Description                           | Benefit          |
| -------------------------- | ------------------------------------- | ---------------- |
| **Dr.LLM**                 | Per-layer routers decide skip/execute | 5 layers saved   |
| **DTRNet**                 | Route 10% tokens through attention    | Quadratic→linear |
| **Mixture-of-Depth (MoD)** | Skip layers for simple tasks          | Speedup          |

### 9.2 Selective Attention

| Technique                     | Description                            |
| ----------------------------- | -------------------------------------- |
| **SEAL**                      | Identify attention heads for retrieval |
| **Gated Attention**           | Filter attention dynamically           |
| **Attention Sink Mitigation** | Reduce position bias                   |

---

## 10. Token Optimization Patterns

### 10.1 Input Optimization

| Pattern                     | Description                     |
| --------------------------- | ------------------------------- |
| **Structured Prompting**    | JSON/bullet formats are concise |
| **Instruction Referencing** | Reference predefined templates  |
| **Template Abstraction**    | Reusable prompt templates       |
| **Relevance Filtering**     | Only include pertinent context  |

### 10.2 Context Budget

| Strategy                | Implementation           |
| ----------------------- | ------------------------ |
| **Fixed Budget**        | Always inject ≤4k tokens |
| **Adaptive Budget**     | Scale by task complexity |
| **Priority Ranking**    | Most relevant first      |
| **Strategic Placement** | Start AND end of context |

### 10.3 Cost Optimization

- Cache recent query-response pairs (semantic cache)
- Batch similar requests
- Use cheaper models for routine tasks
- Stream partial results

---

## 11. Session Management Patterns

### 11.1 Stateless Query (Damocles Pattern)

```
User Prompt → Decompose to facets → BM25 × N → Dedupe → Inject top-K tokens
```

### 11.2 Progressive Condensation

```
Long session → Identify episodes → Summarize each → Store → Inject summary only
```

### 11.3 Multi-Scale Memory

```
Current: Working memory (full context)
Recent: Session buffer (summarized)
Historical: Episodic DB (indexed)
```

### 11.4 Time-Weighted Retrieval

- Recent interactions: higher weight
- Frequent patterns: boost relevance
- Temporal decay for old info

---

## 12. Implementation Decision Matrix

| Use Case      | Compression    | Retrieval       | Memory         |
| ------------- | -------------- | --------------- | -------------- |
| Short chat    | None           | Full history    | SQLite         |
| Long session  | Summarization  | BM25            | SQLite + FTS   |
| Multi-session | Structured     | Hybrid          | Vector + Graph |
| Codebase      | Semantic chunk | Hybrid + rerank | Semantic       |
| Research      | Extraction     | BM25 + semantic | Vector         |

---

## 13. thegent-Specific Recommendations

| Feature       | Current       | Recommended                       |
| ------------- | ------------- | --------------------------------- |
| Session index | SQLite        | SQLite + FTS5                     |
| Context       | Full history  | Budget + summarization            |
| Retrieval     | Keyword       | Hybrid (BM25 + semantic)          |
| Memory types  | Episodic only | 3-layer (episodic/semantic/state) |
| Compression   | None          | Structured summarization          |
