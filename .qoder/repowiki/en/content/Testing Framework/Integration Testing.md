# Integration Testing

<cite>
**Referenced Files in This Document**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py)
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py)
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py)
- [conftest.py](file://codebase_rag/tests/conftest.py)
- [tools.py](file://codebase_rag/mcp/tools.py)
- [INTEGRATION_SUMMARY.md](file://INTEGRATION_SUMMARY.md)
- [INTEGRATION_COMPLETE.md](file://INTEGRATION_COMPLETE.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document provides comprehensive integration testing guidance for the codebase, focusing on end-to-end workflows, multi-component scenarios, and cross-language integrations. It covers:
- End-to-end pipelines from ingestion to querying and tool interactions
- Multi-project indexing and isolation
- Cross-language import and relationship validation
- MCP tools integration and Claude Code compatibility verification
- Semantic search and knowledge graph operations
- Test environment setup, database initialization/cleanup, and real-world scenario coverage
- Running integration tests and interpreting results
- Troubleshooting common failures

## Project Structure
The integration tests reside under codebase_rag/tests/integration and leverage a shared test harness in codebase_rag/tests/conftest.py. They exercise:
- Codebase query tool and Cypher generation
- MCP tools registry and tool execution
- Multi-project indexing and deletion
- Import relationships across languages (Java, Python, JS, TS, Rust, Go, C++, Lua)
- Document analysis and provider integration
- Node labeling and relationship validation
- Shell command execution and approval gating
- Tool calling orchestration and parallel execution

```mermaid
graph TB
subgraph "Integration Tests"
IT1["test_codebase_query_integration.py"]
IT2["test_mcp_tools_integration.py"]
IT3["test_multi_project_integration.py"]
IT4["test_imports_e2e.py"]
IT5["test_document_analyzer_integration.py"]
IT6["test_node_label_e2e.py"]
IT7["test_shell_command_integration.py"]
IT8["test_tool_calling.py"]
end
subgraph "Test Harness"
CF["conftest.py"]
end
subgraph "MCP Tools"
MCPT["mcp/tools.py"]
end
IT1 --- CF
IT2 --- CF
IT3 --- CF
IT4 --- CF
IT5 --- CF
IT6 --- CF
IT7 --- CF
IT8 --- CF
IT2 --> MCPT
IT3 --> MCPT
```

**Diagram sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L1-L208)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L1-L137)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L1-L220)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L1-L674)
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L1-L218)
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py#L1-L961)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L1-L248)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L1-L155)
- [conftest.py](file://codebase_rag/tests/conftest.py#L1-L290)
- [tools.py](file://codebase_rag/mcp/tools.py#L1-L458)

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L1-L208)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L1-L137)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L1-L220)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L1-L674)
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L1-L218)
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py#L1-L961)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L1-L248)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L1-L155)
- [conftest.py](file://codebase_rag/tests/conftest.py#L1-L290)
- [tools.py](file://codebase_rag/mcp/tools.py#L1-L458)

## Core Components
- Query tool integration validates natural language to Cypher translation, result structure, and error handling paths.
- MCP tools integration verifies end-to-end tool execution, schema consistency, and behavior without excessive mocking.
- Multi-project integration validates project listing, deletion, isolation, and clean database operations.
- Cross-language import relationships ensure correct module and relationship creation across Java, Python, JS/TS, Rust, Go, C++, and Lua.
- Document analyzer integration validates provider selection, client behavior, and error handling.
- Node label and relationship validation ensures correct graph labeling and relationship types per language.
- Shell command integration validates read-only commands, approval gating for write commands, and pipeline safety.
- Tool calling integration validates parallel and hybrid orchestration with a tracking agent.

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L53-L208)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L56-L137)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L62-L220)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L290-L674)
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L71-L218)
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py#L445-L961)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L37-L248)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L131-L155)

## Architecture Overview
The integration test suite orchestrates Memgraph-backed ingestion, querying, and tool execution. The MCP tools registry composes multiple tools (query, code retrieval, file operations, directory listing) around a shared ingestor and Cypher generator.

```mermaid
graph TB
subgraph "Memgraph"
MG["MemgraphIngestor"]
end
subgraph "Parsers & Queries"
P["load_parsers()"]
Q["queries"]
end
subgraph "GraphUpdater"
GU["GraphUpdater"]
end
subgraph "MCP Tools Registry"
MTR["MCPToolsRegistry"]
QT["query_code_graph"]
GT["get_code_snippet"]
RF["read_file"]
WF["write_file"]
LF["list_directory"]
end
P --> GU
Q --> GU
GU --> MG
MTR --> MG
MTR --> QT
MTR --> GT
MTR --> RF
MTR --> WF
MTR --> LF
```

**Diagram sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L106-L125)
- [tools.py](file://codebase_rag/mcp/tools.py#L40-L458)

**Section sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L106-L125)
- [tools.py](file://codebase_rag/mcp/tools.py#L40-L458)

## Detailed Component Analysis

### Query Tool Integration
Validates:
- Natural language to Cypher translation and query execution
- Empty result handling and summaries
- Graceful error handling for LLM and database failures
- Unicode and varied input robustness
- Result structure and data type preservation

```mermaid
sequenceDiagram
participant T as "Test Case"
participant Tool as "create_query_tool(...)"
participant Ingestor as "Mock Ingestor"
participant Cypher as "Mock CypherGen"
T->>Tool : "function(natural_language_query)"
Tool->>Cypher : "generate(query)"
Cypher-->>Tool : "Cypher query"
Tool->>Ingestor : "fetch_all()"
Ingestor-->>Tool : "Results"
Tool-->>T : "QueryGraphData"
```

**Diagram sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L54-L123)

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L53-L208)

### MCP Tools Integration
Validates:
- End-to-end tool execution (query, read_file, get_code_snippet, list_directory)
- Consistent takes_ctx settings across tools
- Behavior correctness without heavy mocking

```mermaid
sequenceDiagram
participant T as "Test Case"
participant Reg as "MCPToolsRegistry"
participant Ingestor as "MemgraphIngestor"
participant Cypher as "CypherGenerator"
T->>Reg : "query_code_graph('find all functions')"
Reg->>Ingestor : "list_projects()/fetch_all()"
Ingestor-->>Reg : "Project list / results"
Reg-->>T : "QueryResultDict"
```

**Diagram sources**
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L59-L70)
- [tools.py](file://codebase_rag/mcp/tools.py#L314-L334)

**Section sources**
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L56-L137)
- [tools.py](file://codebase_rag/mcp/tools.py#L40-L458)

### Multi-Project Integration
Validates:
- Project listing before and after indexing
- Deletion behavior and isolation
- Clean database operations
- Namespace separation across projects

```mermaid
flowchart TD
Start(["Start"]) --> Index1["Index project1"]
Index1 --> List1["list_projects() == ['project1']"]
List1 --> Index2["Index project2"]
Index2 --> List2["list_projects() == ['project1','project2']"]
List2 --> Delete1["delete_project('project1')"]
Delete1 --> Check1["list_projects() == ['project2']"]
Check1 --> Clean["clean_database()"]
Clean --> Final["list_projects() == []"]
Final --> End(["End"])
```

**Diagram sources**
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L62-L220)

**Section sources**
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L62-L220)

### Cross-Language Import Relationships
Validates:
- Internal and external import/module creation
- Relationship types and qualified names
- Language-specific patterns (Java packages, Python modules, JS/TS imports, Rust crates/modules, Go packages, C++ includes, Lua requires)

```mermaid
flowchart TD
A["Index Project"] --> B["Parse Files"]
B --> C["Create Module Nodes"]
C --> D["Create IMPORTS Relationships"]
D --> E["Validate Qualified Names"]
E --> F["Assert Expected Relationships"]
```

**Diagram sources**
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L17-L34)

**Section sources**
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L290-L674)

### Document Analyzer Integration
Validates:
- Provider selection and client behavior
- File analysis across text, code, and JSON
- Error handling for missing files and path traversal
- Response handling with candidates and empty content

```mermaid
sequenceDiagram
participant T as "Test Case"
participant DA as "DocumentAnalyzer"
participant Settings as "Settings"
participant Client as "genai.Client"
T->>DA : "analyze(file, question)"
DA->>Settings : "provider/model"
DA->>Client : "generate_content()"
Client-->>DA : "response"
DA-->>T : "Analysis text or error"
```

**Diagram sources**
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L71-L159)

**Section sources**
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L71-L218)

### Node Label and Relationship Validation
Validates:
- Correct node labels per language constructs
- Relationship types (e.g., DEFINES, INHERITS)
- Skipping for unsupported languages in current test runs

```mermaid
flowchart TD
S(["Start"]) --> Parse["Parse Language-Specific Code"]
Parse --> Labels["Assert Node Labels Present"]
Labels --> RelTypes["Assert Relationship Types Present"]
RelTypes --> Skip{"Language Supported?"}
Skip --> |Yes| Pass["Test Passes"]
Skip --> |No| SkipT["Skip Test"]
```

**Diagram sources**
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py#L445-L500)

**Section sources**
- [test_node_label_e2e.py](file://codebase_rag/tests/integration/test_node_label_e2e.py#L445-L961)

### Shell Command Integration
Validates:
- Read-only commands without approval
- Approval gating for write commands
- Pipeline safety and operator restrictions
- Git operations in a non-repo context

```mermaid
flowchart TD
Start(["Execute Command"]) --> Check["Check Command Type"]
Check --> ReadOnly{"Read-only?"}
ReadOnly --> |Yes| Run["Execute without approval"]
ReadOnly --> |No| Approve{"Approved?"}
Approve --> |Yes| Run
Approve --> |No| Block["Raise ApprovalRequired"]
Run --> Safety["Apply Allowlist/Pipeline Checks"]
Safety --> Result(["Return Result"])
```

**Diagram sources**
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L111-L139)

**Section sources**
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L37-L248)

### Tool Calling Integration
Validates:
- Parallel tool execution and hybrid orchestration
- Tracking of called tools and skipped tools
- Message history inspection and assertions

```mermaid
sequenceDiagram
participant Agent as "Agent"
participant Tools as "Tracking Tools"
participant T as "Test Runner"
T->>Agent : "run(prompt)"
Agent->>Tools : "semantic_search/read_file/query_graph/list_directory"
Tools-->>Agent : "Results"
Agent-->>T : "Messages + Output"
T->>T : "Assert called/skipped counts"
```

**Diagram sources**
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L76-L97)

**Section sources**
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L131-L155)

## Dependency Analysis
The integration tests depend on:
- Memgraph container lifecycle managed by conftest fixtures
- Parser loading and GraphUpdater for indexing
- MCP tools registry composition and tool execution
- Mocked or real ingestors depending on test scope

```mermaid
graph TB
CF["conftest.py"] --> MG["Memgraph Container Fixture"]
CF --> Conn["Memgraph Connection Fixture"]
CF --> Ingestor["MemgraphIngestor Fixture"]
IT1["test_codebase_query_integration.py"] --> CF
IT2["test_mcp_tools_integration.py"] --> CF
IT3["test_multi_project_integration.py"] --> CF
IT4["test_imports_e2e.py"] --> CF
IT5["test_document_analyzer_integration.py"] --> CF
IT6["test_node_label_e2e.py"] --> CF
IT7["test_shell_command_integration.py"] --> CF
IT8["test_tool_calling.py"] --> CF
IT2 --> MTR["MCPToolsRegistry"]
IT3 --> GU["GraphUpdater"]
```

**Diagram sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L182-L290)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L38-L53)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L51-L59)

**Section sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L182-L290)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L38-L53)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L51-L59)

## Performance Considerations
- Use batched operations where applicable (e.g., bulk node/relationship creation in GraphUpdater)
- Prefer lightweight fixtures and avoid repeated container startup/shutdown
- Limit test scope to targeted scenarios to reduce runtime
- Leverage async fixtures and tool execution to minimize overhead

## Troubleshooting Guide
Common issues and resolutions:
- Memgraph container not ready
  - Ensure the container starts and exposes port 7687
  - Confirm connectivity and initial “running” logs
- Connection failures during tests
  - Retry connection establishment and clear database state between runs
- MCP tool errors
  - Verify ingestor and Cypher generator mocks are properly configured
  - Check tool schema consistency and handler signatures
- Cross-language import mismatches
  - Validate qualified names and relationship types
  - Confirm parser availability for specific languages
- Shell command rejections
  - Ensure commands are on allowlist and pipelines are permitted
  - Verify approval gating for write operations
- Tool calling skips
  - Inspect agent message history for skipped tool indicators
  - Adjust prompt phrasing to encourage parallel execution

**Section sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L182-L290)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L56-L137)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L290-L674)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L164-L248)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L59-L97)

## Conclusion
The integration test suite comprehensively validates end-to-end workflows, multi-component interactions, and cross-language scenarios. It ensures robustness across ingestion, querying, tool execution, and environment setup. By following the guidance here, teams can confidently extend and maintain the integration suite for evolving codebases and environments.

## Appendices

### Test Environment Setup
- Memgraph container lifecycle and connection fixtures are provided in the test harness
- Database initialization and cleanup are handled per-test to ensure isolation
- Use the provided fixtures to spin up containers, connect clients, and reset state

**Section sources**
- [conftest.py](file://codebase_rag/tests/conftest.py#L182-L290)

### Running Integration Tests
- Execute tests with pytest markers aligned with integration scopes
- For MCP and async tests, configure the anyio backend as needed
- Use temporary repositories and isolated Memgraph instances per test

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L12-L17)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L8-L14)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L12-L12)

### MCP Tools and Claude Code Compatibility
- The MCP tools registry exposes standardized tool schemas and handlers
- Verify tool schemas and handler signatures align with Claude Code’s expectations
- Validate behavior for read-only vs write operations and approval gating

**Section sources**
- [tools.py](file://codebase_rag/mcp/tools.py#L433-L446)
- [test_mcp_tools_integration.py](file://codebase_rag/tests/integration/test_mcp_tools_integration.py#L109-L137)

### Semantic Search and Knowledge Graph Operations
- Query tool integration demonstrates natural language to Cypher translation and result validation
- Multi-project operations illustrate graph isolation and clean-up
- Cross-language import tests validate knowledge graph structure across diverse ecosystems

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L53-L123)
- [test_multi_project_integration.py](file://codebase_rag/tests/integration/test_multi_project_integration.py#L62-L220)
- [test_imports_e2e.py](file://codebase_rag/tests/integration/test_imports_e2e.py#L290-L674)

### Real-World Scenarios and Edge Cases
- Unicode queries and mixed character sets
- LLM and database failure paths
- Path traversal and security checks
- Pipeline operators and subshell restrictions
- Parallel and hybrid tool orchestration

**Section sources**
- [test_codebase_query_integration.py](file://codebase_rag/tests/integration/test_codebase_query_integration.py#L156-L170)
- [test_document_analyzer_integration.py](file://codebase_rag/tests/integration/test_document_analyzer_integration.py#L113-L118)
- [test_shell_command_integration.py](file://codebase_rag/tests/integration/test_shell_command_integration.py#L223-L247)
- [test_tool_calling.py](file://codebase_rag/tests/integration/test_tool_calling.py#L131-L155)

### Integration Documentation References
- Unified adapter, bridge linker, and query engine are documented in integration summaries and completion guides

**Section sources**
- [INTEGRATION_SUMMARY.md](file://INTEGRATION_SUMMARY.md#L1-L562)
- [INTEGRATION_COMPLETE.md](file://INTEGRATION_COMPLETE.md#L1-L576)