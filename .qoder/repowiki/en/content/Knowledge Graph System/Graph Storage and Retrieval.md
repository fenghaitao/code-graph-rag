# Graph Storage and Retrieval

<cite>
**Referenced Files in This Document**
- [graph_service.py](file://codebase_rag/services/graph_service.py)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py)
- [constants.py](file://codebase_rag/constants.py)
- [types_defs.py](file://codebase_rag/types_defs.py)
- [config.py](file://codebase_rag/config.py)
- [main.py](file://codebase_rag/main.py)
- [vector_store.py](file://codebase_rag/vector_store.py)
- [test_memgraph_batching.py](file://codebase_rag/tests/test_memgraph_batching.py)
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
This document explains the graph storage and retrieval mechanisms implemented in the codebase, focusing on Memgraph integration, batching, constraints, and maintenance operations. It covers connection management, transaction handling, error recovery, batch processing for nodes and relationships, constraint enforcement, uniqueness validation, graph maintenance (cleaning and project deletion), fetch and write operation patterns, and performance optimization strategies for large-scale graph operations. Guidance is provided for connection pooling, retry mechanisms, and graceful degradation.

## Project Structure
The graph storage layer centers around a dedicated service that integrates with Memgraph via the mgclient driver. Supporting modules define Cypher helpers, constants, type definitions, configuration, and optional vector storage for embeddings.

```mermaid
graph TB
subgraph "Graph Service Layer"
MG["MemgraphIngestor<br/>Connection + Batching"]
CQ["Cypher Queries<br/>Templates + Helpers"]
CONST["Constants<br/>Labels, Constraints, Keys"]
TYPES["Types Definitions<br/>Batch Rows, Protocols"]
CFG["Config<br/>Settings + Environment"]
VS["Vector Store<br/>Qdrant Embeddings"]
MAIN["Main<br/>Export + Connect Utilities"]
end
MG --> CQ
MG --> CONST
MG --> TYPES
MG --> CFG
VS --> CFG
MAIN --> MG
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L49-L364)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L1-L120)
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [types_defs.py](file://codebase_rag/types_defs.py#L37-L53)
- [config.py](file://codebase_rag/config.py#L50-L57)
- [vector_store.py](file://codebase_rag/vector_store.py#L1-L81)
- [main.py](file://codebase_rag/main.py#L737-L743)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L49-L364)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L1-L120)
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [types_defs.py](file://codebase_rag/types_defs.py#L37-L53)
- [config.py](file://codebase_rag/config.py#L50-L57)
- [vector_store.py](file://codebase_rag/vector_store.py#L1-L81)
- [main.py](file://codebase_rag/main.py#L737-L743)

## Core Components
- MemgraphIngestor: Manages connection lifecycle, batching buffers, transaction execution, and maintenance operations.
- Cypher query builders: Provide reusable templates for constraints, merges, exports, and helper functions.
- Constants: Define node labels, relationship types, unique key mappings, and error substrings.
- Types definitions: Define typed batch rows, wrappers, and protocols for cursor and result handling.
- Config: Centralized settings for Memgraph host/port, batch size, retries, and vector store parameters.
- Vector store: Optional integration with Qdrant for storing and searching embeddings.

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L49-L364)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L97-L120)
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [types_defs.py](file://codebase_rag/types_defs.py#L37-L53)
- [config.py](file://codebase_rag/config.py#L50-L57)
- [vector_store.py](file://codebase_rag/vector_store.py#L1-L81)

## Architecture Overview
The ingestion pipeline connects to Memgraph, buffers node and relationship inserts, and flushes batches using UNWIND operations. Constraints are enforced per node label, and maintenance operations support cleaning and project deletion. Optional embedding storage is handled separately.

```mermaid
sequenceDiagram
participant App as "Caller"
participant MI as "MemgraphIngestor"
participant Conn as "mgclient.Connection"
participant Cur as "Cursor"
App->>MI : ensure_node_batch(label, props)
MI->>MI : append to node_buffer
MI->>MI : if buffer >= batch_size then flush_nodes()
MI->>Conn : get cursor
MI->>Cur : execute UNWIND + MERGE (build_merge_node_query)
Cur-->>MI : results (rows)
MI->>MI : clear node_buffer
App->>MI : ensure_relationship_batch(...)
MI->>MI : append to relationship_buffer
MI->>MI : if buffer >= batch_size then flush_nodes() + flush_relationships()
MI->>Conn : get cursor
MI->>Cur : execute UNWIND + MERGE (build_merge_relationship_query)
Cur-->>MI : results (created counts)
MI->>MI : clear relationship_buffer
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L189-L217)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L219-L265)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L267-L321)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L101-L119)

## Detailed Component Analysis

### MemgraphIngestor: Connection Management, Transactions, and Maintenance
- Connection lifecycle: Context manager establishes a connection with autocommit enabled and ensures flush and close on exit.
- Cursor management: Internal context manager ensures cursors are closed even on exceptions.
- Transaction handling: Uses single-statement executions for reads/writes; batch operations leverage UNWIND for atomicity and performance.
- Maintenance operations:
  - Clean database: Deletes all nodes and relationships.
  - List projects: Returns project names.
  - Delete project: Removes a project and its contained entities recursively.
- Fetch and write patterns:
  - fetch_all: Executes read queries and maps results to typed rows.
  - execute_write: Executes write queries.
  - export_graph_to_dict: Exports nodes and relationships with metadata.

```mermaid
classDiagram
class MemgraphIngestor {
-str _host
-int _port
-int batch_size
-Connection conn
-list node_buffer
-list relationship_buffer
+__enter__() MemgraphIngestor
+__exit__(exc_type, exc_val, exc_tb) void
-_get_cursor() CursorProtocol
-_cursor_to_results(cursor) ResultRow[]
-_execute_query(query, params) ResultRow[]
-_execute_batch(query, params_list) void
-_execute_batch_with_return(query, params_list) ResultRow[]
+clean_database() void
+list_projects() str[]
+delete_project(project_name) void
+ensure_constraints() void
+ensure_node_batch(label, properties) void
+ensure_relationship_batch(from_spec, rel_type, to_spec, properties) void
+flush_nodes() void
+flush_relationships() void
+flush_all() void
+fetch_all(query, params) ResultRow[]
+execute_write(query, params) void
+export_graph_to_dict() GraphData
}
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L49-L364)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L67-L82)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L84-L94)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L104-L123)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L166-L178)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L171-L173)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L175-L178)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L329-L339)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L341-L360)

### Batch Processing System: Nodes and Relationships
- Node batching:
  - Buffer by label and enforce uniqueness via label-specific unique keys.
  - Build merge queries per label and execute UNWIND batches.
  - Log skipped rows when unique key is missing.
- Relationship batching:
  - Group by (from_label, from_key, rel_type, to_label, to_key) pattern.
  - Build merge queries with optional properties and return created counts.
  - Track attempted vs successful creations and warn on failures.
- Threshold-triggered flush: Flush when buffer reaches configured batch size.

```mermaid
flowchart TD
Start(["Batch Insert"]) --> AppendNodes["Append to node_buffer"]
AppendNodes --> CheckNodeSize{"node_buffer >= batch_size?"}
CheckNodeSize --> |Yes| FlushNodes["flush_nodes()"]
CheckNodeSize --> |No| AppendRels["Append to relationship_buffer"]
AppendRels --> CheckRelSize{"relationship_buffer >= batch_size?"}
CheckRelSize --> |Yes| FlushBoth["flush_nodes() + flush_relationships()"]
CheckRelSize --> |No| End(["Idle"])
FlushNodes --> GroupByLabel["Group by label"]
GroupByLabel --> MergeNodes["Build MERGE + SET query"]
MergeNodes --> ExecBatch["Execute UNWIND batch"]
FlushBoth --> GroupByPattern["Group by (from,to) pattern"]
GroupByPattern --> MergeRels["Build MERGE with optional props"]
MergeRels --> ExecBatchRels["Execute UNWIND batch with return"]
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L189-L217)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L219-L265)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L267-L321)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L101-L119)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L189-L217)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L219-L265)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L267-L321)
- [test_memgraph_batching.py](file://codebase_rag/tests/test_memgraph_batching.py#L20-L90)

### Constraint Enforcement and Uniqueness Validation
- Unique key mapping: Each node label maps to a unique property key (e.g., name, path, qualified_name).
- Constraint creation: Iterates over label-property pairs and issues CREATE CONSTRAINT statements.
- Validation during flush: Skips nodes without the required unique property and logs warnings.

```mermaid
flowchart TD
A["Flush Nodes"] --> B["Lookup id_key for label"]
B --> C{"id_key present?"}
C --> |No| D["Skip row + warn"]
C --> |Yes| E["Build batch rows (id, props)"]
E --> F["Execute MERGE + SET"]
```

**Diagram sources**
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L180-L187)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L234-L259)

**Section sources**
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L180-L187)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L234-L259)

### Graph Maintenance Operations
- Clean database: Deletes all nodes and relationships.
- List projects: Returns project names for management.
- Delete project: Recursively removes a project and its contained entities.

```mermaid
sequenceDiagram
participant Admin as "Admin"
participant MI as "MemgraphIngestor"
Admin->>MI : list_projects()
MI-->>Admin : ["proj1","proj2"]
Admin->>MI : delete_project("proj1")
MI->>MI : _execute_query(CYPHER_DELETE_PROJECT, {name})
MI-->>Admin : "Project deleted"
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L171-L173)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L175-L178)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L7-L12)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L166-L178)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L3-L12)

### Fetch and Write Operation Patterns
- Fetch: Wraps query execution and maps results to typed rows for downstream processing.
- Write: Executes write queries with optional parameters.
- Export: Exports entire graph to dictionary format with metadata.

```mermaid
sequenceDiagram
participant Caller as "Caller"
participant MI as "MemgraphIngestor"
Caller->>MI : fetch_all(query, params)
MI->>MI : _execute_query()
MI-->>Caller : list[ResultRow]
Caller->>MI : execute_write(query, params)
MI->>MI : _execute_query()
Caller->>MI : export_graph_to_dict()
MI->>MI : fetch_all(nodes)
MI->>MI : fetch_all(relationships)
MI-->>Caller : GraphData
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L329-L339)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L341-L360)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L329-L360)

### Embeddings and Vector Store Integration
- Optional Qdrant-backed vector store supports storing and searching embeddings.
- Integration occurs after graph updates to enrich nodes with embeddings.

```mermaid
graph LR
G["Graph Updater<br/>fetch_all(CYPHER_QUERY_EMBEDDINGS)"] --> E["Embedder"]
E --> V["Vector Store<br/>store_embedding(node_id, embedding)"]
V --> Q["Qdrant Client"]
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L369-L418)
- [vector_store.py](file://codebase_rag/vector_store.py#L27-L48)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L369-L418)
- [vector_store.py](file://codebase_rag/vector_store.py#L1-L81)

## Dependency Analysis
- MemgraphIngestor depends on:
  - mgclient for connectivity.
  - Cypher templates for query construction.
  - Constants for label-to-unique-key mapping.
  - Types for typed batch parameters and cursor protocol.
  - Config for connection settings and batch size resolution.
- Vector store depends on Qdrant client availability and configuration.

```mermaid
graph TB
MI["MemgraphIngestor"] --> MG["mgclient"]
MI --> CQ["Cypher Templates"]
MI --> CS["Constants"]
MI --> TD["Types"]
MI --> CFG["Config"]
VS["Vector Store"] --> QD["Qdrant Client"]
```

**Diagram sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L6-L46)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L1-L120)
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [types_defs.py](file://codebase_rag/types_defs.py#L37-L53)
- [config.py](file://codebase_rag/config.py#L50-L57)
- [vector_store.py](file://codebase_rag/vector_store.py#L8-L25)

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L6-L46)
- [cypher_queries.py](file://codebase_rag/cypher_queries.py#L1-L120)
- [constants.py](file://codebase_rag/constants.py#L335-L351)
- [types_defs.py](file://codebase_rag/types_defs.py#L37-L53)
- [config.py](file://codebase_rag/config.py#L50-L57)
- [vector_store.py](file://codebase_rag/vector_store.py#L8-L25)

## Performance Considerations
- Batch size tuning: Adjust MEMGRAPH_BATCH_SIZE to balance memory and throughput. Larger batches reduce round-trips but increase memory usage.
- UNWIND batching: Prefer UNWIND for bulk operations to minimize per-row overhead.
- Constraint enforcement: Ensure constraints exist prior to ingestion to avoid runtime conflicts.
- Cursor lifecycle: Always close cursors after use; the context manager enforces this.
- Logging and truncation: Batch errors truncate long parameter lists to avoid noisy logs.
- Optional embeddings: Offload embedding generation and storage to Qdrant to keep graph ingestion fast.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Connection errors: Verify host/port settings and network connectivity. The context manager logs connection and disconnection events.
- Constraint violations: The system suppresses logging for “already exists” and “constraint” errors; inspect logs for unexpected failures.
- Batch failures: On batch errors, logs show truncated parameters for readability; review the query and parameter shapes.
- Cursor lifecycle: Exceptions automatically close cursors; ensure queries are valid and parameters are properly typed.
- Maintenance operations: Use clean_database and delete_project carefully; confirm project names and permissions.

**Section sources**
- [graph_service.py](file://codebase_rag/services/graph_service.py#L67-L82)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L114-L122)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L131-L146)
- [graph_service.py](file://codebase_rag/services/graph_service.py#L84-L94)

## Conclusion
The graph storage subsystem provides robust, batch-oriented ingestion to Memgraph with strong constraint enforcement and maintenance capabilities. By leveraging UNWIND-based batch operations, typed parameters, and careful cursor management, it scales to large codebases. Optional vector store integration enables semantic search post-ingestion. Proper configuration of batch sizes, connection settings, and maintenance routines ensures reliable operation under varied workloads.