#!/usr/bin/env python3
"""
Proof-of-Concept: Unified graph-code + LightRAG Integration

This example demonstrates how to:
1. Connect both systems to the same Memgraph instance
2. Ingest code using graph-code
3. Ingest documentation using LightRAG
4. Create bridge relationships between code and docs
5. Query the unified knowledge graph

Prerequisites:
- Memgraph running on localhost:7687
- pip install lightrag-hku (for LightRAG support)
"""

import asyncio
from pathlib import Path

from loguru import logger

# Import our unified integration components
from codebase_rag.integration import (
    BridgeLinker,
    UnifiedMemgraphAdapter,
    UnifiedQueryEngine,
)


async def main():
    """Main demonstration of unified integration."""

    logger.info("=" * 70)
    logger.info("Unified graph-code + LightRAG Proof-of-Concept")
    logger.info("=" * 70)

    # ========================================================================
    # Step 1: Initialize the Unified Adapter
    # ========================================================================

    logger.info("\n[Step 1] Initializing unified adapter...")

    adapter = UnifiedMemgraphAdapter(
        host="localhost",
        port=7687,
        batch_size=1000,
        working_dir="./unified_storage",
    )

    # Enter context manager for graph-code operations
    with adapter:
        # Initialize LightRAG asynchronously
        logger.info("Initializing LightRAG...")
        try:
            await adapter.initialize_lightrag()
            logger.info("✓ LightRAG initialized")
        except ImportError as e:
            logger.error(f"✗ {e}")
            logger.info(
                "To use LightRAG features, install with: pip install lightrag-hku"
            )
            logger.info("Continuing with code-only demonstration...")

        # ====================================================================
        # Step 2: Ingest Sample Code
        # ====================================================================

        logger.info("\n[Step 2] Ingesting sample code...")

        # Sample code entities (simulating parsed code)
        sample_code = [
            {
                "label": "Function",
                "properties": {
                    "qualified_name": "auth.login",
                    "file_path": "src/auth.py",
                    "line_start": 10,
                    "line_end": 25,
                    "language": "python",
                    "project_name": "demo_project",
                    "source_code": 'def login(username, password):\n    """Authenticate user credentials."""\n    return authenticate(username, password)',
                },
            },
            {
                "label": "Function",
                "properties": {
                    "qualified_name": "auth.authenticate",
                    "file_path": "src/auth.py",
                    "line_start": 27,
                    "line_end": 40,
                    "language": "python",
                    "project_name": "demo_project",
                    "source_code": "def authenticate(username, password):\n    # Verify credentials\n    return verify_password(username, password)",
                },
            },
            {
                "label": "Class",
                "properties": {
                    "qualified_name": "models.User",
                    "file_path": "src/models.py",
                    "line_start": 5,
                    "line_end": 20,
                    "language": "python",
                    "project_name": "demo_project",
                },
            },
            {
                "label": "Function",
                "properties": {
                    "qualified_name": "api.register_user",
                    "file_path": "src/api.py",
                    "line_start": 15,
                    "line_end": 30,
                    "language": "python",
                    "project_name": "demo_project",
                },
            },
        ]

        for code_entity in sample_code:
            adapter.add_code_node(
                label=code_entity["label"], properties=code_entity["properties"]
            )
            logger.info(
                f"  Added {code_entity['label']}: {code_entity['properties']['qualified_name']}"
            )

        # Add relationships
        relationships = [
            # login calls authenticate
            (
                ("Function", "qualified_name", "auth.login"),
                "CALLS",
                ("Function", "qualified_name", "auth.authenticate"),
            ),
            # authenticate uses User model
            (
                ("Function", "qualified_name", "auth.authenticate"),
                "USES",
                ("Class", "qualified_name", "models.User"),
            ),
        ]

        for from_spec, rel_type, to_spec in relationships:
            adapter.add_code_relationship(from_spec, rel_type, to_spec)
            logger.info(f"  Added relationship: {from_spec[2]} -{rel_type}-> {to_spec[2]}")

        # Flush code data
        adapter.flush_all()
        logger.info("✓ Code ingestion complete")

        # ====================================================================
        # Step 3: Ingest Sample Documentation
        # ====================================================================

        logger.info("\n[Step 3] Ingesting sample documentation...")

        sample_docs = [
            """
            # Authentication Guide
            
            Our application uses a secure authentication system. The main entry point 
            is the `login` function which accepts username and password credentials.
            
            ## How Authentication Works
            
            1. User calls the login() function with credentials
            2. The system authenticates the user using the authenticate() function
            3. If successful, a User object is created and returned
            4. Failed attempts are logged for security monitoring
            
            ## Security Features
            
            - Password hashing using bcrypt
            - Rate limiting on login attempts
            - Session management with JWT tokens
            """,
            """
            # User Registration API
            
            The register_user endpoint allows new users to create accounts.
            
            ## Endpoint Details
            
            POST /api/register
            
            This endpoint creates a new User in the system and returns an authentication
            token. The registration process validates email addresses and enforces
            password strength requirements.
            
            ## Example Usage
            
            ```python
            response = api.register_user(
                email="user@example.com",
                password="SecurePassword123!"
            )
            ```
            """,
        ]

        if adapter._lightrag_initialized:
            try:
                await adapter.add_documents(sample_docs)
                logger.info(f"✓ Ingested {len(sample_docs)} documentation files")
            except Exception as e:
                logger.error(f"✗ Failed to ingest documents: {e}")
        else:
            logger.info("⊘ Skipping documentation (LightRAG not available)")

        # ====================================================================
        # Step 4: Create Bridge Relationships
        # ====================================================================

        logger.info("\n[Step 4] Creating bridge relationships...")

        linker = BridgeLinker(adapter)

        # Link documents to code
        all_candidates = []

        for i, doc in enumerate(sample_docs):
            candidates = linker.link_document_to_code(
                doc_entity_name=f"doc_{i}",
                doc_text=doc,
                min_confidence=0.5,
            )
            all_candidates.extend(candidates)
            logger.info(f"  Document {i}: Found {len(candidates)} potential links")

        if all_candidates:
            created = linker.create_bridge_links(all_candidates)
            logger.info(f"✓ Created {created} bridge relationships")
        else:
            logger.info("  No high-confidence links found (this is normal for simple PoC)")
            # Create manual bridge links for demonstration
            logger.info("  Creating manual bridge links for demonstration...")
            adapter.add_bridge_relationship(
                code_qualified_name="auth.login",
                doc_entity_name="Authentication Guide",
                relationship_type="DOCUMENTED_BY",
                properties={"confidence": 1.0, "manual": True},
            )
            adapter.add_bridge_relationship(
                code_qualified_name="api.register_user",
                doc_entity_name="User Registration API",
                relationship_type="DOCUMENTED_BY",
                properties={"confidence": 1.0, "manual": True},
            )
            adapter.flush_all()
            logger.info("✓ Created 2 manual bridge relationships")

        # ====================================================================
        # Step 5: Query the Unified Graph
        # ====================================================================

        logger.info("\n[Step 5] Querying the unified knowledge graph...")

        query_engine = UnifiedQueryEngine(adapter)

        # Example queries
        test_queries = [
            "Show me the login function",
            "What does the authentication guide say?",
            "Find code related to user registration",
        ]

        for i, test_query in enumerate(test_queries, 1):
            logger.info(f"\n  Query {i}: '{test_query}'")

            try:
                result = await query_engine.query(test_query)

                logger.info(f"  Intent: {result.get('intent')}")
                logger.info(f"  Source: {result.get('source')}")

                if result.get("intent") == "code":
                    count = result.get("count", 0)
                    logger.info(f"  Results: {count} code entities found")
                    if count > 0:
                        for item in result.get("results", [])[:3]:
                            logger.info(f"    - {item}")

                elif result.get("intent") == "docs":
                    doc_result = result.get("result")
                    if doc_result:
                        logger.info(f"  Result: {doc_result[:200]}...")

                elif result.get("intent") == "hybrid":
                    code_count = len(result.get("code", {}).get("results", []))
                    connections = len(result.get("connections", []))
                    logger.info(f"  Code results: {code_count}")
                    logger.info(f"  Connections: {connections}")

            except Exception as e:
                logger.error(f"  ✗ Query failed: {e}")

        # ====================================================================
        # Step 6: Show Statistics
        # ====================================================================

        logger.info("\n[Step 6] Knowledge graph statistics...")

        stats = adapter.get_statistics()

        logger.info(f"  Code nodes: {stats['code_nodes']}")
        logger.info(f"  Doc entities: {stats['doc_entities']}")
        logger.info(f"  Bridge relationships: {stats['bridge_relationships']}")
        logger.info(f"  Total relationships: {stats['total_relationships']}")

        # ====================================================================
        # Step 7: Demonstrate Bridge Query
        # ====================================================================

        logger.info("\n[Step 7] Querying bridge relationships...")

        bridges = adapter.query_bridge_relationships()
        logger.info(f"  Found {len(bridges)} bridge relationships")

        for bridge in bridges[:5]:  # Show first 5
            code_node = bridge.get("code", {})
            doc_node = bridge.get("doc", {})
            rel = bridge.get("r", {})

            code_name = code_node.get("qualified_name", "unknown")
            doc_name = doc_node.get("entity_name", "unknown")
            rel_type = rel.get("relationship_type", "unknown")

            logger.info(f"  {code_name} -{rel_type}-> {doc_name}")

    logger.info("\n" + "=" * 70)
    logger.info("✓ Proof-of-concept complete!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("1. Run this with a real codebase using graph-code's parser")
    logger.info("2. Add your project documentation (README, guides, etc.)")
    logger.info("3. Use the auto-linker to connect code and docs")
    logger.info("4. Query the unified graph for comprehensive understanding")


if __name__ == "__main__":
    asyncio.run(main())
