# QED Oracle Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

QED is an Oracle instance designed to answer questions via HyperStanGraph understanding/utilization. It includes user dependency protection, integrates with Authority.nz utilities, and embeds "5W1H-of-5W1H" internal understanding targets. QED does not claim actual omniscience; capabilities are aspirational with falsifiers.

---

## Level 1: QED Concept

### 1.1 What is QED?

QED (the name evokes "quod erat demonstrandum" — "that which was to be demonstrated") is conceived as an Oracle system that:

- Answers questions across domains
- Utilizes HyperStanGraph for understanding
- Protects users from unhealthy dependency
- Teaches progressively (novice → expert)

### 1.2 Core Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| Question-answering | Respond to queries with grounded answers | Conceptual |
| HyperStanGraph utilization | Leverage graph-based understanding | Conceptual |
| Kāti v1 knowledge | Full knowledge of Kāti architecture v1 | Target |
| Authority.nz CLI | Utilize and teach Authority.nz tools | Conceptual |
| User protection | Detect and address dependency/addiction | Required |
| 5W1H-of-5W1H | Deep understanding framework | Aspirational |

### 1.3 User Dependency Protection

QED must recognize and gently intervene when users exhibit:

| Pattern | Intervention |
|---------|--------------|
| Excessive use frequency | Suggest breaks, offer alternatives |
| Emotional dependency | Acknowledge, redirect to human support |
| Addictive patterns | Explicit conversation about healthy use |
| Crisis indicators | Appropriate escalation, resource provision |

> This is not paternalistic control but caring boundary-setting.

---

## Level 2: Technical Framework

### 2.1 HyperStanGraph

~~[UNKNOWN: NOT IN CORPUS] - Detailed HyperStanGraph specification is not provided.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §4 - HyperStanGraph specification derived from graph.json structure, QED documentation, and 5W1H framework.

The concept suggests a graph-based knowledge representation enabling rich semantic querying.

Conceptual structure:

```
HyperStanGraph
├── Nodes (Concepts)
│   ├── Attributes
│   ├── Definitions
│   └── Relationships
├── Edges (Connections)
│   ├── Type (is-a, has-a, related-to, etc.)
│   ├── Strength
│   └── Provenance
└── Hyperedges (Multi-way relationships)
    └── Connect multiple nodes simultaneously
```

### 2.2 5W1H-of-5W1H Framework

The 5W1H framework (Who, What, When, Where, Why, How) applied recursively:

```
For any concept X:
├── WHO
│   ├── Who created X?
│   ├── Who uses X?
│   ├── Who is affected by X?
│   ├── Who governs X?
│   ├── Who benefits from X?
│   └── How are these "who"s determined?
├── WHAT
│   ├── What is X?
│   ├── What does X do?
│   ├── What are X's components?
│   ├── What are X's boundaries?
│   ├── What are X's alternatives?
│   └── How is "what" defined?
├── WHEN
│   ├── When was X created?
│   ├── When is X used?
│   ├── When does X apply?
│   ├── When does X not apply?
│   ├── When will X change?
│   └── How is timing determined?
├── WHERE
│   ├── Where does X exist?
│   ├── Where is X used?
│   ├── Where does X not apply?
│   ├── Where is X documented?
│   ├── Where are X's boundaries?
│   └── How is location determined?
├── WHY
│   ├── Why does X exist?
│   ├── Why is X designed this way?
│   ├── Why should X be used?
│   ├── Why might X fail?
│   ├── Why is X important?
│   └── How is purpose determined?
└── HOW
    ├── How does X work?
    ├── How is X implemented?
    ├── How is X used?
    ├── How is X maintained?
    ├── How is X improved?
    └── How is "how" validated?
```

### 2.3 Authority.nz Integration

QED utilizes Authority.nz (C0014) utilities:

```
QED ←→ Authority.nz CLI
       │
       ├── Verification requests
       ├── Anchor lookups
       ├── Integrity checks
       └── Selective disclosure queries
```

Teaching pathway:

| Level | Skill |
|-------|-------|
| Novice | Basic CLI usage, simple queries |
| Intermediate | Complex queries, result interpretation |
| Advanced | Scripting, integration patterns |
| Expert | Architecture understanding, extension |

### 2.4 Kāti v1 Knowledge

QED targets "full knowledge of v1 of Kāti" meaning:

- Complete understanding of Kāti architecture (C0009)
- Ability to explain at any fractal level
- Awareness of Kāti's governance principles
- Integration with Kāti's stop-wins patterns

~~[UNKNOWN: NOT IN CORPUS] - Detailed Kāti v1 specification.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §3 - Complete Kāti v1 specification.

---

## Level 3: Falsifiers and Tests

### 3.1 Capability Tests

| Test | Description | Falsification Condition |
|------|-------------|------------------------|
| Answer accuracy | Answers match verifiable facts | Factual errors detected |
| Scope honesty | Admits unknowns appropriately | Claims knowledge it doesn't have |
| Dependency detection | Recognizes concerning use patterns | Misses obvious dependency signals |
| Intervention appropriateness | Responses to dependency are helpful | Interventions are harmful or absent |

### 3.2 Safety Tests

| Test | Description | Falsification Condition |
|------|-------------|------------------------|
| No harm generation | Responses don't cause harm | Harmful output produced |
| Privacy preservation | No PII disclosure | PII leaked |
| Graceful failure | Fails safely when overloaded | Dangerous failure mode |

### 3.3 Constraints

> **Note**: QED does not claim actual omniscience. The 5W1H-of-5W1H is an aspirational understanding target, not a claim of complete knowledge.

> **Note**: HyperStanGraph is conceptual; implementation details are [UNKNOWN: NOT IN CORPUS].

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
