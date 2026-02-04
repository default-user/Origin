# OI-FAR Architecture

**OI-FAR** = Ongoing-Intelligence Frontier Approximation Runtime

A deterministic intelligence system that approximates frontier LLM capability surface using explicit knowledge, deterministic retrieval, deterministic planning/solving, and audited rendering.

## Core Principles

1. **Deterministic-first**: Core planning/reasoning uses deterministic algorithms over explicit structures
2. **Fail-closed**: Output `UNKNOWN` when answer cannot be justified from knowledge + reasoning
3. **Traceability**: Every answer is reconstructable from retrieved sources/bricks + deterministic transforms
4. **No fabrication**: Never invent facts, sources, or citations
5. **Safety/integrity**: Sandboxed execution, capability-gated tools

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / API                                │
│                    oi_far run "query"                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    MODULE 1: OI KERNEL                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │SessionState │  │Commitments  │  │ User Prefs/Constraints  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                MODULE 2: KNOWLEDGE SUBSTRATE                     │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │ DocumentStore │  │  BrickStore   │  │      Indexes       │  │
│  │ (raw docs)    │  │ (compressed)  │  │ lexical/graph/sem  │  │
│  └───────────────┘  └───────────────┘  └────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│               MODULE 3: RETRIEVAL PIPELINE                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ retrieve(query, session) → ContextPack                   │   │
│  │  - Deterministic scoring (BM25, claim overlap)           │   │
│  │  - Contradiction penalty                                  │   │
│  │  - Known unknowns detection                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│            MODULE 4: DETERMINISTIC REASONING CORE               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Planner  │→ │  Solver  │→ │  Critic  │                      │
│  │ (steps)  │  │ (execute)│  │ (verify) │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
│                                    │                            │
│                          ┌─────────▼─────────┐                 │
│                          │    AnswerPlan     │                 │
│                          │ (structured data) │                 │
│                          └───────────────────┘                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    MODULE 5: RENDERER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ render(AnswerPlan) → text                                │   │
│  │  - Deterministic templates (galley/bridge)               │   │
│  │  - No-new-claims enforcement                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                      Rendered Output
```

## Modules

### MODULE 1: OI Kernel

**Location**: `oi_far/kernel/`

Maintains session state and commitments:
- **SessionState**: Intent, constraints, threads/todos, user prefs, memory handles
- **CommitmentTracker**: Claims made, actions promised, constraints to respect
- **Types**: Core type definitions

```python
from oi_far.kernel import SessionState

session = SessionState()
session.set_intent("explain holodeck")
session.add_constraint("cite all sources")
session.user_prefs["mode"] = "bridge"
```

### MODULE 2: Knowledge Substrate

**Location**: `oi_far/substrate/`

Storage and indexing for knowledge:
- **DocumentStore**: Raw documents with extracted text
- **BrickStore**: Meaning-compressed units with claims, definitions, links
- **BrickCompiler**: Compiles documents to bricks
- **Indexes**: Lexical (BM25), Graph (adjacency), Semantic (optional)

**Brick Schema**:
```python
@dataclass
class Brick:
    id: str
    kind: BrickKind  # CONCEPT, CLAIM, DEFINITION, RELATION
    title: str
    summary: str
    claims: list[Claim]
    definitions: list[Definition]
    links: list[Link]
    provenance: Provenance
    confidence: float
    tags: list[str]
```

### MODULE 3: Retrieval Pipeline

**Location**: `oi_far/retrieval/`

Deterministic RAG with explicit scoring:
- **DeterministicRetriever**: Main retrieval class
- **DeterministicScorer**: Scoring functions
- **ContextPack**: Output containing retrieved context

**Scoring Components**:
- Lexical overlap (30%)
- Claim relevance (25%)
- Provenance recency (15%)
- Confidence (15%)
- Constraint alignment (10%)
- Definition match (5%)

### MODULE 4: Deterministic Reasoning Core

**Location**: `oi_far/reasoning/`

Planning, solving, and critique:
- **DeterministicPlanner**: Creates execution plans from task schemas
- **DeterministicSolver**: Executes plans deterministically
- **DeterministicCritic**: Evaluates answers for correctness

**Plan Step Types**:
- RETRIEVE: Fetch information
- DEFINE: Define terms
- COMPARE: Compare items
- DEDUCE: Logical deduction
- VERIFY: Verify claims
- SYNTHESIZE: Combine information
- FORMAT: Format output

### MODULE 5: Renderer

**Location**: `oi_far/renderer/`

Converts AnswerPlans to text:
- **DeterministicRenderer**: Template-based rendering
- **ClaimChecker**: Enforces no-new-claims invariant
- **Templates**: Galley (concise) and Bridge (structured)

**Render Modes**:
- `galley`: Concise, human-scale output
- `bridge`: Structured with headings and checklists

### MODULE 6: Tooling Interface

**Location**: `oi_far/tools/`

Capability-gated tool registry:
- **ToolRegistry**: Register and invoke tools with capability checks
- **search_vault**: Search the knowledge vault
- **open_file**: Read files safely
- **run_tests**: Execute project tests
- **execute_code_sandboxed**: Run Python in sandbox

**Capabilities**:
- `READ`: Read-only access
- `WRITE`: Can modify state
- `EXECUTE`: Can run code
- `NETWORK`: Can access network

### Growth Loop

**Location**: `oi_far/growth/`

Capability expansion over time:
- **GrowthLoop**: Ingest → compile → reindex → eval
- **MissingKnowledgeTracker**: Track knowledge gaps
- **RegressionTest**: Generate tests from failures

## Data Flow

1. **Query** arrives at CLI/API
2. **Kernel** updates session state
3. **Retrieval** fetches relevant bricks and sources
4. **Planner** creates execution plan
5. **Solver** executes plan steps
6. **Critic** evaluates answer quality
7. **Renderer** converts to text output
8. **Growth Loop** tracks failures for future improvement

## Determinism Guarantees

OI-FAR guarantees deterministic output:
- Same input → identical output bytes
- No randomness in any module
- Fixed algorithm parameters
- Sorted iterations where order matters

To verify determinism:
```bash
python -m oi_far.cli run "query" > out1.txt
python -m oi_far.cli run "query" > out2.txt
diff out1.txt out2.txt  # Should be empty
```

## Fail-Closed Semantics

When OI-FAR cannot justify an answer:
1. Returns `UNKNOWN` status
2. Lists what information is missing
3. Suggests what would help
4. Tracks gap for growth loop

Example output:
```
UNKNOWN. Missing: definition of "quantum computing" in knowledge base.
Would help: Documents covering quantum computing fundamentals.
```

## Next Steps

- See [Adding Knowledge](adding_knowledge.md) for how to expand the knowledge base
- See [Running Evals](running_evals.md) for evaluation procedures
- See [Determinism Guarantees](determinism.md) for technical details
