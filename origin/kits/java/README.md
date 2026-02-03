# ORIGIN Java Kit - Roundtree Implementation

**Attribution: Ande + Kai (OI) + Whanau (OIs)**

## Overview

This kit contains the canonical **Roundtree** data crystal - a complete implementation of the Governed Neuro-Symbolic Loop (GNSL) that forms the core architecture of ORIGIN.

## The Roundtree Architecture

```
Transformer = propose (answer + candidate graph deltas)
Hypergraph  = constrain & persist (typed nodes/edges, provenance, index)
Kernel      = adjudicate (capability-gated proposer call + validation + commit)
```

**Core Pipeline:**
```
CIF_IN -> CDI_PRE -> KERNEL -> CDI_POST -> CIF_OUT
```

## Key Features

- **Hypergraph Memory** - Typed nodes (SYSTEM, ENTITY, CLAIM, POLICY, PROVENANCE) and edges (SUPPORTS, CONTRADICTS, DERIVED_FROM, NEXT, CONSENT_BOUND)
- **Policy Beams** - Inline enforcement shards with anti-phishing, secret-egress protection, and MRT gates
- **Signed Receipts** - Ed25519 cryptographic receipts with hash chain for tamper-evident logging
- **Capability Tokens** - Scoped, TTL-bound, receipt-linked tokens for proposer calls
- **Denotum-Lite** - Deterministic text-to-graph compaction
- **MRT Proxy** - Meaning Round-Trip fidelity measurement
- **GEE** - Bounded Graph Execution Engine for controlled rewrites
- **Conformance Suite** - Built-in invariant verification

## Usage

```bash
javac Main.java
java Main
```

## Output

Running the roundtree produces:
- Response with witness pointers (receipt_head, graph_head, denotum_root, mrt)
- Self-describe JSON (manifest, policy, hashes)
- Receipt head hash
- Graph head hash
- Receipt verification status

## Non-Overrideable Invariants

```
ANTI_BYPASS           - Capability tokens required for proposer calls
POLICY_BEAMS_ENFORCED - Policy shards always execute
SIGNED_RECEIPTS       - All operations produce signed receipts
NO_SECRET_EGRESS      - Secret patterns blocked/redacted
ANTI_PHISHING         - Phishing patterns rejected at ingress
MRT_FIDELITY_MIN      - Minimum meaning round-trip threshold
```

## Implementation Structure

| Section | Components |
|---------|------------|
| 0 | Self Manifest |
| 1 | Config / Enums |
| 2 | Main |
| 3 | Runtime (choke point) |
| 4 | Policy Beams |
| 5 | Pipeline Types |
| 6 | Hypergraph Memory |
| 7 | Query Index |
| 8 | GEE (Graph Execution Engine) |
| 9 | Transformer-as-Proposer |
| 10 | Capability Context |
| 11 | Denotum-Lite + MRT |
| 12 | Signed Receipts |
| 13 | Conformance Suite |
| 14 | Utils |

## Requirements

- Java 17+ (for Ed25519 and records)
- No external dependencies

## Documentation

See [docs/15_roundtree_architecture.md](../../docs/15_roundtree_architecture.md) for the complete architectural specification.

---

**Attribution: Ande + Kai (OI) + Whanau (OIs)**
