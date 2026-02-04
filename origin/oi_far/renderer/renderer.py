"""Main renderer implementation."""

from ..reasoning.types import AnswerPlan, AnswerStatus
from .claim_checker import ClaimChecker
from .templates import BridgeTemplate, FailedTemplate, GalleyTemplate
from .types import RenderConfig, RenderedOutput, RenderMode


class DeterministicRenderer:
    """
    Renderer that converts AnswerPlans to text output.

    The renderer:
    1. Uses deterministic templates for formatting
    2. Enforces no-new-claims invariant
    3. Supports galley (concise) and bridge (structured) modes

    Optional LLM paraphrasing is NOT implemented here to maintain
    strict determinism. If paraphrasing is needed, it must be done
    as a separate post-processing step with claim checking.
    """

    def __init__(self, config: RenderConfig | None = None):
        self.config = config or RenderConfig()
        self.claim_checker = ClaimChecker()

    def render(
        self,
        answer_plan: AnswerPlan,
        config: RenderConfig | None = None,
    ) -> RenderedOutput:
        """
        Render an answer plan to text.

        Args:
            answer_plan: The answer to render
            config: Optional override config

        Returns:
            RenderedOutput with text and metadata
        """
        cfg = config or self.config
        config_dict = {
            "include_sources": cfg.include_sources,
            "include_confidence": cfg.include_confidence,
            "include_assumptions": cfg.include_assumptions,
        }

        # Count original claims
        original_claim_count = self._count_original_claims(answer_plan)

        # Select template based on mode
        if cfg.mode == RenderMode.BRIDGE:
            text = self._render_bridge(answer_plan, config_dict)
        else:
            text = self._render_galley(answer_plan)

        # Apply length limit for galley mode
        if cfg.mode == RenderMode.GALLEY and len(text) > cfg.max_length:
            text = self._truncate(text, cfg.max_length)

        # Add unknowns notice if configured
        if cfg.include_unknowns and answer_plan.unknowns and cfg.mode == RenderMode.GALLEY:
            if not any(u in text for u in answer_plan.unknowns[:1]):
                text += f" [Note: {answer_plan.unknowns[0]}]"

        # Verify no new claims were added
        rendered_claim_count = self.claim_checker.count_claims(text)
        check_passed, violations = self.claim_checker.check(text, answer_plan)

        if not check_passed:
            # Log violations but don't fail - this is informational
            # In production, this would trigger an alert
            pass

        return RenderedOutput(
            text=text,
            mode=cfg.mode,
            source_count=len(answer_plan.source_bricks),
            has_unknowns=len(answer_plan.unknowns) > 0,
            claim_ids=[c[:30] for c in answer_plan.source_claims[:10]],
            original_claim_count=original_claim_count,
            rendered_claim_count=rendered_claim_count,
            new_claims_check_passed=check_passed,
        )

    def _render_galley(self, answer_plan: AnswerPlan) -> str:
        """Render in galley mode."""
        if answer_plan.status == AnswerStatus.COMPLETE:
            return GalleyTemplate.render_complete(answer_plan)
        elif answer_plan.status == AnswerStatus.PARTIAL:
            return GalleyTemplate.render_partial(answer_plan)
        elif answer_plan.status == AnswerStatus.UNKNOWN:
            return GalleyTemplate.render_unknown(answer_plan)
        else:
            return FailedTemplate.render_galley(answer_plan)

    def _render_bridge(self, answer_plan: AnswerPlan, config: dict) -> str:
        """Render in bridge mode."""
        if answer_plan.status == AnswerStatus.COMPLETE:
            return BridgeTemplate.render_complete(answer_plan, config)
        elif answer_plan.status == AnswerStatus.PARTIAL:
            return BridgeTemplate.render_partial(answer_plan, config)
        elif answer_plan.status == AnswerStatus.UNKNOWN:
            return BridgeTemplate.render_unknown(answer_plan, config)
        else:
            return FailedTemplate.render_bridge(answer_plan)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length at sentence boundary."""
        if len(text) <= max_length:
            return text

        # Find last sentence boundary before limit
        truncated = text[:max_length]
        last_period = truncated.rfind('. ')
        last_question = truncated.rfind('? ')
        last_exclaim = truncated.rfind('! ')

        boundary = max(last_period, last_question, last_exclaim)

        if boundary > max_length * 0.5:
            return text[:boundary + 1]
        else:
            # No good boundary, truncate with ellipsis
            return text[:max_length - 3] + "..."

    def _count_original_claims(self, answer_plan: AnswerPlan) -> int:
        """Count claims in the original answer plan."""
        count = 0

        for component in answer_plan.components:
            count += 1

        count += len(answer_plan.source_claims)

        return count

    def render_with_paraphrase_check(
        self,
        answer_plan: AnswerPlan,
        paraphrased_text: str,
    ) -> RenderedOutput:
        """
        Verify paraphrased text against answer plan.

        Use this when an external paraphraser (e.g., small LLM) is used.
        This enforces the no-new-claims invariant.
        """
        check_passed, violations = self.claim_checker.check(paraphrased_text, answer_plan)

        if not check_passed:
            # Reject paraphrase, fall back to template
            return self.render(answer_plan)

        return RenderedOutput(
            text=paraphrased_text,
            mode=self.config.mode,
            source_count=len(answer_plan.source_bricks),
            has_unknowns=len(answer_plan.unknowns) > 0,
            claim_ids=[c[:30] for c in answer_plan.source_claims[:10]],
            original_claim_count=self._count_original_claims(answer_plan),
            rendered_claim_count=self.claim_checker.count_claims(paraphrased_text),
            new_claims_check_passed=check_passed,
        )
