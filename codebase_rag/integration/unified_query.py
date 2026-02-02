"""
Unified query engine that intelligently routes queries to code or documentation systems.

This module provides a single query interface that:
- Classifies user intent (code, docs, or hybrid)
- Routes queries to appropriate system
- Merges results when needed
"""

import re
from enum import Enum
from typing import Any

from loguru import logger


class QueryIntent(str, Enum):
    """Query intent classification."""

    CODE = "code"  # Query about code structure/implementation
    DOCS = "docs"  # Query about documentation/concepts
    HYBRID = "hybrid"  # Query requires both systems


class UnifiedQueryEngine:
    """
    Intelligent query router for unified code + documentation system.
    
    Analyzes queries and routes them to the appropriate backend(s).
    """

    def __init__(self, adapter: Any):
        """
        Initialize query engine.

        Args:
            adapter: UnifiedMemgraphAdapter instance
        """
        self.adapter = adapter

        # Patterns that indicate code queries
        self.code_indicators = [
            r"\bfunction\b",
            r"\bmethod\b",
            r"\bclass\b",
            r"\bcall\b",
            r"\bimport\b",
            r"\btype\b",
            r"\bparameter\b",
            r"\breturn\b",
            r"\bvariable\b",
            r"\bimplementation\b",
            r"\bsource\b",
            r"\.py\b",
            r"\.ts\b",
            r"\.js\b",
            r"\.java\b",
            r"\.cpp\b",
            r"\.rs\b",
        ]

        # Patterns that indicate documentation queries
        self.docs_indicators = [
            r"\bguide\b",
            r"\btutorial\b",
            r"\bdocumentation\b",
            r"\bhow to\b",
            r"\bexplain\b",
            r"\bwhat is\b",
            r"\bwhy\b",
            r"\bconcept\b",
            r"\bdesign\b",
            r"\barchitecture\b",
            r"\boverview\b",
            r"\bdescribe\b",
        ]

        # Patterns that indicate hybrid queries
        self.hybrid_indicators = [
            r"\bimplement(?:s|ed|ation)?\b.*\bdocument",
            r"\bcode\b.*\bdocument",
            r"\bdocument\b.*\bcode",
            r"\bexample\b.*\bcode",
            r"\bshow.*\bcode",
        ]

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify the intent of a query.

        Args:
            query: User query

        Returns:
            QueryIntent classification
        """
        query_lower = query.lower()

        # Check for hybrid indicators first
        for pattern in self.hybrid_indicators:
            if re.search(pattern, query_lower):
                return QueryIntent.HYBRID

        # Count code vs docs indicators
        code_score = sum(
            1 for pattern in self.code_indicators if re.search(pattern, query_lower)
        )
        docs_score = sum(
            1 for pattern in self.docs_indicators if re.search(pattern, query_lower)
        )

        logger.debug(f"Intent scores - code: {code_score}, docs: {docs_score}")

        # If both are present, it's hybrid
        if code_score > 0 and docs_score > 0:
            return QueryIntent.HYBRID

        # Prefer code if scores are equal (common for technical queries)
        if code_score >= docs_score and code_score > 0:
            return QueryIntent.CODE
        elif docs_score > code_score:
            return QueryIntent.DOCS
        else:
            # Default to hybrid if unclear
            return QueryIntent.HYBRID

    async def query(self, query: str, intent: QueryIntent | None = None) -> dict[str, Any]:
        """
        Execute a unified query.

        Args:
            query: User query
            intent: Optional intent override (auto-detected if None)

        Returns:
            Query results with metadata
        """
        # Auto-detect intent if not provided
        if intent is None:
            intent = self.classify_intent(query)

        logger.info(f"Query intent: {intent}")

        if intent == QueryIntent.CODE:
            return await self._query_code(query)
        elif intent == QueryIntent.DOCS:
            return await self._query_docs(query)
        else:
            return await self._query_hybrid(query)

    async def _query_code(self, query: str) -> dict[str, Any]:
        """
        Query code using graph-code system.

        Args:
            query: User query

        Returns:
            Code query results
        """
        logger.info("Executing code query...")

        try:
            # Simple pattern-based Cypher generation for PoC
            cypher_query = self._generate_simple_cypher(query)

            results = self.adapter.code_ingestor.fetch_all(cypher_query)

            return {
                "intent": QueryIntent.CODE,
                "query": query,
                "cypher": cypher_query,
                "results": results,
                "count": len(results),
                "source": "graph-code",
            }
        except Exception as e:
            logger.error(f"Code query failed: {e}")
            return {
                "intent": QueryIntent.CODE,
                "query": query,
                "error": str(e),
                "results": [],
                "count": 0,
                "source": "graph-code",
            }

    async def _query_docs(self, query: str) -> dict[str, Any]:
        """
        Query documentation using LightRAG.

        Args:
            query: User query

        Returns:
            Documentation query results
        """
        logger.info("Executing documentation query...")

        try:
            result = await self.adapter.query_documents(query, mode="hybrid")

            return {
                "intent": QueryIntent.DOCS,
                "query": query,
                "result": result["result"],
                "mode": result["mode"],
                "source": "lightrag",
            }
        except Exception as e:
            logger.error(f"Documentation query failed: {e}")
            return {
                "intent": QueryIntent.DOCS,
                "query": query,
                "error": str(e),
                "result": None,
                "source": "lightrag",
            }

    async def _query_hybrid(self, query: str) -> dict[str, Any]:
        """
        Execute hybrid query using both systems.

        Args:
            query: User query

        Returns:
            Merged results from both systems
        """
        logger.info("Executing hybrid query...")

        # Query both systems in parallel
        import asyncio

        code_task = asyncio.create_task(self._query_code(query))
        docs_task = asyncio.create_task(self._query_docs(query))

        code_results, docs_results = await asyncio.gather(
            code_task, docs_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(code_results, Exception):
            logger.error(f"Code query failed in hybrid: {code_results}")
            code_results = {"results": [], "error": str(code_results)}

        if isinstance(docs_results, Exception):
            logger.error(f"Docs query failed in hybrid: {docs_results}")
            docs_results = {"result": None, "error": str(docs_results)}

        # Find connections between results
        connections = self._find_connections(code_results, docs_results)

        return {
            "intent": QueryIntent.HYBRID,
            "query": query,
            "code": code_results,
            "docs": docs_results,
            "connections": connections,
            "source": "unified",
        }

    def _find_connections(
        self, code_results: dict[str, Any], docs_results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Find bridge relationships between code and doc results.

        Args:
            code_results: Results from code query
            docs_results: Results from docs query

        Returns:
            List of connections found
        """
        connections = []

        # Extract code qualified names from results
        code_names = []
        if "results" in code_results:
            for result in code_results.get("results", []):
                for key, value in result.items():
                    if isinstance(value, dict) and "qualified_name" in value:
                        code_names.append(value["qualified_name"])

        if not code_names:
            return connections

        # Query for bridge relationships involving these code entities
        query = """
        MATCH (code {node_type: 'code'})-[r {bridge: true}]->(doc)
        WHERE code.qualified_name IN $names
        RETURN code.qualified_name as code_name,
               doc.entity_name as doc_name,
               r.relationship_type as rel_type,
               r.confidence as confidence
        """

        try:
            results = self.adapter.code_ingestor.fetch_all(query, {"names": code_names})
            connections = results
        except Exception as e:
            logger.error(f"Failed to find connections: {e}")

        return connections

    def _generate_simple_cypher(self, query: str) -> str:
        """
        Generate simple Cypher query from natural language.

        This is a basic pattern-based approach for PoC.
        In production, use LLM-based generation from graph-code.

        Args:
            query: Natural language query

        Returns:
            Cypher query string
        """
        query_lower = query.lower()

        # Pattern: "find function X" or "show function X"
        if "function" in query_lower:
            match = re.search(r"function\s+(\w+)", query_lower)
            if match:
                func_name = match.group(1)
                return f"""
                MATCH (n:Function {{node_type: 'code'}})
                WHERE toLower(n.qualified_name) CONTAINS toLower('{func_name}')
                RETURN n
                LIMIT 10
                """

        # Pattern: "find class X"
        if "class" in query_lower:
            match = re.search(r"class\s+(\w+)", query_lower)
            if match:
                class_name = match.group(1)
                return f"""
                MATCH (n:Class {{node_type: 'code'}})
                WHERE toLower(n.qualified_name) CONTAINS toLower('{class_name}')
                RETURN n
                LIMIT 10
                """

        # Pattern: "what calls X"
        if "call" in query_lower:
            match = re.search(r"calls?\s+(\w+)", query_lower)
            if match:
                target = match.group(1)
                return f"""
                MATCH (caller)-[r:CALLS]->(callee)
                WHERE toLower(callee.qualified_name) CONTAINS toLower('{target}')
                RETURN caller, r, callee
                LIMIT 20
                """

        # Pattern: "imports of X"
        if "import" in query_lower:
            match = re.search(r"imports?\s+(?:of\s+)?(\w+)", query_lower)
            if match:
                module = match.group(1)
                return f"""
                MATCH (importer)-[r:IMPORTS]->(imported)
                WHERE toLower(imported.qualified_name) CONTAINS toLower('{module}')
                RETURN importer, r, imported
                LIMIT 20
                """

        # Default: return all code nodes (limited)
        return """
        MATCH (n {node_type: 'code'})
        RETURN n
        LIMIT 10
        """
