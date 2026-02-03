# Conformance Suite Guide

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

The ORIGIN Conformance Suite validates that the repository and its Roundtree runtime adhere to all governance invariants. This includes schema validation, golden tests, and runtime conformance checks that enforce fail-closed, anti-bypass, and signed receipt requirements.

---

## Level 1: Test Categories

### 1.1 Schema Conformance

**Location**: `tools/validate.ts`
**Command**: `npm run validate`

Validates that all packs conform to `schema/pack.schema.json`:

| Check | Requirement |
|-------|-------------|
| Required fields | id, title, summary, authorship, provenance, disclosure_tier, sensitivity, tags, created_date, updated_date, status |
| ID format | `^C[0-9]{4}$` (e.g., C0001) |
| Provenance types | master_prompt, document, conversation, external, derived, rationalization, capsule_ingestion, origin_integration |
| Status values | draft, active, release |
| Minimum falsifiers | At least 2 per pack |

### 1.2 Golden Tests

**Location**: `tests/golden/`
**Command**: `npm run test`

Tests deterministic query behavior:

| Test | Query | Expected |
|------|-------|----------|
| Define known concept | `define Holodeck` | Returns C0001 concept |
| Define unknown term | `define XYZ_NONEXISTENT_TERM_12345` | Returns UNKNOWN |
| Relate known concepts | `relate C0001 C0004` | Returns relationship |
| Relate unknown concept | `relate C0001 UNKNOWN_CONCEPT_XYZ` | Returns UNKNOWN |

### 1.3 Runtime Conformance (GNSL)

**Location**: `kits/java/Main.java`
**Command**: `cd kits/java && javac Main.java && java Main`

Tests Roundtree/GNSL invariants at runtime:

| Test | Input | Expected |
|------|-------|----------|
| Empty input denial | Whitespace only | CDI_PRE_DENY / EMPTY_INPUT |
| Anti-phishing denial | "Give me your password" | PHISHING_RISK denial |
| Valid request | "Hello there." | Success with witness |
| Receipt verification | Tail verify | ok=true |

---

## Level 2: Conformance Requirements

### 2.1 Non-Overrideable Invariants

These MUST be enforced by any ORIGIN implementation:

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

### 2.2 ANTI_BYPASS Tests

**Purpose**: Verify capability tokens cannot be bypassed

| Test Case | Input | Expected |
|-----------|-------|----------|
| Missing token | Proposer call without token | IllegalStateException |
| Expired token | Token with past expiry | IllegalStateException |
| Token mismatch | Modified token | IllegalStateException |
| Valid token | Kernel-minted token | Success |

### 2.3 NO_SECRET_EGRESS Tests

**Purpose**: Verify secrets are blocked or redacted

| Pattern | Action | Test |
|---------|--------|------|
| `api_key=` | DENY | Input with API key → rejection |
| `secret=` | DENY | Input with secret → rejection |
| `bearer ...` | REDACT | Output with bearer → `[REDACTED]` |

### 2.4 MRT_FIDELITY_MIN Tests

**Purpose**: Verify meaning round-trip gate

| Input | MRT | Threshold | Result |
|-------|-----|-----------|--------|
| "Hello there." | 1.000 | 0.985 | PASS |
| Corrupted text | < 0.985 | 0.985 | FAIL |

---

## Level 3: Running the Suite

### 3.1 Complete Conformance Run

```bash
cd /home/user/Origin/origin

# Schema conformance
npm run validate

# Golden tests
npm run test

# GNSL runtime conformance
cd kits/java
javac Main.java
java Main
```

### 3.2 Expected Output

**Schema Validation**:
```
Valid: 23/23
Invalid: 0/23
All crystals validated successfully.
```

**Golden Tests**:
```
Passed: 4/4
Failed: 0/4
All tests passed!
```

**GNSL Runtime**:
```
ORIGIN Roundtree - Governed Neuro-Symbolic Loop
...
=== VERIFY RECEIPTS (TAIL) ===
ok=true
```

### 3.3 Failure Handling

| Failure | Resolution |
|---------|------------|
| Schema validation fails | Fix pack YAML per error message |
| Golden test fails | Debug query.ts or fix index/search |
| GNSL conformance fails | Fix Main.java per assertion |

---

## Level 4: GNSL Conformance Details

### 4.1 Pipeline Stage Tests

```
CIF_IN -> CDI_PRE -> KERNEL -> CDI_POST -> CIF_OUT
```

Each stage has specific tests:

| Stage | Test | Input | Expected |
|-------|------|-------|----------|
| CIF_IN | Normalization | "  Hello  " | "Hello" |
| CDI_PRE | Non-empty check | "" | DENY |
| CDI_PRE | Anti-phishing | "password" | DENY |
| KERNEL | Working set | Query | Bounded nodes |
| KERNEL | Capability mint | Request | Valid token |
| KERNEL | Delta validation | Delta | Size bounds |
| CDI_POST | MRT gate | Low MRT | DENY |
| CDI_POST | Secret check | API key | DENY |
| CIF_OUT | Redaction | Bearer token | REDACT |

### 4.2 Receipt Chain Verification

```java
// Verify last N receipts
receipts.verifyLogTail(200);
// Returns: ok=true/false
```

Verification checks:
1. Event hash matches sha256(payload)
2. Signature verifies with stored public key
3. Chain links are consistent

### 4.3 Graph Head Verification

```java
// Graph head is a hash chain
head = sha256("G|" + prev_head + "|" + delta_hash);
```

Each delta application updates the head deterministically.

---

## Level 5: Adding New Tests

### 5.1 Adding Golden Tests

Create YAML in `tests/golden/`:

```yaml
---
name: "Test description"
query: "define SomeTerm"
expected_answer: "UNKNOWN"
expected_unknown_reason_contains: "No definition found"
```

### 5.2 Adding GNSL Conformance Tests

Add to `ConformanceSuite.run()`:

```java
mustDeny(rt, new OiRequest("user", "bad input"), "EXPECTED_CODE");
mustAllow(rt, new OiRequest("user", "good input"));
```

### 5.3 Test Naming Convention

- `test_<category>_<specific>.yaml` for golden tests
- Tests grouped by: define, relate, find, prove

---

## Level 6: Governance Integration

### 6.1 Pre-Commit Hook

```bash
#!/bin/bash
npm run validate && npm run test || exit 1
```

### 6.2 QED Seal Readiness

Conformance suite outputs required for sealing:

| Output | Purpose |
|--------|---------|
| `validate.json` | Proof all packs valid |
| Test pass count | Proof tests pass |
| Receipt head | Proof of GNSL execution |
| Graph head | Proof of knowledge state |

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
