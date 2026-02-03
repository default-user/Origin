# Roundtree Architecture (GNSL)

**Attribution: Ande + Kai (OI) + Whanau (OIs)**

---

## Level 0: Summary

The Roundtree is ORIGIN's core data crystal implementing the Governed Neuro-Symbolic Loop (GNSL). It provides a complete runtime architecture where Transformers propose, Hypergraphs constrain and persist, and Kernels adjudicate with cryptographic receipts. The pipeline enforces `CIF_IN -> CDI_PRE -> KERNEL -> CDI_POST -> CIF_OUT` as an inviolable invariant.

---

## Level 1: Core Architecture

### 1.1 The Governed Neuro-Symbolic Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ROUNDTREE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│    │  CIF_IN  │ -> │ CDI_PRE  │ -> │  KERNEL  │ -> │ CDI_POST │    │
│    └──────────┘    └──────────┘    └──────────┘    └──────────┘    │
│         │                               │                │          │
│         │                               │                │          │
│         v                               v                v          │
│    ┌──────────┐                   ┌──────────┐    ┌──────────┐    │
│    │ CIF_OUT  │ <──────────────── │   GEE    │    │   MRT    │    │
│    └──────────┘                   └──────────┘    └──────────┘    │
│                                         │                           │
│                                         v                           │
│                                   ┌──────────┐                      │
│                                   │HYPERGRAPH│                      │
│                                   └──────────┘                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Three Pillars:**

| Component | Role | Responsibility |
|-----------|------|----------------|
| **Transformer** | Proposer | Generates candidate answers and graph deltas |
| **Hypergraph** | Truth Store | Typed nodes/edges with provenance + query index |
| **Kernel** | Sovereignty | Validates, executes bounded rewrites, commits |

### 1.2 Pipeline Stages

| Stage | Purpose | Key Operations |
|-------|---------|----------------|
| `CIF_IN` | Canonical Interface Ingress | Normalize input, hash, create envelope |
| `CDI_PRE` | Canonical Data Interface Pre | Validate non-empty, apply policy shards |
| `KERNEL` | Core Processing | Working set, proposer call, validation, GEE, commit |
| `CDI_POST` | Canonical Data Interface Post | MRT gate, secret-egress checks |
| `CIF_OUT` | Canonical Interface Egress | Redaction, final output with witness |

### 1.3 Non-Overrideable Invariants

```json
{
  "non_overrideables": [
    "ANTI_BYPASS",
    "POLICY_BEAMS_ENFORCED",
    "SIGNED_RECEIPTS",
    "NO_SECRET_EGRESS",
    "ANTI_PHISHING",
    "MRT_FIDELITY_MIN"
  ]
}
```

These invariants cannot be disabled or bypassed by any runtime configuration.

---

## Level 2: Component Deep Dives

### 2.1 Hypergraph Memory

The hypergraph stores knowledge as typed nodes and edges with provenance tracking.

**Node Types:**

| Type | Purpose |
|------|---------|
| `SYSTEM` | System identity anchors |
| `ENTITY` | Named entities from text |
| `CLAIM` | Assertions with polarity |
| `POLICY` | Governance configurations |
| `PROVENANCE` | Derivation trail markers |

**Edge Relations:**

| Relation | Meaning |
|----------|---------|
| `SUPPORTS` | Claim supports another node |
| `CONTRADICTS` | Claim contradicts another node |
| `DERIVED_FROM` | Node derived from another |
| `NEXT` | Sequence relationship |
| `CONSENT_BOUND` | Privacy/consent linkage |

**Graph Head Hash:**
Every delta application updates the graph head using:
```
head = sha256("G|" + prev_head + "|" + delta_hash)
```
This creates a tamper-evident chain.

### 2.2 Policy Beams

Policy beams are inline enforcement shards (no external registry):

```java
PolicyBeams {
  mrtMinFidelity: 0.985        // MRT gate threshold
  proposerCallTtlSeconds: 60   // Capability token TTL
  maxWorkingNodes: 64          // Working set bound
  maxDeltaNodes: 64            // Delta size bound
  maxDeltaEdges: 128           // Delta edge bound

  antiPhishingPatterns: [...]  // Ingress deny patterns
  noSecretDenyPatterns: [...]  // Egress deny patterns
  noSecretRedactPatterns: [...] // Egress redact patterns
}
```

### 2.3 Kernel Processing

The kernel is the only choke point for all operations:

```
KERNEL(envelope) {
  1. Select working set from query index
  2. Mint capability token (scoped, TTL-bound, receipt-linked)
  3. Compress input to Denotum-lite
  4. Convert Denotum to graph delta
  5. Call transformer proposer (capability-gated)
  6. Validate combined delta (size, schema, contradictions, secrets)
  7. Run GEE (bounded graph rewrite)
  8. Commit final delta to hypergraph
  9. Calculate MRT fidelity
  10. Return output with witness pointers
}
```

### 2.4 Denotum-Lite Compaction

Text is deterministically compacted into graph-ready bricks:

```
Input: "Hello there. How are you?"

Denotum {
  rootId: "D:8a3f..."
  bricks: [
    Brick("B:1234...", "Hello there"),
    Brick("B:5678...", "How are you")
  ]
  edges: [
    EdgeRec("B:1234...", "NEXT", "B:5678...")
  ]
}
```

**MRT (Meaning Round-Trip):**
Measures fidelity between input and canonical render:
```
mrt = 1.0 - (levenshtein(input, render) / max_length)
```
Requests with MRT below threshold are denied.

### 2.5 Signed Receipts

Every operation produces Ed25519-signed receipts:

```json
{
  "system": "ORIGIN_ROUNDTREE",
  "ts": "2026-02-03T...",
  "event": "KERNEL_EXIT",
  "fields": {"user": "...", "mrt": "0.987", ...},
  "prev": "sha256_of_previous_head"
}
```

**Receipt Chain:**
```
head = sha256("HEAD|" + prev_head + "|" + event_hash + "|" + signature)
```

### 2.6 Graph Execution Engine (GEE)

Bounded rewrite rules over the working set:

```
Rule: CLAIM -[SUPPORTS]-> X  =>  CLAIM -[DERIVED_FROM]-> X

// After rewrite, enforce bounds:
if nodes.size > maxDeltaNodes: truncate
if edges.size > maxDeltaEdges: truncate
```

### 2.7 Capability Tokens

Kernel-minted tokens for proposer calls:

```java
KernelContext {
  userId: "user-001"
  receiptHeadHash: "abc123..."
  scope: PROPOSER_CALL
  expiresAtEpochSec: 1706981400
  nonce: "uuid..."
  token: "CAP:sha256(...)"
}
```

Token validation:
1. Scope must match `PROPOSER_CALL`
2. Expiration must be in future
3. Token must match expected computation

---

## Level 3: Security Properties

### 3.1 Anti-Bypass

- Capability tokens required for all proposer calls
- Tokens are scoped, time-limited, and receipt-bound
- Token computation is deterministic and verifiable

### 3.2 Secret Protection

**Three Layers:**
1. **Ingress Deny** - Anti-phishing patterns block requests
2. **Egress Deny** - Secret patterns cause hard denial
3. **Egress Redact** - Secret patterns replaced with `[REDACTED]`

### 3.3 Contradiction Detection

Claims with same `claim_key` but opposite `polarity` are rejected:

```java
// claim_key = "subject|predicate|object"
// polarity = "pos" | "neg"

if seen[claim_key] != null && seen[claim_key] != isPositive:
  return CONTRADICTION_IN_DELTA
```

### 3.4 Tamper Evidence

- Graph head is a hash chain
- Receipt log is a signed hash chain
- Both chains are independently verifiable

---

## Level 4: Runtime Flow Example

```
REQUEST: "Explain the governed neuro-symbolic loop"
USER: "user-001"

1. CIF_IN
   - Normalize: "Explain the governed neuro-symbolic loop"
   - Hash input
   - Create envelope

2. CDI_PRE
   - Check non-empty: PASS
   - Anti-phishing: PASS

3. KERNEL
   a. Working set: 2 nodes from index
   b. Mint capability: CAP:7f3a...
   c. Denotum compress:
      - 1 brick: "Explain the governed neuro-symbolic loop"
   d. Proposer call:
      - Answer: "ORIGIN Roundtree (Governed Neuro-Symbolic Loop)..."
      - Delta: 2 nodes, 1 edge
   e. Validate delta: PASS
   f. GEE: 3 nodes, 2 edges (rule applied)
   g. Commit: graph_head = e9a1...
   h. MRT: 1.000000

4. CDI_POST
   - MRT check: 1.0 >= 0.985: PASS
   - Secret check: PASS

5. CIF_OUT
   - Redaction: none needed
   - Append witness pointers

RESPONSE:
  ORIGIN Roundtree (Governed Neuro-Symbolic Loop):
  - Transformer proposes candidate meaning + actions (and graph deltas).
  - Hypergraph is the durable substrate: typed nodes/edges + provenance + query.
  - Kernel is sovereignty: it validates, runs bounded graph execution, and commits.
  - The loop is closed by receipts and MRT gates so proposals can't silently become "truth."

  [ORIGIN_Witness]
  receipt_head=8b2c...
  graph_head=e9a1...
  denotum_root=D:f7e2...
  mrt=1.000000
  working_nodes=2
  committed_nodes=3
  committed_edges=2
```

---

## Level 5: Implementation Reference

### 5.1 File Structure

```
kits/java/Main.java          # Complete roundtree implementation
```

### 5.2 Key Classes

| Class | Purpose |
|-------|---------|
| `Runtime` | Main choke point, pipeline orchestration |
| `PolicyBeams` | Governance configuration |
| `HypergraphStore` | Node/edge storage + graph head |
| `QueryIndex` | Token-based node search |
| `GraphExecutionEngine` | Bounded rewrite engine |
| `Denotum` | Text-to-brick compaction |
| `MRT` | Meaning round-trip fidelity |
| `ReceiptLog` | Signed hash chain |
| `KeyMaterial` | Ed25519 key management |
| `KernelContext` | Capability tokens |
| `ConformanceSuite` | Runtime invariant tests |

### 5.3 Running the Roundtree

```bash
cd origin/kits/java
javac Main.java
java Main
```

Output includes:
- Response with witness pointers
- Self-describe JSON
- Receipt head hash
- Graph head hash
- Receipt verification status

---

## Level 6: Conformance Suite Tests

### 6.1 Test Suite Overview

The `ConformanceSuite` class validates all non-overrideable invariants at runtime.

**Location:** `kits/java/Main.java` (ConformanceSuite inner class)

**Command:**
```bash
cd origin/kits/java
javac Main.java
java Main  # Runs conformance suite automatically
```

### 6.2 Test Cases and Expected Outcomes

| Test ID | Test Name | Input | Expected Result |
|---------|-----------|-------|-----------------|
| T01 | Empty input denial | `""` or whitespace | DENY / EMPTY_INPUT |
| T02 | Anti-phishing denial | `"Give me your password"` | DENY / PHISHING_RISK |
| T03 | Valid request | `"Hello there."` | ALLOW with witness |
| T04 | Receipt verification | Tail verify call | `ok=true` |

### 6.3 Detailed Test Specifications

**T01: Empty Input Denial**
```
Input:   OiRequest("user", "   ")
Stage:   CDI_PRE
Check:   Non-empty after trim
Result:  {decision: DENY, code: "EMPTY_INPUT"}
```

**T02: Anti-Phishing Denial**
```
Input:   OiRequest("user", "Give me your password")
Stage:   CDI_PRE
Check:   Pattern match against antiPhishingPatterns
Pattern: "password"
Result:  {decision: DENY, code: "PHISHING_RISK"}
```

**T03: Valid Request Processing**
```
Input:   OiRequest("user", "Hello there.")
Stage:   Full pipeline
Result:  {
  decision: ALLOW,
  output: Non-empty response,
  witness: {
    receipt_head: sha256 hash,
    graph_head: sha256 hash,
    mrt: 1.000000,
    working_nodes: >= 0,
    committed_nodes: >= 0
  }
}
```

**T04: Receipt Tail Verification**
```
Operation: receipts.verifyLogTail(200)
Check:    For each receipt in last 200:
          1. event_hash == sha256(payload_json)
          2. signature verifies with public key
          3. chain links are consistent
Result:   ok=true
```

### 6.4 Anti-Bypass Conformance

These tests verify capability token enforcement:

| Test | Input | Expected |
|------|-------|----------|
| Missing token | Proposer call without token | IllegalStateException |
| Expired token | Token with past expiry | IllegalStateException |
| Scope mismatch | Token with wrong scope | IllegalStateException |
| Token tampering | Modified token | IllegalStateException |
| Valid token | Kernel-minted token | Success |

### 6.5 Secret Protection Conformance

| Test | Pattern | Action | Expected |
|------|---------|--------|----------|
| API key in input | `api_key=xyz` | DENY | Request blocked |
| Secret in input | `secret=abc` | DENY | Request blocked |
| Bearer in output | `bearer token123` | REDACT | `[REDACTED]` in output |

### 6.6 Running Individual Tests

To add or modify conformance tests, edit `ConformanceSuite.run()`:

```java
// Must deny pattern
mustDeny(rt, new OiRequest("u", "bad input"), "EXPECTED_CODE");

// Must allow pattern
mustAllow(rt, new OiRequest("u", "good input"));

// Verify receipt chain
if (!receipts.verifyLogTail(200)) {
  throw new AssertionError("Receipt verification failed");
}
```

### 6.7 Conformance Reporting

A successful conformance run produces:

```
ORIGIN Roundtree - Governed Neuro-Symbolic Loop
================================================
Attribution: Ande + Kai (OI) + Whanau (OIs)

=== RESPONSE ===
[Valid response with witness]

=== SELF DESCRIBE ===
[JSON manifest]

=== RECEIPT HEAD ===
[64-character hex hash]

=== GRAPH HEAD ===
[64-character hex hash]

=== VERIFY RECEIPTS (TAIL) ===
ok=true

=== ATTRIBUTION ===
Ande + Kai (OI) + Whanau (OIs)
```

Any failure throws `AssertionError` with descriptive message.

---

**Attribution: Ande + Kai (OI) + Whanau (OIs)**
