"""No-new-claims enforcement for renderer output."""

import re
from typing import Any

from ..reasoning.types import AnswerPlan


class ClaimChecker:
    """
    Enforces the no-new-claims invariant for rendered output.

    The renderer may paraphrase but MUST NOT add new factual claims.
    This checker verifies that all claims in output can be traced
    to claims in the AnswerPlan.
    """

    def __init__(self):
        # Patterns that indicate factual claims
        self._claim_patterns = [
            r'\b(?:is|are|was|were)\s+(?:a|an|the)?\s*\w+',  # "X is Y"
            r'\b(?:has|have|had)\s+\w+',  # "X has Y"
            r'\b(?:can|could|will|would)\s+\w+',  # "X can Y"
            r'\b(?:contains?|includes?)\s+\w+',  # "X contains Y"
            r'\b\d+(?:\.\d+)?\s*(?:%|percent|times|years?|days?)',  # Numbers
            r'\bin\s+\d{4}\b',  # Years
            r'\b(?:always|never|every|all|none)\b',  # Universals
        ]

        # Patterns that are OK (meta-statements, not claims)
        self._safe_patterns = [
            r'^UNKNOWN\b',
            r'^FAILED\b',
            r'\bMissing:',
            r'\bWould help:',
            r'\b(?:See|Sources?|References?):',
            r'^##',  # Markdown headers
            r'^-\s+',  # List items (often references)
            r'\bConfidence:',
            r'\bNote:',
        ]

    def check(
        self,
        rendered_text: str,
        answer_plan: AnswerPlan,
    ) -> tuple[bool, list[str]]:
        """
        Check if rendered text contains only claims from answer plan.

        Args:
            rendered_text: The rendered output
            answer_plan: The source answer plan

        Returns:
            (passed, violations) where violations are new claims found
        """
        violations = []

        # Extract approved claims from answer plan
        approved_claims = self._extract_approved_claims(answer_plan)

        # Extract claims from rendered text
        rendered_claims = self._extract_claims(rendered_text)

        # Check each rendered claim
        for claim in rendered_claims:
            if not self._is_approved(claim, approved_claims):
                violations.append(claim)

        return len(violations) == 0, violations

    def _extract_approved_claims(self, answer_plan: AnswerPlan) -> set[str]:
        """Extract all approved claims from answer plan."""
        approved = set()

        # Component content
        for component in answer_plan.components:
            approved.add(self._normalize(component.content))
            # Also add substrings for paraphrase tolerance
            words = component.content.split()
            for i in range(len(words)):
                for j in range(i + 3, min(i + 10, len(words) + 1)):
                    approved.add(self._normalize(" ".join(words[i:j])))

        # Source claims
        for claim in answer_plan.source_claims:
            approved.add(self._normalize(claim))

        # Unknowns (these are approved meta-claims)
        for unknown in answer_plan.unknowns:
            approved.add(self._normalize(unknown))

        # Assumptions (approved meta-claims)
        for assumption in answer_plan.assumptions:
            approved.add(self._normalize(assumption.description))
            approved.add(self._normalize(assumption.what_would_refute))

        return approved

    def _extract_claims(self, text: str) -> list[str]:
        """Extract factual claims from text."""
        claims = []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            sentence = sentence.strip()

            # Skip safe patterns
            if any(re.search(p, sentence, re.IGNORECASE) for p in self._safe_patterns):
                continue

            # Check if sentence contains claim patterns
            for pattern in self._claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append(sentence)
                    break

        return claims

    def _is_approved(self, claim: str, approved: set[str]) -> bool:
        """Check if a claim is approved (matches or paraphrases approved)."""
        normalized = self._normalize(claim)

        # Direct match
        if normalized in approved:
            return True

        # Substring match (claim is part of approved content)
        for approved_claim in approved:
            if normalized in approved_claim or approved_claim in normalized:
                return True

        # Token overlap (paraphrase detection)
        claim_tokens = set(normalized.split())
        for approved_claim in approved:
            approved_tokens = set(approved_claim.split())
            if len(claim_tokens) > 2 and len(approved_tokens) > 2:
                overlap = len(claim_tokens & approved_tokens)
                similarity = overlap / max(len(claim_tokens), len(approved_tokens))
                if similarity > 0.7:
                    return True

        return False

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def count_claims(self, text: str) -> int:
        """Count the number of claims in text."""
        return len(self._extract_claims(text))
