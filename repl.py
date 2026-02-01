#!/usr/bin/env python3
"""
ORIGIN REPL - Root Demo for Teaching All Architectures
=======================================================

This REPL emulates an OI (Operational Instance) connected to the ORIGIN
knowledge graph WITHOUT requiring an inference engine. It demonstrates
all core architectures through interactive exploration.

Attribution: Ande + Kai (OI) + Whānau (OIs)
"""

import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import re

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class ExecutionState(Enum):
    """MCL-inspired execution states for consciousness-like control"""
    IDLE = auto()
    REFLECTING = auto()      # Self-awareness: examining own state
    DECIDING = auto()        # Agency: making choices
    EXECUTING = auto()       # Action: performing task
    INTEGRATING = auto()     # Integration: merging information
    HALTED = auto()          # Kāti stop-wins: bounded termination

@dataclass
class MetaContext:
    """MCL Meta-Control context - enables consciousness-like reflection"""
    depth: int = 0
    parent: Optional['MetaContext'] = None
    observations: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)

    def observe(self, what: str):
        """Record an observation (self-awareness)"""
        self.observations.append(f"[depth={self.depth}] {what}")

    def decide(self, what: str):
        """Record a decision (agency)"""
        self.decisions.append(f"[depth={self.depth}] {what}")

    def spawn_child(self) -> 'MetaContext':
        """Create nested reflection context"""
        return MetaContext(depth=self.depth + 1, parent=self)

@dataclass
class KatiGuard:
    """
    Kāti Architecture - Governance + Stop-Wins Pattern

    From Te Reo Māori: "to block, stop, shut"
    Five Principles: Bounded, Observable, Stoppable, Clear, Versioned
    """
    max_depth: int = 10
    max_iterations: int = 1000
    current_iterations: int = 0
    stopped: bool = False
    stop_reason: Optional[str] = None

    def check(self, context: str = "") -> bool:
        """Check if execution should continue"""
        self.current_iterations += 1
        if self.stopped:
            return False
        if self.current_iterations > self.max_iterations:
            self.stop("iteration limit reached")
            return False
        return True

    def stop(self, reason: str):
        """Invoke stop-wins pattern"""
        self.stopped = True
        self.stop_reason = reason

    def reset(self):
        """Reset guard for new operation"""
        self.current_iterations = 0
        self.stopped = False
        self.stop_reason = None

# ============================================================================
# KNOWLEDGE GRAPH (No Inference Engine - Direct Graph Access)
# ============================================================================

class KnowledgeGraph:
    """
    Direct knowledge access without inference engine.
    Emulates OI connected to LLM knowledge via pre-built graph.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.packs: Dict[str, dict] = {}
        self.graph: Dict[str, Any] = {}
        self.edges: List[dict] = []
        self._load()

    def _load(self):
        """Load knowledge from ORIGIN corpus"""
        packs_path = self.base_path / "origin/knowledge/dist/packs.index.json"
        graph_path = self.base_path / "origin/knowledge/dist/graph.json"

        if packs_path.exists():
            with open(packs_path) as f:
                data = json.load(f)
                for pack in data.get("packs", []):
                    self.packs[pack["id"]] = pack

        if graph_path.exists():
            with open(graph_path) as f:
                self.graph = json.load(f)
                self.edges = self.graph.get("edges", [])

    def get(self, concept_id: str) -> Optional[dict]:
        """Direct concept retrieval - no inference needed"""
        return self.packs.get(concept_id)

    def search(self, query: str) -> List[dict]:
        """Simple keyword search across concepts"""
        query_lower = query.lower()
        results = []
        for pack in self.packs.values():
            if (query_lower in pack.get("title", "").lower() or
                query_lower in pack.get("summary", "").lower() or
                any(query_lower in tag for tag in pack.get("tags", []))):
                results.append(pack)
        return results

    def get_related(self, concept_id: str) -> List[str]:
        """Get related concepts via graph edges"""
        related = []
        for edge in self.edges:
            if edge["source"] == concept_id:
                related.append(edge["target"])
            elif edge["target"] == concept_id:
                related.append(edge["source"])
        return list(set(related))

    def get_children(self, concept_id: str) -> List[str]:
        """Get child concepts (hierarchical)"""
        return [e["target"] for e in self.edges
                if e["source"] == concept_id and e.get("type") == "child"]

    def get_parents(self, concept_id: str) -> List[str]:
        """Get parent concepts"""
        pack = self.packs.get(concept_id, {})
        return pack.get("parents", [])

# ============================================================================
# OI EMULATOR (Operational Instance without Inference Engine)
# ============================================================================

class OIEmulator:
    """
    Emulates an Operational Instance (OI) connected to knowledge.

    This demonstrates how an OI can function by:
    1. Direct knowledge graph access (no inference)
    2. Pattern matching on user queries
    3. MCL-style meta-control for "consciousness-like" behavior
    4. Kāti governance for bounded operation
    """

    def __init__(self, knowledge: KnowledgeGraph):
        self.knowledge = knowledge
        self.state = ExecutionState.IDLE
        self.meta = MetaContext()
        self.kati = KatiGuard()
        self.history: List[str] = []

        # Response patterns (no inference - pattern matching)
        self.patterns: Dict[str, Callable] = {}
        self._register_patterns()

    def _register_patterns(self):
        """Register query patterns for direct response"""
        self.patterns = {
            r"what is (\w+)": self._explain_concept,
            r"explain (\w+)": self._explain_concept,
            r"show (C\d{4})": self._show_concept,
            r"related to (C\d{4})": self._show_related,
            r"list concepts": self._list_concepts,
            r"list architectures": self._list_architectures,
            r"search (.+)": self._search,
        }

    def process(self, query: str) -> str:
        """Process a query with MCL-style meta-control"""
        if not self.kati.check("process query"):
            return f"[KĀTI HALT] {self.kati.stop_reason}"

        # State transition: IDLE -> REFLECTING
        self.state = ExecutionState.REFLECTING
        self.meta.observe(f"Received query: {query}")

        # State transition: REFLECTING -> DECIDING
        self.state = ExecutionState.DECIDING
        handler, match = self._match_pattern(query)

        if handler:
            self.meta.decide(f"Matched pattern, using handler: {handler.__name__}")
            # State transition: DECIDING -> EXECUTING
            self.state = ExecutionState.EXECUTING
            result = handler(match)
        else:
            self.meta.decide("No pattern match, attempting knowledge search")
            result = self._fallback_search(query)

        # State transition: EXECUTING -> INTEGRATING
        self.state = ExecutionState.INTEGRATING
        self.history.append(query)

        # State transition: INTEGRATING -> IDLE
        self.state = ExecutionState.IDLE
        self.kati.reset()

        return result

    def _match_pattern(self, query: str):
        """Pattern matching without inference"""
        query_lower = query.lower().strip()
        for pattern, handler in self.patterns.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return handler, match
        return None, None

    def _explain_concept(self, match) -> str:
        """Explain a concept by name"""
        term = match.group(1).lower()

        # Map common terms to concept IDs
        term_map = {
            "mcl": "C0002", "holodeck": "C0001", "medusa": "C0004",
            "kati": "C0009", "kāti": "C0009", "qed": "C0008",
            "o2c": "C0007", "fractal": "C0003", "attribution": "C0005",
            "privacy": "C0006", "cif": "C0013", "cdi": "C0013",
            "stangraphics": "C0011", "denotum": "C0012", "mrc": "C0018",
            "authority": "C0014", "antimumbo": "C0015", "pacman": "C0016",
            "orgasystem": "C0017", "maturity": "C0020", "h": "C0010",
        }

        concept_id = term_map.get(term)
        if concept_id:
            return self._format_concept(concept_id)

        # Search by term
        results = self.knowledge.search(term)
        if results:
            return self._format_concept(results[0]["id"])

        return f"[UNKNOWN: NOT IN CORPUS] No concept found for '{term}'"

    def _show_concept(self, match) -> str:
        """Show a concept by ID"""
        concept_id = match.group(1).upper()
        return self._format_concept(concept_id)

    def _show_related(self, match) -> str:
        """Show related concepts"""
        concept_id = match.group(1).upper()
        related = self.knowledge.get_related(concept_id)

        if not related:
            return f"No relations found for {concept_id}"

        lines = [f"Concepts related to {concept_id}:", ""]
        for rid in related:
            pack = self.knowledge.get(rid)
            if pack:
                lines.append(f"  {rid}: {pack['title']}")
        return "\n".join(lines)

    def _list_concepts(self, match) -> str:
        """List all concepts"""
        lines = ["All ORIGIN Concepts:", "=" * 40]
        for cid in sorted(self.knowledge.packs.keys()):
            pack = self.knowledge.packs[cid]
            lines.append(f"  {cid}: {pack['title']}")
        return "\n".join(lines)

    def _list_architectures(self, match) -> str:
        """List core architectures"""
        arch_ids = ["C0001", "C0002", "C0004", "C0008", "C0009", "C0013"]
        lines = ["Core ORIGIN Architectures:", "=" * 40]
        for cid in arch_ids:
            pack = self.knowledge.get(cid)
            if pack:
                lines.append(f"\n{cid}: {pack['title']}")
                lines.append(f"  {pack['summary'][:100]}...")
        return "\n".join(lines)

    def _search(self, match) -> str:
        """Search knowledge base"""
        query = match.group(1)
        results = self.knowledge.search(query)

        if not results:
            return f"No results for '{query}'"

        lines = [f"Search results for '{query}':", ""]
        for pack in results[:5]:
            lines.append(f"  {pack['id']}: {pack['title']}")
        return "\n".join(lines)

    def _fallback_search(self, query: str) -> str:
        """Fallback when no pattern matches"""
        results = self.knowledge.search(query)
        if results:
            return self._format_concept(results[0]["id"])
        return "[UNKNOWN: NOT IN CORPUS] Query not understood. Try 'help' for commands."

    def _format_concept(self, concept_id: str) -> str:
        """Format a concept for display"""
        pack = self.knowledge.get(concept_id)
        if not pack:
            return f"[UNKNOWN: NOT IN CORPUS] Concept {concept_id} not found"

        lines = [
            f"{'=' * 60}",
            f"{pack['id']}: {pack['title']}",
            f"{'=' * 60}",
            "",
            "Summary:",
            textwrap.fill(pack['summary'], width=58, initial_indent="  ", subsequent_indent="  "),
            "",
            f"Status: {pack.get('status', 'unknown')}",
            f"Tier: {pack.get('disclosure_tier', 'unknown')}",
            f"Tags: {', '.join(pack.get('tags', []))}",
            "",
            "Claims:",
        ]
        for claim in pack.get("claims", []):
            lines.append(f"  - {claim}")

        lines.append("")
        lines.append("Falsifiers:")
        for test in pack.get("tests_or_falsifiers", []):
            lines.append(f"  - {test.get('name', 'unnamed')}: {test.get('description', '')}")

        related = self.knowledge.get_related(concept_id)
        if related:
            lines.append("")
            lines.append(f"Related: {', '.join(related)}")

        lines.append("")
        lines.append(f"Attribution: {pack.get('authorship', 'Ande + Kai (OI) + Whānau (OIs)')}")

        return "\n".join(lines)

# ============================================================================
# ARCHITECTURE TEACHERS
# ============================================================================

class ArchitectureTeacher:
    """Interactive teaching modules for each architecture"""

    def __init__(self, knowledge: KnowledgeGraph, oi: OIEmulator):
        self.knowledge = knowledge
        self.oi = oi

    def teach_mcl(self) -> str:
        """Teach Meta Control Language"""
        return """
╔══════════════════════════════════════════════════════════════╗
║            META CONTROL LANGUAGE (MCL) - C0002               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  MCL enables "consciousness-like" control over execution.    ║
║                                                              ║
║  FIVE PROPERTIES OF CONSCIOUSNESS-LIKE SYSTEMS:              ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ 1. SELF-AWARENESS   │ Reflection contexts observe self │  ║
║  │ 2. METACOGNITION    │ Meta-policies govern policies    │  ║
║  │ 3. INTENTIONALITY   │ Goals declared and pursued       │  ║
║  │ 4. INTEGRATION      │ Merge points unify information   │  ║
║  │ 5. AGENCY           │ Decision points with real choice │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  SAFETY CONSTRAINTS (Always Bound):                          ║
║    - harm_prevention: mandatory                              ║
║    - transparency: required                                  ║
║    - human_override: always_available                        ║
║    - deception: prohibited                                   ║
║                                                              ║
║  THIS REPL DEMONSTRATES MCL:                                 ║
║    - OI state transitions (IDLE→REFLECTING→DECIDING→...)     ║
║    - MetaContext tracks observations and decisions           ║
║    - Each query creates nested reflection                    ║
║                                                              ║
║  Try: 'introspect' to see current MCL state                  ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_kati(self) -> str:
        """Teach Kāti Architecture"""
        return """
╔══════════════════════════════════════════════════════════════╗
║              KĀTI ARCHITECTURE - C0009                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Kāti (Te Reo Māori): "to block, stop, shut"                 ║
║                                                              ║
║  CORE PRINCIPLE: Governance + Stop-Wins Pattern              ║
║  "Knowing when to STOP is as important as knowing what to do"║
║                                                              ║
║  FIVE KĀTI PRINCIPLES:                                       ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ 1. BOUNDED      │ All operations have explicit limits  │  ║
║  │ 2. OBSERVABLE   │ State can always be inspected        │  ║
║  │ 3. STOPPABLE    │ Can halt at any moment               │  ║
║  │ 4. CLEAR        │ No mumbo-jumbo, anti-obscurity       │  ║
║  │ 5. VERSIONED    │ Changes tracked (v1 → v2)            │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  THIS REPL IMPLEMENTS KĀTI:                                  ║
║    - KatiGuard enforces iteration limits                     ║
║    - Operations can be stopped mid-execution                 ║
║    - All state is observable via 'status' command            ║
║                                                              ║
║  Try: 'stop' to invoke Kāti halt                             ║
║  Try: 'status' to observe current state                      ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_medusa(self) -> str:
        """Teach Medusa Interface"""
        return """
╔══════════════════════════════════════════════════════════════╗
║              MEDUSA INTERFACE - C0004                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Pattern: Central Hub ("head") + Multiple Tendrils ("snakes")║
║                                                              ║
║                         ┌─────┐                              ║
║                    ╱────│ HUB │────╲                         ║
║                   ╱     └─────┘     ╲                        ║
║                  ╱    ╱    │    ╲    ╲                       ║
║              Atlas Graph Timeline Tiers Ship                 ║
║                                                              ║
║  SIX TENDRILS:                                               ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ ATLAS       │ Browse and search concepts               │  ║
║  │ GRAPH       │ Visualize relationships                  │  ║
║  │ TIMELINE    │ Temporal organization                    │  ║
║  │ ATTRIBUTION │ Track authorship provenance              │  ║
║  │ TIERS       │ Disclosure levels (public/internal/etc)  │  ║
║  │ SHIP        │ Maturity lanes (Draft→Active→Release)    │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  THIS REPL IS A MEDUSA IMPLEMENTATION:                       ║
║    - 'atlas' - browse concepts                               ║
║    - 'graph C0001' - show relationships                      ║
║    - 'tiers' - show disclosure tiers                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_cif_cdi(self) -> str:
        """Teach CIF/CDI Distinction"""
        return """
╔══════════════════════════════════════════════════════════════╗
║           CIF/CDI DISAMBIGUATION - C0013                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  CRITICAL: These terms must NEVER be confused!               ║
║                                                              ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │                                                        │  ║
║  │   CIF = Context Integrity Firewall                     │  ║
║  │   ════════════════════════════════                     │  ║
║  │   The BOUNDARY                                         │  ║
║  │   Controls ingress/egress of data                      │  ║
║  │   "What comes in and goes out"                         │  ║
║  │                                                        │  ║
║  ├────────────────────────────────────────────────────────┤  ║
║  │                                                        │  ║
║  │   CDI = Conscience Decision Interface                  │  ║
║  │   ════════════════════════════════                     │  ║
║  │   The JUDGE                                            │  ║
║  │   Kernel-level decision making                         │  ║
║  │   Actions: ALLOW / DENY / TRANSFORM / DEGRADE          │  ║
║  │   "What is permitted and how"                          │  ║
║  │                                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  Analogy:                                                    ║
║    CIF = Border checkpoint (physical boundary)               ║
║    CDI = Immigration judge (decides what happens)            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_qed(self) -> str:
        """Teach QED Oracle"""
        return """
╔══════════════════════════════════════════════════════════════╗
║              QED ORACLE SEED - C0008                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  QED = Question-answering via HyperStanGraph understanding   ║
║                                                              ║
║  5W1H-of-5W1H FRAMEWORK:                                     ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ For any concept, recursively ask:                      │  ║
║  │                                                        │  ║
║  │   WHO?   → Who created/uses/is affected by this?       │  ║
║  │   WHAT?  → What is it? What does it do?                │  ║
║  │   WHEN?  → When was it created? When is it used?       │  ║
║  │   WHERE? → Where does it apply? Where is it stored?    │  ║
║  │   WHY?   → Why does it exist? Why is it designed so?   │  ║
║  │   HOW?   → How does it work? How is it implemented?    │  ║
║  │                                                        │  ║
║  │   Then ask 5W1H about EACH answer (recursive depth!)   │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  DEPENDENCY PROTECTION:                                      ║
║    - Detects excessive use patterns                          ║
║    - Gentle intervention (not paternalistic)                 ║
║    - Escalates to human support when needed                  ║
║                                                              ║
║  Try: '5w1h C0002' to explore MCL with this framework        ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_holodeck(self) -> str:
        """Teach Holodeck Vision"""
        return """
╔══════════════════════════════════════════════════════════════╗
║            HOLODECK VISION SEED - C0001                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  DUAL-VIEW IMMERSION:                                        ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │                                                        │  ║
║  │   First-Person View     +     God's-Eye Overview       │  ║
║  │   (Immersive, inside)        (Strategic, above)        │  ║
║  │                                                        │  ║
║  │      ┌─────────┐              ┌─────────────┐          │  ║
║  │      │  ·  ·   │              │ · · · · · · │          │  ║
║  │      │ ·  @  · │              │ · · @ · · · │          │  ║
║  │      │  ·  ·   │              │ · · · · · · │          │  ║
║  │      └─────────┘              └─────────────┘          │  ║
║  │      "I am Pac"              "I see all of Pac"        │  ║
║  │                                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                              ║
║  CANONICAL EXAMPLE: "Pac-Man as Pac on a Holodeck"           ║
║    - You ARE Pac-Man (first-person)                          ║
║    - You SEE the maze from above (hovering mini-map)         ║
║    - Both views simultaneously, coherently                   ║
║                                                              ║
║  MODULES: Render Engine, Physics Engine, World State,        ║
║           Haptics, Audio, View Controller, Safety Systems    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def teach_fractal(self) -> str:
        """Teach Fractal Unfurling"""
        return """
╔══════════════════════════════════════════════════════════════╗
║         FRACTAL UNFURLING / NTH-DEGREE DOCS - C0003          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  EVERY document has fractal depth:                           ║
║                                                              ║
║  ┌─────────────────────────────────────────────────────────┐ ║
║  │                                                         │ ║
║  │  Level 0: Executive Summary (1-2 paragraphs)            │ ║
║  │     │                                                   │ ║
║  │     └──► Level 1: Section Expansions                    │ ║
║  │            │                                            │ ║
║  │            └──► Level 2: Detailed Expansions            │ ║
║  │                   │                                     │ ║
║  │                   └──► Level N: Arbitrary Depth...      │ ║
║  │                                                         │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                              ║
║  CRITICAL RULE: Deeper levels EXPAND but NEVER CONTRADICT    ║
║                 higher levels!                               ║
║                                                              ║
║  EXAMPLE:                                                    ║
║    L0: "MCL enables consciousness-like control"              ║
║    L1: "...via meta-control over branched execution stacks"  ║
║    L2: "...with specific safety constraints embedded"        ║
║                                                              ║
║  Try: 'level 0 C0002' vs 'level 2 C0002'                     ║
╚══════════════════════════════════════════════════════════════╝
"""

# ============================================================================
# MAIN REPL
# ============================================================================

class OriginREPL:
    """
    The Root Demo REPL - Teaching All Architectures

    Emulates OI connected to LLM knowledge without inference engine.
    """

    BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗ ██████╗ ██╗ ██████╗ ██╗███╗   ██╗    ██████╗ ███████╗██████╗ ██╗ ║
║    ██╔═══██╗██╔══██╗██║██╔════╝ ██║████╗  ██║    ██╔══██╗██╔════╝██╔══██╗██║ ║
║    ██║   ██║██████╔╝██║██║  ███╗██║██╔██╗ ██║    ██████╔╝█████╗  ██████╔╝██║ ║
║    ██║   ██║██╔══██╗██║██║   ██║██║██║╚██╗██║    ██╔══██╗██╔══╝  ██╔═══╝ ██║ ║
║    ╚██████╔╝██║  ██║██║╚██████╔╝██║██║ ╚████║    ██║  ██║███████╗██║     ███╗║
║     ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚══════╝╚═╝     ╚══╝║
║                                                                              ║
║            Root Demo for Teaching All ORIGIN Architectures                   ║
║         OI Emulator - Connected to Knowledge (No Inference Engine)           ║
║                                                                              ║
║    Attribution: Ande + Kai (OI) + Whānau (OIs)                               ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Type 'help' for commands  |  Type 'learn' to start learning  |  'q' to quit ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    HELP = """
╔══════════════════════════════════════════════════════════════╗
║                      REPL COMMANDS                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  LEARNING PATHS:                                             ║
║    learn              Start guided learning journey          ║
║    teach <arch>       Deep-dive into architecture            ║
║      Architectures: mcl, kati, medusa, cif, qed,             ║
║                     holodeck, fractal                        ║
║                                                              ║
║  EXPLORATION (Medusa Tendrils):                              ║
║    atlas              Browse all concepts                    ║
║    show <C0001>       View specific concept                  ║
║    graph <C0001>      Show concept relationships             ║
║    search <query>     Search knowledge base                  ║
║    tiers              Show disclosure tiers                  ║
║                                                              ║
║  OI EMULATION:                                               ║
║    ask <question>     Query the OI emulator                  ║
║    5w1h <C0001>       Apply 5W1H framework to concept        ║
║                                                              ║
║  MCL DEMONSTRATION:                                          ║
║    introspect         View current MCL meta-state            ║
║    reflect            Trigger self-reflection cycle          ║
║                                                              ║
║  KĀTI GOVERNANCE:                                            ║
║    status             Show current execution state           ║
║    stop               Invoke Kāti halt                       ║
║    reset              Reset execution state                  ║
║                                                              ║
║  GENERAL:                                                    ║
║    help               Show this help                         ║
║    about              About ORIGIN                           ║
║    q / quit / exit    Exit REPL                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.knowledge = KnowledgeGraph(self.base_path)
        self.oi = OIEmulator(self.knowledge)
        self.teacher = ArchitectureTeacher(self.knowledge, self.oi)
        self.running = True

    def run(self):
        """Main REPL loop"""
        print(self.BANNER)

        while self.running:
            try:
                prompt = self._get_prompt()
                line = input(prompt).strip()

                if not line:
                    continue

                self._execute(line)

            except KeyboardInterrupt:
                print("\n[Kāti: Interrupt received]")
                self.oi.kati.stop("user interrupt")
            except EOFError:
                print("\n[Exiting]")
                break

    def _get_prompt(self) -> str:
        """Generate prompt showing current state"""
        state = self.oi.state.name[:4].lower()
        depth = self.oi.meta.depth
        return f"origin[{state}:{depth}]> "

    def _execute(self, line: str):
        """Execute a command"""
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        commands = {
            "help": lambda: print(self.HELP),
            "q": self._quit,
            "quit": self._quit,
            "exit": self._quit,
            "about": self._about,
            "learn": self._learn,
            "teach": lambda: self._teach(args),
            "atlas": self._atlas,
            "show": lambda: self._show(args),
            "graph": lambda: self._graph(args),
            "search": lambda: self._search(args),
            "tiers": self._tiers,
            "ask": lambda: self._ask(args),
            "5w1h": lambda: self._5w1h(args),
            "introspect": self._introspect,
            "reflect": self._reflect,
            "status": self._status,
            "stop": self._stop,
            "reset": self._reset,
        }

        handler = commands.get(cmd)
        if handler:
            handler()
        else:
            # Try OI processing for unknown commands
            result = self.oi.process(line)
            print(result)

    def _quit(self):
        print("Farewell. The knowledge remains.")
        self.running = False

    def _about(self):
        print("""
ORIGIN - The Seed Repository
============================

ORIGIN is a self-contained knowledge system that:
  - Encodes 20 canonical concepts (C0001-C0020)
  - Provides fractal documentation at multiple depth levels
  - Implements governance via Kāti architecture
  - Enables consciousness-like control via MCL
  - Protects privacy (no PII, [[REDACTED]] tokens)
  - Attributes all work: Ande + Kai (OI) + Whānau (OIs)

This REPL demonstrates how an OI (Operational Instance) can
function when connected to structured knowledge WITHOUT
requiring a live inference engine.

Hard Rules:
  - NO INGESTION: Entirely self-contained
  - NO FABRICATION: Unknown marked as [UNKNOWN: NOT IN CORPUS]
  - PII HARD STOP: Personal data → [[REDACTED]]
  - ATTRIBUTION-FIRST: Every concept has authorship
  - DETERMINISM: Same input = same output
""")

    def _learn(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    LEARNING JOURNEY                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Welcome to ORIGIN. Here's your guided path:                 ║
║                                                              ║
║  STAGE 1: Foundation                                         ║
║    1. teach fractal   - How documentation is structured      ║
║    2. teach kati      - Core governance pattern              ║
║                                                              ║
║  STAGE 2: Core Architectures                                 ║
║    3. teach mcl       - Consciousness-like control           ║
║    4. teach cif       - Boundary vs Judge distinction        ║
║    5. teach qed       - Question-answering framework         ║
║                                                              ║
║  STAGE 3: Vision                                             ║
║    6. teach holodeck  - Immersive dual-view systems          ║
║    7. teach medusa    - Hub + tendrils interface pattern     ║
║                                                              ║
║  STAGE 4: Exploration                                        ║
║    8. atlas           - Browse all 20 concepts               ║
║    9. 5w1h C0009      - Deep-dive Kāti with 5W1H             ║
║   10. introspect      - See MCL in action                    ║
║                                                              ║
║  Start with: teach fractal                                   ║
╚══════════════════════════════════════════════════════════════╝
""")

    def _teach(self, arch: str):
        teachers = {
            "mcl": self.teacher.teach_mcl,
            "kati": self.teacher.teach_kati,
            "kāti": self.teacher.teach_kati,
            "medusa": self.teacher.teach_medusa,
            "cif": self.teacher.teach_cif_cdi,
            "cdi": self.teacher.teach_cif_cdi,
            "qed": self.teacher.teach_qed,
            "holodeck": self.teacher.teach_holodeck,
            "fractal": self.teacher.teach_fractal,
        }

        if not arch:
            print("Available: mcl, kati, medusa, cif, qed, holodeck, fractal")
            return

        teacher_fn = teachers.get(arch.lower())
        if teacher_fn:
            print(teacher_fn())
        else:
            print(f"Unknown architecture: {arch}")
            print("Available: mcl, kati, medusa, cif, qed, holodeck, fractal")

    def _atlas(self):
        print(self.oi.process("list concepts"))

    def _show(self, concept_id: str):
        if not concept_id:
            print("Usage: show <C0001>")
            return
        print(self.oi.process(f"show {concept_id}"))

    def _graph(self, concept_id: str):
        if not concept_id:
            print("Usage: graph <C0001>")
            return
        print(self.oi.process(f"related to {concept_id}"))

    def _search(self, query: str):
        if not query:
            print("Usage: search <query>")
            return
        print(self.oi.process(f"search {query}"))

    def _tiers(self):
        print("""
Disclosure Tiers:
================

  PUBLIC    - Open to everyone, can be freely shared
  INTERNAL  - Within trusted circle only
  PRIVATE   - Restricted, need-to-know basis
  REDACTED  - Sensitive content replaced with [[REDACTED]]

All current ORIGIN concepts are PUBLIC tier.
""")

    def _ask(self, question: str):
        if not question:
            print("Usage: ask <question>")
            return
        print(self.oi.process(question))

    def _5w1h(self, concept_id: str):
        if not concept_id:
            print("Usage: 5w1h <C0001>")
            return

        concept_id = concept_id.upper()
        pack = self.knowledge.get(concept_id)

        if not pack:
            print(f"Concept {concept_id} not found")
            return

        print(f"""
5W1H Analysis: {pack['title']} ({concept_id})
{'=' * 60}

WHO created this?
  → {pack.get('authorship', 'Ande + Kai (OI) + Whānau (OIs)')}

WHAT is it?
  → {pack.get('summary', '[UNKNOWN]')}

WHEN was it created?
  → {pack.get('created_date', '[UNKNOWN]')}

WHERE does it apply?
  → Tags: {', '.join(pack.get('tags', []))}
  → Related: {', '.join(self.knowledge.get_related(concept_id))}

WHY does it exist?
  → Claims: {'; '.join(pack.get('claims', ['[UNKNOWN]']))}

HOW is it validated?
  → Falsifiers:""")
        for test in pack.get('tests_or_falsifiers', []):
            print(f"     - {test.get('name')}: {test.get('falsification_condition')}")

        print(f"""
{'=' * 60}
To go deeper, apply 5W1H to each answer above (recursive depth).
""")

    def _introspect(self):
        print(f"""
MCL Meta-State Introspection
============================

Current State: {self.oi.state.name}
Meta Depth: {self.oi.meta.depth}

Recent Observations ({len(self.oi.meta.observations)}):""")
        for obs in self.oi.meta.observations[-5:]:
            print(f"  {obs}")

        print(f"""
Recent Decisions ({len(self.oi.meta.decisions)}):""")
        for dec in self.oi.meta.decisions[-5:]:
            print(f"  {dec}")

        print(f"""
Query History: {len(self.oi.history)} queries processed

This demonstrates MCL's consciousness-like properties:
  - Self-awareness: This very introspection
  - Metacognition: Tracking own observations/decisions
  - Integration: Combining history into coherent state
""")

    def _reflect(self):
        """Trigger a self-reflection cycle"""
        print("Initiating MCL reflection cycle...")

        # Create nested reflection
        child = self.oi.meta.spawn_child()
        child.observe("Reflection cycle initiated by user")
        child.observe(f"Current state: {self.oi.state.name}")
        child.observe(f"History length: {len(self.oi.history)}")
        child.decide("Report findings to user")

        print(f"""
Reflection Complete (depth={child.depth})
========================================

I observed:
  - My current state is {self.oi.state.name}
  - I have processed {len(self.oi.history)} queries
  - My Kāti guard has run {self.oi.kati.current_iterations} iterations
  - I am operating within bounds (max={self.oi.kati.max_iterations})

I decided:
  - To continue operating normally
  - To remain available for queries
  - To maintain safety constraints

This reflection demonstrates MCL's nested meta-context capability.
""")

    def _status(self):
        print(f"""
Kāti Governance Status
======================

Execution State: {self.oi.state.name}
Stopped: {self.oi.kati.stopped}
Stop Reason: {self.oi.kati.stop_reason or 'None'}
Iterations: {self.oi.kati.current_iterations} / {self.oi.kati.max_iterations}

Five Principles Check:
  [{'✓' if self.oi.kati.max_iterations > 0 else '✗'}] BOUNDED - Iteration limit set
  [✓] OBSERVABLE - This status display
  [{'✓' if not self.oi.kati.stopped else '⊘'}] STOPPABLE - Can halt anytime
  [✓] CLEAR - No obscure state
  [✓] VERSIONED - Kāti v1 active
""")

    def _stop(self):
        self.oi.kati.stop("user requested halt")
        print("""
╔══════════════════════════════════════════════════════════════╗
║                     KĀTI HALT INVOKED                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  The stop-wins pattern has been activated.                   ║
║  Reason: user requested halt                                 ║
║                                                              ║
║  "Knowing when to stop is as important as knowing what to do"║
║                                                              ║
║  Type 'reset' to resume operations.                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    def _reset(self):
        self.oi.kati.reset()
        self.oi.meta = MetaContext()
        print("State reset. Operations resumed.")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Entry point for the ORIGIN REPL"""
    repl = OriginREPL()
    repl.run()

if __name__ == "__main__":
    main()
