"""Deterministic planner for reasoning tasks."""

from typing import Any

from ..kernel.session import SessionState
from ..retrieval.types import ContextPack
from .types import Assumption, PlanStep, StepType


class DeterministicPlanner:
    """
    Deterministic task planner.

    Creates execution plans based on:
    - Query intent classification
    - Available context (bricks, sources)
    - Session constraints
    - Predefined task schemas

    All planning is deterministic: same inputs -> same plan.
    """

    def __init__(self):
        # Task schemas: intent -> list of step templates
        self._task_schemas = {
            "define": [
                ("retrieve", "Retrieve definitions for {query}"),
                ("synthesize", "Synthesize definition from sources"),
                ("format", "Format definition response"),
            ],
            "explain": [
                ("retrieve", "Retrieve explanatory content for {query}"),
                ("deduce", "Build explanation chain"),
                ("synthesize", "Combine explanation components"),
                ("format", "Format explanation response"),
            ],
            "compare": [
                ("retrieve", "Retrieve information for comparison items"),
                ("compare", "Identify similarities and differences"),
                ("synthesize", "Build comparison summary"),
                ("format", "Format comparison response"),
            ],
            "find": [
                ("retrieve", "Search for matching items"),
                ("verify", "Verify matches meet criteria"),
                ("format", "Format search results"),
            ],
            "prove": [
                ("retrieve", "Retrieve relevant premises"),
                ("deduce", "Construct proof chain"),
                ("verify", "Verify proof validity"),
                ("format", "Format proof response"),
            ],
            "verify": [
                ("retrieve", "Retrieve evidence for/against claim"),
                ("deduce", "Evaluate evidence"),
                ("format", "Format verification response"),
            ],
            "unknown": [
                ("retrieve", "Attempt general retrieval"),
                ("synthesize", "Synthesize available information"),
                ("format", "Format response or UNKNOWN"),
            ],
        }

        self._step_counter = 0

    def plan(
        self,
        task: str,
        context: ContextPack,
        session_state: SessionState | None = None,
    ) -> list[PlanStep]:
        """
        Create an execution plan for a task.

        Args:
            task: The task/query to plan for
            context: Retrieved context
            session_state: Current session state

        Returns:
            List of PlanStep objects
        """
        intent = context.query_intent
        schema = self._task_schemas.get(intent, self._task_schemas["unknown"])

        steps = []
        self._step_counter = 0

        for step_type_str, description_template in schema:
            step = self._create_step(
                step_type_str,
                description_template,
                task,
                context,
                steps,
                session_state,
            )
            steps.append(step)

        # Add constraint enforcement steps if needed
        if session_state and session_state.constraints:
            steps.append(self._create_constraint_check_step(
                session_state.constraints,
                steps,
            ))

        return steps

    def _create_step(
        self,
        step_type_str: str,
        description_template: str,
        task: str,
        context: ContextPack,
        prior_steps: list[PlanStep],
        session_state: SessionState | None,
    ) -> PlanStep:
        """Create a single plan step."""
        self._step_counter += 1
        step_id = f"step_{self._step_counter}"

        step_type = StepType(step_type_str)
        description = description_template.format(query=task)

        # Determine inputs based on step type
        inputs = self._determine_inputs(step_type, context, prior_steps)

        # Determine expected output
        expected_output = self._determine_expected_output(step_type, context)

        # Extract constraints applicable to this step
        constraints = self._extract_step_constraints(step_type, session_state)

        # Create assumptions for this step
        assumptions = self._create_step_assumptions(step_type, context)

        return PlanStep(
            step_id=step_id,
            step_type=step_type,
            description=description,
            inputs=inputs,
            expected_output=expected_output,
            constraints=constraints,
            assumptions=assumptions,
        )

    def _determine_inputs(
        self,
        step_type: StepType,
        context: ContextPack,
        prior_steps: list[PlanStep],
    ) -> list[str]:
        """Determine inputs needed for a step."""
        inputs = []

        if step_type == StepType.RETRIEVE:
            # No prior step inputs, uses context directly
            pass

        elif step_type == StepType.DEFINE:
            # Needs brick IDs with definitions
            for brick in context.top_bricks[:5]:
                inputs.append(brick.brick_id)

        elif step_type == StepType.COMPARE:
            # Needs multiple brick IDs
            for brick in context.top_bricks[:10]:
                inputs.append(brick.brick_id)

        elif step_type == StepType.DEDUCE:
            # Needs prior retrieve step output
            for step in prior_steps:
                if step.step_type == StepType.RETRIEVE:
                    inputs.append(step.step_id)
            # Also add relevant bricks
            for brick in context.top_bricks[:5]:
                inputs.append(brick.brick_id)

        elif step_type == StepType.VERIFY:
            # Needs prior deduce or retrieve step
            for step in prior_steps:
                if step.step_type in (StepType.DEDUCE, StepType.RETRIEVE):
                    inputs.append(step.step_id)

        elif step_type == StepType.SYNTHESIZE:
            # Needs all prior step outputs
            for step in prior_steps:
                inputs.append(step.step_id)

        elif step_type == StepType.FORMAT:
            # Needs synthesize or last substantive step
            for step in reversed(prior_steps):
                if step.step_type in (StepType.SYNTHESIZE, StepType.DEDUCE, StepType.COMPARE):
                    inputs.append(step.step_id)
                    break

        return inputs

    def _determine_expected_output(
        self,
        step_type: StepType,
        context: ContextPack,
    ) -> str:
        """Determine expected output type for a step."""
        outputs = {
            StepType.RETRIEVE: "list[Brick]",
            StepType.DEFINE: "Definition",
            StepType.COMPARE: "ComparisonTable",
            StepType.DEDUCE: "DeductionChain",
            StepType.VERIFY: "VerificationResult",
            StepType.SYNTHESIZE: "SynthesizedContent",
            StepType.FORMAT: "FormattedResponse",
            StepType.UNKNOWN: "Unknown",
        }
        return outputs.get(step_type, "Unknown")

    def _extract_step_constraints(
        self,
        step_type: StepType,
        session_state: SessionState | None,
    ) -> list[str]:
        """Extract constraints applicable to a step."""
        if not session_state:
            return []

        constraints = []

        # Global constraints apply to all steps
        constraints.extend(session_state.constraints)

        # Add step-specific constraints
        if step_type == StepType.FORMAT:
            # Formatting mode constraint
            mode = getattr(session_state.user_prefs, "style_mode", None)
            mode_value = mode.value if mode is not None else "galley"
            constraints.append(f"Output mode: {mode_value}")

        if step_type == StepType.DEDUCE:
            # Deduction constraints
            constraints.append("Only use claims from retrieved bricks")
            constraints.append("Make all assumptions explicit")

        return constraints

    def _create_step_assumptions(
        self,
        step_type: StepType,
        context: ContextPack,
    ) -> list[Assumption]:
        """Create assumptions for a step."""
        assumptions = []
        assumption_counter = 0

        if step_type == StepType.RETRIEVE:
            if context.total_bricks_scanned > 0:
                assumption_counter += 1
                assumptions.append(Assumption(
                    id=f"assume_{assumption_counter}",
                    description="Retrieved bricks are representative of available knowledge",
                    confidence=0.9,
                    what_would_refute="Finding highly relevant bricks not in top results",
                    source="default",
                ))

        elif step_type == StepType.DEDUCE:
            assumption_counter += 1
            assumptions.append(Assumption(
                id=f"assume_{assumption_counter}",
                description="Claims from different sources can be combined",
                confidence=0.8,
                what_would_refute="Finding contradictory claims from sources",
                source="default",
            ))

        elif step_type == StepType.VERIFY:
            if context.has_conflicts():
                assumption_counter += 1
                assumptions.append(Assumption(
                    id=f"assume_{assumption_counter}",
                    description="More recent sources take precedence",
                    confidence=0.7,
                    what_would_refute="Finding that older source is more authoritative",
                    source="inferred",
                ))

        return assumptions

    def _create_constraint_check_step(
        self,
        constraints: list[str],
        prior_steps: list[PlanStep],
    ) -> PlanStep:
        """Create a step to verify constraints are met."""
        self._step_counter += 1

        return PlanStep(
            step_id=f"step_{self._step_counter}",
            step_type=StepType.VERIFY,
            description="Verify all session constraints are satisfied",
            inputs=[step.step_id for step in prior_steps],
            expected_output="ConstraintVerification",
            constraints=constraints,
            assumptions=[],
        )

    def plan_for_unknown(
        self,
        task: str,
        context: ContextPack,
        session_state: SessionState | None = None,
    ) -> list[PlanStep]:
        """
        Create a plan that acknowledges we cannot answer.

        Used when retrieval returns insufficient context.
        """
        self._step_counter = 0

        steps = []

        # Step 1: Document what we don't know
        self._step_counter += 1
        steps.append(PlanStep(
            step_id=f"step_{self._step_counter}",
            step_type=StepType.UNKNOWN,
            description=f"Document knowledge gaps for: {task}",
            inputs=[],
            expected_output="KnowledgeGapReport",
            constraints=[],
            assumptions=[],
        ))

        # Step 2: Format UNKNOWN response
        self._step_counter += 1
        steps.append(PlanStep(
            step_id=f"step_{self._step_counter}",
            step_type=StepType.FORMAT,
            description="Format UNKNOWN response with needed information",
            inputs=[f"step_{self._step_counter - 1}"],
            expected_output="FormattedUnknown",
            constraints=["Must list what information is missing"],
            assumptions=[],
        ))

        return steps
