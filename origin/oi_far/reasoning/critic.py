"""Critic for evaluating answer plans."""

from ..retrieval.types import ContextPack
from .types import (
    AnswerPlan,
    AnswerStatus,
    Assumption,
    CriticFix,
    CriticResult,
)


class DeterministicCritic:
    """
    Critic that evaluates answer plans for correctness and completeness.

    Performs:
    - Contradiction scanning
    - Missing support detection
    - Assumption ledger maintenance
    - Fix suggestions

    All evaluation is deterministic: same input -> same result.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.3,
        max_unsupported_claims: int = 2,
    ):
        self.min_confidence_threshold = min_confidence_threshold
        self.max_unsupported_claims = max_unsupported_claims

    def critic(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> CriticResult:
        """
        Evaluate an answer plan.

        Args:
            answer_plan: The answer to evaluate
            context: Original context pack

        Returns:
            CriticResult with pass/fail and fixes
        """
        fixes = []

        # 1. Contradiction scan
        contradictions = self._scan_contradictions(answer_plan, context)

        # 2. Missing support scan
        unsupported = self._scan_missing_support(answer_plan, context)

        # 3. Build assumption ledger
        assumption_ledger = self._build_assumption_ledger(answer_plan, context)

        # 4. Check confidence threshold
        confidence_issues = self._check_confidence(answer_plan)

        # 5. Generate fixes
        fixes.extend(contradictions["fixes"])
        fixes.extend(unsupported["fixes"])
        fixes.extend(confidence_issues["fixes"])

        # 6. Determine what's needed
        needed_sources = self._identify_needed_sources(answer_plan, context)
        needed_claims = self._identify_needed_claims(answer_plan, context)

        # 7. Check missing assumptions
        missing_assumptions = self._check_missing_assumptions(answer_plan)

        # Determine pass/fail
        passed = (
            contradictions["count"] == 0 and
            unsupported["count"] <= self.max_unsupported_claims and
            answer_plan.status != AnswerStatus.FAILED and
            len(confidence_issues["fixes"]) == 0
        )

        return CriticResult(
            passed=passed,
            fixes=fixes,
            contradiction_count=contradictions["count"],
            unsupported_claim_count=unsupported["count"],
            missing_assumptions=missing_assumptions,
            needed_sources=needed_sources,
            needed_claims=needed_claims,
            assumption_ledger=assumption_ledger,
        )

    def _scan_contradictions(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> dict:
        """Scan for contradictions in the answer."""
        fixes = []
        count = 0

        # Check context conflicts
        for conflict in context.conflicts:
            count += 1
            fixes.append(CriticFix(
                fix_type="resolve_conflict",
                target=f"{conflict.item1_id} vs {conflict.item2_id}",
                description=conflict.description,
                severity="error",
            ))

        # Check for self-contradictions in components
        claims = []
        for component in answer_plan.components:
            claims.append(component.content.lower())

        # Simple negation check
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i + 1:]:
                if self._are_contradictory(claim1, claim2):
                    count += 1
                    fixes.append(CriticFix(
                        fix_type="remove_contradiction",
                        target=claim1[:50],
                        description=f"Contradicts: {claim2[:50]}",
                        severity="error",
                    ))

        return {"count": count, "fixes": fixes}

    def _are_contradictory(self, claim1: str, claim2: str) -> bool:
        """Check if two claims contradict each other."""
        # Simple pattern matching for contradictions
        negation_patterns = [
            ("is", "is not"),
            ("are", "are not"),
            ("can", "cannot"),
            ("will", "will not"),
            ("true", "false"),
            ("yes", "no"),
            ("always", "never"),
            ("all", "none"),
        ]

        for pos, neg in negation_patterns:
            # Check if one claim has positive and other has negative
            if f" {pos} " in claim1 and f" {neg} " in claim2:
                # Check if they're about the same thing
                words1 = set(claim1.split())
                words2 = set(claim2.split())
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap > 0.5:
                    return True

            if f" {neg} " in claim1 and f" {pos} " in claim2:
                words1 = set(claim1.split())
                words2 = set(claim2.split())
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap > 0.5:
                    return True

        return False

    def _scan_missing_support(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> dict:
        """Scan for claims without supporting evidence."""
        fixes = []
        count = 0

        for component in answer_plan.components:
            if not component.supporting_bricks or all(b == "" for b in component.supporting_bricks):
                count += 1
                fixes.append(CriticFix(
                    fix_type="add_source",
                    target=component.content[:50],
                    description="No supporting brick for this claim",
                    severity="warning",
                ))

        # Check source claims
        brick_ids = set(context.top_bricks[i].brick_id for i in range(len(context.top_bricks)))
        for claim in answer_plan.source_claims:
            # Check if claim can be traced to a brick
            claim_found = False
            for brick in context.top_bricks:
                if claim in brick.claims:
                    claim_found = True
                    break

            if not claim_found and claim:
                count += 1
                fixes.append(CriticFix(
                    fix_type="verify_claim",
                    target=claim[:50] if len(claim) > 50 else claim,
                    description="Claim not traceable to source brick",
                    severity="warning",
                ))

        return {"count": count, "fixes": fixes}

    def _build_assumption_ledger(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> list[Assumption]:
        """Build ledger of all assumptions made."""
        ledger = []

        # Include explicit assumptions from plan
        ledger.extend(answer_plan.assumptions)

        # Add implicit assumptions based on context gaps
        if context.known_unknowns:
            for i, unknown in enumerate(context.known_unknowns):
                ledger.append(Assumption(
                    id=f"implicit_{i}",
                    description=f"Assuming answer is valid despite unknown: {unknown.question}",
                    confidence=0.5,
                    what_would_refute=f"Finding information about: {unknown.topic}",
                    source="inferred",
                ))

        # Add assumptions about conflicts
        if context.conflicts:
            ledger.append(Assumption(
                id="conflict_resolution",
                description="Assuming most recent/confident source is correct",
                confidence=0.7,
                what_would_refute="Finding authoritative older source",
                source="inferred",
            ))

        return ledger

    def _check_confidence(self, answer_plan: AnswerPlan) -> dict:
        """Check confidence levels."""
        fixes = []

        if answer_plan.overall_confidence < self.min_confidence_threshold:
            fixes.append(CriticFix(
                fix_type="flag_low_confidence",
                target="overall_answer",
                description=f"Overall confidence {answer_plan.overall_confidence:.2f} below threshold {self.min_confidence_threshold}",
                severity="warning",
            ))

        # Check individual components
        for component in answer_plan.components:
            if component.confidence < 0.2:
                fixes.append(CriticFix(
                    fix_type="flag_low_confidence",
                    target=component.content[:30],
                    description=f"Component confidence very low: {component.confidence:.2f}",
                    severity="warning",
                ))

        return {"fixes": fixes}

    def _identify_needed_sources(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> list[str]:
        """Identify what sources would improve the answer."""
        needed = []

        # Based on unknowns
        for unknown in context.known_unknowns:
            for help_item in unknown.what_would_help:
                if help_item not in needed:
                    needed.append(help_item)

        # Based on low confidence components
        for component in answer_plan.components:
            if component.confidence < 0.5 and not component.supporting_bricks:
                needed.append(f"Source for: {component.content[:40]}...")

        # Based on query coverage
        if answer_plan.claim_coverage < 0.5:
            needed.append("Additional sources to improve claim coverage")

        return needed[:10]  # Limit

    def _identify_needed_claims(
        self,
        answer_plan: AnswerPlan,
        context: ContextPack,
    ) -> list[str]:
        """Identify what claims would help."""
        needed = []

        # Claims that would resolve conflicts
        for conflict in context.conflicts:
            needed.append(f"Authoritative claim to resolve: {conflict.description[:40]}")

        # Claims for uncovered query aspects
        for unknown in answer_plan.unknowns:
            needed.append(f"Claim addressing: {unknown[:40]}")

        return needed[:10]  # Limit

    def _check_missing_assumptions(self, answer_plan: AnswerPlan) -> list[str]:
        """Check for assumptions that should be explicit but aren't."""
        missing = []

        # If answer has deductions but no deduction assumptions
        has_deductions = any(
            r.output and "deductions" in r.output and r.output["deductions"]
            for r in answer_plan.step_results
        )
        has_deduction_assumption = any(
            "combine" in a.description.lower() or "deduc" in a.description.lower()
            for a in answer_plan.assumptions
        )

        if has_deductions and not has_deduction_assumption:
            missing.append("Missing assumption about combining claims from different sources")

        # If using low-confidence sources
        low_conf_bricks = [
            b for b in answer_plan.source_bricks
            if any(
                brick.brick_id == b and brick.confidence < 0.5
                for brick in answer_plan.components
                for brick in []  # Would need context
            )
        ]
        if answer_plan.overall_confidence < 0.6 and not any(
            "confidence" in a.description.lower() for a in answer_plan.assumptions
        ):
            missing.append("Missing assumption about reliability of low-confidence sources")

        return missing

    def apply_fixes(
        self,
        answer_plan: AnswerPlan,
        fixes: list[CriticFix],
    ) -> AnswerPlan:
        """
        Apply fixes to an answer plan.

        Note: This creates a new plan with fixes applied.
        Not all fixes can be automatically applied.
        """
        # Create a copy of components
        new_components = []

        for component in answer_plan.components:
            should_remove = False

            for fix in fixes:
                if fix.fix_type == "remove_contradiction":
                    if component.content.lower().startswith(fix.target.lower()):
                        should_remove = True
                        break

            if not should_remove:
                new_components.append(component)

        # Add flag for low confidence if needed
        new_unknowns = list(answer_plan.unknowns)
        for fix in fixes:
            if fix.fix_type == "flag_low_confidence":
                new_unknowns.append(f"Low confidence: {fix.target}")

        # Add missing assumptions
        new_assumptions = list(answer_plan.assumptions)
        for fix in fixes:
            if fix.fix_type == "add_source":
                new_assumptions.append(Assumption(
                    id=f"fix_assumption_{len(new_assumptions)}",
                    description=f"Assumed valid without source: {fix.target}",
                    confidence=0.4,
                    what_would_refute="Finding contradicting source",
                    source="fix_applied",
                ))

        # Adjust status if needed
        new_status = answer_plan.status
        error_fixes = [f for f in fixes if f.severity == "error"]
        if error_fixes and answer_plan.status == AnswerStatus.COMPLETE:
            new_status = AnswerStatus.PARTIAL

        return AnswerPlan(
            query=answer_plan.query,
            intent=answer_plan.intent,
            status=new_status,
            components=new_components,
            source_bricks=answer_plan.source_bricks,
            source_claims=answer_plan.source_claims,
            assumptions=new_assumptions,
            unknowns=new_unknowns,
            plan_steps=answer_plan.plan_steps,
            step_results=answer_plan.step_results,
            overall_confidence=answer_plan.overall_confidence,
            claim_coverage=answer_plan.claim_coverage,
            reasoning_time_ms=answer_plan.reasoning_time_ms,
        )
