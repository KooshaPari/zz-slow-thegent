# generators API Reference

> **Source**: `src/thegent/artifacts/generators.py`

Artifact Generators - Specialized factories for creating domain-specific artifacts.

Provides high-level APIs for creating artifacts with domain context.

---

## ArtifactGeneratorFactory

Factory for creating specialized artifact generators.

### Methods

#### ArtifactGeneratorFactory.**init**

```python
__init__(self: Any, maif_generator: MAIFArtifactGenerator)
```

Initialize generator factory.

**Parameters**:

- `maif_generator`: MAIF artifact generator

---

#### ArtifactGeneratorFactory.code

```python
code(self: Any)
```

Get code artifact generator.

**Returns**: CodeArtifactGenerator instance

---

#### ArtifactGeneratorFactory.decision

```python
decision(self: Any)
```

Get decision artifact generator.

**Returns**: DecisionArtifactGenerator instance

---

#### ArtifactGeneratorFactory.tool

```python
tool(self: Any)
```

Get tool artifact generator.

**Returns**: ToolArtifactGenerator instance

---

---

## CodeArtifactGenerator

Generator for code-related artifacts.

### Methods

#### CodeArtifactGenerator.**init**

```python
__init__(self: Any, maif_generator: MAIFArtifactGenerator)
```

Initialize code artifact generator.

**Parameters**:

- `maif_generator`: MAIF artifact generator

---

#### CodeArtifactGenerator.create_code_change

```python
create_code_change(self: Any, agent_id: str, session_id: str, file_path: str, change_type: CodeChangeType, before_content: bytes, after_content: bytes, language: Any)
```

Create code change artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `file_path`: Path to modified file
- `change_type`: Type of change
- `before_content`: Content before change
- `after_content`: Content after change
- `language`: Programming language
- `**metadata`: Additional metadata (tags, affected_symbols, etc.)

**Returns**: CodeChangeArtifact instance

---

#### CodeArtifactGenerator.create_file_operation

```python
create_file_operation(self: Any, agent_id: str, session_id: str, operation_type: FileOperationType, source_path: str, dest_path: Any, before_content: Any, after_content: Any)
```

Create file operation artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `operation_type`: Type of operation
- `source_path`: Source file path
- `dest_path`: Destination path (if applicable)
- `before_content`: Content before operation
- `after_content`: Content after operation
- `**metadata`: Additional metadata

**Returns**: FileOperationArtifact instance

---

---

## DecisionArtifactGenerator

Generator for decision-related artifacts.

### Methods

#### DecisionArtifactGenerator.**init**

```python
__init__(self: Any, maif_generator: MAIFArtifactGenerator)
```

Initialize decision artifact generator.

**Parameters**:

- `maif_generator`: MAIF artifact generator

---

#### DecisionArtifactGenerator.create_branching_point

```python
create_branching_point(self: Any, agent_id: str, session_id: str, condition: str, condition_result: bool, true_branch: str, false_branch: str, input_data: bytes, output_data: bytes)
```

Create branching point artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `condition`: Condition evaluated
- `condition_result`: Condition result
- `true_branch`: True branch description
- `false_branch`: False branch description
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: BranchingPointArtifact instance

---

#### DecisionArtifactGenerator.create_decision

```python
create_decision(self: Any, agent_id: str, session_id: str, decision_type: DecisionType, options_considered: list[str], selected_option: str, input_data: bytes, output_data: bytes)
```

Create decision artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `decision_type`: Type of decision
- `options_considered`: Options evaluated
- `selected_option`: Selected option
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: DecisionArtifact instance

---

---

## ToolArtifactGenerator

Generator for tool-related artifacts.

### Methods

#### ToolArtifactGenerator.**init**

```python
__init__(self: Any, maif_generator: MAIFArtifactGenerator)
```

Initialize tool artifact generator.

**Parameters**:

- `maif_generator`: MAIF artifact generator

---

#### ToolArtifactGenerator.create_mcp_call

```python
create_mcp_call(self: Any, agent_id: str, session_id: str, mcp_server: str, mcp_tool: str, call_status: ToolResultStatus, request_parameters: dict[(str, Any)], input_data: bytes, output_data: bytes)
```

Create MCP call artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `mcp_server`: MCP server name
- `mcp_tool`: MCP tool name
- `call_status`: Call status
- `request_parameters`: Request parameters
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: MCPCallArtifact instance

---

#### ToolArtifactGenerator.create_tool_invocation

```python
create_tool_invocation(self: Any, agent_id: str, session_id: str, tool_type: ToolType, tool_name: str, arguments: dict[(str, Any)], result_status: ToolResultStatus, input_data: bytes, output_data: bytes)
```

Create tool invocation artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `tool_type`: Type of tool
- `tool_name`: Name of tool
- `arguments`: Tool arguments
- `result_status`: Execution status
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: ToolInvocationArtifact instance

---

---

## code

```python
code(self: Any)
```

Get code artifact generator.

**Returns**: CodeArtifactGenerator instance

---

## create_branching_point

```python
create_branching_point(self: Any, agent_id: str, session_id: str, condition: str, condition_result: bool, true_branch: str, false_branch: str, input_data: bytes, output_data: bytes)
```

Create branching point artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `condition`: Condition evaluated
- `condition_result`: Condition result
- `true_branch`: True branch description
- `false_branch`: False branch description
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: BranchingPointArtifact instance

---

## create_code_change

```python
create_code_change(self: Any, agent_id: str, session_id: str, file_path: str, change_type: CodeChangeType, before_content: bytes, after_content: bytes, language: Any)
```

Create code change artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `file_path`: Path to modified file
- `change_type`: Type of change
- `before_content`: Content before change
- `after_content`: Content after change
- `language`: Programming language
- `**metadata`: Additional metadata (tags, affected_symbols, etc.)

**Returns**: CodeChangeArtifact instance

---

## create_decision

```python
create_decision(self: Any, agent_id: str, session_id: str, decision_type: DecisionType, options_considered: list[str], selected_option: str, input_data: bytes, output_data: bytes)
```

Create decision artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `decision_type`: Type of decision
- `options_considered`: Options evaluated
- `selected_option`: Selected option
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: DecisionArtifact instance

---

## create_file_operation

```python
create_file_operation(self: Any, agent_id: str, session_id: str, operation_type: FileOperationType, source_path: str, dest_path: Any, before_content: Any, after_content: Any)
```

Create file operation artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `operation_type`: Type of operation
- `source_path`: Source file path
- `dest_path`: Destination path (if applicable)
- `before_content`: Content before operation
- `after_content`: Content after operation
- `**metadata`: Additional metadata

**Returns**: FileOperationArtifact instance

---

## create_mcp_call

```python
create_mcp_call(self: Any, agent_id: str, session_id: str, mcp_server: str, mcp_tool: str, call_status: ToolResultStatus, request_parameters: dict[(str, Any)], input_data: bytes, output_data: bytes)
```

Create MCP call artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `mcp_server`: MCP server name
- `mcp_tool`: MCP tool name
- `call_status`: Call status
- `request_parameters`: Request parameters
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: MCPCallArtifact instance

---

## create_tool_invocation

```python
create_tool_invocation(self: Any, agent_id: str, session_id: str, tool_type: ToolType, tool_name: str, arguments: dict[(str, Any)], result_status: ToolResultStatus, input_data: bytes, output_data: bytes)
```

Create tool invocation artifact.

**Parameters**:

- `agent_id`: Agent identifier
- `session_id`: Session identifier
- `tool_type`: Type of tool
- `tool_name`: Name of tool
- `arguments`: Tool arguments
- `result_status`: Execution status
- `input_data`: Input data
- `output_data`: Output data
- `**metadata`: Additional metadata

**Returns**: ToolInvocationArtifact instance

---

## decision

```python
decision(self: Any)
```

Get decision artifact generator.

**Returns**: DecisionArtifactGenerator instance

---

## tool

```python
tool(self: Any)
```

Get tool artifact generator.

**Returns**: ToolArtifactGenerator instance

---
