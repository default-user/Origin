"""OI Capability Growth Loop."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..reasoning.types import AnswerStatus, CriticResult
from ..retrieval.types import ContextPack
from ..substrate.brick_compiler import BrickCompiler
from ..substrate.brick_store import BrickStore
from ..substrate.document_store import DocumentStore
from ..substrate.types import Document
from .missing import (
    MissingKind,
    MissingKnowledge,
    MissingKnowledgeTracker,
    NeededSource,
    RegressionTest,
)


@dataclass
class GrowthIteration:
    """Result of a single growth iteration."""
    iteration: int
    documents_ingested: int
    bricks_compiled: int
    eval_results: dict[str, Any]
    failure_rate: float
    unknown_rate: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "documents_ingested": self.documents_ingested,
            "bricks_compiled": self.bricks_compiled,
            "eval_results": self.eval_results,
            "failure_rate": self.failure_rate,
            "unknown_rate": self.unknown_rate,
            "timestamp": self.timestamp,
        }


class GrowthLoop:
    """
    OI Capability Growth Loop.

    When OI-FAR returns UNKNOWN or critic fails:
    1. Emit MissingKnowledge[] (brick types/claim families missing)
    2. Emit NeededSources[] (doc classes to ingest)
    3. Generate regression test

    Loop:
    1. Ingest new documents
    2. Compile to bricks
    3. Reindex
    4. Rerun eval
    5. Track improvement

    Goal: Shrink failure rate over time without turning into a frontier LLM.
    """

    def __init__(
        self,
        document_store: DocumentStore,
        brick_store: BrickStore,
        brick_compiler: BrickCompiler,
        storage_path: str | Path | None = None,
    ):
        self.document_store = document_store
        self.brick_store = brick_store
        self.brick_compiler = brick_compiler
        self.storage_path = Path(storage_path) if storage_path else None

        self.tracker = MissingKnowledgeTracker()
        self.iterations: list[GrowthIteration] = []
        self._iteration_counter = 0

    def analyze_failure(
        self,
        query: str,
        context: ContextPack,
        critic_result: CriticResult | None,
        answer_status: AnswerStatus,
    ) -> tuple[list[MissingKnowledge], list[NeededSource], RegressionTest | None]:
        """
        Analyze a failure or UNKNOWN result.

        Returns:
            (missing_knowledge, needed_sources, regression_test)
        """
        missing = []
        sources = []
        test = None

        # Analyze based on status
        if answer_status == AnswerStatus.UNKNOWN:
            # Complete lack of knowledge
            missing.append(self.tracker.record_missing(
                kind=MissingKind.CONCEPT,
                topic=query,
                description=f"No information found for query: {query}",
                query=query,
                priority=0.8,
                what_would_resolve=[
                    f"Definition of key terms in: {query}",
                    f"Related concepts for: {query}",
                ],
            ))

            sources.append(self.tracker.record_needed_source(
                source_type="document",
                description=f"Documentation covering: {query}",
                topics=context.query_tokens[:5],
                priority=0.8,
                suggested_search=query,
            ))

            test = self.tracker.generate_regression_test(
                prompt=query,
                expected_behavior="answer",  # Should answer after knowledge added
                expected_contains=context.query_tokens[:3],
                failure_description="UNKNOWN - no relevant knowledge found",
            )

        elif answer_status == AnswerStatus.FAILED:
            # Processing failed
            missing.append(self.tracker.record_missing(
                kind=MissingKind.CLAIM,
                topic=query,
                description="Processing failed - likely contradictory or incomplete data",
                query=query,
                priority=0.9,
            ))

        # Analyze critic failures
        if critic_result and not critic_result.passed:
            # Contradictions
            if critic_result.contradiction_count > 0:
                missing.append(self.tracker.record_missing(
                    kind=MissingKind.CLAIM,
                    topic=query,
                    description=f"Contradictory claims found ({critic_result.contradiction_count})",
                    query=query,
                    priority=0.7,
                    what_would_resolve=["Authoritative source to resolve conflict"],
                ))

            # Unsupported claims
            if critic_result.unsupported_claim_count > 0:
                missing.append(self.tracker.record_missing(
                    kind=MissingKind.SOURCE,
                    topic=query,
                    description=f"Unsupported claims ({critic_result.unsupported_claim_count})",
                    query=query,
                    priority=0.6,
                ))

            # Add needed sources from critic
            for needed in critic_result.needed_sources:
                sources.append(self.tracker.record_needed_source(
                    source_type="document",
                    description=needed,
                    topics=[query],
                    priority=0.6,
                ))

            # Add needed claims from critic
            for needed_claim in critic_result.needed_claims:
                missing.append(self.tracker.record_missing(
                    kind=MissingKind.CLAIM,
                    topic=query,
                    description=needed_claim,
                    query=query,
                    priority=0.5,
                ))

        # Analyze known unknowns from context
        for unknown in context.known_unknowns:
            missing.append(self.tracker.record_missing(
                kind=MissingKind.CONCEPT,
                topic=unknown.topic,
                description=unknown.question,
                query=query,
                priority=0.6,
                what_would_resolve=unknown.what_would_help,
            ))

        return missing, sources, test

    def ingest_document(self, doc: Document) -> int:
        """
        Ingest a document and compile to bricks.

        Returns number of bricks created.
        """
        # Store document
        self.document_store.add(doc)

        # Compile to bricks
        bricks = self.brick_compiler.compile_document(doc)

        # Store bricks
        for brick in bricks:
            self.brick_store.add(brick)

        return len(bricks)

    def reindex(self) -> dict[str, int]:
        """
        Reindex all stores.

        Returns index statistics.
        """
        # Rebuild brick store indexes
        self.brick_store.rebuild_indexes()

        # Rebuild document store search index
        self.document_store.rebuild_index()

        return {
            "bricks_indexed": self.brick_store.count(),
            "documents_indexed": self.document_store.count(),
        }

    def run_iteration(
        self,
        eval_runner: Callable[[], dict[str, Any]],
        new_documents: list[Document] | None = None,
    ) -> GrowthIteration:
        """
        Run a single growth loop iteration.

        Args:
            eval_runner: Function that runs evaluation and returns results
            new_documents: Optional new documents to ingest

        Returns:
            GrowthIteration with results
        """
        self._iteration_counter += 1
        docs_ingested = 0
        bricks_compiled = 0

        # Ingest new documents if provided
        if new_documents:
            for doc in new_documents:
                bricks = self.ingest_document(doc)
                docs_ingested += 1
                bricks_compiled += bricks

        # Reindex
        self.reindex()

        # Run evaluation
        eval_results = eval_runner()

        # Calculate rates
        total = eval_results.get("total", 1)
        failures = eval_results.get("failures", 0)
        unknowns = eval_results.get("unknowns", 0)

        failure_rate = failures / total if total > 0 else 0
        unknown_rate = unknowns / total if total > 0 else 0

        # Create iteration record
        iteration = GrowthIteration(
            iteration=self._iteration_counter,
            documents_ingested=docs_ingested,
            bricks_compiled=bricks_compiled,
            eval_results=eval_results,
            failure_rate=failure_rate,
            unknown_rate=unknown_rate,
        )

        self.iterations.append(iteration)

        # Save state if storage path configured
        if self.storage_path:
            self._save_state()

        return iteration

    def get_improvement_metrics(self) -> dict[str, Any]:
        """Get metrics showing improvement over iterations."""
        if len(self.iterations) < 2:
            return {"insufficient_data": True}

        first = self.iterations[0]
        last = self.iterations[-1]

        return {
            "iterations": len(self.iterations),
            "initial_failure_rate": first.failure_rate,
            "current_failure_rate": last.failure_rate,
            "failure_rate_improvement": first.failure_rate - last.failure_rate,
            "initial_unknown_rate": first.unknown_rate,
            "current_unknown_rate": last.unknown_rate,
            "unknown_rate_improvement": first.unknown_rate - last.unknown_rate,
            "total_documents_added": sum(i.documents_ingested for i in self.iterations),
            "total_bricks_compiled": sum(i.bricks_compiled for i in self.iterations),
        }

    def get_growth_recommendations(self) -> list[dict[str, Any]]:
        """Get recommendations for what to add next."""
        recommendations = []

        # High priority missing knowledge
        for m in self.tracker.get_high_priority_missing():
            recommendations.append({
                "type": "missing_knowledge",
                "priority": m.priority,
                "topic": m.topic,
                "description": m.description,
                "action": f"Add knowledge about: {m.topic}",
            })

        # High priority sources
        for s in self.tracker.get_high_priority_sources():
            recommendations.append({
                "type": "needed_source",
                "priority": s.priority,
                "description": s.description,
                "action": f"Ingest: {s.suggested_search or s.description}",
            })

        # Sort by priority
        recommendations.sort(key=lambda r: -r["priority"])

        return recommendations[:10]  # Top 10

    def _save_state(self) -> None:
        """Save growth loop state to disk."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)

        state = {
            "iterations": [i.to_dict() for i in self.iterations],
            "tracker": self.tracker.export(),
            "metrics": self.get_improvement_metrics(),
        }

        state_path = self.storage_path / "growth_state.json"
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """Load growth loop state from disk."""
        if not self.storage_path:
            return False

        state_path = self.storage_path / "growth_state.json"
        if not state_path.exists():
            return False

        try:
            with open(state_path) as f:
                state = json.load(f)

            # Restore iterations
            self.iterations = [
                GrowthIteration(**i) for i in state.get("iterations", [])
            ]
            self._iteration_counter = len(self.iterations)

            return True
        except Exception:
            return False

    def export_regression_tests(self) -> list[dict]:
        """Export all regression tests for eval suite."""
        return [t.to_dict() for t in self.tracker.regression_tests]
