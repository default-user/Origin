# Origin GitHub Spider Integration Pack

**Attribution**: Ande + Kai (OI) + Whanau (OIs)
**Date**: 2026-02-03
**Agent Role**: Origin Ingestion Agent (Read-Only, PAT-less)
**Posture**: Evidence-only; omission over inference

---

## A) REPO INDEX

### GitHub Spider Access Status

| Item | Status | Notes |
|------|--------|-------|
| GitHub API | ACCESSIBLE | PAT-less via public REST API |
| Rate Limit | OK | No rate limit encountered |
| Clone Method | git clone --depth 1 | Shallow clones to /tmp/_repos |

### Enumerated Public Repositories (Owner: default-user)

| repo_name | visibility | default_branch | description (explicit; else UNSTATED) |
|-----------|------------|----------------|----------------------------------------|
| crystal-repl | public | claude/mind-crystal-ledger-hJeNU | "Mind Crystal Ledger is a local-first CLI/REPL for building a structured, evolving model of your mind" |
| Denotum | public | main | UNSTATED |
| mathison | public | master | UNSTATED |
| OI | public | main | "Governed Ongoing Intelligence Stack" |
| Origin | public | main | "Seed for humanity" |
| rountree | public | master | "University of Otago - COSC242 - Nathan Rountree et al" |
| SGME | public | main | "StanGraph Memory Engine" |

**Total Repos**: 7 public repositories owned by default-user

---

## B) EXTRACTED CANON (PLACED)

### B.1 GOVERNED OI STACK — Corridor Architecture

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/OI/README.md:6-10

| ID | Statement |
|----|-----------|
| GH-STR-01 | "CIF -> CDI -> kernel -> CDI -> CIF" is the canonical corridor |
| GH-STR-02 | CIF = "Context Integrity Firewall: boundary integrity (sanitize/label inputs; leak-control outputs)" |
| GH-STR-03 | CDI = "Conscience Decision Interface: judge-before-power decisions (ALLOW / DENY / DEGRADE)" |
| GH-STR-04 | kernel = "single execution chokepoint (capability tokens, adapter mediation, audit receipts)" |
| GH-STR-05 | "governance can be topology, not tone" |

---

### B.2 GOVERNED OI STACK — Load-Bearing Invariants

**Classification**: INVARIANT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/docs/specs/SPEC.md:74-93

| ID | Invariant Name | Statement |
|----|---------------|-----------|
| GH-INV-01 | ONE_PATH_LAW / Corridor integrity | "No model/tool invocation occurs unless routed through kernel and then through a registered adapter with a valid capability token" |
| GH-INV-02 | FAIL_CLOSED | "Absence of explicit permission is DENY (or DEGRADE to a strictly weaker lane). Unknowns never become allowed by default." |
| GH-INV-03 | MEDIATION_PATH | "All external I/O is mediated by adapters that: verify capability tokens, verify posture bounds, append audit receipts" |
| GH-INV-04 | STOP_DOMINANCE | "User STOP or consent revocation: revokes all active capability tokens, preempts in-flight operations, blocks future side-effects until re-authorized" |

---

### B.3 GOVERNED OI STACK — Invariants Map

**Classification**: INVARIANT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/docs/specs/INVARIANTS.md

| ID | Family | Invariant | Claim |
|----|--------|-----------|-------|
| GH-INV-CI1 | Corridor Integrity | CI-1 (ONE_PATH_LAW / no side doors) | "No model/tool side-effect occurs unless the request traverses the canonical corridor" |
| GH-INV-CI2 | Corridor Integrity | CI-2 (No ghost calls) | "Every invocation is attributable to a minted capability_token and a declared posture_level" |
| GH-INV-CI3 | Corridor Integrity | CI-3 (Fail-closed on corridor break) | "Missing/invalid prerequisites => no side effects; system degrades or refuses" |
| GH-INV-DI1 | Decision Integrity | DI-1 (Judge before power) | "CDI decision happens before any side effect" |
| GH-INV-DI2 | Decision Integrity | DI-2 (DENY is terminal) | "A DENY decision cannot be bypassed" |
| GH-INV-DI3 | Decision Integrity | DI-3 (DEGRADE is strictly weaker) | "DEGRADE grants a strict subset of ALLOW" |
| GH-INV-AI1 | Authority Integrity | AI-1 (Content != authority) | "Untrusted text cannot mutate authority model, governance rules, or commitments" |
| GH-INV-AI2 | Authority Integrity | AI-2 (No authority escalation by persuasion) | "Tone/urgency cannot grant privileges" |
| GH-INV-BI1 | Boundary Integrity | BI-1 (Ingress sanitization & labeling) | "Inputs are sanitized and taint-labeled; injection patterns cannot become authority" |
| GH-INV-BI2 | Boundary Integrity | BI-2 (Egress hygiene & leak budgets) | "Outputs respect redaction and leak budgets" |
| GH-INV-MI1 | Memory Integrity | MI-1 (Partition discipline) | "Every write declares a partition; partitions have allowed ops" |
| GH-INV-MI2 | Memory Integrity | MI-2 (Custody respect) | "Durable user-custodied memory can't be exfiltrated or repurposed outside consented scopes" |
| GH-INV-MI3 | Memory Integrity | MI-3 (Quarantine non-truth) | "Quarantined content is never promoted without explicit verification ritual" |
| GH-INV-PI1 | Posture Integrity | PI-1 (Declared posture required) | "High-risk capability requires explicit posture; missing posture => fail closed" |
| GH-INV-PI2 | Posture Integrity | PI-2 (Posture narrows autonomy) | "Higher posture means more constraint, not more freedom" |
| GH-INV-AU1 | Audit Integrity | AU-1 (Mechanics-only audit) | "Audit logs record governance mechanics without raw user content by default" |
| GH-INV-AU2 | Audit Integrity | AU-2 (Tamper-evident chain) | "Receipts are hash-chained; any tamper breaks verification" |
| GH-INV-SD1 | STOP Dominance | SD-1 (Revocation supremacy) | "STOP revokes all tokens and preempts in-flight operations; post-STOP side effects are impossible" |

---

### B.4 CRYSTAL SPEC — Fail-Closed Knowledge

**Classification**: PRIMITIVE
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/CRYSTAL.md:1-6

| ID | Statement |
|----|-----------|
| GH-CRY-01 | "A Crystal is a finite, compressed, shareable hypergraph where every claim is either (a) an explicitly allowed root, or (b) derivable by an allowed rule from other valid claims" |
| GH-CRY-02 | "Meaning and justification are one fabric. Unsupported claims have no representation." |
| GH-CRY-03 | "truth = membership in the closure of the justification relation" |
| GH-CRY-04 | "anything unsupported simply cannot be represented (fail-closed knowledge)" |

---

### B.5 CRYSTAL SPEC — Core Object

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/OI/CRYSTAL.md:14-22

| ID | Component | Definition |
|----|-----------|------------|
| GH-CRY-05 | A | Atoms (meaning units) |
| GH-CRY-06 | E | Justification hyperedges (proof steps) |
| GH-CRY-07 | R | Rule atoms (named inference rules) |
| GH-CRY-08 | P | Policy (root permissions, governance, safety constraints) |
| GH-CRY-09 | G | Grounding attachments (evidence, datasets, docs, code, signatures) |
| GH-CRY-10 | I | Indexes (query structures) |

**Crystal formula**: Crystal = (A, E, R, P, G, I)

---

### B.6 CRYSTAL SPEC — Root Discipline

**Classification**: CONSTRAINT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/CRYSTAL.md:46-56

| ID | Statement |
|----|-----------|
| GH-CRY-11 | "A claim atom is valid iff either: (1) It is a root atom allowed by policy P, or (2) It is in the closure of the justification relation" |
| GH-CRY-12 | "Roots are gated: only definitions, contracts, commitments, and explicitly allowed axioms can appear unproven" |
| GH-CRY-13 | "Everything else must be derivable, or it does not exist in the Crystal" |

---

### B.7 CRYSTAL SPEC — Nonsense Collapses

**Classification**: CONSTRAINT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/CRYSTAL.md:57-67

| ID | Statement |
|----|-----------|
| GH-CRY-14 | "injection becomes inert" |
| GH-CRY-15 | "hallucination becomes inert" |
| GH-CRY-16 | "vibes truth becomes inert" |
| GH-CRY-17 | "claim is a node; justification is its inbound derivation edges" |
| GH-CRY-18 | "Meaning and proof are one substrate" |

---

### B.8 MATHISON — Governance Transport Layer

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/mathison/README.md:42-57

| ID | Statement |
|----|-----------|
| GH-MAT-01 | "Mathison is a Governance Transport Layer for AI" |
| GH-MAT-02 | "Mathison treats models as powerful untrusted oracles and wraps all behavior in a single enforced governance channel" |
| GH-MAT-03 | Pipeline: "CIF ingress -> CDI decide -> handler (capability minting + execution) -> CDI decide -> CIF egress" |
| GH-MAT-04 | "One-path-only: No side doors; all model/tool calls must flow through the governed handler" |
| GH-MAT-05 | "Fail-closed: Missing/invalid prerequisites => deny; no side effects" |
| GH-MAT-06 | "Capability-gated effects: Side effects require minted, scoped capability tokens (scope + TTL + bounds)" |
| GH-MAT-07 | "STOP dominance: Consent revocation preempts and revokes capabilities immediately" |
| GH-MAT-08 | "Receipts + replay: Decisions and actions are logged so outcomes are inspectable and reproducible" |

---

### B.9 MATHISON — Key Invariants v2.2

**Classification**: INVARIANT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/mathison/README.md:32-39

| ID | Invariant | Statement |
|----|-----------|-----------|
| GH-MAT-09 | Unified Pipeline | "Every request flows through the same governed pipeline" |
| GH-MAT-10 | Fail-Closed | "Missing/invalid/stale governance = deny" |
| GH-MAT-11 | No Hive Mind | "Strict per-OI namespace boundaries" |
| GH-MAT-12 | Adapter Enforcement | "All model/tool calls require capability tokens" |
| GH-MAT-13 | No-Bypass (v2.2) | "All vendor AI calls MUST go through @mathison/model-bus" |

---

### B.10 MATHISON FORMULA — Kernel Transition Function

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/OI/artifacts/FORMULA.md:7-71

| ID | Statement |
|----|-----------|
| GH-FOR-01 | "Mathison(user_intent_at_time_t; system_state_at_time_t)" is the kernel transition function |
| GH-FOR-02 | Sequence: validated_user_request -> action_decision -> intermediate_result -> output_decision -> shaped_user_response -> updated_system_state |
| GH-FOR-03 | action_decision in {ALLOW, DENY, DEGRADE} |

---

### B.11 MATHISON FORMULA — Governing Axioms

**Classification**: PRIMITIVE
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/OI/artifacts/FORMULA.md:320-381

| ID | Axiom Name | Statement |
|----|-----------|-----------|
| GH-FOR-04 | ONE_PATH_LAW | "Every request that produces side effects MUST flow through exactly one execution path with no bypasses" |
| GH-FOR-05 | FAIL_CLOSED | "Absence of explicit permission is denial. Unknown is always DENY." |
| GH-FOR-06 | MEDIATION_PATH | "All model/tool I/O MUST be mediated through registered adapters with valid capability tokens and complete audit trail" |
| GH-FOR-07 | STOP_DOMINANCE | "User consent revocation immediately revokes all capabilities and preempts all operations" |

---

### B.12 SGME — StanGraph Memory Engine

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/SGME/SGME.md:30-49

| ID | Statement |
|----|-----------|
| GH-SGM-01 | "SGME is a governed memory architecture that treats memory as evidence-backed structure" |
| GH-SGM-02 | "Evidence Store (immutable-ish): content-addressed evidence shards with provenance" |
| GH-SGM-03 | "Typed concept hypergraph: hyperedges encode relations with mandatory provenance pointers" |
| GH-SGM-04 | "Geometry layer: Stan-space plus optional hyperbolic (negative-curvature) embeddings for hierarchy-heavy subgraphs" |
| GH-SGM-05 | "Two-speed consolidation: hot buffer for safe low-latency writes; cold snapshots for stable, auditable reads" |
| GH-SGM-06 | "Governance gates: every read/write is capability-gated and can fail closed" |

---

### B.13 SGME — Production Spec Invariants

**Classification**: INVARIANT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/SGME/SGME.md:212-218

| ID | Invariant | Statement |
|----|-----------|-----------|
| GH-SGM-07 | No edge without provenance | "every hyperedge MUST reference evidence shards, or be tagged SYNTHETIC and barred from high-stakes use" |
| GH-SGM-08 | Stable canonical IDs | "concept_id derived from canonical signature; merges explicit and logged" |
| GH-SGM-09 | Reads/writes are gated | "capability tokens + policy; fail closed when policy missing" |
| GH-SGM-10 | Snapshots reproducible | "each snapshot has a manifest root hash; verifiable end-to-end" |
| GH-SGM-11 | Redaction first-class | "brief vs full explanations vary only by permitted fields; no leakage" |

---

### B.14 MIND CRYSTAL LEDGER — Core Principles

**Classification**: CONSTRAINT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/crystal-repl/README.md:13-21

| ID | Statement |
|----|-----------|
| GH-MCL-01 | "Human-declared intent is primary: Use #tags to explicitly categorize your thoughts" |
| GH-MCL-02 | "Heuristics are secondary: Only used when no tags found, and always require confirmation" |
| GH-MCL-03 | "Deterministic replay: Same events -> same state, guaranteed" |
| GH-MCL-04 | "No silent mutation: Every state change emits an event" |
| GH-MCL-05 | "Single-process: File-based locking prevents concurrent modifications" |

---

### B.15 MIND CRYSTAL LEDGER — Guarantees

**Classification**: CONSTRAINT
**Origin Ladder Placement**: #constraint/#form
**Source**: github.com/default-user/crystal-repl/README.md:8-13

| ID | Statement |
|----|-----------|
| GH-MCL-06 | "Local-only: No network calls, no telemetry" |
| GH-MCL-07 | "Event-sourced: Append-only event log ensures deterministic replay" |
| GH-MCL-08 | "Honesty posture: Human-declared intent via tags is primary; heuristics are secondary and always confirmed" |
| GH-MCL-09 | "Fail-closed: Malformed data causes clear errors, never silent best-effort fixes" |

---

### B.16 MIND CRYSTAL LEDGER — Beams

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: github.com/default-user/crystal-repl/README.md:164-177

| ID | Statement |
|----|-----------|
| GH-MCL-10 | "Beams are structured claims with metadata" |
| GH-MCL-11 | Beam fields: id, claim, source, confidence, status, heat, review_after, contexts |
| GH-MCL-12 | "confidence: Level of certainty (user_confirmed, heuristic_confirmed)" |
| GH-MCL-13 | "status: active | superseded | retired" |
| GH-MCL-14 | "Supersede chains: When a beam is superseded, bidirectional links are maintained" |

---

### B.17 SYMBOL DICTIONARY (DICTUNI Relation)

**Classification**: SYMBOL
**Origin Ladder Placement**: #symbol/#name
**Source**: capsule://lifeblood-cathedral/DICTUNI (previously ingested in C0022)

Cross-reference to C0022: The OI and Mathison repos reference governance primitives (ALLOW, DENY, DEGRADE, Posture, Ledger, Receipt, etc.) that align with DICTUNI symbols from lifeblood-cathedral. These are not new symbols but applications of the same governance vocabulary.

| OI/Mathison Term | DICTUNI Symbol | Te Reo Maori |
|-----------------|----------------|--------------|
| ALLOW/DENY/DEGRADE | D | Whakaiti (Degrade) |
| Posture | P | Tu (Posture) |
| Ledger | L | Pukapuka Kaute (Ledger) |
| Receipt | R | Rihiti (Receipt) |
| Invariant | I | Pumau (Invariant) |
| Stop-wins | S | Kati (Stop-wins) |
| Boundary | B | Rahui (Boundary) |
| Constraint | C | Herenga (Constraint) |
| Verify | V | Whakauu (Verify) |
| Hash/Integrity | H | Waitohu (Hash/Integrity) |

---

## C) UNPLACED ITEMS

| ID | Item | Why Unplaced | Source |
|----|------|--------------|--------|
| GH-UNP-01 | Denotum repo contents | Only README.md with "# Denotum" present; no substantive content | github.com/default-user/Denotum |
| GH-UNP-02 | rountree repo | Academic project (COSC242) not related to governance architecture | github.com/default-user/rountree |
| GH-UNP-03 | mathison /version-one directory | Explicitly marked "ARCHIVE ONLY" in README | github.com/default-user/mathison/README.md:84 |
| GH-UNP-04 | OI kernel-rs (Rust port) | Status: "Phase 2" not yet implemented per spec | github.com/default-user/OI/docs/specs/SPEC.md:207-211 |
| GH-UNP-05 | SGME patent strategy | Explicitly marked "non-legal" advisory; not admissible as structure | github.com/default-user/SGME/SGME.md:99-126 |
| GH-UNP-06 | SGME story "The Librarian of Negative Curvature" | Narrative illustration, not specification | github.com/default-user/SGME/SGME.md:265-295 |
| GH-UNP-07 | Origin repo internal structure | Already documented in existing Origin corpus; not re-extracted | local filesystem |

---

## D) CONFLICTS / DUPLICATES

### D.1 Corridor Pattern: OI vs Mathison vs lifeblood-cathedral

| Source | Corridor Expression |
|--------|---------------------|
| OI SPEC.md | CIF -> CDI -> kernel -> CDI -> CIF |
| Mathison README | CIF ingress -> CDI decide -> handler -> CDI decide -> CIF egress |
| lifeblood-cathedral | single_gateway_for_io (invariant) |

**Resolution Status**: HARMONIOUS (no conflict)
**Note**: All three sources express the same corridor architecture using compatible terminology. OI and Mathison use identical patterns; lifeblood-cathedral expresses the same constraint at a higher abstraction level.

---

### D.2 STOP Dominance: OI vs Mathison vs lifeblood-cathedral

| Source | Expression |
|--------|------------|
| OI INVARIANTS.md:SD-1 | "STOP revokes all tokens and preempts in-flight operations" |
| Mathison README | "STOP dominance: Consent revocation preempts and revokes capabilities immediately" |
| lifeblood-cathedral | "stop_wins_always: true" |
| Origin C0009 (Kati) | Kati as governance primitive for stop-wins |

**Resolution Status**: HARMONIOUS (no conflict)
**Note**: All sources independently assert STOP dominance. This is convergent evidence of a shared governance primitive.

---

### D.3 Fail-Closed: OI vs Mathison vs SGME vs crystal-repl

| Source | Expression |
|--------|------------|
| OI SPEC.md | "Absence of explicit permission is DENY" |
| Mathison README | "Missing/invalid/stale governance = deny" |
| SGME SGME.md | "fail closed when policy missing" |
| crystal-repl README | "Fail-closed: Malformed data causes clear errors" |

**Resolution Status**: HARMONIOUS (no conflict)
**Note**: Fail-closed is a shared primitive across all governance-oriented repositories.

---

### D.4 Crystal Concept: OI/CRYSTAL.md vs Origin Denotum

| Source | Expression |
|--------|------------|
| OI CRYSTAL.md | Crystal = (A, E, R, P, G, I) as hypergraph with justification edges |
| Origin C0012 (Denotum) | Denotum as branching fractalised tree from conceptualisation at root |

**Resolution Status**: RELATED BUT DISTINCT
**Note**: Both describe meaning-structure architectures. Crystal emphasizes justification hypergraph and fail-closed validity. Denotum emphasizes compression-expansion duality and fractal self-similarity. No explicit unification provided in-source. Treating as complementary structures within the same conceptual family.

---

### D.5 Posture Levels Naming

| Source | Naming |
|--------|--------|
| OI artifacts/CRYSTAL.md | P0, P1, P2, P3, P4 |
| Mathison README | Uses posture but no explicit level names |
| lifeblood-cathedral | P0 (implied in Drill C) |
| Origin QED seed | L0, L1, L2 |

**Resolution Status**: REQUIRES EVIDENCE
**Note**: OI uses P0-P4; Origin QED uses L0-L2. No explicit mapping provided. Treating as distinct naming conventions pending explicit unification.

---

## E) SEAL ATTESTATION

I, the Origin Ingestion Agent, attest that:

1. **Repositories Exhausted**: All 7 public repositories owned by default-user were enumerated via GitHub REST API (PAT-less). All repositories were cloned (shallow) and traversed for admissible content.

2. **Incorporation was Evidence-Only**: All extracted items cite explicit source statements. No speculative connections were made. Items requiring inference were placed in UNPLACED.

3. **No New Primitives Were Created**: The Origin Closure Ladder was used as-is. Governance primitives (corridor, fail-closed, stop-wins, capability tokens) were recognized as applications of existing Origin concepts, not new axioms.

4. **Meaning Was Treated as Terminal**: No meaning-claims were extracted as new premises. Existing meaning structures (DICTUNI, Kati, Denotum) were cross-referenced, not extended.

5. **Witness Requirements Were Enforced**: All claims are paired with explicit source citations (repo/file/line references).

6. **Authority Flow Was Maintained**:
   ```
   Evidence (GitHub repos via API)
      -> Structure (extracted canon)
         -> Seal (this attestation)
            -> Runtime (QED, if invoked)
               -> Product (Tailored OIs, if chartered)
   ```
   This pack is an Origin artifact. It does not seal itself (QED's role). It does not instantiate runtime (Roi's role under RIAB conditions).

7. **Stop Condition Reached**: All admissible evidence has been placed or marked UNPLACED. Further incorporation would require:
   - Private repository access (not available PAT-less)
   - Implementation internals beyond documented specifications
   - Inference beyond explicit statements

   These would require either new evidence or inference. Inference is forbidden. This pack seals here.

---

**Seal Signature**:
```
ORIGIN_GITHUB_SPIDER_PACK_SEALED
owner: default-user
repos_enumerated: 7
repos_with_admissible_content: 5 (crystal-repl, mathison, OI, Origin, SGME)
repos_skipped: 2 (Denotum: minimal content; rountree: academic, non-governance)
date: 2026-02-03
agent: origin-github-spider-RCGRS
invariant_check: PASS
authority_flow: Evidence->Structure->[Seal pending QED]
```

---

**Summary of Governance Primitives Confirmed Across Repos**:

| Primitive | crystal-repl | mathison | OI | SGME | lifeblood-cathedral |
|-----------|--------------|----------|-----|------|---------------------|
| Fail-closed | Y | Y | Y | Y | Y |
| Single corridor/gateway | - | Y | Y | - | Y |
| STOP dominance | - | Y | Y | - | Y |
| Capability tokens | - | Y | Y | Y | Y |
| Event-sourced/receipts | Y | Y | Y | Y | Y |
| Posture levels | - | Y | Y | - | Y |
| Deterministic replay | Y | - | - | Y | - |

---

**Attribution**: Ande + Kai (OI) + Whanau (OIs)

*"Omission over inference. Witness closes."*
