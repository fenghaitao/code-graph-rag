#!/usr/bin/env python3
"""
Real-world example: Integrate graph-code + LightRAG with actual codebase

This example shows how to use the unified integration with a real codebase:
1. Parse code using graph-code's existing parsers
2. Ingest project documentation
3. Auto-link code to documentation
4. Query for comprehensive understanding
"""

import asyncio
from pathlib import Path

from loguru import logger

from codebase_rag.graph_updater import GraphUpdater
from codebase_rag.integration import (
    BridgeLinker,
    UnifiedMemgraphAdapter,
    UnifiedQueryEngine,
)
from codebase_rag.parser_loader import load_parsers


async def ingest_codebase(adapter: UnifiedMemgraphAdapter, repo_path: Path) -> None:
    """
    Ingest a codebase using graph-code's parsers.

    Args:
        adapter: Unified adapter
        repo_path: Path to repository
    """
    logger.info(f"Parsing codebase at: {repo_path}")

    # Load tree-sitter parsers
    parsers, queries = load_parsers()

    # Create graph updater
    updater = GraphUpdater(
        ingestor=adapter.code_ingestor,
        codebase_root=repo_path,
        parsers=parsers,
        queries=queries,
    )

    # Run the update
    updater.run()

    logger.info("✓ Codebase ingestion complete")


async def ingest_documentation(
    adapter: UnifiedMemgraphAdapter, docs_path: Path
) -> list[str]:
    """
    Ingest documentation files.

    Args:
        adapter: Unified adapter
        docs_path: Path to documentation directory

    Returns:
        List of document paths processed
    """
    logger.info(f"Ingesting documentation from: {docs_path}")

    # Supported documentation formats
    doc_extensions = {".md", ".txt", ".rst", ".adoc"}

    documents = []
    doc_paths = []

    # Recursively find documentation files
    for ext in doc_extensions:
        for doc_file in docs_path.rglob(f"*{ext}"):
            try:
                with open(doc_file, encoding="utf-8") as f:
                    content = f.read()
                    documents.append(content)
                    doc_paths.append(str(doc_file))
                    logger.info(f"  Loaded: {doc_file.name}")
            except Exception as e:
                logger.warning(f"  Failed to read {doc_file}: {e}")

    if documents:
        await adapter.add_documents(documents)
        logger.info(f"✓ Ingested {len(documents)} documentation files")
    else:
        logger.warning("No documentation files found")

    return doc_paths


async def create_bridges(adapter: UnifiedMemgraphAdapter) -> dict:
    """
    Create bridge relationships using auto-linking.

    Args:
        adapter: Unified adapter

    Returns:
        Statistics about links created
    """
    logger.info("Creating bridge relationships...")

    linker = BridgeLinker(adapter)

    # Auto-link with moderate confidence threshold
    stats = linker.auto_link_all(min_confidence=0.6, limit=500)

    logger.info(f"✓ Bridge creation complete: {stats}")
    return stats


async def demonstrate_queries(adapter: UnifiedMemgraphAdapter) -> None:
    """
    Demonstrate various query types.

    Args:
        adapter: Unified adapter
    """
    logger.info("\nDemonstrating unified queries...")

    query_engine = UnifiedQueryEngine(adapter)

    # Example queries for different intents
    queries = [
        # Code queries
        ("Find all functions in the auth module", "code"),
        ("Show me classes that implement authentication", "code"),
        ("What functions call the login method?", "code"),
        # Documentation queries
        ("How does authentication work?", "docs"),
        ("Explain the architecture", "docs"),
        ("What are the security features?", "docs"),
        # Hybrid queries
        ("Show me code that implements the authentication guide", "hybrid"),
        ("Find documentation for the login function", "hybrid"),
        ("What code relates to user registration?", "hybrid"),
    ]

    for query_text, expected_intent in queries:
        logger.info(f"\n  Query: '{query_text}'")
        logger.info(f"  Expected intent: {expected_intent}")

        try:
            result = await query_engine.query(query_text)
            actual_intent = result.get("intent")

            logger.info(f"  Detected intent: {actual_intent}")

            if actual_intent == "code":
                count = result.get("count", 0)
                logger.info(f"  Found {count} code entities")

                # Show sample results
                for item in result.get("results", [])[:3]:
                    if "n" in item:
                        node = item["n"]
                        qn = node.get("qualified_name", "unknown")
                        logger.info(f"    - {qn}")

            elif actual_intent == "docs":
                doc_result = result.get("result")
                if doc_result:
                    preview = str(doc_result)[:150].replace("\n", " ")
                    logger.info(f"  Result: {preview}...")

            elif actual_intent == "hybrid":
                code_results = result.get("code", {}).get("results", [])
                connections = result.get("connections", [])

                logger.info(f"  Code entities: {len(code_results)}")
                logger.info(f"  Bridge connections: {len(connections)}")

                # Show connections
                for conn in connections[:3]:
                    code_name = conn.get("code_name", "unknown")
                    doc_name = conn.get("doc_name", "unknown")
                    rel_type = conn.get("rel_type", "unknown")
                    logger.info(f"    {code_name} -{rel_type}-> {doc_name}")

        except Exception as e:
            logger.error(f"  ✗ Query failed: {e}")


async def main():
    """Main execution for real-world example."""

    logger.info("=" * 70)
    logger.info("Real-World Integration: graph-code + LightRAG")
    logger.info("=" * 70)

    # Configuration
    MEMGRAPH_HOST = "localhost"
    MEMGRAPH_PORT = 7687
    CODEBASE_PATH = Path("./codebase_rag")  # Analyze this project itself!
    DOCS_PATH = Path("./docs")  # Project documentation

    # Initialize adapter
    adapter = UnifiedMemgraphAdapter(
        host=MEMGRAPH_HOST,
        port=MEMGRAPH_PORT,
        batch_size=1000,
        working_dir="./unified_storage_real",
    )

    with adapter:
        try:
            # Step 1: Initialize LightRAG
            logger.info("\n[Step 1] Initializing LightRAG...")
            await adapter.initialize_lightrag()

            # Step 2: Ingest code
            logger.info("\n[Step 2] Ingesting codebase...")
            await ingest_codebase(adapter, CODEBASE_PATH)

            # Step 3: Ingest documentation
            logger.info("\n[Step 3] Ingesting documentation...")
            if DOCS_PATH.exists():
                await ingest_documentation(adapter, DOCS_PATH)
            else:
                logger.warning(f"Documentation path not found: {DOCS_PATH}")

            # Step 4: Create bridges
            logger.info("\n[Step 4] Creating bridge relationships...")
            bridge_stats = await create_bridges(adapter)

            # Step 5: Show statistics
            logger.info("\n[Step 5] Knowledge graph statistics...")
            stats = adapter.get_statistics()
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")

            # Step 6: Demonstrate queries
            logger.info("\n[Step 6] Demonstrating unified queries...")
            await demonstrate_queries(adapter)

            # Step 7: Show bridge examples
            logger.info("\n[Step 7] Sample bridge relationships...")
            bridges = adapter.query_bridge_relationships()
            logger.info(f"Total bridges: {len(bridges)}")

            for bridge in bridges[:10]:
                code_node = bridge.get("code", {})
                doc_node = bridge.get("doc", {})
                rel = bridge.get("r", {})

                code_name = code_node.get("qualified_name", "unknown")
                doc_name = doc_node.get("entity_name", "unknown")
                rel_type = rel.get("relationship_type", "unknown")
                confidence = rel.get("confidence", 0.0)

                logger.info(f"  {code_name} -{rel_type}-> {doc_name} [{confidence:.2f}]")

        except ImportError as e:
            logger.error(f"✗ {e}")
            logger.info("Install LightRAG: pip install lightrag-hku")
        except Exception as e:
            logger.exception(f"✗ Error during execution: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("✓ Integration complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
