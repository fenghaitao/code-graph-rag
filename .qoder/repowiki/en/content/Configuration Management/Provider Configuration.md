# Provider Configuration

<cite>
**Referenced Files in This Document**
- [config.py](file://codebase_rag/config.py)
- [constants.py](file://codebase_rag/constants.py)
- [exceptions.py](file://codebase_rag/exceptions.py)
- [providers/base.py](file://codebase_rag/providers/base.py)
- [services/llm.py](file://codebase_rag/services/llm.py)
- [main.py](file://codebase_rag/main.py)
- [README.md](file://README.md)
- [tests/test_provider_configuration.py](file://codebase_rag/tests/test_provider_configuration.py)
- [tests/test_provider_classes.py](file://codebase_rag/tests/test_provider_classes.py)
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

## Introduction
This document explains the Graph-Code provider configuration system. It covers the ModelConfig class structure, how providers are configured for both orchestrator and Cypher roles, supported provider types (OpenAI, Google, Ollama), the provider-explicit configuration system that allows mixing different providers for different roles, model string parsing format (provider:model_id), default fallback mechanisms, provider-specific parameters, examples of configuring popular providers, troubleshooting connectivity issues, and security considerations for API key management.

## Project Structure
The provider configuration system spans several modules:
- Configuration and defaults: AppConfig and ModelConfig
- Provider registry and factories: ModelProvider subclasses and provider lookup
- Runtime usage: LLM service creation and CLI model switching
- Tests validating configuration behavior

```mermaid
graph TB
subgraph "Configuration"
CFG["AppConfig<br/>ModelConfig"]
CONST["Constants<br/>Provider, Region, Defaults"]
EXC["Exceptions<br/>Validation Messages"]
end
subgraph "Providers"
REG["Provider Registry<br/>get_provider()"]
GP["GoogleProvider"]
OP["OpenAIProvider"]
OPV["OllamaProvider"]
end
subgraph "Runtime"
LLM["LLM Service<br/>CypherGenerator"]
MAIN["CLI / Model Switching"]
end
CFG --> REG
CONST --> REG
EXC --> REG
REG --> GP
REG --> OP
REG --> OPV
CFG --> LLM
REG --> LLM
MAIN --> CFG
MAIN --> REG
```

**Diagram sources**
- [config.py](file://codebase_rag/config.py#L20-L234)
- [constants.py](file://codebase_rag/constants.py#L17-L143)
- [exceptions.py](file://codebase_rag/exceptions.py#L1-L60)
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)
- [services/llm.py](file://codebase_rag/services/llm.py#L23-L45)
- [main.py](file://codebase_rag/main.py#L535-L602)

**Section sources**
- [config.py](file://codebase_rag/config.py#L20-L234)
- [constants.py](file://codebase_rag/constants.py#L17-L143)

## Core Components
- ModelConfig: Holds provider, model_id, and provider-specific parameters (api_key, endpoint, project_id, region, provider_type, thinking_budget, service_account_file).
- AppConfig: Loads environment variables, constructs ModelConfig for orchestrator and Cypher roles, and provides default fallbacks.
- Provider classes: GoogleProvider, OpenAIProvider, OllamaProvider implement ModelProvider and create provider-specific model instances.
- Provider registry: get_provider() resolves provider names to classes; get_provider_from_config() instantiates providers from ModelConfig.

Key behaviors:
- Environment-driven configuration with explicit overrides for orchestrator and Cypher.
- Default fallback to Ollama when no explicit configuration is provided.
- Validation errors surfaced via exceptions with actionable messages.

**Section sources**
- [config.py](file://codebase_rag/config.py#L20-L234)
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)
- [exceptions.py](file://codebase_rag/exceptions.py#L1-L60)

## Architecture Overview
The provider configuration pipeline connects environment inputs to runtime model instantiation:

```mermaid
sequenceDiagram
participant ENV as "Environment Variables"
participant CFG as "AppConfig"
participant MC as "ModelConfig"
participant REG as "get_provider()"
participant PR as "Provider Instance"
participant LLM as "LLM Service"
ENV->>CFG : Load .env and OS env
CFG->>MC : Build orchestrator/cypher configs
MC->>REG : Resolve provider class
REG->>PR : Instantiate provider with kwargs
PR-->>CFG : Provider instance
CFG->>LLM : Create model via provider
LLM-->>CFG : Ready for use
```

**Diagram sources**
- [config.py](file://codebase_rag/config.py#L39-L234)
- [providers/base.py](file://codebase_rag/providers/base.py#L165-L189)
- [services/llm.py](file://codebase_rag/services/llm.py#L23-L25)

## Detailed Component Analysis

### ModelConfig and AppConfig
- ModelConfig stores provider, model_id, and optional provider-specific fields.
- AppConfig loads settings from .env and OS environment, constructs ModelConfig for orchestrator and Cypher, and falls back to Ollama when no provider/model is set.
- Active configs are exposed as properties and can be overridden at runtime.

```mermaid
classDiagram
class ModelConfig {
+string provider
+string model_id
+string? api_key
+string? endpoint
+string? project_id
+string? region
+string? provider_type
+int? thinking_budget
+string? service_account_file
+to_update_kwargs() ModelConfigKwargs
}
class AppConfig {
+string ORCHESTRATOR_PROVIDER
+string ORCHESTRATOR_MODEL
+string? ORCHESTRATOR_API_KEY
+string? ORCHESTRATOR_ENDPOINT
+string? ORCHESTRATOR_PROJECT_ID
+string ORCHESTRATOR_REGION
+string? ORCHESTRATOR_PROVIDER_TYPE
+int? ORCHESTRATOR_THINKING_BUDGET
+string? ORCHESTRATOR_SERVICE_ACCOUNT_FILE
+string CYPHER_PROVIDER
+string CYPHER_MODEL
+string? CYPHER_API_KEY
+string? CYPHER_ENDPOINT
+string? CYPHER_PROJECT_ID
+string CYPHER_REGION
+string? CYPHER_PROVIDER_TYPE
+int? CYPHER_THINKING_BUDGET
+string? CYPHER_SERVICE_ACCOUNT_FILE
+AnyHttpUrl LOCAL_MODEL_ENDPOINT
+int MEMGRAPH_BATCH_SIZE
+float OLLAMA_HEALTH_TIMEOUT
+active_orchestrator_config ModelConfig
+active_cypher_config ModelConfig
+set_orchestrator(provider, model, **kwargs) void
+set_cypher(provider, model, **kwargs) void
+parse_model_string(model_string) (string, string)
+resolve_batch_size(batch_size) int
}
AppConfig --> ModelConfig : "creates"
```

**Diagram sources**
- [config.py](file://codebase_rag/config.py#L20-L234)

**Section sources**
- [config.py](file://codebase_rag/config.py#L20-L234)

### Provider Classes and Registry
- ModelProvider defines the interface for provider implementations.
- GoogleProvider supports GLA and Vertex AI variants with validation for required keys and project IDs.
- OpenAIProvider validates presence of API key and accepts a custom endpoint.
- OllamaProvider validates local server availability and uses a default API key when unspecified.
- Provider registry maps provider names to classes and supports dynamic registration.

```mermaid
classDiagram
class ModelProvider {
<<abstract>>
+create_model(model_id, **kwargs) Model
+validate_config() void
+provider_name Provider
}
class GoogleProvider {
+string? api_key
+GoogleProviderType provider_type
+string? project_id
+string region
+string? service_account_file
+int? thinking_budget
+validate_config() void
+create_model(model_id) GoogleModel
}
class OpenAIProvider {
+string? api_key
+string endpoint
+validate_config() void
+create_model(model_id) OpenAIResponsesModel
}
class OllamaProvider {
+string endpoint
+string api_key
+validate_config() void
+create_model(model_id) OpenAIChatModel
}
ModelProvider <|-- GoogleProvider
ModelProvider <|-- OpenAIProvider
ModelProvider <|-- OllamaProvider
```

**Diagram sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)
- [constants.py](file://codebase_rag/constants.py#L17-L143)

**Section sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)
- [constants.py](file://codebase_rag/constants.py#L132-L143)

### Provider Resolution and Model Creation
- get_provider() resolves a provider name to a class and instantiates it with kwargs.
- get_provider_from_config() extracts provider-specific parameters from ModelConfig and creates a provider instance.
- LLM service uses the provider to create a model for Cypher generation.

```mermaid
sequenceDiagram
participant CFG as "ModelConfig"
participant REG as "get_provider_from_config"
participant GP as "GoogleProvider"
participant OP as "OpenAIProvider"
participant OPV as "OllamaProvider"
participant LLM as "CypherGenerator"
CFG->>REG : provider, api_key, endpoint, project_id, region, provider_type, thinking_budget, service_account_file
REG->>GP : instantiate if provider == google
REG->>OP : instantiate if provider == openai
REG->>OPV : instantiate if provider == ollama
GP-->>REG : provider instance
OP-->>REG : provider instance
OPV-->>REG : provider instance
REG-->>LLM : provider.create_model(model_id)
```

**Diagram sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L165-L189)
- [services/llm.py](file://codebase_rag/services/llm.py#L23-L25)

**Section sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L165-L189)
- [services/llm.py](file://codebase_rag/services/llm.py#L23-L25)

### Model String Parsing and Runtime Overrides
- parse_model_string() splits "provider:model_id" and enforces non-empty provider and model parts.
- CLI supports runtime model switching via a command that parses a provider:model string and updates the active configuration.
- When provider is omitted, defaults to Ollama with a default endpoint and API key.

```mermaid
flowchart TD
Start(["User enters 'provider:model'"]) --> Split["Split by ':'"]
Split --> CheckColon{"Contains ':'?"}
CheckColon --> |No| ErrorFormat["Raise MODEL_FORMAT_INVALID"]
CheckColon --> |Yes| Extract["Extract provider, model"]
Extract --> ValidateProvider{"Provider empty?"}
ValidateProvider --> |Yes| ErrorProvider["Raise PROVIDER_EMPTY"]
ValidateProvider --> |No| ValidateModel{"Model empty?"}
ValidateModel --> |Yes| ErrorModel["Raise MODEL_ID_EMPTY"]
ValidateModel --> |No| BuildConfig["Build ModelConfig"]
BuildConfig --> CreateModel["get_provider_from_config()<br/>create_model()"]
CreateModel --> End(["Ready"])
```

**Diagram sources**
- [config.py](file://codebase_rag/config.py#L219-L225)
- [main.py](file://codebase_rag/main.py#L535-L564)

**Section sources**
- [config.py](file://codebase_rag/config.py#L219-L225)
- [main.py](file://codebase_rag/main.py#L535-L602)

### Supported Providers and Configuration Requirements
- OpenAI
  - Required: api_key
  - Optional: endpoint (default provided)
  - Configure via environment variables or runtime overrides
- Google
  - GLA variant: api_key required
  - Vertex variant: project_id required; optional region and service_account_file
  - Optional: thinking_budget
- Ollama
  - Validates local server availability; endpoint defaults to a local URL
  - API key defaults to a specific value when not provided

Examples in the repository demonstrate environment-based configuration for all three providers and mixed provider setups.

**Section sources**
- [providers/base.py](file://codebase_rag/providers/base.py#L100-L156)
- [exceptions.py](file://codebase_rag/exceptions.py#L2-L17)
- [README.md](file://README.md#L145-L216)
- [tests/test_provider_configuration.py](file://codebase_rag/tests/test_provider_configuration.py#L12-L130)

### Provider-Explicit Configuration for Roles
- Separate environment variables for ORCHESTRATOR_* and CYPHER_* roles enable independent provider selection.
- Each role can independently select provider, model, and provider-specific parameters.
- Tests confirm that explicit environment variables are respected and that mixed provider configurations work.

**Section sources**
- [config.py](file://codebase_rag/config.py#L58-L76)
- [tests/test_provider_configuration.py](file://codebase_rag/tests/test_provider_configuration.py#L12-L130)

## Dependency Analysis
Provider configuration depends on:
- Constants for provider names, default endpoints, and default values
- Exceptions for validation errors
- Provider registry for dynamic provider resolution
- AppConfig for environment-driven defaults and runtime overrides

```mermaid
graph LR
CONST["constants.py"] --> CFG["config.py"]
EXC["exceptions.py"] --> BASE["providers/base.py"]
CONST --> BASE
CFG --> BASE
CFG --> LLM["services/llm.py"]
CFG --> MAIN["main.py"]
```

**Diagram sources**
- [constants.py](file://codebase_rag/constants.py#L17-L143)
- [config.py](file://codebase_rag/config.py#L20-L234)
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)
- [services/llm.py](file://codebase_rag/services/llm.py#L23-L25)
- [main.py](file://codebase_rag/main.py#L535-L602)

**Section sources**
- [constants.py](file://codebase_rag/constants.py#L17-L143)
- [config.py](file://codebase_rag/config.py#L20-L234)
- [providers/base.py](file://codebase_rag/providers/base.py#L20-L194)

## Performance Considerations
- Provider validation occurs at instantiation time; Ollama validation performs a network request to the health endpoint. Keep timeouts reasonable to avoid blocking startup.
- Default fallback to Ollama reduces configuration overhead but may increase latency if local models are slower than cloud providers.
- Consider setting custom endpoints for providers to reduce latency and improve reliability.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Unknown provider name
  - Symptom: Error indicating unknown provider with available list
  - Cause: Typo or unsupported provider name
  - Fix: Use supported provider names (google, openai, ollama)
- Missing API key
  - OpenAI: Set ORCHESTRATOR_API_KEY or CYPHER_API_KEY
  - Google GLA: Set ORCHESTRATOR_API_KEY or CYPHER_API_KEY
  - Resolution: Provide the appropriate API key environment variable
- Missing project ID for Google Vertex
  - Symptom: Error requiring project_id
  - Fix: Set ORCHESTRATOR_PROJECT_ID or CYPHER_PROJECT_ID
- Ollama server not responding
  - Symptom: Error indicating Ollama not running at endpoint
  - Fix: Start Ollama locally and ensure the endpoint is reachable
- Invalid model string format
  - Symptom: Errors for missing colon, empty provider, or empty model
  - Fix: Use "provider:model" format with non-empty parts

Security considerations:
- Store API keys in environment variables or secure secret managers; avoid committing secrets to version control.
- Restrict permissions on service account files and ensure they are only readable by the application.
- Prefer HTTPS endpoints and restrict network access to trusted providers.

**Section sources**
- [exceptions.py](file://codebase_rag/exceptions.py#L1-L60)
- [providers/base.py](file://codebase_rag/providers/base.py#L143-L147)
- [README.md](file://README.md#L616-L643)

## Conclusion
The Graph-Code provider configuration system offers flexible, environment-driven configuration with explicit separation of concerns for orchestrator and Cypher roles. It supports mixing providers, provides sensible defaults, validates inputs rigorously, and integrates seamlessly with runtime model switching. By following the configuration patterns and security practices outlined here, users can reliably configure OpenAI, Google, and Ollama providers for diverse operational needs.