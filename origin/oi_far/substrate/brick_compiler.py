"""Brick compiler - converts documents to bricks."""

import hashlib
import re
from typing import Any

from .types import (
    Brick,
    BrickKind,
    Claim,
    Definition,
    Link,
    Provenance,
    Document,
)


class BrickCompiler:
    """
    Compiles documents into meaning-compressed bricks.

    The compiler extracts structured knowledge from documents:
    - Claims (factual assertions)
    - Definitions (term explanations)
    - Links (relationships between concepts)

    This is a deterministic process - same input always produces same output.
    """

    def __init__(self):
        self._brick_counter = 0
        self._claim_counter = 0

    def compile_document(self, doc: Document) -> list[Brick]:
        """
        Compile a document into bricks.

        Args:
            doc: Document to compile

        Returns:
            List of extracted bricks
        """
        if doc.source_type == "pack":
            return self._compile_pack(doc)
        else:
            return self._compile_text(doc)

    def _compile_pack(self, doc: Document) -> list[Brick]:
        """Compile an Origin concept pack into bricks."""
        metadata = doc.metadata
        bricks = []

        # Create main concept brick
        self._brick_counter += 1
        brick_id = f"brick_{doc.id}_{self._brick_counter}"

        # Extract claims from pack
        claims = []
        pack_claims = metadata.get("claims", [])
        for i, claim_data in enumerate(pack_claims):
            self._claim_counter += 1
            claim_id = f"claim_{brick_id}_{self._claim_counter}"

            if isinstance(claim_data, dict):
                claim_text = claim_data.get("text", str(claim_data))
                confidence = claim_data.get("confidence", 1.0)
            else:
                claim_text = str(claim_data)
                confidence = 1.0

            claims.append(Claim(
                id=claim_id,
                text=claim_text,
                confidence=confidence,
                source_refs=[doc.id],
            ))

        # Extract definitions
        definitions = []
        title = metadata.get("title", "")
        summary = metadata.get("summary", "")
        if title and summary:
            definitions.append(Definition(
                term=title,
                text=summary,
                scope="origin",
            ))

        # Extract links from relationships
        links = []
        for parent_id in metadata.get("parents", []):
            links.append(Link(
                target_id=f"pack_{parent_id}",
                relation="parent",
            ))
        for child_id in metadata.get("children", []):
            links.append(Link(
                target_id=f"pack_{child_id}",
                relation="child",
            ))
        for related_id in metadata.get("related", []):
            links.append(Link(
                target_id=f"pack_{related_id}",
                relation="related",
            ))

        # Create provenance
        provenance = Provenance(
            source_id=doc.id,
            source_type="pack",
            path=doc.source_path,
            content_hash=doc.content_hash,
        )

        # Determine brick kind
        kind = BrickKind.CONCEPT

        brick = Brick(
            id=brick_id,
            kind=kind,
            title=title or doc.title,
            summary=summary,
            claims=claims,
            definitions=definitions,
            links=links,
            provenance=provenance,
            confidence=1.0,
            tags=metadata.get("tags", []),
            metadata={
                "pack_id": metadata.get("id"),
                "status": metadata.get("status"),
                "disclosure_tier": metadata.get("disclosure_tier"),
            },
        )

        bricks.append(brick)

        # Also compile claims as separate bricks for fine-grained retrieval
        for claim in claims:
            self._brick_counter += 1
            claim_brick = Brick(
                id=f"brick_claim_{claim.id}",
                kind=BrickKind.CLAIM,
                title=f"Claim: {claim.text[:50]}...",
                summary=claim.text,
                claims=[claim],
                definitions=[],
                links=[Link(target_id=brick_id, relation="parent")],
                provenance=provenance,
                confidence=claim.confidence,
                tags=metadata.get("tags", []),
            )
            bricks.append(claim_brick)

        return bricks

    def _compile_text(self, doc: Document) -> list[Brick]:
        """Compile a text document into bricks."""
        bricks = []
        text = doc.extracted_text or doc.content

        # Split into sections
        sections = self._split_sections(text)

        for i, (heading, content) in enumerate(sections):
            self._brick_counter += 1
            brick_id = f"brick_{doc.id}_{self._brick_counter}"

            # Extract claims from content
            claims = self._extract_claims(content, brick_id)

            # Extract definitions
            definitions = self._extract_definitions(content)

            # Create provenance
            provenance = Provenance(
                source_id=doc.id,
                source_type=doc.source_type,
                path=doc.source_path,
                content_hash=doc.content_hash,
            )

            brick = Brick(
                id=brick_id,
                kind=BrickKind.CONCEPT if definitions else BrickKind.CLAIM,
                title=heading or doc.title,
                summary=content[:200] if len(content) > 200 else content,
                claims=claims,
                definitions=definitions,
                links=[],
                provenance=provenance,
                confidence=0.8,  # Lower confidence for auto-extracted
                tags=[],
            )

            bricks.append(brick)

        return bricks

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        """Split text into sections by headings."""
        sections = []

        # Match markdown headings
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            # No headings, treat whole text as one section
            return [("", text.strip())]

        # Extract sections between headings
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                sections.append((heading, content))

        return sections

    def _extract_claims(self, text: str, brick_id: str) -> list[Claim]:
        """Extract claims from text."""
        claims = []

        # Look for bullet points and numbered lists
        bullet_pattern = re.compile(r'^[\-\*\•]\s+(.+)$', re.MULTILINE)
        number_pattern = re.compile(r'^\d+[\.\)]\s+(.+)$', re.MULTILINE)

        for pattern in [bullet_pattern, number_pattern]:
            for match in pattern.finditer(text):
                self._claim_counter += 1
                claim_text = match.group(1).strip()
                if len(claim_text) > 10:  # Skip very short items
                    claims.append(Claim(
                        id=f"claim_{brick_id}_{self._claim_counter}",
                        text=claim_text,
                        confidence=0.7,  # Lower for auto-extracted
                    ))

        # If no bullet points, extract sentences that look like claims
        if not claims:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sentence in sentences[:5]:  # Limit to first 5
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 300:
                    self._claim_counter += 1
                    claims.append(Claim(
                        id=f"claim_{brick_id}_{self._claim_counter}",
                        text=sentence,
                        confidence=0.5,  # Even lower for sentence extraction
                    ))

        return claims

    def _extract_definitions(self, text: str) -> list[Definition]:
        """Extract definitions from text."""
        definitions = []

        # Look for "X is Y" patterns
        is_pattern = re.compile(r'([A-Z][a-zA-Z\s]+)\s+is\s+(.+?)\.', re.IGNORECASE)

        for match in is_pattern.finditer(text):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if len(term) < 50 and len(definition) > 10:
                definitions.append(Definition(
                    term=term,
                    text=definition,
                ))

        # Look for "X: Y" patterns (definition style)
        colon_pattern = re.compile(r'^([A-Z][a-zA-Z\s]+):\s+(.+)$', re.MULTILINE)

        for match in colon_pattern.finditer(text):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if len(term) < 50 and len(definition) > 10:
                definitions.append(Definition(
                    term=term,
                    text=definition,
                ))

        return definitions

    def compile_claim(
        self,
        text: str,
        source_id: str,
        confidence: float = 1.0,
        tags: list[str] | None = None,
    ) -> Brick:
        """
        Create a single claim brick.

        This is useful for adding individual claims programmatically.
        """
        self._brick_counter += 1
        self._claim_counter += 1

        brick_id = f"brick_manual_{self._brick_counter}"
        claim_id = f"claim_{brick_id}_{self._claim_counter}"

        claim = Claim(
            id=claim_id,
            text=text,
            confidence=confidence,
            source_refs=[source_id],
        )

        provenance = Provenance(
            source_id=source_id,
            source_type="manual",
        )

        return Brick(
            id=brick_id,
            kind=BrickKind.CLAIM,
            title=f"Claim: {text[:50]}...",
            summary=text,
            claims=[claim],
            definitions=[],
            links=[],
            provenance=provenance,
            confidence=confidence,
            tags=tags or [],
        )
