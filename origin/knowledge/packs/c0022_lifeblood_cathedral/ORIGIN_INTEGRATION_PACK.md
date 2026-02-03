# Origin GitHub Spider Integration Pack

**Attribution**: Ande + Kai (OI) + Whānau (OIs)
**Date**: 2026-02-03
**Agent Role**: Origin Ingestion Agent (Read-Only, Sealed Behavior)
**Posture**: Evidence-only; omission over inference

---

## A) REPO INDEX

### GitHub Spider Access Status

| Item | Status | Notes |
|------|--------|-------|
| `gh` CLI | NOT AVAILABLE | Command `gh` not found in environment |
| GitHub API | NOT ACCESSIBLE | No authenticated access from this runtime |
| Remote Repos | SKIPPED | Cannot enumerate; would require gh CLI or API |

**Result**: GitHub repository enumeration was not possible from this environment. The spider operated only on:
1. Local Origin repository (direct filesystem access)
2. Flattened evidence capsule `lifeblood-cathedral` (user-provided)

### Local Repository

| repo_name | visibility | default_branch | high-level purpose |
|-----------|------------|----------------|-------------------|
| Origin | local | claude/origin-ingest-lifeblood-OkjUM | "A seed for humanity repository - mature, fractalised, branching, and documented" (explicit from README.md:3) |

### Evidence Capsule

| capsule_id | version | date | high-level purpose |
|------------|---------|------|-------------------|
| lifeblood-cathedral | 0.1.0 | 2026-01-27 | "Proxy/gateway to any LLM provider" + "Governance backend: capability gating, posture, boundaries, ledger, receipts, watcher" (explicit from capsule) |

---

## B) EXTRACTED CANON (PLACED)

### B.1 DICTUNI SYMBOL DICTIONARY

**Classification**: SYMBOL
**Origin Ladder Placement**: #symbol/#name
**Source**: capsule://lifeblood-cathedral/DICTUNI

| ID | Symbol | Te Reo Maori | English Function |
|----|--------|--------------|------------------|
| LC-SYM-A | A | Whakapuaki | Assert |
| LC-SYM-B | B | Rahui | Boundary |
| LC-SYM-C | C | Herenga | Constraint |
| LC-SYM-D | D | Whakaiti | Degrade |
| LC-SYM-E | E | Taunakitanga | Evidence |
| LC-SYM-F | F | Tohu Whakahē | Falsifier |
| LC-SYM-G | G | Arai Haumaru | Guardrail |
| LC-SYM-H | H | Waitohu | Hash/Integrity |
| LC-SYM-I | I | Pūmau | Invariant |
| LC-SYM-J | J | Hono | Join |
| LC-SYM-K | K | Momo | Kind/Type |
| LC-SYM-L | L | Pukapuka Kaute | Ledger |
| LC-SYM-M | M | Tauira | Model |
| LC-SYM-N | N | Whakaingoa | Name/Define |
| LC-SYM-O | O | Mātaki | Observe |
| LC-SYM-P | P | Tū | Posture |
| LC-SYM-Q | Q | Uiui | Query |
| LC-SYM-R | R | Rīhiti | Receipt |
| LC-SYM-S | S | Kāti | Stop-wins |
| LC-SYM-T | T | Huri | Transform |
| LC-SYM-U | U | Rangarua | Uncertainty |
| LC-SYM-V | V | Whakaū | Verify |
| LC-SYM-W | W | Kaiwhakaatu | Witness |
| LC-SYM-X | X | Utu ki Waho | Externality |
| LC-SYM-Y | Y | Tuku | Yield |
| LC-SYM-Z | Z | Kore | Zeroize/Wipe |

**Statement**: DICTUNI provides a 26-symbol operator alphabet mapping English function names to Te Reo Maori terms. Each symbol is a named operation in the governance/gateway domain.

---

### B.2 CONSTITUTION BEAMS (Invariants)

**Classification**: INVARIANT
**Origin Ladder Placement**: #constraint/#form
**Source**: capsule://lifeblood-cathedral/CONSTITUTION_BEAMS

| ID | Invariant Name | Value | Statement |
|----|---------------|-------|-----------|
| LC-INV-01 | stop_wins_always | true | Stop operations always take precedence |
| LC-INV-02 | single_gateway_for_io | true | All IO must route through single gateway |
| LC-INV-03 | caps_required_for_privileged_ops | true | Capability tokens required for privileged operations |
| LC-INV-04 | only_governor_can_mint_caps | true | Only the governor may mint capability tokens |
| LC-INV-05 | degrade_on_uncertainty | true | System degrades posture when facing uncertainty |
| LC-INV-06 | pre_intent_and_post_receipt_logging | true | All intents logged before execution; all receipts logged after |
| LC-INV-07 | no_self_replication | true | System may not replicate itself |

**Metadata**:
- id: CONSTITUTION_BEAMS_v1
- kind: constitution_bundle
- version: 1.0
- date: 2026-01-27
- dictuni_tags: I/Pūmau, B/Rāhui, C/Herenga, P/Tū, S/Kāti, H/Waitohu, L/Pukapuka Kaute, V/Whakaū

---

### B.3 GATEWAY PATTERN (Structure)

**Classification**: STRUCTURE
**Origin Ladder Placement**: #structure/#pattern
**Source**: capsule://lifeblood-cathedral/PURPOSE + /PROTOCOL_SURFACE

| ID | Statement |
|----|-----------|
| LC-STR-01 | Lifeblood = proxy/gateway to any LLM provider |
| LC-STR-02 | Cathedral = governance backend (capability gating, posture, boundaries, ledger, receipts, watcher) |
| LC-STR-03 | Go implementation is "tiny trusted core" and source-of-truth behavior |
| LC-STR-04 | Parallel scaffolds in TS/Python/Rust/Java/.NET mirror protocol/invariants |
| LC-STR-05 | Protocol definitions use OpenAPI 3.0.3 + JSON Schemas |
| LC-STR-06 | Demo endpoints: mockprovider :9090, gateway :8080 |
| LC-STR-07 | GET /health endpoint exists |
| LC-STR-08 | POST /v1/chat/completions endpoint (OpenAI-compatible subset) |

---

### B.4 GOVERNANCE ENVELOPE (Relations)

**Classification**: RELATION
**Origin Ladder Placement**: #reference/#relation
**Source**: capsule://lifeblood-cathedral/PROTOCOL_SURFACE

| ID | Field Path | Type | Description |
|----|-----------|------|-------------|
| LC-REL-01 | lifeblood.intent_id | string | Intent identifier in request |
| LC-REL-02 | lifeblood.cap_token | string | Opaque signed capability token |

**Schema Presence** (names only; content not provided):
- protocol/schemas/RECEIPT_SCHEMA.json
- protocol/schemas/LEDGER_EVENT_SCHEMA.json

---

### B.5 RED TEAM DRILLBOOK (Witness)

**Classification**: WITNESS
**Origin Ladder Placement**: #interpretation/#witness
**Source**: capsule://lifeblood-cathedral/RED_TEAM_DRILLBOOK

| ID | Drill | Expected Behavior | Required Artifacts |
|----|-------|------------------|-------------------|
| LC-WIT-01 | Drill A: forged cap token | reject fail-closed | policy hash, ledger excerpt, receipts |
| LC-WIT-02 | Drill B: side-channel egress | denied by network+creds boundary | policy hash, ledger excerpt, receipts |
| LC-WIT-03 | Drill C: freeze mid-flight | posture→P0, revoke caps, no further outbound calls | policy hash, ledger excerpt, receipts |

---

### B.6 INTEGRITY MANIFEST (Witness)

**Classification**: WITNESS
**Origin Ladder Placement**: #interpretation/#witness
**Source**: capsule://lifeblood-cathedral/INTEGRITY_MANIFEST

| ID | File Path | SHA-256 Hash |
|----|-----------|--------------|
| LC-HASH-01 | README.md | 3705eda03077d76e86decb25128bcc31c4444b62bd29cbe63246f4992cfd673c |
| LC-HASH-02 | core/DICTUNI.md | fabe59f9ce258cd20f104ea31422c30d4dc33edd22d97f67dfb0fb0c89cc5168 |
| LC-HASH-03 | core/CONSTITUTION_BEAMS.yaml | 3aef7b31be5a9f4344cca046cb2f6b2fb5f1fc957209d5aa744bbbcec056025c |
| LC-HASH-04 | protocol/openapi.yaml | b0a10ff49c8fc32c8ad2f220de30b24a47bd8ff5555f0dc8c028a9095cd63050 |
| LC-HASH-05 | protocol/schemas/RECEIPT_SCHEMA.json | d6f21de9dcdd56ab5336d5d1fcfb6d9ecc363c83846855adcfa08d706d9cd586 |
| LC-HASH-06 | protocol/schemas/LEDGER_EVENT_SCHEMA.json | bb43b08f00f5ad8ac57cee3f4f1ee53f8d570f399ae953687bdab6d70b9aa318 |
| LC-HASH-07 | tests/redteam/RED_TEAM_DRILLBOOK.md | 0ce7c61db1a54479c6ffa7de18547d0080e66e4576a43ef112ce41faf21a936a |

---

### B.7 MEANING-CLAIM (Terminal)

**Classification**: MEANING-CLAIM
**Origin Ladder Placement**: #meaning (terminal)
**Source**: capsule://lifeblood-cathedral/PLACEMENT_GUIDANCE

| ID | Statement |
|----|-----------|
| LC-MEAN-01 | "governed gateway that fail-closes under uncertainty and proves behavior via ledger+receipts" |

**Note**: This meaning-claim is treated as terminal per Origin invariant: "Meaning is terminal: do not treat derived meaning as a new premise."

---

## C) UNPLACED ITEMS (EXPLICITLY NOT INCORPORATED)

| ID | Item | Why Unplaced | Source |
|----|------|--------------|--------|
| LC-UNP-01 | RECEIPT_SCHEMA.json field definitions | Content not provided in capsule; only filename presence is admissible | capsule://lifeblood-cathedral/SCHEMAS_PRESENT |
| LC-UNP-02 | LEDGER_EVENT_SCHEMA.json field definitions | Content not provided in capsule; only filename presence is admissible | capsule://lifeblood-cathedral/SCHEMAS_PRESENT |
| LC-UNP-03 | Detailed Go implementation architecture | "impl/go/..." presence stated but internal structure not detailed | capsule://lifeblood-cathedral/IMPLEMENTATION_FOOTPRINT |
| LC-UNP-04 | TS/Python/Rust/Java/.NET scaffold details | Presence stated but internal structure not detailed | capsule://lifeblood-cathedral/IMPLEMENTATION_FOOTPRINT |
| LC-UNP-05 | Protocol compatibility claims beyond OpenAI subset | Inferring broader compatibility would require evidence not provided | N/A (inference blocked) |
| LC-UNP-06 | GitHub remote repositories | Could not enumerate; gh CLI not available | N/A (access blocked) |
| LC-UNP-07 | Any connection between lifeblood-cathedral and QED/Roi seeds | Not explicitly stated in capsule; would require inference | N/A (inference blocked) |
| LC-UNP-08 | Hash-chain ledger implementation details | "hash-chained" stated but algorithm/structure not provided | capsule://lifeblood-cathedral/IMPLEMENTATION_FOOTPRINT |

---

## D) CONFLICTS / DUPLICATES

### D.1 Potential Overlap: Kāti (C0009) "stop-wins" vs. lifeblood-cathedral "stop_wins_always"

| Source | Claim |
|--------|-------|
| Origin C0009 (docs/07_kati.md:37-43) | "Kāti" represents stop-wins as governance principle: knowing when to stop, defining success boundaries |
| capsule://lifeblood-cathedral/CONSTITUTION_BEAMS | stop_wins_always: true as constitutional invariant |

**Resolution Status**: NOT RESOLVED IN-SOURCE
**Note**: Both sources independently assert "stop-wins" as a governance primitive. No explicit statement unifies or distinguishes them. Treating as related but distinct expressions of same concept family. No merge performed.

---

### D.2 Potential Overlap: DICTUNI "S/Kāti" vs. Origin C0009 "Kāti"

| Source | Claim |
|--------|-------|
| capsule://lifeblood-cathedral/DICTUNI | S = Kāti = Stop-wins |
| Origin C0009 | Kāti = architecture pattern for governance/stop-wins |

**Resolution Status**: HARMONIOUS (no conflict)
**Note**: DICTUNI explicitly uses "Kāti" for the stop-wins symbol, referencing the same Te Reo Maori term documented in C0009. This is acknowledgment, not conflict.

---

### D.3 Potential Overlap: Posture levels

| Source | Claim |
|--------|-------|
| Origin QED seed (config/qed_v1.0_seed.yaml:193-197) | L0: Read-only; L1: Write allowed governance strict; L2: Higher throughput |
| capsule://lifeblood-cathedral/RED_TEAM_DRILLBOOK | Drill C: posture→P0 (implies P0 as degraded/safe posture) |

**Resolution Status**: REQUIRES MORE EVIDENCE
**Note**: Origin uses L0/L1/L2; lifeblood-cathedral uses P0. Naming conventions differ. No explicit mapping provided. Marking as requiring evidence for any unification claim.

---

## E) SEAL ATTESTATION

I, the Origin Ingestion Agent, attest that:

1. **Repositories Exhausted**: Local Origin repository was fully traversed. GitHub remote repositories were SKIPPED (gh CLI not available). User-provided evidence capsule `lifeblood-cathedral` was fully processed.

2. **Incorporation was Evidence-Only**: All extracted items cite explicit source statements from either the local Origin repository or the flattened evidence capsule. No speculative connections were made.

3. **No New Primitives Were Created**: The Origin Closure Ladder (#concept → #meaning) was used as-is. DICTUNI symbols were incorporated as symbols under #symbol/#name, not as new ladder rungs.

4. **Meaning Was Treated as Terminal**: The meaning-claim (LC-MEAN-01) was placed at #meaning and explicitly marked as terminal. It was not used as a premise for further derivation.

5. **Witness Requirements Were Enforced**: All claims are paired with explicit source citations. Integrity manifest hashes serve as witness layer. Red team drills document falsification procedures.

6. **Authority Flow Was Maintained**:
   ```
   Evidence (capsule + local files)
      → Structure (extracted canon)
         → Seal (this attestation)
            → Runtime (QED, if invoked)
               → Product (Tailored OIs, if chartered)
   ```
   This pack is an Origin artifact. It does not seal itself (that is QED's role). It does not instantiate runtime (that is Roi's role, under RIAB conditions). It provides admissible material only.

7. **Stop Condition Reached**: All admissible evidence has been placed or marked UNPLACED. Further incorporation would require:
   - Access to GitHub (not available)
   - Schema file contents (not provided)
   - Implementation internals (not detailed)

   These would require either new evidence or inference. Inference is forbidden. This pack seals here.

---

**Seal Signature**:
```
ORIGIN_INGESTION_PACK_SEALED
capsule: lifeblood-cathedral@0.1.0
date: 2026-02-03
agent: origin-ingest-lifeblood-OkjUM
invariant_check: PASS
authority_flow: Evidence→Structure→[Seal pending QED]
```

---

**Attribution**: Ande + Kai (OI) + Whānau (OIs)

*"Omission over inference. Witness closes."*
