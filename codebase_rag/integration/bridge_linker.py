"""
Bridge linker for automatically connecting code entities to documentation entities.

This module analyzes documentation text and code to find relationships:
- Code mentions in documentation
- Documentation references in code comments
- Conceptual links between features and implementations
"""

import re
from dataclasses import dataclass
from typing import Any

from loguru import logger

from codebase_rag.types_defs import PropertyValue


@dataclass
class LinkCandidate:
    """Represents a potential link between code and documentation."""

    code_qualified_name: str
    doc_entity_name: str
    relationship_type: str
    confidence: float
    evidence: str  # Why this link was suggested


class BridgeLinker:
    """
    Automatically creates bridge relationships between code and documentation.

    Uses pattern matching, heuristics, and optional LLM-based analysis
    to find meaningful connections.
    """

    def __init__(self, adapter: Any):
        """
        Initialize bridge linker.

        Args:
            adapter: UnifiedMemgraphAdapter instance
        """
        self.adapter = adapter

        # Patterns for detecting code references in text
        self.code_patterns = [
            # Function calls: functionName()
            r'\b([a-z_][a-z0-9_]*)\s*\(',
            # Class names: ClassName, MyClass
            r'\b([A-Z][a-zA-Z0-9]*)\b',
            # Qualified names: module.function, package.Class.method
            r'\b([a-z_][a-z0-9_]*\.[a-zA-Z0-9_.]+)\b',
            # Code blocks with identifiers
            r'`([a-zA-Z_][a-zA-Z0-9_.]*)`',
        ]

        # Relationship types
        self.DOCUMENTS = "DOCUMENTS"  # Doc describes code
        self.IMPLEMENTS = "IMPLEMENTS"  # Code implements doc concept
        self.REFERENCES = "REFERENCES"  # Code references doc
        self.MENTIONS = "MENTIONS"  # Doc mentions code

    def extract_code_references_from_text(self, text: str) -> set[str]:
        """
        Extract potential code references from documentation text.

        Args:
            text: Documentation text

        Returns:
            Set of potential code identifiers
        """
        references = set()

        for pattern in self.code_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Get the captured group (identifier)
                identifier = match.group(1) if match.groups() else match.group(0)
                # Clean up
                identifier = identifier.strip('`"\' ')
                if identifier and len(identifier) > 2:  # Skip very short matches
                    references.add(identifier)

        return references

    def find_matching_code_entities(
        self, reference: str
    ) -> list[dict[str, PropertyValue]]:
        """
        Find code entities that match a reference string.

        Args:
            reference: Identifier from documentation

        Returns:
            List of matching code nodes
        """
        # Try exact match first
        exact_query = """
        MATCH (n {node_type: 'code'})
        WHERE n.qualified_name = $ref
        RETURN n
        """
        exact_matches = self.adapter.code_ingestor.fetch_all(
            exact_query, {"ref": reference}
        )

        if exact_matches:
            return exact_matches

        # Try partial match (ends with reference)
        partial_query = """
        MATCH (n {node_type: 'code'})
        WHERE n.qualified_name ENDS WITH $ref
        RETURN n
        LIMIT 10
        """
        partial_matches = self.adapter.code_ingestor.fetch_all(
            partial_query, {"ref": f".{reference}"}
        )

        if partial_matches:
            return partial_matches

        # Try name-only match (for simple function/class names)
        # Extract just the name part from qualified name
        name_query = """
        MATCH (n {node_type: 'code'})
        WHERE n.qualified_name CONTAINS $ref
        RETURN n
        LIMIT 10
        """
        return self.adapter.code_ingestor.fetch_all(name_query, {"ref": reference})

    def calculate_confidence(
        self,
        reference: str,
        code_qualified_name: str,
        context: str,
    ) -> float:
        """
        Calculate confidence score for a code-doc link.

        Args:
            reference: Reference string from doc
            code_qualified_name: Qualified name of code entity
            context: Context where reference appears

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0

        # Exact match = high confidence
        if reference == code_qualified_name:
            score = 1.0
        # Name ends with reference = good confidence
        elif code_qualified_name.endswith(f".{reference}"):
            score = 0.8
        # Contains reference = moderate confidence
        elif reference in code_qualified_name:
            score = 0.5
        else:
            score = 0.3

        # Boost confidence if reference appears in code block
        if f"`{reference}`" in context or f"```{reference}" in context:
            score = min(1.0, score + 0.2)

        # Boost if reference appears multiple times
        count = context.count(reference)
        if count > 1:
            score = min(1.0, score + 0.1 * (count - 1))

        return score

    def link_document_to_code(
        self,
        doc_entity_name: str,
        doc_text: str,
        min_confidence: float = 0.5,
    ) -> list[LinkCandidate]:
        """
        Find and create links from a document entity to code entities.

        Args:
            doc_entity_name: Name of the document entity
            doc_text: Full text of the document
            min_confidence: Minimum confidence threshold

        Returns:
            List of link candidates created
        """
        logger.info(f"Linking document '{doc_entity_name}' to code...")

        # Extract code references from text
        references = self.extract_code_references_from_text(doc_text)
        logger.debug(f"Found {len(references)} potential code references")

        candidates = []

        for reference in references:
            # Find matching code entities
            matches = self.find_matching_code_entities(reference)

            for match in matches:
                code_qn = match["n"]["qualified_name"]

                # Calculate confidence
                confidence = self.calculate_confidence(reference, code_qn, doc_text)

                if confidence >= min_confidence:
                    candidate = LinkCandidate(
                        code_qualified_name=code_qn,
                        doc_entity_name=doc_entity_name,
                        relationship_type=self.MENTIONS,
                        confidence=confidence,
                        evidence=f"Document mentions '{reference}' which matches {code_qn}",
                    )
                    candidates.append(candidate)

        logger.info(f"Found {len(candidates)} high-confidence links")
        return candidates

    def link_code_to_documentation(
        self,
        code_qualified_name: str,
        source_code: str | None = None,
        min_confidence: float = 0.5,
    ) -> list[LinkCandidate]:
        """
        Find and create links from code to relevant documentation.

        Args:
            code_qualified_name: Qualified name of code entity
            source_code: Optional source code (for extracting comments)
            min_confidence: Minimum confidence threshold

        Returns:
            List of link candidates
        """
        logger.info(f"Linking code '{code_qualified_name}' to documentation...")

        candidates = []

        # Extract key terms from code name
        terms = self._extract_terms_from_code_name(code_qualified_name)

        # If we have source code, extract from comments too
        if source_code:
            comment_terms = self._extract_terms_from_comments(source_code)
            terms.update(comment_terms)

        logger.debug(f"Extracted terms: {terms}")

        # Find doc entities mentioning these terms
        for term in terms:
            if len(term) < 3:  # Skip very short terms
                continue

            # Query for doc entities containing the term
            doc_query = """
            MATCH (n:entity)
            WHERE toLower(n.entity_name) CONTAINS toLower($term)
               OR toLower(n.description) CONTAINS toLower($term)
            RETURN n
            LIMIT 5
            """
            matches = self.adapter.code_ingestor.fetch_all(doc_query, {"term": term})

            for match in matches:
                entity_name = match["n"].get("entity_name", "")
                description = match["n"].get("description", "")

                # Calculate confidence based on term presence
                confidence = self._calculate_doc_confidence(
                    term, entity_name, description
                )

                if confidence >= min_confidence:
                    candidate = LinkCandidate(
                        code_qualified_name=code_qualified_name,
                        doc_entity_name=entity_name,
                        relationship_type=self.IMPLEMENTS,
                        confidence=confidence,
                        evidence=f"Code contains term '{term}' related to documentation",
                    )
                    candidates.append(candidate)

        logger.info(f"Found {len(candidates)} documentation links")
        return candidates

    def create_bridge_links(
        self, candidates: list[LinkCandidate], batch: bool = True
    ) -> int:
        """
        Create bridge relationships in the graph from candidates.

        Args:
            candidates: List of link candidates to create
            batch: Whether to batch the operations

        Returns:
            Number of links created
        """
        created = 0

        for candidate in candidates:
            try:
                self.adapter.add_bridge_relationship(
                    code_qualified_name=candidate.code_qualified_name,
                    doc_entity_name=candidate.doc_entity_name,
                    relationship_type=candidate.relationship_type,
                    properties={
                        "confidence": candidate.confidence,
                        "evidence": candidate.evidence,
                        "auto_generated": True,
                    },
                )
                created += 1
            except Exception as e:
                logger.warning(
                    f"Failed to create bridge link: {candidate.code_qualified_name} "
                    f"-> {candidate.doc_entity_name}: {e}"
                )

        if batch and created > 0:
            self.adapter.flush_all()

        logger.info(f"Created {created} bridge relationships")
        return created

    def auto_link_all(
        self, min_confidence: float = 0.6, limit: int = 100
    ) -> dict[str, int]:
        """
        Automatically link all code and documentation in the graph.

        Args:
            min_confidence: Minimum confidence threshold
            limit: Maximum number of entities to process

        Returns:
            Statistics about links created
        """
        logger.info("Starting automatic linking process...")

        stats = {
            "code_entities_processed": 0,
            "doc_entities_processed": 0,
            "links_created": 0,
            "candidates_found": 0,
        }

        # Get all code entities
        code_query = """
        MATCH (n {node_type: 'code'})
        RETURN n.qualified_name as qn, n.source_code as source
        LIMIT $limit
        """
        code_entities = self.adapter.code_ingestor.fetch_all(
            code_query, {"limit": limit}
        )

        logger.info(f"Processing {len(code_entities)} code entities...")

        all_candidates = []

        # Link code to docs
        for entity in code_entities:
            qn = entity.get("qn")
            source = entity.get("source")

            if qn:
                candidates = self.link_code_to_documentation(
                    qn, source, min_confidence
                )
                all_candidates.extend(candidates)
                stats["code_entities_processed"] += 1

        stats["candidates_found"] = len(all_candidates)

        # Create the links
        stats["links_created"] = self.create_bridge_links(all_candidates)

        logger.info(f"Auto-linking complete: {stats}")
        return stats

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_terms_from_code_name(self, qualified_name: str) -> set[str]:
        """Extract meaningful terms from a qualified name."""
        terms = set()

        # Split by dots
        parts = qualified_name.split(".")

        for part in parts:
            # Split camelCase and snake_case
            # CamelCase -> ['Camel', 'Case']
            words = re.findall(r"[A-Z][a-z]+|[a-z]+", part)
            terms.update(w.lower() for w in words if len(w) > 2)

            # snake_case -> ['snake', 'case']
            words = part.split("_")
            terms.update(w.lower() for w in words if len(w) > 2)

        return terms

    def _extract_terms_from_comments(self, source_code: str) -> set[str]:
        """Extract meaningful terms from code comments."""
        terms = set()

        # Find single-line comments (# or //)
        single_line = re.findall(r"(?:#|//)(.+?)$", source_code, re.MULTILINE)
        for comment in single_line:
            words = re.findall(r"\b\w{3,}\b", comment)
            terms.update(w.lower() for w in words)

        # Find multi-line comments (/* */ or """ """)
        multi_line = re.findall(
            r'(?:/\*(.+?)\*/|"""(.+?)""")', source_code, re.DOTALL
        )
        for groups in multi_line:
            for comment in groups:
                if comment:
                    words = re.findall(r"\b\w{3,}\b", comment)
                    terms.update(w.lower() for w in words)

        # Remove common words
        common_words = {
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "from",
            "have",
            "has",
            "are",
            "was",
            "were",
            "been",
            "not",
            "but",
            "can",
            "will",
            "should",
        }
        return terms - common_words

    def _calculate_doc_confidence(
        self, term: str, entity_name: str, description: str
    ) -> float:
        """Calculate confidence for code-to-doc link."""
        score = 0.0

        term_lower = term.lower()
        name_lower = entity_name.lower()
        desc_lower = description.lower()

        # Exact match in entity name = high confidence
        if term_lower == name_lower:
            score = 0.9
        elif term_lower in name_lower:
            score = 0.7
        elif term_lower in desc_lower:
            # Count occurrences in description
            count = desc_lower.count(term_lower)
            score = min(0.8, 0.4 + 0.1 * count)

        return score
