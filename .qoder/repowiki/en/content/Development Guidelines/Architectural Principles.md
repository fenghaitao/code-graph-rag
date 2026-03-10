# Architectural Principles

<cite>
**Referenced Files in This Document**
- [main.py](file://codebase_rag/main.py)
- [cli.py](file://codebase_rag/cli.py)
- [config.py](file://codebase_rag/config.py)
- [models.py](file://codebase_rag/models.py)
- [schemas.py](file://codebase_rag/schemas.py)
- [types_defs.py](file://codebase_rag/types_defs.py)
- [constants.py](file://codebase_rag/constants.py)
- [providers/base.py](file://codebase_rag/providers/base.py)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py)
- [services/llm.py](file://codebase_rag/services/llm.py)
- [services/__init__.py](file://codebase_rag/services/__init__.py)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py)
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
This document codifies the architectural principles for Graph-Code development. It establishes:
- The official agentic framework: PydanticAI
- The rationale for avoiding alternative frameworks
- Encouraged design patterns: factory, strategy, command, and observer
- Architectural layers and component separation
- Emphasis on Pydantic models for validation and serialization
- Explicit imports and single-source-of-truth principles
- Guidance for maintaining architectural consistency when extending the codebase

## Project Structure
The project is organized into cohesive layers:
- CLI layer: user-facing commands and orchestration
- Application layer: agent orchestration, loops, and UI
- Services layer: LLM orchestration, graph ingestion/query, and provider abstraction
- Tools layer: domain-specific capabilities exposed to agents
- Models and schemas: typed data contracts and Pydantic models
- Types and constants: shared protocols, enums, and configuration keys

```mermaid
graph TB
CLI["CLI (Typer)"] --> APP["Application (Agent Loops)"]
APP --> LLM["Services: LLM Orchestrator"]
APP --> TOOLS["Tools (Domain Capabilities)"]
APP --> GRAPH["Services: Graph Ingestion/Query"]
LLM --> PROVIDERS["Providers (PydanticAI Models)"]
TOOLS --> MODELS["Models & Schemas (Pydantic)"]
GRAPH --> MODELS
APP --> MODELS
MODELS --> TYPES["Types & Constants"]
```

**Diagram sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

**Section sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

## Core Components
- PydanticAI as the official agentic framework: Agents, tools, and deferred tool requests are central to the application loop and tool orchestration.
- Typed configuration via Pydantic settings for model providers and runtime behavior.
- Pydantic models for all structured outputs and results to ensure validation and serialization consistency.
- Explicit imports and single-source-of-truth for configuration, constants, and types.

Key architectural anchors:
- Agent orchestration and interactive loops in the application layer
- Provider abstraction for model creation and configuration
- Typed protocols for ingestion/query contracts
- Pydantic models for tool outputs and query results

**Section sources**
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [services/__init__.py](file://codebase_rag/services/__init__.py#L1-L28)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [config.py](file://codebase_rag/config.py#L1-L274)

## Architecture Overview
The system is built around PydanticAI agents that:
- Use a configured LLM provider
- Execute tools that operate on the codebase and filesystem
- Persist results to a graph database and export to JSON

```mermaid
sequenceDiagram
participant User as "User"
participant CLI as "CLI (Typer)"
participant App as "Application Loop"
participant Orchestrator as "Agent Orchestrator"
participant Tools as "Tools"
participant LLM as "PydanticAI Agent"
participant Providers as "Provider Registry"
participant Graph as "Graph Service"
User->>CLI : "graph-code start/update/optimize ..."
CLI->>App : "Initialize and run"
App->>Providers : "Resolve provider/model"
Providers-->>App : "Model instance"
App->>LLM : "Create orchestrator agent"
App->>Tools : "Register tools"
App->>Orchestrator : "Run loop with deferred tool requests"
Orchestrator->>LLM : "Prompt + retries"
LLM-->>Orchestrator : "Response or tool requests"
Orchestrator->>Tools : "Invoke tool with validated args"
Tools->>Graph : "Write/read via ingestion/query"
Graph-->>Tools : "Results"
Tools-->>Orchestrator : "Structured result (Pydantic)"
Orchestrator-->>App : "Final response"
App-->>User : "Rendered output"
```

**Diagram sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)

## Detailed Component Analysis

### PydanticAI as the Official Agentic Framework
- Agents encapsulate LLM behavior, retries, and tool invocation.
- Deferred tool requests enable interactive approvals and controlled execution.
- Tool registration uses PydanticAI’s Tool type with explicit schemas.

```mermaid
classDiagram
class Agent {
+run(input) Any
+retries int
}
class Tool {
+function callable
+name str
+description str
}
class CypherGenerator {
+generate(query) str
}
class ModelProvider {
<<abstract>>
+create_model(model_id) Model
+validate_config() void
}
class GoogleProvider
class OpenAIProvider
class OllamaProvider
Agent --> Tool : "invokes"
CypherGenerator --> Agent : "uses"
ModelProvider <|-- GoogleProvider
ModelProvider <|-- OpenAIProvider
ModelProvider <|-- OllamaProvider
```

**Diagram sources**
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)

**Section sources**
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)

### Design Patterns Encouraged
- Factory pattern: Provider registry and provider classes instantiate model instances.
- Strategy pattern: Different providers (Google, OpenAI, Ollama) implement a common interface.
- Command pattern: CLI commands encapsulate actions; tools encapsulate domain operations.
- Observer pattern: Event-driven patterns appear across languages and tests; in the system, tool outputs and graph updates act as observed events.

```mermaid
flowchart TD
Start(["Tool Invocation"]) --> Validate["Validate Args (Pydantic)"]
Validate --> Approve{"User Approval?"}
Approve --> |No| Deny["ToolDenied"]
Approve --> |Yes| Execute["Execute Tool"]
Execute --> Write["Write to Graph"]
Write --> Serialize["Serialize Results (Pydantic)"]
Serialize --> Return["Return to Agent"]
Deny --> Return
```

**Diagram sources**
- [main.py](file://codebase_rag/main.py#L218-L248)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)

**Section sources**
- [main.py](file://codebase_rag/main.py#L218-L248)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)

### Architectural Layers and Component Separation
- CLI layer: Typer commands, option parsing, and lifecycle orchestration.
- Application layer: Agent loops, interactive sessions, and tool approval flows.
- Services layer: LLM orchestration, provider abstraction, and graph ingestion/query.
- Tools layer: Domain capabilities (query, read/edit, shell, etc.) with explicit schemas.
- Models and schemas: Pydantic models for validation and serialization.
- Types and constants: Shared protocols, enums, and configuration keys.

```mermaid
graph TB
subgraph "CLI Layer"
CLI["cli.py"]
end
subgraph "App Layer"
MAIN["main.py"]
end
subgraph "Services Layer"
LLM["services/llm.py"]
GRAPH["services/graph_service.py"]
PROVIDERS["providers/base.py"]
SVC_PROTOCOLS["services/__init__.py"]
end
subgraph "Tools Layer"
TOOL_QUERY["tools/codebase_query.py"]
end
subgraph "Models & Schemas"
MODELS["models.py"]
SCHEMAS["schemas.py"]
TYPES["types_defs.py"]
CONST["constants.py"]
end
CLI --> MAIN
MAIN --> LLM
MAIN --> TOOL_QUERY
MAIN --> GRAPH
LLM --> PROVIDERS
TOOL_QUERY --> GRAPH
GRAPH --> MODELS
MAIN --> MODELS
MODELS --> SCHEMAS
MODELS --> TYPES
TYPES --> CONST
```

**Diagram sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [services/__init__.py](file://codebase_rag/services/__init__.py#L1-L28)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

**Section sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [services/__init__.py](file://codebase_rag/services/__init__.py#L1-L28)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

### Pydantic Models for Validation and Serialization
- Structured outputs: QueryGraphData, CodeSnippet, ShellCommandResult, EditResult, FileReadResult, FileCreationResult.
- Validators ensure robustness and consistent shapes for downstream consumers.
- Configuration uses Pydantic settings with environment loading.

```mermaid
classDiagram
class QueryGraphData {
+query_used : str
+results : list[ResultRow]
+summary : str
}
class CodeSnippet {
+qualified_name : str
+source_code : str
+file_path : str
+line_start : int
+line_end : int
+docstring : str?
+found : bool
+error_message : str?
}
class ShellCommandResult {
+return_code : int
+stdout : str
+stderr : str
}
class EditResult {
+file_path : str
+success : bool
+error_message : str?
}
class FileReadResult {
+file_path : str
+content : str?
+error_message : str?
}
class FileCreationResult {
+file_path : str
+success : bool
+error_message : str?
}
class AppConfig {
+active_orchestrator_config : ModelConfig
+active_cypher_config : ModelConfig
+parse_model_string()
+resolve_batch_size()
}
class ModelConfig {
+provider : str
+model_id : str
+api_key : str?
+endpoint : str?
+project_id : str?
+region : str?
+provider_type : str?
+thinking_budget : int?
+service_account_file : str?
}
QueryGraphData --> ResultRow
EditResult <.. FileCreationResult
AppConfig --> ModelConfig
```

**Diagram sources**
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [config.py](file://codebase_rag/config.py#L1-L274)

**Section sources**
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [config.py](file://codebase_rag/config.py#L1-L274)

### Explicit Imports and Single-Source-of-Truth Principles
- Explicit imports are used throughout to avoid ambiguity and improve discoverability.
- Single-source-of-truth for configuration via Pydantic settings and constants.
- Centralized enums and typed dictionaries define contracts across layers.

Examples of explicit imports and centralized definitions:
- Application imports tools, services, and models explicitly.
- Constants and enums are defined centrally and referenced across modules.
- Typed protocols and schemas enforce consistent interfaces.

**Section sources**
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [constants.py](file://codebase_rag/constants.py#L1-L800)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)

### Maintaining Architectural Consistency When Extending
- Use PydanticAI for any new agent or tool logic.
- Define tool inputs/outputs with Pydantic models for validation.
- Register new providers via the provider registry following the existing pattern.
- Keep CLI commands focused on orchestration; delegate domain logic to services/tools.
- Maintain explicit imports and avoid star imports.
- Add new constants and enums to centralized files to preserve single-source-of-truth.

**Section sources**
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [cli.py](file://codebase_rag/cli.py#L1-L395)

## Dependency Analysis
The system exhibits low coupling and high cohesion:
- CLI depends on application and services
- Application depends on providers, tools, and schemas
- Services depend on providers and graph infrastructure
- Tools depend on services and schemas
- Models and schemas are consumed across layers

```mermaid
graph LR
CLI["cli.py"] --> MAIN["main.py"]
MAIN --> LLM["services/llm.py"]
MAIN --> TOOLS["tools/*"]
MAIN --> GRAPH["services/graph_service.py"]
LLM --> PROVIDERS["providers/base.py"]
TOOLS --> GRAPH
TOOLS --> SCHEMAS["schemas.py"]
GRAPH --> MODELS["models.py"]
MODELS --> TYPES["types_defs.py"]
TYPES --> CONST["constants.py"]
```

**Diagram sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

**Section sources**
- [cli.py](file://codebase_rag/cli.py#L1-L395)
- [main.py](file://codebase_rag/main.py#L1-L1062)
- [services/llm.py](file://codebase_rag/services/llm.py#L1-L93)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L1-L364)
- [providers/base.py](file://codebase_rag/providers/base.py#L1-L209)
- [tools/codebase_query.py](file://codebase_rag/tools/codebase_query.py#L1-L95)
- [schemas.py](file://codebase_rag/schemas.py#L1-L82)
- [models.py](file://codebase_rag/models.py#L1-L95)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L555)
- [constants.py](file://codebase_rag/constants.py#L1-L800)

## Performance Considerations
- Batch graph writes to reduce round-trips and improve throughput.
- Configure retries and timeouts thoughtfully to balance reliability and responsiveness.
- Use Pydantic validators to catch invalid outputs early and avoid expensive downstream errors.
- Prefer explicit imports to keep module resolution fast and predictable.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common areas to inspect:
- Provider health checks and model initialization failures
- Tool argument validation and serialization errors
- Graph ingestion batch failures and constraint violations
- CLI configuration and environment variable issues

**Section sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L201-L209)
- [services/graph_service.py](file://codebase_rag/services/graph_service.py#L124-L165)
- [schemas.py](file://codebase_rag/schemas.py#L59-L82)
- [config.py](file://codebase_rag/config.py#L227-L231)

## Conclusion
Graph-Code’s architecture centers on PydanticAI for agent orchestration, Pydantic models for validation and serialization, and a layered design that separates concerns across CLI, application, services, tools, and models. By adhering to explicit imports, single-source-of-truth principles, and the encouraged design patterns, contributors can extend the system reliably and consistently.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices
- Provider registry supports multiple LLM providers with a uniform interface.
- Typed protocols define ingestion and query contracts for pluggable backends.
- Centralized constants and enums ensure consistency across modules.

**Section sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L158-L199)
- [services/__init__.py](file://codebase_rag/services/__init__.py#L6-L28)
- [constants.py](file://codebase_rag/constants.py#L12-L800)