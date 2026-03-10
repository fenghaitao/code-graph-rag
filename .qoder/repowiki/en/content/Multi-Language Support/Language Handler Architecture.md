# Language Handler Architecture

<cite>
**Referenced Files in This Document**
- [language_spec.py](file://codebase_rag/language_spec.py)
- [models.py](file://codebase_rag/models.py)
- [constants.py](file://codebase_rag/constants.py)
- [parser_loader.py](file://codebase_rag/parser_loader.py)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py)
- [factory.py](file://codebase_rag/parsers/factory.py)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py)
- [base.py](file://codebase_rag/parsers/handlers/base.py)
- [python.py](file://codebase_rag/parsers/handlers/python.py)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py)
- [types_defs.py](file://codebase_rag/types_defs.py)
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
This document explains the Graph-Code language handler architecture, focusing on how language capabilities are defined via LanguageSpec and FQNSpec, how language handlers are registered and instantiated, and how Tree-sitter grammars are loaded and queried. It also documents Fully Qualified Name (FQN) resolution, extensibility points for adding new languages, and debugging strategies for language-specific parsing issues.

## Project Structure
The language handler architecture spans several modules:
- Language specification definitions and mappings
- Tree-sitter grammar loading and query construction
- Handler registration and instantiation
- FQN extraction and resolution utilities
- Processor factory for orchestrating parsing and graph building

```mermaid
graph TB
subgraph "Language Specs"
LS["language_spec.py"]
M["models.py"]
C["constants.py"]
end
subgraph "Tree-sitter Loader"
PL["parser_loader.py"]
end
subgraph "Handlers"
REG["handlers/registry.py"]
BASE["handlers/base.py"]
PYH["handlers/python.py"]
JSH["handlers/js_ts.py"]
end
subgraph "Utilities"
FQN["utils/fqn_resolver.py"]
TDEF["types_defs.py"]
FAC["parsers/factory.py"]
end
LS --> PL
LS --> REG
LS --> FQN
REG --> BASE
BASE --> PYH
BASE --> JSH
PL --> FAC
LS --> TDEF
PL --> TDEF
```

**Diagram sources**
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [models.py](file://codebase_rag/models.py#L50-L95)
- [constants.py](file://codebase_rag/constants.py#L425-L929)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L1-L293)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L1-L108)
- [factory.py](file://codebase_rag/parsers/factory.py#L1-L116)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)
- [base.py](file://codebase_rag/parsers/handlers/base.py#L1-L108)
- [python.py](file://codebase_rag/parsers/handlers/python.py#L1-L23)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py#L1-L116)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L200)

**Section sources**
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L1-L293)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L1-L108)
- [factory.py](file://codebase_rag/parsers/factory.py#L1-L116)
- [models.py](file://codebase_rag/models.py#L50-L95)
- [constants.py](file://codebase_rag/constants.py#L425-L929)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L200)

## Core Components
- LanguageSpec: Defines per-language AST node type mappings, function/class detection patterns, import/call patterns, and optional Tree-sitter queries.
- FQNSpec: Encapsulates FQN extraction helpers and module-to-parts conversion for fully qualified name computation.
- Parser loader: Dynamically loads Tree-sitter language bindings, constructs parsers, and builds queries from LanguageSpec.
- Handler registry and base handler: Provides a factory to instantiate language-specific handlers and a base class for shared behavior.
- FQN resolver: Traverses AST nodes to compute qualified names and supports reverse lookup by FQN.

**Section sources**
- [models.py](file://codebase_rag/models.py#L50-L95)
- [language_spec.py](file://codebase_rag/language_spec.py#L11-L426)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L1-L293)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)
- [base.py](file://codebase_rag/parsers/handlers/base.py#L1-L108)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L1-L108)

## Architecture Overview
The system integrates Tree-sitter grammars with language-specific handlers and processors. The pipeline:
- Loads language grammars and builds queries from LanguageSpec
- Instantiates handlers per language for AST-aware processing
- Resolves FQNs from AST nodes for graph node labeling
- Orchestrates ingestion, imports, definitions, types, and calls

```mermaid
sequenceDiagram
participant CFG as "LanguageSpec"
participant LOADER as "ParserLoader"
participant TS as "Tree-sitter"
participant QUERIES as "LanguageQueries"
participant REG as "HandlerRegistry"
participant HANDLER as "LanguageHandler"
participant FQN as "FQN Resolver"
CFG->>LOADER : "Provide specs and queries"
LOADER->>TS : "Load grammar and create Parser"
TS-->>LOADER : "LanguageLoader"
LOADER->>QUERIES : "Build queries from LanguageSpec"
REG->>REG : "Select handler by SupportedLanguage"
REG-->>HANDLER : "Instantiate handler"
HANDLER->>FQN : "Resolve FQN from AST"
FQN-->>HANDLER : "Qualified name"
```

**Diagram sources**
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L251-L293)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L28-L32)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)

## Detailed Component Analysis

### LanguageSpec and FQNSpec
- LanguageSpec defines:
  - Language key and file extensions
  - AST node type tuples for functions, classes, modules, calls, imports
  - Optional Tree-sitter query strings for functions/classes/calls
  - Name/body field names and package indicators
- FQNSpec defines:
  - Scope and function node types for hierarchical name assembly
  - A callable to extract a node’s name from the AST
  - A callable to convert file path to module parts

```mermaid
classDiagram
class LanguageSpec {
+language
+file_extensions
+function_node_types
+class_node_types
+module_node_types
+call_node_types
+import_node_types
+import_from_node_types
+name_field
+body_field
+package_indicators
+function_query
+class_query
+call_query
}
class FQNSpec {
+scope_node_types
+function_node_types
+get_name(node) str?
+file_to_module_parts(path, repo) list[str]
}
class SupportedLanguage {
<<enum>>
+PYTHON
+JS
+TS
+RUST
+GO
+SCALA
+JAVA
+CPP
+CSHARP
+PHP
+LUA
}
LanguageSpec --> SupportedLanguage : "language"
FQNSpec --> SupportedLanguage : "used by"
```

**Diagram sources**
- [models.py](file://codebase_rag/models.py#L57-L95)
- [constants.py](file://codebase_rag/constants.py#L426-L438)

**Section sources**
- [models.py](file://codebase_rag/models.py#L57-L95)
- [language_spec.py](file://codebase_rag/language_spec.py#L113-L202)
- [constants.py](file://codebase_rag/constants.py#L426-L438)

### Parser Factory Pattern and Handler Registration
- ProcessorFactory lazily instantiates processors (import, structure, definition, type inference, call) and wires them with shared services and caches.
- HandlerRegistry maps SupportedLanguage to handler classes and caches instances.

```mermaid
classDiagram
class ProcessorFactory {
-ingestor
-repo_path
-project_name
-queries
-function_registry
-simple_name_lookup
-ast_cache
-unignore_paths
-exclude_paths
+import_processor
+structure_processor
+definition_processor
+type_inference
+call_processor
}
class Registry {
<<static>>
+get_handler(language) LanguageHandler
}
ProcessorFactory --> Registry : "uses"
```

**Diagram sources**
- [factory.py](file://codebase_rag/parsers/factory.py#L18-L116)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L15-L32)

**Section sources**
- [factory.py](file://codebase_rag/parsers/factory.py#L18-L116)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)

### Base Language Handler and Specializations
- BaseLanguageHandler provides default behaviors for extracting names, building qualified names, detecting decorators, and constructing nested function QNs.
- PythonHandler adds Python-specific decorator extraction.
- JsTsHandler extends behavior for JavaScript/TypeScript, including nested function QN derivation and method/object literal detection.

```mermaid
classDiagram
class BaseLanguageHandler {
+extract_function_name(node) str?
+build_function_qualified_name(...)
+is_function_exported(node) bool
+build_method_qualified_name(...)
+extract_base_class_name(base_node) str?
+extract_decorators(node) list[str]
+build_nested_function_qn(...)
-_collect_ancestor_path_parts(...)
-_extract_node_name(node) str?
-_format_nested_qn(...)
}
class PythonHandler {
+extract_decorators(node) list[str]
}
class JsTsHandler {
+extract_decorators(node) list[str]
+is_inside_method_with_object_literals(node) bool
+is_class_method(node) bool
+is_export_inside_function(node) bool
+extract_function_name(node) str?
+build_nested_function_qn(...)
-_collect_js_ancestor_path_parts(...)
}
BaseLanguageHandler <|-- PythonHandler
BaseLanguageHandler <|-- JsTsHandler
```

**Diagram sources**
- [base.py](file://codebase_rag/parsers/handlers/base.py#L15-L108)
- [python.py](file://codebase_rag/parsers/handlers/python.py#L13-L23)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py#L14-L116)

**Section sources**
- [base.py](file://codebase_rag/parsers/handlers/base.py#L15-L108)
- [python.py](file://codebase_rag/parsers/handlers/python.py#L13-L23)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py#L14-L116)

### Tree-sitter Integration and Grammar Loading
- ParserLoader dynamically imports or builds Tree-sitter language bindings, creates Language and Parser instances, and constructs LanguageQueries from LanguageSpec.
- It supports fallback to submodule-built bindings and logs diagnostics for failures.

```mermaid
flowchart TD
Start(["Start"]) --> TryImport["Try import language module"]
TryImport --> Found{"Loader found?"}
Found --> |Yes| BuildQueries["Build LanguageQueries from LanguageSpec"]
Found --> |No| TrySubmodule["Try load from submodule"]
TrySubmodule --> SubFound{"Submodule loader found?"}
SubFound --> |Yes| BuildQueries
SubFound --> |No| SkipLang["Skip language"]
BuildQueries --> Done(["Done"])
SkipLang --> Done
```

**Diagram sources**
- [parser_loader.py](file://codebase_rag/parser_loader.py#L17-L172)
- [constants.py](file://codebase_rag/constants.py#L724-L734)

**Section sources**
- [parser_loader.py](file://codebase_rag/parser_loader.py#L17-L293)
- [constants.py](file://codebase_rag/constants.py#L724-L734)

### FQN Resolution System
- resolve_fqn_from_ast traverses ancestors to collect scope names, combines with module parts derived from file path, and prefixes with project name.
- find_function_source_by_fqn walks the AST to locate a function by its computed FQN.
- extract_function_fqns collects all function FQNs in a subtree.

```mermaid
flowchart TD
Entry(["resolve_fqn_from_ast"]) --> GetName["Get function name"]
GetName --> Loop{"Has parent scope?"}
Loop --> |Yes| IsScope{"Parent is scope?"}
IsScope --> |Yes| AddPart["Add scope name to parts"] --> Up["Go to parent"] --> Loop
IsScope --> |No| Up --> Loop
Loop --> |No| Reverse["Reverse parts"]
Reverse --> ModuleParts["Compute module parts from file path"]
ModuleParts --> Join["Join [project, module, ...func] with dot"]
Join --> Return(["Return FQN"])
```

**Diagram sources**
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)
- [language_spec.py](file://codebase_rag/language_spec.py#L113-L160)

**Section sources**
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L108)
- [language_spec.py](file://codebase_rag/language_spec.py#L11-L160)

### Practical Examples

- Configuring a language specification:
  - Define node types for functions, classes, modules, calls, and imports.
  - Optionally provide Tree-sitter query strings for functions/classes/calls.
  - Example references:
    - [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)

- Instantiating a language handler:
  - Use the registry to get a handler for a given SupportedLanguage.
  - Example references:
    - [registry.py](file://codebase_rag/parsers/handlers/registry.py#L28-L32)

- Building a processor pipeline:
  - Use ProcessorFactory to lazily construct processors with shared dependencies.
  - Example references:
    - [factory.py](file://codebase_rag/parsers/factory.py#L18-L116)

- Resolving FQNs:
  - Compute a function’s qualified name from AST and file path.
  - Example references:
    - [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)

**Section sources**
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L28-L32)
- [factory.py](file://codebase_rag/parsers/factory.py#L18-L116)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)

## Dependency Analysis
Key dependencies:
- language_spec.py depends on constants for node types and patterns, and models for LanguageSpec/FQNSpec.
- parser_loader.py depends on language_spec.py for LanguageSpec and constants for module names and attributes.
- Handlers depend on base.py and types_defs.py for AST node typing and protocols.
- fqn_resolver.py depends on language_spec.py for FQNSpec and constants for separators.

```mermaid
graph LR
C["constants.py"] --> LS["language_spec.py"]
M["models.py"] --> LS
LS --> PL["parser_loader.py"]
LS --> REG["handlers/registry.py"]
REG --> BASE["handlers/base.py"]
BASE --> PYH["handlers/python.py"]
BASE --> JSH["handlers/js_ts.py"]
LS --> FQN["utils/fqn_resolver.py"]
TDEF["types_defs.py"] --> BASE
TDEF --> PL
```

**Diagram sources**
- [constants.py](file://codebase_rag/constants.py#L425-L929)
- [models.py](file://codebase_rag/models.py#L50-L95)
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L1-L293)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)
- [base.py](file://codebase_rag/parsers/handlers/base.py#L1-L108)
- [python.py](file://codebase_rag/parsers/handlers/python.py#L1-L23)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py#L1-L116)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L1-L108)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L200)

**Section sources**
- [constants.py](file://codebase_rag/constants.py#L425-L929)
- [models.py](file://codebase_rag/models.py#L50-L95)
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L1-L293)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L1-L32)
- [base.py](file://codebase_rag/parsers/handlers/base.py#L1-L108)
- [python.py](file://codebase_rag/parsers/handlers/python.py#L1-L23)
- [js_ts.py](file://codebase_rag/parsers/handlers/js_ts.py#L1-L116)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L1-L108)
- [types_defs.py](file://codebase_rag/types_defs.py#L1-L200)

## Performance Considerations
- Lazy initialization: ProcessorFactory defers creation of processors until accessed, reducing startup overhead.
- Query caching: Tree-sitter queries are built once per language and reused across parsing.
- FQN traversal: FQN resolution walks ancestor scopes; keep ASTs reasonably structured to avoid deep traversals.
- Handler specialization: Language-specific handlers minimize generic AST scanning by leveraging language-specific patterns.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Grammar not available:
  - Symptom: No parsers initialized.
  - Action: Verify Tree-sitter bindings are installed or submodule build succeeds.
  - References:
    - [parser_loader.py](file://codebase_rag/parser_loader.py#L251-L293)
    - [constants.py](file://codebase_rag/constants.py#L724-L734)

- FQN resolution failure:
  - Symptom: Missing or incorrect qualified names.
  - Action: Confirm FQNSpec scope and function node types match the language grammar and that file_to_module_parts aligns with project layout.
  - References:
    - [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)
    - [language_spec.py](file://codebase_rag/language_spec.py#L113-L160)

- Handler not found:
  - Symptom: Default handler used unexpectedly.
  - Action: Ensure SupportedLanguage is registered in the handler registry.
  - References:
    - [registry.py](file://codebase_rag/parsers/handlers/registry.py#L15-L32)

- Query pattern errors:
  - Symptom: Queries fail to compile.
  - Action: Validate Tree-sitter query syntax against LanguageSpec and fallback to auto-generated patterns.
  - References:
    - [parser_loader.py](file://codebase_rag/parser_loader.py#L222-L248)

**Section sources**
- [parser_loader.py](file://codebase_rag/parser_loader.py#L251-L293)
- [fqn_resolver.py](file://codebase_rag/utils/fqn_resolver.py#L17-L45)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L15-L32)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L222-L248)

## Conclusion
The language handler architecture cleanly separates language capability definitions (LanguageSpec/FQNSpec), Tree-sitter integration (parser loader), handler instantiation (registry), and FQN resolution. This modular design enables straightforward addition of new languages and robust debugging of language-specific parsing issues.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Extensibility: Adding a New Language
Steps:
- Define LanguageSpec with:
  - language key and file_extensions
  - function_node_types, class_node_types, module_node_types, call_node_types, import_node_types
  - Optional function_query, class_query, call_query
- Define FQNSpec with:
  - scope_node_types, function_node_types
  - get_name and file_to_module_parts
- Register language in:
  - LANGUAGE_SPECS mapping
  - Handler registry mapping
  - Parser loader imports and submodule fallback
- Provide Tree-sitter bindings:
  - Install official module or build submodule bindings
- Validate:
  - Load parsers succeed
  - Handlers instantiate and resolve FQNs correctly

References:
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [models.py](file://codebase_rag/models.py#L57-L95)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L15-L32)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L96-L172)

**Section sources**
- [language_spec.py](file://codebase_rag/language_spec.py#L205-L426)
- [models.py](file://codebase_rag/models.py#L57-L95)
- [registry.py](file://codebase_rag/parsers/handlers/registry.py#L15-L32)
- [parser_loader.py](file://codebase_rag/parser_loader.py#L96-L172)