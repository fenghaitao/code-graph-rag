# Unified Integration: graph-code + LightRAG

This directory contains examples demonstrating the integration of graph-code and LightRAG into a unified knowledge system.

## Overview

The unified integration combines:
- **graph-code**: Code structure analysis and understanding
- **LightRAG**: Document knowledge extraction and Q&A
- **Bridge relationships**: Automatic linking between code and documentation

## Architecture

```
┌─────────────────────────────────────────────┐
│        Unified Knowledge System              │
├─────────────────────────────────────────────┤
│                                               │
│  ┌──────────────┐     ┌──────────────┐      │
│  │  graph-code  │     │   LightRAG   │      │
│  │  (Code)      │     │   (Docs)     │      │
│  └──────┬───────┘     └──────┬───────┘      │
│         │                     │              │
│         └──────┐     ┐────────┘              │
│                │     │                       │
│         ┌──────▼─────▼──────┐               │
│         │  Shared Memgraph  │               │
│         │  Knowledge Graph  │               │
│         └───────────────────┘               │
│                                               │
└─────────────────────────────────────────────┘
```

## Components

### 1. UnifiedMemgraphAdapter
`codebase_rag/integration/unified_adapter.py`

Provides unified access to both systems using a shared Memgraph instance.

**Key Features:**
- Single connection to Memgraph
- Separate node types (code vs docs)
- Bridge relationship management
- Async support for LightRAG

**Usage:**
```python
from codebase_rag.integration import UnifiedMemgraphAdapter

adapter = UnifiedMemgraphAdapter(
    host="localhost",
    port=7687,
    batch_size=1000,
)

with adapter:
    # Initialize LightRAG
    await adapter.initialize_lightrag()
    
    # Add code nodes
    adapter.add_code_node("Function", {
        "qualified_name": "mymodule.myfunction",
        "file_path": "src/mymodule.py",
        ...
    })
    
    # Add documents
    await adapter.add_documents(["doc1", "doc2"])
    
    # Create bridge
    adapter.add_bridge_relationship(
        code_qualified_name="mymodule.myfunction",
        doc_entity_name="Feature Guide",
        relationship_type="DOCUMENTED_BY",
    )
```

### 2. BridgeLinker
`codebase_rag/integration/bridge_linker.py`

Automatically creates relationships between code and documentation.

**Key Features:**
- Pattern-based code reference extraction
- Confidence scoring
- Bidirectional linking (code→docs, docs→code)
- Auto-linking with configurable thresholds

**Usage:**
```python
from codebase_rag.integration import BridgeLinker

linker = BridgeLinker(adapter)

# Link a specific document
candidates = linker.link_document_to_code(
    doc_entity_name="Authentication Guide",
    doc_text=doc_content,
    min_confidence=0.5,
)

# Create the links
linker.create_bridge_links(candidates)

# Or auto-link everything
stats = linker.auto_link_all(min_confidence=0.6)
```

### 3. UnifiedQueryEngine
`codebase_rag/integration/unified_query.py`

Intelligent query routing that classifies intent and uses appropriate system.

**Key Features:**
- Automatic intent classification (code/docs/hybrid)
- Pattern-based query understanding
- Parallel querying for hybrid mode
- Connection discovery across systems

**Usage:**
```python
from codebase_rag.integration import UnifiedQueryEngine

query_engine = UnifiedQueryEngine(adapter)

# Query automatically routes to appropriate system
result = await query_engine.query("How does authentication work?")

# Or specify intent explicitly
result = await query_engine.query(
    "Show me the login function",
    intent=QueryIntent.CODE
)
```

## Examples

### Simple Proof-of-Concept
`examples/unified_poc.py`

Demonstrates basic integration with sample data.

**Run:**
```bash
# Start Memgraph
docker run -p 7687:7687 memgraph/memgraph-platform

# Install dependencies
pip install lightrag-hku

# Run example
python examples/unified_poc.py
```

**What it does:**
1. Initializes unified adapter
2. Creates sample code entities
3. Adds sample documentation
4. Creates bridge relationships
5. Demonstrates various queries
6. Shows statistics

### Real-World Example
`examples/unified_real_example.py`

Integrates with actual codebase and documentation.

**Run:**
```bash
# Configure paths in the script
CODEBASE_PATH = Path("./your_repo")
DOCS_PATH = Path("./your_docs")

# Run
python examples/unified_real_example.py
```

**What it does:**
1. Parses real codebase using graph-code
2. Ingests project documentation (MD, RST, TXT)
3. Auto-links code to documentation
4. Provides statistics
5. Demonstrates comprehensive queries

## Bridge Relationship Types

The integration uses several relationship types:

| Type | Direction | Description |
|------|-----------|-------------|
| `DOCUMENTS` | Doc → Code | Documentation describes code entity |
| `IMPLEMENTS` | Code → Doc | Code implements documented concept |
| `REFERENCES` | Code → Doc | Code references documentation |
| `MENTIONS` | Doc → Code | Documentation mentions code entity |

## Query Intent Classification

The system automatically classifies queries:

**Code Intent:**
- Keywords: function, method, class, call, import, type
- File extensions: .py, .ts, .java, etc.
- Example: "Show me the login function"

**Docs Intent:**
- Keywords: guide, tutorial, documentation, explain, what is
- Example: "How does authentication work?"

**Hybrid Intent:**
- Mixed keywords or explicit cross-references
- Example: "Find code that implements the authentication guide"

## Prerequisites

1. **Memgraph Database**
   ```bash
   docker run -p 7687:7687 memgraph/memgraph-platform
   ```

2. **Python Dependencies**
   ```bash
   # Core (already in graph-code)
   pip install -e .
   
   # LightRAG support
   pip install lightrag-hku
   ```

3. **Optional: Tree-sitter parsers**
   ```bash
   pip install -e ".[treesitter-full]"
   ```

## Configuration

### Memgraph Connection
```python
adapter = UnifiedMemgraphAdapter(
    host="localhost",      # Memgraph host
    port=7687,             # Memgraph port
    batch_size=1000,       # Batch size for operations
    working_dir="./data",  # LightRAG working directory
)
```

### LightRAG Settings
```python
await adapter.initialize_lightrag(
    # Optional: Override LightRAG settings
    llm="gpt-4",
    embedding_func=custom_embedder,
    # ... other LightRAG parameters
)
```

### Bridge Linking
```python
linker = BridgeLinker(adapter)

# Configure thresholds
stats = linker.auto_link_all(
    min_confidence=0.6,  # Minimum confidence (0.0-1.0)
    limit=500,           # Max entities to process
)
```

## Node Types in Graph

### Code Nodes (from graph-code)
- Labels: `Function`, `Class`, `Method`, `File`, `Module`
- Property: `node_type = "code"`
- Key: `qualified_name`

### Documentation Nodes (from LightRAG)
- Labels: `entity`, `__Entity__`
- Properties: `entity_name`, `entity_type`, `description`

### Bridge Relationships
- Property: `bridge = true`
- Properties: `relationship_type`, `confidence`, `evidence`

## Querying Examples

### Query Code
```python
result = await query_engine.query("Find all functions in auth module")
# Returns: code entities matching pattern
```

### Query Docs
```python
result = await query_engine.query("Explain the authentication system")
# Returns: LightRAG response using documentation
```

### Hybrid Query
```python
result = await query_engine.query("Show code implementing user registration")
# Returns: both code entities and related documentation
```

### Direct Bridge Query
```python
# Find what documents a code entity
bridges = adapter.query_bridge_relationships(
    code_name="auth.login"
)

# Find what code implements a doc concept
bridges = adapter.query_bridge_relationships(
    doc_entity="Authentication System"
)
```

## Statistics

Get insights into your unified graph:

```python
stats = adapter.get_statistics()
print(stats)
# {
#     "code_nodes": 150,
#     "doc_entities": 25,
#     "bridge_relationships": 45,
#     "total_relationships": 500,
# }
```

## Performance Considerations

1. **Batch Operations**: Use `batch_size` parameter to control memory usage
2. **Confidence Threshold**: Higher thresholds = fewer, more accurate links
3. **Processing Limits**: Use `limit` parameter when auto-linking large codebases
4. **Async Operations**: LightRAG operations are async for better performance

## Troubleshooting

### LightRAG Not Found
```bash
pip install lightrag-hku
```

### Memgraph Connection Failed
```bash
# Check Memgraph is running
docker ps | grep memgraph

# Check connection
docker exec -it <container> mgconsole
```

### No Bridge Relationships Created
- Lower confidence threshold: `min_confidence=0.4`
- Check code entities exist: `adapter.get_code_nodes_by_pattern("")`
- Verify documentation ingested: `await adapter.get_doc_entities()`

## Next Steps

1. **Integrate with your codebase**: Modify paths in `unified_real_example.py`
2. **Add more documentation**: Include READMEs, guides, API docs
3. **Tune confidence thresholds**: Experiment with `min_confidence` values
4. **Build custom queries**: Extend `UnifiedQueryEngine` with domain-specific logic
5. **Add visualization**: Use Memgraph Lab to visualize the unified graph

## Contributing

Contributions welcome! Areas for improvement:
- LLM-based linking (vs pattern-based)
- More sophisticated query classification
- Support for more document formats (PDF, DOCX)
- Performance optimizations
- Web UI for unified system

## License

Same as graph-code project.
