"""Deterministic templates for rendering."""

from typing import Any

from ..reasoning.types import AnswerPlan, AnswerStatus


class GalleyTemplate:
    """Template for galley mode (concise)."""

    @staticmethod
    def render_complete(answer: AnswerPlan) -> str:
        """Render a complete answer."""
        parts = []

        # Main content from components
        for component in answer.components:
            if component.component_type == "formatted":
                parts.append(component.content)
            elif component.component_type == "definition":
                parts.append(component.content)
            else:
                parts.append(component.content)

        if not parts:
            # Fallback to source claims
            if answer.source_claims:
                parts.append(". ".join(answer.source_claims[:3]))

        return " ".join(parts)

    @staticmethod
    def render_partial(answer: AnswerPlan) -> str:
        """Render a partial answer."""
        parts = []

        # Add available content
        for component in answer.components:
            parts.append(component.content)

        # Note what's missing
        if answer.unknowns:
            parts.append(f"Note: {answer.unknowns[0]}")

        return " ".join(parts) if parts else "Partial information available."

    @staticmethod
    def render_unknown(answer: AnswerPlan) -> str:
        """Render an UNKNOWN response."""
        parts = ["UNKNOWN."]

        if answer.unknowns:
            parts.append(f"Missing: {answer.unknowns[0]}")

        # List what would help
        if answer.assumptions:
            needed = [a.what_would_refute for a in answer.assumptions[:2]]
            if needed:
                parts.append(f"Would help: {', '.join(needed)}")

        return " ".join(parts)


class BridgeTemplate:
    """Template for bridge mode (structured)."""

    @staticmethod
    def render_complete(answer: AnswerPlan, config: dict) -> str:
        """Render a complete answer with structure."""
        sections = []

        # Summary section
        sections.append("## Summary\n")
        summary_parts = []
        for component in answer.components:
            if component.component_type == "formatted":
                summary_parts.append(component.content)
        if summary_parts:
            sections.append(summary_parts[0])
        else:
            sections.append("Information retrieved successfully.")

        # Details section
        if len(answer.components) > 1:
            sections.append("\n\n## Details\n")
            for component in answer.components[1:]:
                sections.append(f"- {component.content}")

        # Sources section
        if config.get("include_sources", True) and answer.source_bricks:
            sections.append("\n\n## Sources\n")
            for brick_id in answer.source_bricks[:5]:
                sections.append(f"- {brick_id}")

        # Confidence section
        if config.get("include_confidence", False):
            sections.append(f"\n\n## Confidence\n")
            sections.append(f"Overall: {answer.overall_confidence:.0%}")
            sections.append(f"Claim coverage: {answer.claim_coverage:.0%}")

        # Assumptions section
        if config.get("include_assumptions", False) and answer.assumptions:
            sections.append("\n\n## Assumptions\n")
            for assumption in answer.assumptions[:3]:
                sections.append(f"- {assumption.description}")

        return "\n".join(sections)

    @staticmethod
    def render_partial(answer: AnswerPlan, config: dict) -> str:
        """Render a partial answer with structure."""
        sections = []

        sections.append("## Partial Answer\n")

        # Available information
        if answer.components:
            sections.append("### Available Information\n")
            for component in answer.components:
                sections.append(f"- {component.content}")

        # Gaps
        sections.append("\n### Knowledge Gaps\n")
        for unknown in answer.unknowns[:3]:
            sections.append(f"- {unknown}")

        # Sources
        if config.get("include_sources", True) and answer.source_bricks:
            sections.append("\n### Sources Consulted\n")
            for brick_id in answer.source_bricks[:3]:
                sections.append(f"- {brick_id}")

        return "\n".join(sections)

    @staticmethod
    def render_unknown(answer: AnswerPlan, config: dict) -> str:
        """Render an UNKNOWN response with structure."""
        sections = []

        sections.append("## UNKNOWN\n")
        sections.append("Unable to provide a reliable answer.\n")

        # What we don't know
        sections.append("### Missing Information\n")
        for unknown in answer.unknowns[:5]:
            sections.append(f"- {unknown}")

        # What would help
        sections.append("\n### What Would Help\n")
        for assumption in answer.assumptions[:3]:
            sections.append(f"- {assumption.what_would_refute}")

        # What we did find
        if answer.source_bricks:
            sections.append("\n### Related Sources Found\n")
            for brick_id in answer.source_bricks[:3]:
                sections.append(f"- {brick_id}")

        return "\n".join(sections)


class FailedTemplate:
    """Template for failed responses."""

    @staticmethod
    def render_galley(answer: AnswerPlan) -> str:
        """Render failed response in galley mode."""
        return "FAILED. Unable to process request. Check logs for details."

    @staticmethod
    def render_bridge(answer: AnswerPlan) -> str:
        """Render failed response in bridge mode."""
        sections = [
            "## Processing Failed\n",
            "Unable to complete the request.\n",
            "### Possible Causes\n",
            "- Insufficient knowledge in the substrate",
            "- Contradictory information found",
            "- Query could not be parsed",
        ]

        if answer.unknowns:
            sections.append("\n### Identified Issues\n")
            for unknown in answer.unknowns[:3]:
                sections.append(f"- {unknown}")

        return "\n".join(sections)
