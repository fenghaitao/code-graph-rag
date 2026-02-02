"""
Integration module for combining graph-code with LightRAG.

This module provides unified access to both code analysis (graph-code)
and document knowledge (LightRAG) using a shared Memgraph instance.
"""

from .unified_adapter import UnifiedMemgraphAdapter
from .bridge_linker import BridgeLinker
from .unified_query import UnifiedQueryEngine

__all__ = ["UnifiedMemgraphAdapter", "BridgeLinker", "UnifiedQueryEngine"]
