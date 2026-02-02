"""
Unified storage adapter that connects graph-code and LightRAG to the same Memgraph instance.

This adapter provides a bridge between:
- graph-code's MemgraphIngestor (synchronous, mgclient-based)
- LightRAG's async interface (Neo4j driver compatible)
"""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger

from codebase_rag.services.graph_service import MemgraphIngestor
from codebase_rag.types_defs import PropertyValue


class UnifiedMemgraphAdapter:
    """
    Unified adapter for both graph-code and LightRAG storage.
    
    Uses a single Memgraph instance with separate node types:
    - Code nodes: Function, Class, Method, File, Module (from graph-code)
    - Doc nodes: entity, __Entity__ (from LightRAG)
    - Bridge nodes: Custom relationships connecting code ↔ docs
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 7687,
        batch_size: int = 1000,
        working_dir: str = "./unified_storage",
    ):
        """
        Initialize unified adapter.

        Args:
            host: Memgraph host
            port: Memgraph port
            batch_size: Batch size for graph-code operations
            working_dir: Working directory for LightRAG storage
        """
        self.host = host
        self.port = port
        self.batch_size = batch_size
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(exist_ok=True, parents=True)

        # graph-code connection (synchronous)
        self.code_ingestor = MemgraphIngestor(
            host=host, port=port, batch_size=batch_size
        )

        # LightRAG instance (will be initialized lazily)
        self._lightrag = None
        self._lightrag_initialized = False

    def __enter__(self) -> "UnifiedMemgraphAdapter":
        """Enter context manager for graph-code operations."""
        self.code_ingestor.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.code_ingestor.__exit__(exc_type, exc_val, exc_tb)

    async def initialize_lightrag(self, **kwargs) -> None:
        """
        Initialize LightRAG instance asynchronously.

        This must be called before using any LightRAG features.
        
        Args:
            **kwargs: Additional arguments passed to LightRAG constructor
        """
        if self._lightrag_initialized:
            logger.info("LightRAG already initialized")
            return

        try:
            # Import LightRAG here to avoid forcing dependency
            from lightrag import LightRAG
            from lightrag.base import QueryParam
        except ImportError as e:
            logger.error(
                "LightRAG not installed. Install with: pip install lightrag-hku"
            )
            raise ImportError(
                "LightRAG required for document processing. "
                "Install with: pip install lightrag-hku"
            ) from e

        logger.info("Initializing LightRAG...")

        # Configure LightRAG to use our Memgraph instance
        config = {
            "working_dir": str(self.working_dir),
            "graph_storage": "MemgraphStorage",
            # Use simpler storage for KV and vectors in PoC
            "kv_storage": "JsonKVStorage",
            "vector_storage": "NanoVectorDBStorage",
            # Pass through any additional config
            **kwargs,
        }

        self._lightrag = LightRAG(**config)
        self._lightrag_initialized = True
        logger.info("LightRAG initialized successfully")

    @property
    def lightrag(self):
        """Get LightRAG instance."""
        if not self._lightrag_initialized:
            raise RuntimeError(
                "LightRAG not initialized. Call initialize_lightrag() first."
            )
        return self._lightrag

    # ========================================================================
    # Code Node Operations (graph-code)
    # ========================================================================

    def add_code_node(
        self, label: str, properties: dict[str, PropertyValue]
    ) -> None:
        """
        Add a code node using graph-code API.

        Args:
            label: Node label (Function, Class, Method, File, Module)
            properties: Node properties (qualified_name, file_path, etc.)
        """
        # Mark as code node for filtering
        properties["node_type"] = "code"
        self.code_ingestor.ensure_node_batch(label, properties)

    def add_code_relationship(
        self,
        from_spec: tuple[str, str, PropertyValue],
        rel_type: str,
        to_spec: tuple[str, str, PropertyValue],
        properties: dict[str, PropertyValue] | None = None,
    ) -> None:
        """
        Add a relationship between code nodes.

        Args:
            from_spec: (label, key, value) for source node
            rel_type: Relationship type (CALLS, IMPORTS, etc.)
            to_spec: (label, key, value) for target node
            properties: Optional relationship properties
        """
        self.code_ingestor.ensure_relationship_batch(
            from_spec, rel_type, to_spec, properties
        )

    # ========================================================================
    # Document Operations (LightRAG)
    # ========================================================================

    async def add_documents(self, documents: str | list[str]) -> None:
        """
        Add documents to LightRAG for knowledge extraction.

        Args:
            documents: Single document or list of documents to process
        """
        if not self._lightrag_initialized:
            await self.initialize_lightrag()

        logger.info(f"Inserting documents into LightRAG...")
        await self.lightrag.ainsert(documents)
        logger.info("Documents inserted successfully")

    async def query_documents(
        self, query: str, mode: str = "hybrid"
    ) -> dict[str, Any]:
        """
        Query LightRAG for document knowledge.

        Args:
            query: Natural language query
            mode: Query mode (naive, local, global, hybrid)

        Returns:
            Query results from LightRAG
        """
        if not self._lightrag_initialized:
            raise RuntimeError("Cannot query documents before initialization")

        from lightrag.base import QueryParam

        result = await self.lightrag.aquery(query, param=QueryParam(mode=mode))
        return {"mode": mode, "query": query, "result": result}

    # ========================================================================
    # Bridge Operations (Connect code ↔ docs)
    # ========================================================================

    def add_bridge_relationship(
        self,
        code_qualified_name: str,
        doc_entity_name: str,
        relationship_type: str,
        properties: dict[str, PropertyValue] | None = None,
    ) -> None:
        """
        Create a bridge relationship between code and documentation.

        Args:
            code_qualified_name: Qualified name of code entity (e.g., "mymodule.MyClass.method")
            doc_entity_name: Entity name from LightRAG documentation
            relationship_type: Type of relationship (DOCUMENTS, IMPLEMENTS, REFERENCES, MENTIONS)
            properties: Optional properties (confidence, source, etc.)
        """
        props = properties or {}
        props["bridge"] = True  # Mark as bridge relationship
        props["relationship_type"] = relationship_type

        # Create relationship from code to doc
        # We use generic node matching since we don't know the exact labels
        self.code_ingestor.ensure_relationship_batch(
            from_spec=("Function", "qualified_name", code_qualified_name),
            rel_type=relationship_type,
            to_spec=("entity", "entity_name", doc_entity_name),
            properties=props,
        )

    def query_bridge_relationships(
        self, code_name: str | None = None, doc_entity: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Query bridge relationships between code and docs.

        Args:
            code_name: Optional code qualified name to filter
            doc_entity: Optional doc entity name to filter

        Returns:
            List of bridge relationships
        """
        # Build query based on filters
        if code_name and doc_entity:
            query = """
            MATCH (code {node_type: 'code', qualified_name: $code_name})
                  -[r {bridge: true}]->
                  (doc {entity_name: $doc_entity})
            RETURN code, r, doc
            """
            params = {"code_name": code_name, "doc_entity": doc_entity}
        elif code_name:
            query = """
            MATCH (code {node_type: 'code', qualified_name: $code_name})
                  -[r {bridge: true}]->
                  (doc)
            RETURN code, r, doc
            """
            params = {"code_name": code_name}
        elif doc_entity:
            query = """
            MATCH (code {node_type: 'code'})
                  -[r {bridge: true}]->
                  (doc {entity_name: $doc_entity})
            RETURN code, r, doc
            """
            params = {"doc_entity": doc_entity}
        else:
            query = """
            MATCH (code {node_type: 'code'})
                  -[r {bridge: true}]->
                  (doc)
            RETURN code, r, doc
            LIMIT 100
            """
            params = {}

        return self.code_ingestor.fetch_all(query, params)

    # ========================================================================
    # Utility Operations
    # ========================================================================

    def flush_all(self) -> None:
        """Flush all buffered operations to Memgraph."""
        self.code_ingestor.flush_all()

    def get_code_nodes_by_pattern(self, name_pattern: str) -> list[dict[str, Any]]:
        """
        Get code nodes matching a name pattern.

        Args:
            name_pattern: Pattern to match (supports % wildcard)

        Returns:
            List of matching code nodes
        """
        query = """
        MATCH (n {node_type: 'code'})
        WHERE n.qualified_name CONTAINS $pattern
        RETURN n
        LIMIT 100
        """
        return self.code_ingestor.fetch_all(query, {"pattern": name_pattern})

    async def get_doc_entities(self, entity_type: str | None = None) -> list[dict]:
        """
        Get document entities from LightRAG.

        Args:
            entity_type: Optional entity type filter

        Returns:
            List of document entities
        """
        if not self._lightrag_initialized:
            return []

        # Query Memgraph for entities created by LightRAG
        if entity_type:
            query = """
            MATCH (n:entity {entity_type: $entity_type})
            RETURN n
            LIMIT 100
            """
            params = {"entity_type": entity_type}
        else:
            query = """
            MATCH (n:entity)
            RETURN n
            LIMIT 100
            """
            params = {}

        return self.code_ingestor.fetch_all(query, params)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the unified knowledge graph.

        Returns:
            Dictionary with node and relationship counts
        """
        stats = {}

        # Count code nodes
        code_query = """
        MATCH (n {node_type: 'code'})
        RETURN count(n) as count
        """
        code_result = self.code_ingestor.fetch_all(code_query)
        stats["code_nodes"] = code_result[0]["count"] if code_result else 0

        # Count doc entities
        doc_query = """
        MATCH (n:entity)
        RETURN count(n) as count
        """
        doc_result = self.code_ingestor.fetch_all(doc_query)
        stats["doc_entities"] = doc_result[0]["count"] if doc_result else 0

        # Count bridge relationships
        bridge_query = """
        MATCH ()-[r {bridge: true}]->()
        RETURN count(r) as count
        """
        bridge_result = self.code_ingestor.fetch_all(bridge_query)
        stats["bridge_relationships"] = (
            bridge_result[0]["count"] if bridge_result else 0
        )

        # Count all relationships
        all_rels_query = """
        MATCH ()-[r]->()
        RETURN count(r) as count
        """
        all_rels_result = self.code_ingestor.fetch_all(all_rels_query)
        stats["total_relationships"] = (
            all_rels_result[0]["count"] if all_rels_result else 0
        )

        return stats
