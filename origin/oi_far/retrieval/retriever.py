"""Deterministic retrieval pipeline."""

import re
import time
from typing import Any

from ..kernel.session import SessionState
from ..substrate.brick_store import BrickStore
from ..substrate.document_store import DocumentStore
from ..substrate.types import Brick
from .scoring import DeterministicScorer, ScoringWeights
from .types import (
    ActiveConstraint,
    Conflict,
    ConflictType,
    ContextPack,
    KnownUnknown,
    RetrievedBrick,
    RetrievedSource,
)


class DeterministicRetriever:
    """
    Deterministic retrieval pipeline.

    This is the core RAG component that:
    1. Parses and classifies queries
    2. Retrieves relevant bricks and sources
    3. Scores and ranks results deterministically
    4. Detects conflicts and knowledge gaps
    5. Builds a ContextPack for reasoning

    All operations are deterministic: same inputs -> same outputs.
    """

    def __init__(
        self,
        brick_store: BrickStore,
        document_store: DocumentStore,
        scorer: DeterministicScorer | None = None,
        max_bricks: int = 20,
        max_sources: int = 10,
    ):
        self.brick_store = brick_store
        self.document_store = document_store
        self.scorer = scorer or DeterministicScorer()
        self.max_bricks = max_bricks
        self.max_sources = max_sources

        # Intent classification patterns (deterministic regex)
        self._intent_patterns = [
            (r'^(what is|define|explain)\s+', "define"),
            (r'^(how|why|when|where)\s+', "explain"),
            (r'^(compare|difference|versus|vs)\s+', "compare"),
            (r'^(find|search|list|show)\s+', "find"),
            (r'^(prove|verify|confirm|check)\s+', "prove"),
            (r'^(is it true|does|can|will)\s+', "verify"),
        ]

    def retrieve(
        self,
        query: str,
        session_state: SessionState | None = None,
    ) -> ContextPack:
        """
        Retrieve context for a query.

        Args:
            query: User query string
            session_state: Current session state (optional)

        Returns:
            ContextPack with all retrieved context
        """
        timestamp = time.time()

        # 1. Parse query
        query_tokens = self.scorer.tokenize(query)
        query_intent = self._classify_intent(query)

        # 2. Get active constraints from session
        active_constraints = self._get_active_constraints(session_state)
        constraint_texts = [c.description for c in active_constraints]

        # 3. Retrieve candidate bricks
        candidate_bricks = self._retrieve_candidate_bricks(query, query_tokens)

        # 4. Score and rank bricks
        scored_bricks = []
        for brick in candidate_bricks:
            score, breakdown = self.scorer.score_brick(
                brick,
                query_tokens,
                constraint_texts,
                timestamp,
            )
            scored_bricks.append((brick, score, breakdown))

        # Sort by score descending, then by ID for determinism
        scored_bricks.sort(key=lambda x: (-x[1], x[0].id))

        # 5. Select top bricks with contradiction penalty
        selected_bricks: list[tuple[Brick, float, dict]] = []
        for brick, score, breakdown in scored_bricks:
            if len(selected_bricks) >= self.max_bricks:
                break

            # Apply contradiction penalty
            penalty = self.scorer.compute_contradiction_penalty(
                brick,
                [b for b, _, _ in selected_bricks],
            )
            adjusted_score = score * (1.0 - penalty * 0.5)

            if adjusted_score > 0.1:  # Minimum threshold
                selected_bricks.append((brick, adjusted_score, breakdown))

        # 6. Convert to RetrievedBrick objects
        top_bricks = [
            RetrievedBrick(
                brick_id=brick.id,
                title=brick.title,
                summary=brick.summary,
                claims=[c.text for c in brick.claims],
                score=score,
                score_breakdown=breakdown,
                provenance=brick.provenance.to_dict() if brick.provenance else {},
                confidence=brick.confidence,
            )
            for brick, score, breakdown in selected_bricks
        ]

        # 7. Retrieve relevant sources
        top_sources = self._retrieve_sources(query, query_tokens)

        # 8. Detect conflicts
        conflicts = self._detect_conflicts(top_bricks)

        # 9. Identify knowledge gaps
        known_unknowns = self._identify_unknowns(query, query_tokens, top_bricks)

        # 10. Get relevant commitments from session
        relevant_commitments = self._get_relevant_commitments(session_state, query_tokens)

        return ContextPack(
            query=query,
            query_tokens=query_tokens,
            query_intent=query_intent,
            top_bricks=top_bricks,
            top_sources=top_sources,
            known_unknowns=known_unknowns,
            conflicts=conflicts,
            active_constraints=active_constraints,
            relevant_commitments=relevant_commitments,
            retrieval_timestamp=timestamp,
            total_bricks_scanned=len(candidate_bricks),
            total_sources_scanned=self.document_store.count(),
        )

    def _classify_intent(self, query: str) -> str:
        """Classify query intent deterministically."""
        query_lower = query.lower().strip()

        for pattern, intent in self._intent_patterns:
            if re.match(pattern, query_lower):
                return intent

        # Default to "unknown" if no pattern matches
        return "unknown"

    def _get_active_constraints(self, session_state: SessionState | None) -> list[ActiveConstraint]:
        """Extract active constraints from session state."""
        if not session_state:
            return []

        constraints = []

        # User-specified constraints
        for constraint in session_state.constraints:
            constraints.append(ActiveConstraint(
                constraint_id=constraint.id if hasattr(constraint, 'id') else f"user_{len(constraints)}",
                description=constraint.description if hasattr(constraint, 'description') else str(constraint),
                source="user",
            ))

        # System constraints from prefs
        if getattr(session_state.user_prefs, 'strict_sourcing', False):
            constraints.append(ActiveConstraint(
                constraint_id="sys_strict_sourcing",
                description="All claims must have explicit source citations",
                source="system",
            ))

        return constraints

    def _retrieve_candidate_bricks(
        self,
        query: str,
        query_tokens: list[str],
    ) -> list[Brick]:
        """Retrieve candidate bricks using available indexes."""
        candidates = []
        seen_ids = set()

        # 1. Lexical search
        lexical_hits = self.brick_store.search_lexical(query, limit=self.max_bricks * 3)
        for hit in lexical_hits:
            brick_id = hit.brick_id
            if brick_id not in seen_ids:
                brick = self.brick_store.get(brick_id)
                if brick:
                    candidates.append(brick)
                    seen_ids.add(brick_id)

        # 2. Graph traversal for related concepts
        for hit in lexical_hits[:5]:  # Top 5 seed bricks
            related_bricks = self.brick_store.find_related(hit.brick_id)
            for related_brick in related_bricks:
                if related_brick.id not in seen_ids:
                    candidates.append(related_brick)
                    seen_ids.add(related_brick.id)

        # 3. Tag-based retrieval
        for token in query_tokens[:3]:  # Top 3 tokens as potential tags
            tagged = self.brick_store.get_by_tag(token)
            for brick in tagged:
                if brick.id not in seen_ids:
                    candidates.append(brick)
                    seen_ids.add(brick.id)

        return candidates

    def _retrieve_sources(
        self,
        query: str,
        query_tokens: list[str],
    ) -> list[RetrievedSource]:
        """Retrieve relevant source documents."""
        sources = []

        # Search document store
        doc_hits = self.document_store.search(query, limit=self.max_sources)

        for doc, score in doc_hits:
            # Extract relevant excerpt
            excerpt = self._extract_excerpt(doc.content, query_tokens)

            sources.append(RetrievedSource(
                source_id=doc.id,
                title=doc.title,
                relevance_score=score,
                excerpt=excerpt,
                path=doc.source_path,
            ))

        return sources

    def _extract_excerpt(self, content: str, query_tokens: list[str]) -> str:
        """Extract relevant excerpt from content."""
        if not content:
            return ""

        # Find sentence containing most query tokens
        sentences = re.split(r'(?<=[.!?])\s+', content)

        best_sentence = ""
        best_score = 0

        for sentence in sentences:
            sentence_tokens = set(self.scorer.tokenize(sentence))
            overlap = len(set(query_tokens) & sentence_tokens)
            if overlap > best_score:
                best_score = overlap
                best_sentence = sentence

        if best_sentence:
            # Truncate if too long
            if len(best_sentence) > 300:
                return best_sentence[:297] + "..."
            return best_sentence

        # Fallback to first 200 chars
        return content[:200] + "..." if len(content) > 200 else content

    def _detect_conflicts(self, bricks: list[RetrievedBrick]) -> list[Conflict]:
        """Detect conflicts between retrieved bricks."""
        conflicts = []

        # Check each pair of bricks
        for i, brick1 in enumerate(bricks):
            for brick2 in bricks[i + 1:]:
                # Check claim contradictions
                for claim1 in brick1.claims:
                    for claim2 in brick2.claims:
                        if self.scorer._are_contradictory(claim1.lower(), claim2.lower()):
                            conflicts.append(Conflict(
                                conflict_type=ConflictType.CONTRADICTION,
                                item1_id=brick1.brick_id,
                                item2_id=brick2.brick_id,
                                description=f"Contradictory claims: '{claim1[:50]}...' vs '{claim2[:50]}...'",
                                resolution_hint="Check source provenance and recency",
                            ))

        return conflicts

    def _identify_unknowns(
        self,
        query: str,
        query_tokens: list[str],
        bricks: list[RetrievedBrick],
    ) -> list[KnownUnknown]:
        """Identify knowledge gaps."""
        unknowns = []

        # Check if any query tokens are not covered by retrieved bricks
        covered_tokens = set()
        for brick in bricks:
            brick_tokens = self.scorer.tokenize(f"{brick.title} {brick.summary}")
            covered_tokens.update(brick_tokens)

        uncovered = set(query_tokens) - covered_tokens
        if uncovered:
            unknowns.append(KnownUnknown(
                topic=query,
                question=f"No information found for: {', '.join(sorted(uncovered))}",
                what_would_help=[
                    f"Documents containing: {', '.join(sorted(uncovered))}",
                    "Related concept definitions",
                ],
            ))

        # Check if retrieved bricks have low confidence
        low_confidence_bricks = [b for b in bricks if b.confidence < 0.5]
        if low_confidence_bricks and len(low_confidence_bricks) == len(bricks):
            unknowns.append(KnownUnknown(
                topic=query,
                question="All retrieved information has low confidence",
                what_would_help=[
                    "Higher-confidence sources",
                    "Verification of existing claims",
                ],
                confidence_if_resolved=0.8,
            ))

        return unknowns

    def _get_relevant_commitments(
        self,
        session_state: SessionState | None,
        query_tokens: list[str],
    ) -> list[str]:
        """Get commitment IDs relevant to the query."""
        if not session_state:
            return []

        relevant = []
        for commitment in session_state.commitment_tracker.get_active():
            commitment_tokens = self.scorer.tokenize(commitment.description)
            overlap = len(set(query_tokens) & set(commitment_tokens))
            if overlap > 0:
                relevant.append(commitment.id)

        return relevant
