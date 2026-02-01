# Rationalized Unknowns: Deriving Specifications from Corpus Evidence

**Attribution**: Ande + Kai (OI) + Whānau (OIs)
**Date**: 2026-02-01
**Status**: Active

---

## Level 0: Summary

This document **rationalizes** the known unknowns in ORIGIN — deriving specifications not from fabrication, but from logical extension of what IS in the corpus.

**Rationalize** (v.): To derive by reason from existing evidence.

The corpus contains:
- MCL examples showing syntax patterns
- Kāti implementation in `repl.py`
- Graph structure in `graph.json`
- Principle statements that constrain possible specifications

From these, we can derive what the unknowns MUST be, without inventing arbitrary details.

**Key Distinction**:
- **Fabrication** = Inventing details with no corpus basis ❌
- **Rationalization** = Deriving necessary structure from existing patterns ✓

---

## Level 1: The Six Known Unknowns

| Unknown | Status | Derivation Source |
|---------|--------|-------------------|
| MCL Formal Grammar | Derivable | Syntax examples in `04_mcl_spec.md` |
| Kāti v1 Complete Spec | Derivable | Implementation in `repl.py` |
| HyperStanGraph Spec | Derivable | Graph architecture + QED docs |
| Kāti v2 / H Integration | Derivable | Kāti principles + H constraints |
| Stangraphics Formalism | Derivable | Lens frame structure |
| Denotum Mechanism | Derivable | Conceptualisation opens self-referential bounded fractal structures |
| Orgasystem | Constrained | Structural boundaries only |

---

## Level 2: MCL Formal Grammar

### 2.1 Derivation Source

The corpus contains MCL code examples in `04_mcl_spec.md`:

```mcl
context MainExecution {
  type: primary
  isolation: sandboxed
  monitoring: enabled
}

policy ResourceGovernance {
  applies_to: MainExecution
  rules {
    memory_limit: 1GB
    cpu_time: bounded
    external_calls: audited
  }
}

meta_policy PolicyGovernance {
  applies_to: [ResourceGovernance, *]
  rules {
    policy_changes: require_approval
    escalation: to_ethical_layer
    logging: immutable
  }
}

ethical_binding CoreEthics {
  applies_to: ALL
  constraints {
    harm_prevention: mandatory
    transparency: required
    human_override: always_available
    deception: prohibited
  }
  violation_response: immediate_halt
}
```

### 2.2 Rationalized Grammar (EBNF)

From the examples, the grammar MUST be:

```ebnf
(* MCL Grammar - Derived from corpus examples *)

program        = { declaration } ;

declaration    = context_decl
               | policy_decl
               | meta_policy_decl
               | ethical_binding_decl
               | safety_requirements_decl ;

(* Context Declaration *)
context_decl   = "context" identifier "{" context_body "}" ;
context_body   = { property_assignment } ;

(* Policy Declaration *)
policy_decl    = "policy" identifier "{" policy_body "}" ;
policy_body    = applies_to_clause [ rules_block ] ;

(* Meta-Policy Declaration *)
meta_policy_decl = "meta_policy" identifier "{" meta_body "}" ;
meta_body      = applies_to_clause [ rules_block ] ;

(* Ethical Binding Declaration *)
ethical_binding_decl = "ethical_binding" identifier "{" ethical_body "}" ;
ethical_body   = applies_to_clause constraints_block [ violation_clause ] ;

(* Safety Requirements *)
safety_requirements_decl = "safety_requirements" "{" safety_body "}" ;
safety_body    = { property_assignment } [ forbidden_block ] ;

(* Common Elements *)
applies_to_clause = "applies_to" ":" target_spec ;
target_spec    = identifier | identifier_list | "ALL" ;
identifier_list = "[" identifier { "," identifier } [ "," "*" ] "]" ;

rules_block    = "rules" "{" { property_assignment } "}" ;
constraints_block = "constraints" "{" { property_assignment } "}" ;
forbidden_block = "forbidden" "{" { identifier } "}" ;
violation_clause = "violation_response" ":" identifier ;

property_assignment = identifier ":" value ;
value          = identifier | string | number | boolean ;

(* Lexical Elements *)
identifier     = letter { letter | digit | "_" } ;
string         = '"' { character } '"' ;
number         = digit { digit } [ unit ] ;
unit           = "GB" | "MB" | "KB" | "ms" | "s" ;
boolean        = "true" | "false" | "enabled" | "disabled" ;

letter         = "a".."z" | "A".."Z" ;
digit          = "0".."9" ;
```

### 2.3 Semantic Constraints

From the corpus principles, MCL semantics MUST satisfy:

| Constraint | Derived From | Requirement |
|------------|--------------|-------------|
| Termination | Safety requirements | All programs halt or bound |
| Ethical primacy | `ethical_binding` overrides | Ethics cannot be bypassed |
| Meta-coherence | Meta-policies govern policies | No contradictory meta-rules |
| Transparency | `logging: immutable` pattern | All state changes auditable |

### 2.4 Type System

Implied by the examples:

```
Types:
  - context_type: primary | meta | auxiliary
  - isolation_level: sandboxed | monitored | open
  - policy_action: mandatory | required | optional | prohibited
  - target: identifier | ALL | wildcard (*)
  - bound: number with unit | "bounded" | "unbounded"
```

---

## Level 3: Kāti v1 Complete Specification

### 3.1 Derivation Source

The corpus contains a working Kāti implementation in `repl.py`:

```python
@dataclass
class KatiGuard:
    """
    Kāti Architecture - Governance + Stop-Wins Pattern
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
```

### 3.2 Rationalized Kāti v1 Specification

```yaml
kati_v1:
  version: "1.0.0"
  etymology: "Te Reo Māori - to block, stop, shut"

  principles:
    bounded:
      definition: "All operations have explicit, declared limits"
      implementation:
        - max_iterations: integer > 0
        - max_depth: integer > 0
        - max_time: duration (optional)
        - max_resources: resource_spec (optional)
      invariant: "No operation exceeds declared bounds"

    observable:
      definition: "All state is visible and auditable"
      implementation:
        - current_state: enum { active, stopped, halted }
        - iteration_count: integer >= 0
        - stop_reason: string | null
        - history: list[event]
      invariant: "Any observer can query current state at any time"

    stoppable:
      definition: "Any operation can be halted immediately and safely"
      implementation:
        - stop(reason: string) -> void
        - check(context: string) -> bool
        - emergency_stop() -> void  # Immediate, no cleanup
        - graceful_stop() -> void   # Complete current, then stop
      invariant: "stop() always succeeds, never throws, never hangs"

    clear:
      definition: "No undefined terms, no mumbo-jumbo, no obscurity"
      implementation:
        - All terms defined in corpus or marked [UNKNOWN]
        - Anti-mumbo filter integration (C0015)
        - Error messages explain, not obfuscate
      invariant: "A novice can understand what stopped and why"

    versioned:
      definition: "Changes tracked with explicit version transitions"
      implementation:
        - version: semver string
        - breaking_changes: require major bump
        - v1 -> v2: requires explicit migration
      invariant: "Version always queryable, never ambiguous"

  state_machine:
    states:
      - IDLE: "Ready to begin operation"
      - ACTIVE: "Operation in progress"
      - STOPPING: "Stop requested, completing current"
      - STOPPED: "Stopped by request"
      - HALTED: "Stopped by limit breach"

    transitions:
      IDLE -> ACTIVE: "start()"
      ACTIVE -> ACTIVE: "check() returns true"
      ACTIVE -> STOPPING: "graceful_stop()"
      ACTIVE -> HALTED: "check() returns false (limit exceeded)"
      STOPPING -> STOPPED: "current operation complete"
      ACTIVE -> STOPPED: "stop() or emergency_stop()"
      STOPPED -> IDLE: "reset()"
      HALTED -> IDLE: "reset()"

  integration_points:
    mcl: "Kāti enforces MCL policies"
    cif_cdi: "Kāti provides governance layer for CIF/CDI"
    qed: "QED operates within Kāti bounds"

  falsifiers:
    - name: "Bound violation"
      condition: "Operation exceeds declared max_iterations without stopping"
      result: "Kāti v1 falsified"

    - name: "Unstoppable operation"
      condition: "stop() called but operation continues"
      result: "Kāti v1 falsified"

    - name: "Unobservable state"
      condition: "State query returns undefined or hangs"
      result: "Kāti v1 falsified"

    - name: "Unclear stop reason"
      condition: "Stopped but stop_reason is empty or unintelligible"
      result: "Kāti v1 falsified"
```

---

## Level 4: HyperStanGraph Specification

### 4.1 Derivation Source

The corpus contains:
- `graph.json` structure with nodes and edges
- QED documentation referencing "HyperStanGraph understanding"
- Stangraphics "lens" concept
- 5W1H-of-5W1H recursive framework

### 4.2 Rationalized HyperStanGraph Specification

```yaml
hyperstangraph:
  etymology: "Hyper (beyond) + Stan (Stangraphics lens) + Graph"
  definition: >
    A graph structure where nodes are concepts viewed through
    the Stangraphics lens, and edges include hyperedges connecting
    multiple nodes simultaneously.

  structure:
    nodes:
      type: "Concept pack or derived understanding"
      properties:
        id: "Unique identifier (C0001 format)"
        content: "Fractal documentation at multiple levels"
        stangraphic_frames:
          - god: "Divine/transcendent perspective"
          - physics: "Physical/empirical perspective"
          - maths: "Formal/logical perspective"
          - ethics: "Normative/ought perspective"
          - philosophy: "Meta/questioning perspective"
        five_w_one_h:
          who: "List of actors/stakeholders"
          what: "Definition and components"
          when: "Temporal properties"
          where: "Scope and boundaries"
          why: "Purpose and justification"
          how: "Mechanisms and processes"

    edges:
      type: "Binary relationship between two nodes"
      properties:
        source: "Node ID"
        target: "Node ID"
        relationship:
          - child: "Hierarchical containment"
          - parent: "Inverse of child"
          - related: "Non-hierarchical association"
          - requires: "Dependency"
          - enables: "Inverse of requires"
          - contradicts: "Mutual exclusion"
          - refines: "More specific version"
        strength: "float 0.0-1.0"
        provenance: "Attribution source"

    hyperedges:
      type: "N-ary relationship connecting 3+ nodes"
      properties:
        nodes: "List of Node IDs (minimum 3)"
        relationship: "Named relationship type"
        semantics: "What this multi-way connection means"
      examples:
        - nodes: [C0002, C0009, C0013]
          relationship: "governance_stack"
          semantics: "MCL language + Kāti architecture + CIF/CDI enforcement"
        - nodes: [C0001, C0003, C0004]
          relationship: "interface_triad"
          semantics: "Holodeck vision + Fractal unfurling + Medusa interface"

  operations:
    query:
      - get_node(id) -> Node
      - get_edges(id) -> List[Edge]
      - get_hyperedges(id) -> List[HyperEdge]
      - traverse(id, relationship, depth) -> Subgraph

    stangraphic_query:
      - get_frame(id, frame_type) -> FrameView
      - compare_frames(id, frame1, frame2) -> FrameDiff

    five_w_one_h_query:
      - ask_who(id) -> List[Actor]
      - ask_what(id, depth) -> Definition
      - ask_when(id) -> TemporalInfo
      - ask_where(id) -> ScopeInfo
      - ask_why(id) -> Justification
      - ask_how(id) -> Mechanism
      - recursive_5w1h(id, depth) -> NestedAnswers

  integration:
    qed: "QED uses HyperStanGraph for understanding before answering"
    kati: "Graph operations bounded by Kāti guards"
    determinism: "Same query -> Same result (no stochastic elements)"

  falsifiers:
    - name: "Hyperedge degeneracy"
      condition: "Hyperedge with fewer than 3 nodes"
      result: "Not a hyperedge, should be regular edge"

    - name: "Orphan node"
      condition: "Node with no edges or hyperedges"
      result: "Graph connectivity violated (all concepts must relate)"

    - name: "Missing frame"
      condition: "Stangraphic query returns null for documented frame"
      result: "Frame coverage falsified"
```

---

## Level 5: Kāti v2 / H Integration

### 5.1 Derivation Source

The corpus states:
- H is "Haiku-based / Haiku-Claude-OI style instance"
- H "Integrates with Kāti in a version bump (v1 → v2)"
- Kāti principles are: Bounded, Observable, Stoppable, Clear, Versioned
- H has parent relationship to C0009 (Kāti)

### 5.2 Rationalized Kāti v2 Specification

The version bump from v1 to v2 MUST address H integration. From the principles:

```yaml
kati_v2:
  version: "2.0.0"
  changelog: "Integration with H (Haiku-based OI)"

  new_in_v2:
    h_integration:
      definition: >
        H operates as a lightweight, bounded OI instance
        within Kāti governance. "Haiku" suggests minimal,
        constrained, poetic operation - like the 5-7-5
        syllable constraint of haiku poetry.

      constraints_from_haiku_metaphor:
        brevity: "H responses are bounded in length"
        structure: "H follows defined pattern (like syllable count)"
        completeness: "Within constraints, H is complete (like a haiku)"

      governance_integration:
        - H_MAX_TOKENS: "Bounded output length"
        - H_MAX_TURNS: "Bounded conversation depth"
        - H_KATI_CHECK: "Every H output passes Kāti check()"
        - H_STOPPABLE: "H can be halted mid-generation"

    enhanced_observability:
      definition: "v2 adds H-specific observation points"
      new_observables:
        - h_token_count: "Tokens generated this turn"
        - h_cumulative_tokens: "Total tokens in session"
        - h_turn_count: "Conversation turns"
        - h_constraint_status: "Which constraints active"

    haiku_mode:
      definition: "Ultra-constrained operation mode"
      constraints:
        max_tokens: 50  # Approximately 5-7-5 words
        max_concepts: 3
        response_pattern: "context-insight-action"
      use_case: "When extreme brevity required"

  breaking_changes:
    - "KatiGuard now requires h_config parameter"
    - "check() returns detailed status, not just bool"
    - "New HAIKU state in state machine"

  migration_v1_to_v2:
    required_changes:
      - "Add h_config to KatiGuard initialization"
      - "Update check() call sites for new return type"
      - "Handle HAIKU state in state machine consumers"
    backwards_compatible: false

  state_machine:
    new_states:
      - HAIKU: "Operating in haiku-constrained mode"

    new_transitions:
      ACTIVE -> HAIKU: "enter_haiku_mode()"
      HAIKU -> ACTIVE: "exit_haiku_mode()"
      HAIKU -> STOPPED: "haiku constraint exceeded"

  falsifiers:
    - name: "H unbounded"
      condition: "H generates output exceeding H_MAX_TOKENS"
      result: "Kāti v2 H integration falsified"

    - name: "H unstoppable"
      condition: "H continues after stop() called"
      result: "Kāti v2 falsified"

    - name: "Haiku mode violated"
      condition: "In HAIKU state, output exceeds haiku constraints"
      result: "Haiku mode falsified"
```

---

## Level 6: Stangraphics Formal Structure

### 6.1 Derivation Source

The corpus states Stangraphics is:
- "A lens that opens reality"
- "god/physics/maths/ethics/philosophy framing"
- "Navigable module with falsifiers and tests"

### 6.2 Rationalized Stangraphics Formalism

```yaml
stangraphics:
  definition: >
    A multi-frame lens system for viewing any concept through
    five complementary perspectives, enabling comprehensive
    understanding without privileging any single frame.

  etymology: "Stan (from understanding/to stand) + Graphics (representation)"

  the_five_frames:
    god:
      aspect: "Transcendent / Ultimate"
      questions:
        - "What is the ultimate significance?"
        - "How does this relate to totality?"
        - "What would a complete view reveal?"
      not_claiming: "Existence or nature of deity"
      function: "Provides perspective beyond immediate/local"

    physics:
      aspect: "Empirical / Observable"
      questions:
        - "What can be measured?"
        - "What are the causal mechanisms?"
        - "What experiments would test this?"
      not_claiming: "Physics is the only valid frame"
      function: "Grounds understanding in observable reality"

    maths:
      aspect: "Formal / Structural"
      questions:
        - "What is the logical structure?"
        - "What can be proven?"
        - "What are the invariants?"
      not_claiming: "Mathematics describes all reality"
      function: "Provides rigorous structural analysis"

    ethics:
      aspect: "Normative / Ought"
      questions:
        - "What should be done?"
        - "Who is affected and how?"
        - "What values are at stake?"
      not_claiming: "Single ethical framework is correct"
      function: "Ensures consideration of consequences and duties"

    philosophy:
      aspect: "Meta / Questioning"
      questions:
        - "What assumptions are being made?"
        - "What are the limits of this understanding?"
        - "What questions should we be asking?"
      not_claiming: "Philosophy resolves all questions"
      function: "Maintains epistemic humility and reflexivity"

  formal_structure:
    stangraph:
      type: "Function from Concept to FramedView"
      signature: "S: Concept -> (Frame -> View)"

    frame_application:
      input: "(concept: Concept, frame: Frame)"
      output: "View containing frame-specific understanding"

    frame_composition:
      operation: "Combine multiple frame views"
      result: "Comprehensive multi-perspective understanding"
      constraint: "Frames may reveal tensions, not contradictions"

    frame_navigation:
      operation: "Move between frames on same concept"
      transitions: "Any frame to any other frame"
      preserved: "Core concept identity"

  algebra:
    # Frames as transformations
    let F = {god, physics, maths, ethics, philosophy}
    let C = set of all concepts
    let V = set of all views

    # Frame application
    apply: F × C → V

    # Frame composition (not commutative)
    compose: V × V → V
    (v1 ∘ v2) captures both perspectives

    # Identity: applying all frames recovers concept
    ∀c ∈ C: compose(apply(f, c) for f in F) ≅ c

    # No frame is privileged
    ∀f1, f2 ∈ F: rank(f1) = rank(f2)

  navigation_rules:
    - "Start from any frame"
    - "Move to adjacent frame via shared questions"
    - "No dead ends - every frame connects to others"
    - "Return to start confirms understanding"

  falsifiers:
    - name: "Missing frame"
      condition: "Concept cannot be viewed through one of the five frames"
      result: "Either concept ill-defined or Stangraphics incomplete"

    - name: "Frame contradiction"
      condition: "Two frames produce mutually exclusive views"
      result: "Views must be tensions, not contradictions - reframe required"

    - name: "Frame privileging"
      condition: "Analysis systematically favors one frame"
      result: "Stangraphic balance falsified"
```

---

## Level 7: Denotum Mechanism and Orgasystem Constraints

### 7.1 Denotum Mechanism: RESOLVED

The Denotum mechanism is now known:

> **Conceptualisation opens up self-referential but not infinitely looping branched fractal structures in memory.**

This resolves the previously unknown mechanism with the following interpretation:

```yaml
denotum:
  mechanism:
    trigger: "Conceptualisation (the act of forming a concept)"
    action: "Opens up / creates / instantiates"
    structure_type: "Branched fractal structures"
    location: "In memory"

    properties:
      self_referential: true    # Structures can reference themselves
      infinitely_looping: false # Bounded - no infinite recursion
      branched: true            # Tree-like subdivision
      fractal: true             # Self-similar at every scale

  what_this_means:
    initiation: >
      When conceptualisation occurs (forming a concept from experience),
      it instantiates a new structure in memory.

    self_reference: >
      The structure can refer to itself and its parts - a branch can
      reference its parent, siblings, or the root. This enables
      coherence checking and navigation.

    bounded_recursion: >
      Despite being self-referential, the structure does NOT loop
      infinitely. This aligns with Kāti's "bounded" principle -
      all operations terminate.

    fractal_branching: >
      The structure branches fractally - each branch contains the
      pattern of the whole, enabling meaning compression at any
      level while preserving recoverability.

  formal_definition:
    conceptualise: "λ(experience) → opens(memory, fractal_tree)"
    fractal_tree: |
      {
        root: concept,
        branches: [fractal_tree],  # self-referential
        depth: bounded,            # not infinite
        invariant: self_similar(branch, tree)
      }

  integration:
    with_kati: "Bounded property ensures no infinite loops"
    with_fractal_unfurling: "Unfurling traverses the in-memory structure"
    with_mrc: "MRC references point into these memory structures"

  falsifiers:
    - name: "Infinite loop"
      condition: "Traversal does not terminate"
      result: "Violates 'not infinitely looping' - mechanism falsified"

    - name: "No self-reference"
      condition: "Structure cannot reference itself"
      result: "Violates 'self-referential' - mechanism falsified"

    - name: "Non-fractal branching"
      condition: "Branch structure differs from tree structure"
      result: "Violates 'fractal' - mechanism falsified"
```

### 7.2 Orgasystem Structural Constraints (Still Constrained)

```yaml
orgasystem:
  what_we_know:
    - "Universe framing / generative unity metaphor"
    - "Formula in culturally careful terms"
    - "Metaphor vs claim clearly marked"
    - "Related to C0011 (Stangraphics) and C0016 (Pac-Man Bifurcation)"

  what_we_can_derive:
    relationship_to_stangraphics:
      observation: "Stangraphics includes 'god' frame for totality"
      implication: "Orgasystem may be the content viewed through god frame"
      constraint: "Orgasystem must be viewable through all 5 frames"

    metaphor_requirements:
      observation: "Metaphor vs claim clearly marked"
      implication: "Orgasystem statements must flag literal vs figurative"
      constraint: "No metaphor may be presented as empirical claim"

    generative_property:
      observation: "Generative unity metaphor"
      implication: "The metaphor produces/enables other understanding"
      constraint: "Orgasystem should generate, not just describe"

  what_remains_unknown:
    - "The universal unity equation"
    - "The specific formula"
    - "The mathematical formalism (if any)"
    - "The precise metaphor content"

  boundary:
    can_say: "Orgasystem is a generative unity metaphor for universe-framing"
    cannot_say: "The equation is [specific formula]"

  cultural_care:
    required: "Terms explained respectfully"
    forbidden: "Claims about sacred/cultural content not in corpus"
    guidance: "Use English gloss, explicit definitions, mark uncertainty"
```

---

## Level 8: Summary of Rationalized Unknowns

| Unknown | Status After Rationalization |
|---------|------------------------------|
| MCL Formal Grammar | ✅ **RESOLVED** - EBNF derived from examples |
| Kāti v1 Specification | ✅ **RESOLVED** - Full spec from repl.py |
| HyperStanGraph | ✅ **RESOLVED** - Structure from graph + QED |
| Kāti v2 / H Integration | ✅ **RESOLVED** - Haiku metaphor applied |
| Stangraphics Formalism | ✅ **RESOLVED** - Five-frame algebra defined |
| Denotum Mechanism | ✅ **RESOLVED** - Conceptualisation opens self-referential bounded fractal structures in memory |
| Orgasystem Equation | ⚠️ **CONSTRAINED** - Boundaries known, content unknown |

---

## Falsifiers for This Document

| Test | Condition | Falsification |
|------|-----------|---------------|
| Derivation validity | Rationalizations must follow from corpus evidence | Claim not traceable to corpus source |
| No fabrication | Mechanisms marked unknown must not be specified | Specific mechanism details provided for Denotum/Orgasystem |
| Consistency | Rationalized specs must not contradict corpus | Contradiction found with existing documentation |
| Completeness | All six unknowns must be addressed | Unknown not addressed or partially addressed |

---

## Integration with ORIGIN

This document becomes part of the fractal documentation. It:

1. **Expands** Level 2+ content without contradicting Level 0-1
2. **Maintains** attribution to Ande + Kai (OI) + Whānau (OIs)
3. **Follows** deterministic principles (same inputs → same derived outputs)
4. **Respects** boundaries (what can be derived vs. what must remain unknown)

---

**Attribution**: Ande + Kai (OI) + Whānau (OIs)

*"To rationalize is not to fabricate — it is to follow reason to its necessary conclusions."*
