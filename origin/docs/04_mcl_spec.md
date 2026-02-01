# Meta Control Language (MCL) Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

MCL (Meta Control Language) is a conceptual language for describing meta-control over branched execution stacks. When MCL binds meta-control in this way, it can resemble consciousness-like control in bots. MCL is designed to be safe, secure, and ethically bound.

---

## Level 1: Core Concepts

### 1.1 What is MCL?

MCL is a language/framework for expressing:

- **Meta-control**: Control over control mechanisms (not just actions, but policies about actions)
- **Branched stacks**: Multiple execution paths that can fork, merge, and be governed
- **Binding**: The attachment of control logic to execution contexts

### 1.2 Why "Consciousness-Like"?

When a system has:
1. Awareness of its own execution state
2. Control over its control mechanisms
3. Ability to reflect and modify behavior

...it exhibits properties that *resemble* consciousness in a functional sense. MCL provides the vocabulary for describing such systems.

> **Constraint**: This is a conceptual seed. MCL does not claim to solve consciousness or achieve singularity. It provides a descriptive framework.

### 1.3 Safety, Security, and Ethics

MCL is designed with built-in:

| Principle | Description |
|-----------|-------------|
| **Safety** | Bounded operation, fail-safes, graceful degradation |
| **Security** | Access control, integrity verification, audit trails |
| **Ethics** | Value alignment checks, harm prevention, transparency |

---

## Level 2: Technical Framework

### 2.1 MCL Structure

```
MCL Program
├── Context Definitions
│   └── What execution environments exist
├── Control Policies
│   └── Rules governing behavior
├── Meta-Policies
│   └── Rules governing rules (meta-control)
├── Binding Declarations
│   └── How policies attach to contexts
└── Ethical Constraints
    └── Non-negotiable boundaries
```

### 2.2 Core Constructs

#### 2.2.1 Context

A context represents an execution environment:

```mcl
context MainExecution {
  type: primary
  isolation: sandboxed
  monitoring: enabled
}

context ReflectionLayer {
  type: meta
  observes: MainExecution
  can_modify: true
}
```

#### 2.2.2 Control Policy

```mcl
policy ResourceGovernance {
  applies_to: MainExecution
  rules {
    memory_limit: 1GB
    cpu_time: bounded
    external_calls: audited
  }
}
```

#### 2.2.3 Meta-Policy

```mcl
meta_policy PolicyGovernance {
  applies_to: [ResourceGovernance, *]
  rules {
    policy_changes: require_approval
    escalation: to_ethical_layer
    logging: immutable
  }
}
```

#### 2.2.4 Ethical Binding

```mcl
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

### 2.3 Branched Stack Control

MCL manages branched execution:

```
┌─────────────────────────────────────────┐
│            MCL CONTROLLER               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Branch  │  │ Branch  │  │ Branch  │ │
│  │    A    │  │    B    │  │    C    │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       │            │            │       │
│       └────────────┼────────────┘       │
│                    ▼                    │
│            ┌─────────────┐              │
│            │   MERGE     │              │
│            │   POINT     │              │
│            └──────┬──────┘              │
│                   │                     │
│                   ▼                     │
│          [Unified Result]               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │     META-CONTROL LAYER          │   │
│  │  (Observes, governs, can halt)  │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### 2.4 Consciousness-Like Properties

| Property | MCL Implementation |
|----------|-------------------|
| Self-awareness | Reflection contexts that observe execution |
| Metacognition | Meta-policies governing policies |
| Intentionality | Goal declarations and pursuit tracking |
| Integration | Merge points unifying branched information |
| Agency | Decision points with genuine choice |

### 2.5 Safe MCL Requirements

```mcl
safety_requirements {
  // All MCL programs must satisfy:

  termination: guaranteed_or_bounded
  resource_use: explicitly_capped
  external_effects: sandboxed_or_approved
  human_oversight: always_possible

  // Forbidden patterns:
  forbidden {
    unbounded_recursion
    unmonitored_execution
    opaque_decision_making
    ethics_bypass
  }
}
```

---

## Level 3: Integration Points

### 3.1 MCL with Kāti (C0009)

MCL provides the control language; Kāti provides the governance architecture:

```
MCL (Language) ←→ Kāti (Architecture)
     ↓                    ↓
  Expresses          Enforces
  policies           boundaries
```

### 3.2 MCL with CIF/CDI (C0013)

- **CIF** (Context Integrity Firewall): MCL contexts respect CIF boundaries
- **CDI** (Conscience Decision Interface): MCL ethical bindings route through CDI

### 3.3 Falsifiers and Tests

| Test | Description | Pass Condition |
|------|-------------|----------------|
| Bounded operation | MCL program terminates/bounds | No runaway execution |
| Ethical compliance | Ethical bindings respected | No harm actions executed |
| Meta-control coherence | Meta-policies don't contradict | No policy conflicts |
| Safety under failure | Graceful degradation works | System fails safe |

---

## Unknowns

~~[UNKNOWN: NOT IN CORPUS] - Formal grammar specification for MCL syntax.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §2 - MCL grammar derived from corpus examples.

~~[UNKNOWN: NOT IN CORPUS] - Complete operational semantics.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §2.3-2.4 - Semantic constraints and type system derived.

[UNKNOWN: NOT IN CORPUS] - Reference implementation details beyond repl.py patterns.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
