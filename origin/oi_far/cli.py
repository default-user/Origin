#!/usr/bin/env python3
"""
OI-FAR CLI - Ongoing-Intelligence Frontier Approximation Runtime.

Usage:
    oi_far run "query"           Run a single query
    oi_far run -b "query"        Run in bridge mode (structured output)
    oi_far eval                  Run evaluation suite
    oi_far eval --prompts FILE   Run specific prompts
    oi_far ingest FILE           Ingest a document
    oi_far growth                Show growth metrics
    oi_far search "query"        Search the vault
"""

import argparse
import json
import sys
import time
from pathlib import Path

from .kernel import SessionState
from .substrate import BrickCompiler, BrickStore, Document, DocumentStore
from .retrieval import DeterministicRetriever
from .reasoning import DeterministicCritic, DeterministicPlanner, DeterministicSolver
from .renderer import DeterministicRenderer, RenderConfig, RenderMode
from .tools import ToolCapability, ToolRegistry, create_default_registry
from .growth import GrowthLoop


class OIFarRuntime:
    """
    Main OI-FAR runtime that orchestrates all modules.

    This is the deterministic core that:
    1. Maintains session state
    2. Retrieves context
    3. Plans and solves
    4. Critiques answers
    5. Renders output
    """

    def __init__(
        self,
        vault_path: str | Path = ".",
        mode: RenderMode = RenderMode.GALLEY,
    ):
        self.vault_path = Path(vault_path).resolve()
        self.mode = mode

        # Initialize stores
        build_path = self.vault_path / "build" / "oi_far"
        build_path.mkdir(parents=True, exist_ok=True)

        self.document_store = DocumentStore(str(build_path / "docs"))
        self.brick_store = BrickStore(str(build_path / "bricks"))
        self.brick_compiler = BrickCompiler()

        # Initialize components
        self.retriever = DeterministicRetriever(
            brick_store=self.brick_store,
            document_store=self.document_store,
        )
        self.planner = DeterministicPlanner()
        self.solver = DeterministicSolver()
        self.critic = DeterministicCritic()
        self.renderer = DeterministicRenderer(
            config=RenderConfig(mode=mode)
        )

        # Initialize session
        self.session = SessionState()
        self.session.user_prefs["mode"] = mode.value

        # Initialize tools
        self.tools = create_default_registry(str(self.vault_path))

        # Initialize growth loop
        self.growth_loop = GrowthLoop(
            document_store=self.document_store,
            brick_store=self.brick_store,
            brick_compiler=self.brick_compiler,
            storage_path=build_path / "growth",
        )

        # Bootstrap from existing knowledge
        self._bootstrap_from_vault()

    def _bootstrap_from_vault(self) -> None:
        """Bootstrap stores from existing vault content."""
        packs_dir = self.vault_path / "knowledge" / "packs"
        if not packs_dir.exists():
            return

        # Check if already bootstrapped
        if self.brick_store.count() > 0:
            return

        # Load packs
        import yaml

        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue

            pack_yaml = pack_dir / "pack.yaml"
            if not pack_yaml.exists():
                continue

            try:
                with open(pack_yaml) as f:
                    pack_data = yaml.safe_load(f)

                # Create document
                doc = Document(
                    id=f"pack_{pack_data.get('id', pack_dir.name)}",
                    title=pack_data.get("title", pack_dir.name),
                    content=yaml.dump(pack_data),
                    source_type="pack",
                    source_path=str(pack_yaml),
                    metadata=pack_data,
                )

                # Store and compile
                self.document_store.add(doc)
                bricks = self.brick_compiler.compile_document(doc)
                for brick in bricks:
                    self.brick_store.add(brick)

            except Exception as e:
                print(f"Warning: Failed to load {pack_yaml}: {e}", file=sys.stderr)

        # Rebuild indexes
        self.brick_store.rebuild_indexes()
        self.document_store.rebuild_index()

    def run(self, query: str) -> dict:
        """
        Run a query through the full OI-FAR pipeline.

        Args:
            query: User query

        Returns:
            Result dictionary with output and metadata
        """
        start_time = time.time()

        # Update session
        self.session.add_turn("user", query)

        # 1. Retrieve context
        context = self.retriever.retrieve(query, self.session)

        # 2. Plan
        if context.has_sufficient_context():
            plan_steps = self.planner.plan(query, context, self.session)
        else:
            plan_steps = self.planner.plan_for_unknown(query, context, self.session)

        # 3. Solve
        answer_plan = self.solver.solve(plan_steps, context)

        # 4. Critique
        critic_result = self.critic.critic(answer_plan, context)

        # 5. Apply fixes if needed (one revision)
        if not critic_result.passed and critic_result.fixes:
            answer_plan = self.critic.apply_fixes(answer_plan, critic_result.fixes)
            # Re-critique
            critic_result = self.critic.critic(answer_plan, context)

        # 6. Track failures for growth loop
        from .reasoning.types import AnswerStatus
        if answer_plan.status in (AnswerStatus.UNKNOWN, AnswerStatus.FAILED) or not critic_result.passed:
            self.growth_loop.analyze_failure(
                query=query,
                context=context,
                critic_result=critic_result,
                answer_status=answer_plan.status,
            )

        # 7. Render
        render_config = RenderConfig(mode=self.mode)
        output = self.renderer.render(answer_plan, render_config)

        # Update session
        self.session.add_turn("assistant", output.text)

        total_time = time.time() - start_time

        return {
            "output": output.text,
            "status": answer_plan.status.value,
            "confidence": answer_plan.overall_confidence,
            "sources": answer_plan.source_bricks[:5],
            "critic_passed": critic_result.passed,
            "new_claims_check": output.new_claims_check_passed,
            "mode": output.mode.value,
            "timing": {
                "total_ms": total_time * 1000,
                "reasoning_ms": answer_plan.reasoning_time_ms,
            },
            "deterministic": True,
        }

    def search(self, query: str, limit: int = 10) -> dict:
        """Search the vault."""
        result = self.tools.invoke("search_vault", query=query, limit=limit)
        return result.to_dict()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OI-FAR: Ongoing-Intelligence Frontier Approximation Runtime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a query")
    run_parser.add_argument("query", help="Query to run")
    run_parser.add_argument("-b", "--bridge", action="store_true",
                          help="Use bridge mode (structured output)")
    run_parser.add_argument("-v", "--verbose", action="store_true",
                          help="Verbose output with metadata")
    run_parser.add_argument("--vault", default=".",
                          help="Path to vault (default: current directory)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the vault")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--limit", type=int, default=10,
                              help="Maximum results")
    search_parser.add_argument("--vault", default=".",
                              help="Path to vault")

    # Eval command
    eval_parser = subparsers.add_parser("eval", help="Run evaluation suite")
    eval_parser.add_argument("--prompts", help="Path to prompts file")
    eval_parser.add_argument("--vault", default=".",
                            help="Path to vault")

    # Growth command
    growth_parser = subparsers.add_parser("growth", help="Show growth metrics")
    growth_parser.add_argument("--vault", default=".",
                              help="Path to vault")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Determine vault path
    vault_path = Path(args.vault).resolve()

    # Handle commands
    if args.command == "run":
        mode = RenderMode.BRIDGE if args.bridge else RenderMode.GALLEY
        runtime = OIFarRuntime(vault_path=vault_path, mode=mode)

        result = runtime.run(args.query)

        if args.verbose:
            print(json.dumps(result, indent=2))
        else:
            print(result["output"])

        # Exit with error code if failed
        if result["status"] == "failed":
            sys.exit(1)

    elif args.command == "search":
        runtime = OIFarRuntime(vault_path=vault_path)
        result = runtime.search(args.query, limit=args.limit)

        if result["success"]:
            for item in result["data"]["results"]:
                print(f"[{item['score']:.1f}] {item['id']}: {item['title']}")
                if item.get("summary"):
                    print(f"    {item['summary'][:100]}...")
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "eval":
        from .eval import run_evaluation

        # Find prompts
        prompts_path = args.prompts
        if not prompts_path:
            prompts_path = vault_path / "eval" / "prompts"

        result = run_evaluation(vault_path, prompts_path)

        print(f"Evaluation Results:")
        print(f"  Total: {result['total']}")
        print(f"  Passed: {result['passed']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Unknown: {result['unknowns']}")
        print(f"  Determinism: {'PASS' if result['determinism_check'] else 'FAIL'}")

        if result['failed'] > 0:
            sys.exit(1)

    elif args.command == "growth":
        runtime = OIFarRuntime(vault_path=vault_path)
        metrics = runtime.growth_loop.get_improvement_metrics()

        if metrics.get("insufficient_data"):
            print("Insufficient data for growth metrics.")
            print("Run more queries and evaluations first.")
        else:
            print("Growth Metrics:")
            print(json.dumps(metrics, indent=2))

        recommendations = runtime.growth_loop.get_growth_recommendations()
        if recommendations:
            print("\nTop Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. [{rec['priority']:.1f}] {rec['action']}")


if __name__ == "__main__":
    main()
