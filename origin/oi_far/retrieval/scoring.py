"""Deterministic scoring functions for retrieval."""

import math
import re
from dataclasses import dataclass
from typing import Any

from ..substrate.types import Brick, Claim


@dataclass
class ScoringWeights:
    """Configurable weights for scoring components."""
    lexical_overlap: float = 0.3
    claim_relevance: float = 0.25
    provenance_recency: float = 0.15
    confidence: float = 0.15
    constraint_alignment: float = 0.1
    definition_match: float = 0.05

    def normalize(self) -> "ScoringWeights":
        """Normalize weights to sum to 1.0."""
        total = (
            self.lexical_overlap +
            self.claim_relevance +
            self.provenance_recency +
            self.confidence +
            self.constraint_alignment +
            self.definition_match
        )
        if total == 0:
            return self
        return ScoringWeights(
            lexical_overlap=self.lexical_overlap / total,
            claim_relevance=self.claim_relevance / total,
            provenance_recency=self.provenance_recency / total,
            confidence=self.confidence / total,
            constraint_alignment=self.constraint_alignment / total,
            definition_match=self.definition_match / total,
        )


class DeterministicScorer:
    """
    Deterministic scoring for brick retrieval.

    All scoring functions are pure and deterministic:
    - Same inputs always produce same outputs
    - No randomness or external dependencies
    - Reproducible across runs
    """

    def __init__(self, weights: ScoringWeights | None = None):
        self.weights = (weights or ScoringWeights()).normalize()
        self._stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because",
            "until", "while", "although", "though", "what", "which",
            "who", "whom", "this", "that", "these", "those", "it",
        }

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text deterministically."""
        # Lowercase and extract word tokens
        text = text.lower()
        tokens = re.findall(r'\b[a-z][a-z0-9]*\b', text)
        # Remove stopwords
        tokens = [t for t in tokens if t not in self._stopwords]
        return tokens

    def score_brick(
        self,
        brick: Brick,
        query_tokens: list[str],
        constraints: list[str] | None = None,
        current_time: float = 0.0,
    ) -> tuple[float, dict[str, float]]:
        """
        Score a brick against a query.

        Args:
            brick: Brick to score
            query_tokens: Tokenized query
            constraints: Active constraints from session
            current_time: Current timestamp for recency calculation

        Returns:
            (total_score, breakdown_dict)
        """
        breakdown = {}

        # 1. Lexical overlap score
        brick_tokens = self.tokenize(f"{brick.title} {brick.summary}")
        breakdown["lexical_overlap"] = self._lexical_overlap(query_tokens, brick_tokens)

        # 2. Claim relevance score
        claim_texts = [c.text for c in brick.claims]
        breakdown["claim_relevance"] = self._claim_relevance(query_tokens, claim_texts)

        # 3. Provenance recency score
        breakdown["provenance_recency"] = self._provenance_recency(brick, current_time)

        # 4. Confidence score (direct from brick)
        breakdown["confidence"] = brick.confidence

        # 5. Constraint alignment score
        breakdown["constraint_alignment"] = self._constraint_alignment(brick, constraints or [])

        # 6. Definition match score
        breakdown["definition_match"] = self._definition_match(query_tokens, brick)

        # Calculate weighted total
        total = (
            breakdown["lexical_overlap"] * self.weights.lexical_overlap +
            breakdown["claim_relevance"] * self.weights.claim_relevance +
            breakdown["provenance_recency"] * self.weights.provenance_recency +
            breakdown["confidence"] * self.weights.confidence +
            breakdown["constraint_alignment"] * self.weights.constraint_alignment +
            breakdown["definition_match"] * self.weights.definition_match
        )

        return total, breakdown

    def _lexical_overlap(self, query_tokens: list[str], brick_tokens: list[str]) -> float:
        """Calculate lexical overlap using Jaccard-like similarity."""
        if not query_tokens or not brick_tokens:
            return 0.0

        query_set = set(query_tokens)
        brick_set = set(brick_tokens)

        intersection = len(query_set & brick_set)
        union = len(query_set | brick_set)

        if union == 0:
            return 0.0

        # Weighted by query coverage (how much of query is covered)
        query_coverage = intersection / len(query_set) if query_tokens else 0
        jaccard = intersection / union

        return 0.7 * query_coverage + 0.3 * jaccard

    def _claim_relevance(self, query_tokens: list[str], claim_texts: list[str]) -> float:
        """Score claim relevance to query."""
        if not claim_texts or not query_tokens:
            return 0.0

        query_set = set(query_tokens)
        max_score = 0.0

        for claim in claim_texts:
            claim_tokens = set(self.tokenize(claim))
            if not claim_tokens:
                continue

            overlap = len(query_set & claim_tokens)
            score = overlap / len(query_set) if query_set else 0
            max_score = max(max_score, score)

        return max_score

    def _provenance_recency(self, brick: Brick, current_time: float) -> float:
        """Score based on provenance recency."""
        if not brick.provenance or not brick.provenance.timestamp:
            return 0.5  # Neutral score for unknown age

        if current_time == 0:
            return 0.5  # No time context

        age_seconds = current_time - brick.provenance.timestamp
        age_days = age_seconds / (24 * 3600)

        # Decay function: score decreases with age
        # Half-life of 365 days
        half_life = 365
        decay = math.exp(-0.693 * age_days / half_life)

        return max(0.1, decay)  # Minimum score of 0.1

    def _constraint_alignment(self, brick: Brick, constraints: list[str]) -> float:
        """Score alignment with active constraints."""
        if not constraints:
            return 1.0  # No constraints = perfect alignment

        brick_text = f"{brick.title} {brick.summary}".lower()

        violations = 0
        for constraint in constraints:
            # Simple constraint checking: negative constraints start with "not" or "no"
            constraint_lower = constraint.lower()
            if constraint_lower.startswith("not ") or constraint_lower.startswith("no "):
                # Check if brick violates negative constraint
                forbidden = constraint_lower.replace("not ", "").replace("no ", "")
                if forbidden in brick_text:
                    violations += 1
            else:
                # Positive constraint: check if brick aligns
                if constraint_lower not in brick_text:
                    violations += 0.5  # Partial penalty for not matching

        # Convert violations to score
        if violations == 0:
            return 1.0
        return max(0.0, 1.0 - (violations * 0.2))

    def _definition_match(self, query_tokens: list[str], brick: Brick) -> float:
        """Score definition matches."""
        if not brick.definitions:
            return 0.0

        query_text = " ".join(query_tokens)
        max_score = 0.0

        for defn in brick.definitions:
            term_tokens = self.tokenize(defn.term)
            if not term_tokens:
                continue

            # Check if query is asking about this term
            term_overlap = len(set(query_tokens) & set(term_tokens))
            if term_overlap > 0:
                score = term_overlap / len(term_tokens)
                max_score = max(max_score, score)

        return max_score

    def compute_contradiction_penalty(
        self,
        brick: Brick,
        selected_bricks: list[Brick],
    ) -> float:
        """
        Compute penalty for contradictions with already-selected bricks.

        Returns penalty in [0, 1] where 0 = no contradiction, 1 = severe contradiction
        """
        if not selected_bricks:
            return 0.0

        brick_claims = set(c.text.lower() for c in brick.claims)
        penalty = 0.0

        for selected in selected_bricks:
            selected_claims = set(c.text.lower() for c in selected.claims)

            # Check for direct negation patterns
            for claim in brick_claims:
                for sel_claim in selected_claims:
                    if self._are_contradictory(claim, sel_claim):
                        penalty += 0.5

        return min(1.0, penalty)

    def _are_contradictory(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are contradictory."""
        # Simple negation detection
        negation_pairs = [
            ("is", "is not"),
            ("are", "are not"),
            ("can", "cannot"),
            ("will", "will not"),
            ("does", "does not"),
            ("has", "has not"),
            ("true", "false"),
            ("yes", "no"),
            ("always", "never"),
        ]

        for pos, neg in negation_pairs:
            if pos in claim1 and neg in claim2:
                # Check if rest of claim is similar
                c1_clean = claim1.replace(pos, "").strip()
                c2_clean = claim2.replace(neg, "").strip()
                if self._similar_text(c1_clean, c2_clean):
                    return True
            if neg in claim1 and pos in claim2:
                c1_clean = claim1.replace(neg, "").strip()
                c2_clean = claim2.replace(pos, "").strip()
                if self._similar_text(c1_clean, c2_clean):
                    return True

        return False

    def _similar_text(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar."""
        tokens1 = set(self.tokenize(text1))
        tokens2 = set(self.tokenize(text2))

        if not tokens1 or not tokens2:
            return False

        overlap = len(tokens1 & tokens2)
        similarity = overlap / max(len(tokens1), len(tokens2))

        return similarity > 0.6
