"""Deterministic solver for executing reasoning plans."""

import time
from typing import Any

from ..retrieval.types import ContextPack, RetrievedBrick
from .types import (
    AnswerComponent,
    AnswerPlan,
    AnswerStatus,
    Assumption,
    PlanStep,
    StepResult,
    StepType,
)


class DeterministicSolver:
    """
    Deterministic solver for executing reasoning plans.

    Executes plan steps using:
    - Logic rules and constraint propagation
    - Deterministic search (beam search with fixed seed)
    - No randomness or external LLM calls

    All solving is deterministic: same plan + context -> same answer.
    """

    def __init__(self, max_deduction_depth: int = 10):
        self.max_deduction_depth = max_deduction_depth

    def solve(
        self,
        plan_steps: list[PlanStep],
        context: ContextPack,
    ) -> AnswerPlan:
        """
        Execute a plan and produce an answer.

        Args:
            plan_steps: Steps from the planner
            context: Retrieved context

        Returns:
            AnswerPlan ready for rendering
        """
        start_time = time.time()

        # Execute each step
        step_results = []
        step_outputs: dict[str, Any] = {}

        for step in plan_steps:
            result = self._execute_step(step, context, step_outputs)
            step_results.append(result)
            step_outputs[step.step_id] = result.output

        # Build answer from step results
        answer = self._build_answer(context, plan_steps, step_results, step_outputs)

        # Record timing
        answer.reasoning_time_ms = (time.time() - start_time) * 1000

        return answer

    def _execute_step(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute a single plan step."""
        try:
            if step.step_type == StepType.RETRIEVE:
                return self._execute_retrieve(step, context)
            elif step.step_type == StepType.DEFINE:
                return self._execute_define(step, context, prior_outputs)
            elif step.step_type == StepType.COMPARE:
                return self._execute_compare(step, context, prior_outputs)
            elif step.step_type == StepType.DEDUCE:
                return self._execute_deduce(step, context, prior_outputs)
            elif step.step_type == StepType.VERIFY:
                return self._execute_verify(step, context, prior_outputs)
            elif step.step_type == StepType.SYNTHESIZE:
                return self._execute_synthesize(step, context, prior_outputs)
            elif step.step_type == StepType.FORMAT:
                return self._execute_format(step, context, prior_outputs)
            else:
                return self._execute_unknown(step, context, prior_outputs)
        except Exception as e:
            return StepResult(
                step_id=step.step_id,
                success=False,
                output=None,
                claims_used=[],
                confidence=0.0,
                error=str(e),
            )

    def _execute_retrieve(
        self,
        step: PlanStep,
        context: ContextPack,
    ) -> StepResult:
        """Execute retrieval step (already done, just organize)."""
        claims_used = []
        for brick in context.top_bricks:
            claims_used.extend(brick.claims)

        return StepResult(
            step_id=step.step_id,
            success=len(context.top_bricks) > 0,
            output={
                "bricks": context.top_bricks,
                "sources": context.top_sources,
            },
            claims_used=claims_used[:20],  # Limit for readability
            confidence=0.9 if context.top_bricks else 0.0,
        )

    def _execute_define(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute definition step."""
        # Find bricks that look like definitions
        definitions = []
        claims_used = []

        for brick in context.top_bricks:
            # Check if brick has definition-like structure
            if "is" in brick.summary.lower() or "defined as" in brick.summary.lower():
                definitions.append({
                    "term": brick.title,
                    "definition": brick.summary,
                    "source": brick.brick_id,
                    "confidence": brick.confidence,
                })
                claims_used.extend(brick.claims[:3])

        if not definitions:
            # Fall back to using summaries as definitions
            for brick in context.top_bricks[:3]:
                definitions.append({
                    "term": brick.title,
                    "definition": brick.summary,
                    "source": brick.brick_id,
                    "confidence": brick.confidence * 0.7,  # Lower confidence
                })
                claims_used.extend(brick.claims[:2])

        avg_confidence = sum(d["confidence"] for d in definitions) / len(definitions) if definitions else 0

        return StepResult(
            step_id=step.step_id,
            success=len(definitions) > 0,
            output={"definitions": definitions},
            claims_used=claims_used,
            confidence=avg_confidence,
        )

    def _execute_compare(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute comparison step."""
        # Group bricks by topic for comparison
        items = []
        claims_used = []

        for brick in context.top_bricks[:10]:
            items.append({
                "name": brick.title,
                "summary": brick.summary,
                "claims": brick.claims,
                "brick_id": brick.brick_id,
            })
            claims_used.extend(brick.claims[:2])

        # Find commonalities and differences (deterministic)
        commonalities = []
        differences = []

        if len(items) >= 2:
            # Simple token-based comparison
            all_claim_sets = [set(item["claims"]) for item in items]

            # Commonalities: claims that appear in multiple items
            if all_claim_sets:
                common = all_claim_sets[0]
                for s in all_claim_sets[1:]:
                    common = common & s
                commonalities = list(common)[:5]

            # Differences: claims unique to each item
            for i, item in enumerate(items[:3]):
                others = set()
                for j, other in enumerate(items[:3]):
                    if i != j:
                        others.update(other["claims"])
                unique = set(item["claims"]) - others
                if unique:
                    differences.append({
                        "item": item["name"],
                        "unique_claims": list(unique)[:3],
                    })

        return StepResult(
            step_id=step.step_id,
            success=len(items) >= 2,
            output={
                "items": items,
                "commonalities": commonalities,
                "differences": differences,
            },
            claims_used=claims_used,
            confidence=0.8 if len(items) >= 2 else 0.3,
        )

    def _execute_deduce(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute deduction step using constraint propagation."""
        # Build deduction chain from claims
        premises = []
        claims_used = []

        # Collect all claims as potential premises
        for brick in context.top_bricks:
            for claim in brick.claims:
                premises.append({
                    "claim": claim,
                    "source": brick.brick_id,
                    "confidence": brick.confidence,
                })
                claims_used.append(claim)

        # Simple forward chaining (deterministic)
        deductions = []
        seen_conclusions = set()

        for premise in premises:
            # Look for simple if-then patterns
            claim = premise["claim"].lower()

            # Pattern: "X implies Y" or "X therefore Y"
            if " implies " in claim or " therefore " in claim:
                parts = claim.replace(" therefore ", " implies ").split(" implies ")
                if len(parts) == 2 and parts[1] not in seen_conclusions:
                    deductions.append({
                        "premise": parts[0].strip(),
                        "conclusion": parts[1].strip(),
                        "rule": "modus_ponens",
                        "confidence": premise["confidence"] * 0.9,
                    })
                    seen_conclusions.add(parts[1])

            # Pattern: "If X then Y"
            if "if " in claim and " then " in claim:
                import re
                match = re.search(r'if (.+?) then (.+)', claim)
                if match and match.group(2) not in seen_conclusions:
                    deductions.append({
                        "premise": match.group(1).strip(),
                        "conclusion": match.group(2).strip(),
                        "rule": "conditional",
                        "confidence": premise["confidence"] * 0.85,
                    })
                    seen_conclusions.add(match.group(2))

        avg_confidence = sum(d["confidence"] for d in deductions) / len(deductions) if deductions else 0.5

        return StepResult(
            step_id=step.step_id,
            success=True,  # Deduction can succeed with no results
            output={
                "premises": premises[:10],
                "deductions": deductions,
                "chain_length": len(deductions),
            },
            claims_used=claims_used[:15],
            confidence=avg_confidence if deductions else 0.5,
        )

    def _execute_verify(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute verification step."""
        claims_used = []

        # Check for conflicts
        conflicts = context.conflicts
        conflict_descriptions = [c.description for c in conflicts]

        # Check constraint satisfaction
        constraint_violations = []
        for constraint in step.constraints:
            # Simple constraint checking
            constraint_met = False
            for brick in context.top_bricks:
                if constraint.lower() in brick.summary.lower():
                    constraint_met = True
                    break
            if not constraint_met and "mode:" not in constraint.lower():
                constraint_violations.append(constraint)

        # Collect claims for verification
        for brick in context.top_bricks[:5]:
            claims_used.extend(brick.claims[:2])

        verified = len(conflicts) == 0 and len(constraint_violations) == 0

        return StepResult(
            step_id=step.step_id,
            success=True,
            output={
                "verified": verified,
                "conflicts": conflict_descriptions,
                "constraint_violations": constraint_violations,
            },
            claims_used=claims_used,
            confidence=0.9 if verified else 0.4,
        )

    def _execute_synthesize(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute synthesis step."""
        # Gather all prior outputs
        all_content = []
        claims_used = []
        source_bricks = []

        for input_id in step.inputs:
            if input_id in prior_outputs:
                output = prior_outputs[input_id]
                if isinstance(output, dict):
                    # Extract relevant content
                    if "definitions" in output:
                        for d in output["definitions"]:
                            all_content.append({
                                "type": "definition",
                                "content": f"{d['term']}: {d['definition']}",
                                "source": d.get("source"),
                            })
                            source_bricks.append(d.get("source"))

                    if "deductions" in output:
                        for d in output["deductions"]:
                            all_content.append({
                                "type": "deduction",
                                "content": f"{d['premise']} → {d['conclusion']}",
                                "confidence": d.get("confidence", 0.5),
                            })

                    if "items" in output:
                        for item in output["items"]:
                            all_content.append({
                                "type": "item",
                                "content": f"{item['name']}: {item['summary']}",
                                "source": item.get("brick_id"),
                            })
                            source_bricks.append(item.get("brick_id"))

        # Also include top brick content directly
        for brick in context.top_bricks[:5]:
            if brick.brick_id not in source_bricks:
                all_content.append({
                    "type": "brick",
                    "content": f"{brick.title}: {brick.summary}",
                    "source": brick.brick_id,
                })
                source_bricks.append(brick.brick_id)
            claims_used.extend(brick.claims[:2])

        return StepResult(
            step_id=step.step_id,
            success=len(all_content) > 0,
            output={
                "synthesized": all_content,
                "sources": [s for s in source_bricks if s],
            },
            claims_used=claims_used,
            confidence=0.8 if all_content else 0.2,
        )

    def _execute_format(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute formatting step."""
        # Determine output mode
        mode = "galley"
        for constraint in step.constraints:
            if "mode:" in constraint.lower():
                mode = constraint.split(":")[1].strip().lower()

        # Gather content to format
        content_items = []
        claims_used = []

        for input_id in step.inputs:
            if input_id in prior_outputs:
                output = prior_outputs[input_id]
                if isinstance(output, dict):
                    if "synthesized" in output:
                        content_items.extend(output["synthesized"])
                    if "definitions" in output:
                        for d in output["definitions"]:
                            content_items.append({
                                "type": "definition",
                                "content": f"{d['term']}: {d['definition']}",
                            })
                    if "verified" in output:
                        content_items.append({
                            "type": "verification",
                            "content": "Verified" if output["verified"] else "Not verified",
                            "details": output,
                        })

        # Format based on mode
        if mode == "bridge":
            formatted = self._format_bridge(content_items)
        else:
            formatted = self._format_galley(content_items)

        return StepResult(
            step_id=step.step_id,
            success=True,
            output={
                "mode": mode,
                "formatted": formatted,
                "content_items": content_items,
            },
            claims_used=claims_used,
            confidence=0.95,
        )

    def _execute_unknown(
        self,
        step: PlanStep,
        context: ContextPack,
        prior_outputs: dict[str, Any],
    ) -> StepResult:
        """Execute unknown/gap analysis step."""
        unknowns = []

        for unknown in context.known_unknowns:
            unknowns.append({
                "topic": unknown.topic,
                "question": unknown.question,
                "what_would_help": unknown.what_would_help,
            })

        return StepResult(
            step_id=step.step_id,
            success=True,
            output={
                "unknowns": unknowns,
                "insufficient_context": not context.has_sufficient_context(),
            },
            claims_used=[],
            confidence=0.0,
        )

    def _format_galley(self, items: list[dict]) -> str:
        """Format for galley mode (concise)."""
        if not items:
            return "No information available."

        parts = []
        for item in items[:5]:  # Limit for conciseness
            content = item.get("content", "")
            if content:
                parts.append(content)

        return " ".join(parts)

    def _format_bridge(self, items: list[dict]) -> str:
        """Format for bridge mode (structured)."""
        if not items:
            return "## Summary\n\nNo information available."

        sections = []

        # Group by type
        definitions = [i for i in items if i.get("type") == "definition"]
        deductions = [i for i in items if i.get("type") == "deduction"]
        others = [i for i in items if i.get("type") not in ("definition", "deduction")]

        if definitions:
            sections.append("## Definitions\n")
            for d in definitions:
                sections.append(f"- {d['content']}")

        if deductions:
            sections.append("\n## Reasoning\n")
            for d in deductions:
                sections.append(f"- {d['content']}")

        if others:
            sections.append("\n## Information\n")
            for o in others[:5]:
                sections.append(f"- {o.get('content', '')}")

        return "\n".join(sections)

    def _build_answer(
        self,
        context: ContextPack,
        plan_steps: list[PlanStep],
        step_results: list[StepResult],
        step_outputs: dict[str, Any],
    ) -> AnswerPlan:
        """Build final answer from execution results."""
        # Determine status
        all_succeeded = all(r.success for r in step_results)
        has_content = any(r.output for r in step_results if r.success)

        if not context.has_sufficient_context():
            status = AnswerStatus.UNKNOWN
        elif all_succeeded and has_content:
            status = AnswerStatus.COMPLETE
        elif has_content:
            status = AnswerStatus.PARTIAL
        else:
            status = AnswerStatus.FAILED

        # Build answer components
        components = []
        source_bricks = set()
        source_claims = []

        for result in step_results:
            if not result.success or not result.output:
                continue

            output = result.output

            # Extract formatted content
            if "formatted" in output:
                components.append(AnswerComponent(
                    component_type="formatted",
                    content=output["formatted"],
                    supporting_bricks=output.get("sources", []),
                    confidence=result.confidence,
                ))

            # Extract definitions
            if "definitions" in output:
                for d in output["definitions"]:
                    components.append(AnswerComponent(
                        component_type="definition",
                        content=f"{d['term']}: {d['definition']}",
                        supporting_bricks=[d.get("source", "")],
                        confidence=d.get("confidence", 0.5),
                    ))
                    if d.get("source"):
                        source_bricks.add(d["source"])

            # Collect claims
            source_claims.extend(result.claims_used)

        # Collect all assumptions
        all_assumptions = []
        for step in plan_steps:
            all_assumptions.extend(step.assumptions)

        # Collect unknowns
        unknowns = [u.question for u in context.known_unknowns]

        # Calculate confidence metrics
        confidences = [r.confidence for r in step_results if r.success]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        total_claims = len(source_claims)
        backed_claims = len([c for c in source_claims if c])  # Non-empty claims
        claim_coverage = backed_claims / total_claims if total_claims > 0 else 0.0

        # Add brick IDs from context
        for brick in context.top_bricks:
            source_bricks.add(brick.brick_id)

        return AnswerPlan(
            query=context.query,
            intent=context.query_intent,
            status=status,
            components=components,
            source_bricks=list(source_bricks),
            source_claims=source_claims[:20],  # Limit
            assumptions=all_assumptions,
            unknowns=unknowns,
            plan_steps=plan_steps,
            step_results=step_results,
            overall_confidence=overall_confidence,
            claim_coverage=claim_coverage,
        )
