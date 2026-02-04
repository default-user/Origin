"""Missing knowledge and needed sources tracking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MissingKind(Enum):
    """Types of missing knowledge."""
    CONCEPT = "concept"  # Missing concept definition
    CLAIM = "claim"  # Missing factual claim
    RELATION = "relation"  # Missing relationship
    SOURCE = "source"  # Missing source document
    PROOF = "proof"  # Missing proof/derivation


@dataclass
class MissingKnowledge:
    """A piece of missing knowledge identified during processing."""
    kind: MissingKind
    topic: str
    description: str
    query_that_exposed: str
    priority: float  # 0.0-1.0, higher = more important
    what_would_resolve: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "topic": self.topic,
            "description": self.description,
            "query_that_exposed": self.query_that_exposed,
            "priority": self.priority,
            "what_would_resolve": self.what_would_resolve,
        }


@dataclass
class NeededSource:
    """A source document that would improve coverage."""
    source_type: str  # "document", "paper", "definition", "example"
    description: str
    topics_covered: list[str]
    priority: float
    suggested_search: str | None = None

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "description": self.description,
            "topics_covered": self.topics_covered,
            "priority": self.priority,
            "suggested_search": self.suggested_search,
        }


@dataclass
class RegressionTest:
    """A regression test generated from a failure."""
    test_id: str
    prompt: str
    expected_behavior: str  # "answer", "unknown", "partial"
    expected_contains: list[str]  # Strings that should appear
    expected_not_contains: list[str]  # Strings that should NOT appear
    source_failure: str  # Description of what failed

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "prompt": self.prompt,
            "expected_behavior": self.expected_behavior,
            "expected_contains": self.expected_contains,
            "expected_not_contains": self.expected_not_contains,
            "source_failure": self.source_failure,
        }


class MissingKnowledgeTracker:
    """
    Tracks missing knowledge across queries.

    Aggregates gaps to identify high-priority knowledge to add.
    """

    def __init__(self):
        self.missing: list[MissingKnowledge] = []
        self.needed_sources: list[NeededSource] = []
        self.regression_tests: list[RegressionTest] = []
        self._test_counter = 0

    def record_missing(
        self,
        kind: MissingKind,
        topic: str,
        description: str,
        query: str,
        priority: float = 0.5,
        what_would_resolve: list[str] | None = None,
    ) -> MissingKnowledge:
        """Record a piece of missing knowledge."""
        missing = MissingKnowledge(
            kind=kind,
            topic=topic,
            description=description,
            query_that_exposed=query,
            priority=priority,
            what_would_resolve=what_would_resolve or [],
        )
        self.missing.append(missing)
        return missing

    def record_needed_source(
        self,
        source_type: str,
        description: str,
        topics: list[str],
        priority: float = 0.5,
        suggested_search: str | None = None,
    ) -> NeededSource:
        """Record a needed source."""
        source = NeededSource(
            source_type=source_type,
            description=description,
            topics_covered=topics,
            priority=priority,
            suggested_search=suggested_search,
        )
        self.needed_sources.append(source)
        return source

    def generate_regression_test(
        self,
        prompt: str,
        expected_behavior: str,
        expected_contains: list[str],
        failure_description: str,
    ) -> RegressionTest:
        """Generate a regression test from a failure."""
        self._test_counter += 1
        test = RegressionTest(
            test_id=f"regtest_{self._test_counter}",
            prompt=prompt,
            expected_behavior=expected_behavior,
            expected_contains=expected_contains,
            expected_not_contains=[],
            source_failure=failure_description,
        )
        self.regression_tests.append(test)
        return test

    def get_high_priority_missing(self, threshold: float = 0.7) -> list[MissingKnowledge]:
        """Get high-priority missing knowledge."""
        return sorted(
            [m for m in self.missing if m.priority >= threshold],
            key=lambda m: -m.priority,
        )

    def get_high_priority_sources(self, threshold: float = 0.7) -> list[NeededSource]:
        """Get high-priority needed sources."""
        return sorted(
            [s for s in self.needed_sources if s.priority >= threshold],
            key=lambda s: -s.priority,
        )

    def aggregate_by_topic(self) -> dict[str, list[MissingKnowledge]]:
        """Aggregate missing knowledge by topic."""
        by_topic: dict[str, list[MissingKnowledge]] = {}
        for m in self.missing:
            if m.topic not in by_topic:
                by_topic[m.topic] = []
            by_topic[m.topic].append(m)
        return by_topic

    def export(self) -> dict:
        """Export all tracked data."""
        return {
            "missing_knowledge": [m.to_dict() for m in self.missing],
            "needed_sources": [s.to_dict() for s in self.needed_sources],
            "regression_tests": [t.to_dict() for t in self.regression_tests],
            "summary": {
                "total_missing": len(self.missing),
                "total_needed_sources": len(self.needed_sources),
                "total_regression_tests": len(self.regression_tests),
                "high_priority_missing": len(self.get_high_priority_missing()),
            },
        }

    def clear(self) -> None:
        """Clear all tracked data."""
        self.missing.clear()
        self.needed_sources.clear()
        self.regression_tests.clear()
