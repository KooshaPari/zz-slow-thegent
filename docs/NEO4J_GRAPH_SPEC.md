# Specification: Neo4j Agentic Knowledge Graph (Z-Graph)

## 1. Objective

To provide a high-fidelity relationship map of agent actions, codebase evolution, and system state. This enables "long-term memory" for agents to understand _who_ changed _what_, _why_, and _how_ different tasks are interconnected.

## 2. Data Model (Schema)

### Nodes

- **Agent**: `{ id, name, type (human/ai), provider }`
- **Task**: `{ id, summary, status, priority, phase }`
- **File**: `{ path, hash, language }`
- **Command**: `{ id, command_line, exit_code, timestamp }`
- **Context**: `{ id, type (git/cwd/env) }`

### Relationships

- `(Agent)-[:EXECUTED]->(Command)`
- `(Command)-[:MODIFIED]->(File)`
- `(Agent)-[:ASSIGNED_TO]->(Task)`
- `(Task)-[:DEPENDS_ON]->(Task)`
- `(Command)-[:RUN_IN]->(Context)`

## 3. Integration Path

- **Hooks**: Use `preexec` and `precmd` in Zsh to stream shell events to the graph.
- **MCP Tool**: Expose a `graph_query` tool via the Z-MCP server to allow agents to perform Cypher queries.
- **Persistence**: Store in the local Neo4j instance (`bolt://localhost:7687`).

## 4. Use Cases

- **Traceability**: "Which agent was responsible for the bug in `auth.go`?"
- **Impact Analysis**: "If I change the `Database` schema, which tasks are affected?"
- **Context Retrieval**: "Show me the last 5 successful commands executed by a Claude agent in this directory."

## 5. Performance

- **Streaming**: Events are emitted asynchronously to avoid blocking the shell.
- **Buffering**: Batch updates using **NATS** as a buffer before ingestion into Neo4j.
