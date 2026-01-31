# Privacy Boundary Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

ORIGIN encodes knowledge while strictly excluding "personal personal data" (PII). Any accidental personal identifiers must be replaced with `[[REDACTED]]` tokens. This document defines the privacy boundary and handling protocols.

---

## Level 1: Core Principles

### 1.1 What is "Personal Personal Data"?

The term emphasizes truly personal, identifying information:

| Category | Examples | Status |
|----------|----------|--------|
| Names (private) | Home addresses, personal phone numbers | EXCLUDED |
| Identifiers | SSN, passport numbers, license numbers | EXCLUDED |
| Private health | Medical records, diagnoses | EXCLUDED |
| Private financial | Bank accounts, credit cards | EXCLUDED |
| Relationship incidents | Private family matters, personal conflicts | EXCLUDED |
| Private emails/phones | personal@email.com, +1-555-private | EXCLUDED |

### 1.2 What is NOT Excluded?

| Category | Examples | Status |
|----------|----------|--------|
| Attribution names | "Ande", "Kai (OI)" | INCLUDED (authorship) |
| Public entities | "Authority.nz" | INCLUDED (concepts) |
| Conceptual references | "Whānau (OIs)" | INCLUDED (group reference) |

### 1.3 The [[REDACTED]] Token

When PII is accidentally encountered:

```
Before: "Contact John Smith at 123 Main St, 555-1234"
After:  "Contact [[REDACTED]] at [[REDACTED]]"
```

The token:
- Is visually distinct
- Indicates removal occurred
- Preserves document structure
- Does not reveal original content

---

## Level 2: Implementation

### 2.1 Pack Sensitivity Schema

Each `pack.yaml` includes:

```yaml
sensitivity:
  pii_risk: none | low | medium | high
  contains_personal: false | true
  redacted: false | true
```

| Field | Description |
|-------|-------------|
| `pii_risk` | Assessed risk level for this content |
| `contains_personal` | Does content reference individuals? |
| `redacted` | Have any [[REDACTED]] tokens been applied? |

### 2.2 Disclosure Tiers

Tiers provide access control layers:

| Tier | Access | PII Handling |
|------|--------|--------------|
| public | Unrestricted | No PII possible |
| internal | Organization | Minimal PII risk, reviewed |
| restricted | Limited | May reference individuals (redacted) |

### 2.3 Review Process

Before content enters ORIGIN:

```
Content Draft
     │
     ▼
┌─────────────┐
│ PII Scan    │ ← Automated pattern detection
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Human       │ ← Manual review for edge cases
│ Review      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Redaction   │ ← Apply [[REDACTED]] where needed
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Tier        │ ← Assign appropriate tier
│ Assignment  │
└──────┬──────┘
       │
       ▼
  Approved Content
```

### 2.4 PII Patterns (Detection)

Patterns to scan for (examples):

```regex
# Email patterns
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}

# Phone patterns (various formats)
\+?[0-9]{1,3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}

# Address patterns
[0-9]+\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr)

# ID patterns
[0-9]{3}-[0-9]{2}-[0-9]{4}  # SSN format
```

> Note: Patterns are illustrative. Real implementation requires comprehensive coverage.

---

## Level 3: Privacy Boundary in Practice

### 3.1 Example: Valid Content

```markdown
# MCL Specification

Attribution: Ande + Kai (OI) + Whānau (OIs)

MCL provides meta-control language capabilities...
```

✅ Attribution names are authorship, not private PII.

### 3.2 Example: Content Requiring Redaction

```markdown
# Meeting Notes

Discussed with John Smith (john.smith@company.com)
at 123 Oak Street, Springfield.
```

After redaction:

```markdown
# Meeting Notes

Discussed with [[REDACTED]] at [[REDACTED]].
```

### 3.3 Example: Edge Case

```markdown
# Concept Discussion

The Kāti pattern was developed in Wellington, New Zealand.
```

✅ Geographic references to cities/countries are generally NOT PII.

```markdown
# Concept Discussion

Developed at 42 Specific Address, Wellington.
```

❌ Specific addresses should be [[REDACTED]].

---

## Level 4: Falsifiers and Tests

| Test | Description | Falsification |
|------|-------------|---------------|
| No raw PII | Scan finds no PII patterns | PII pattern detected |
| Redaction applied | [[REDACTED]] used where needed | Missing redaction |
| Tier consistency | PII risk matches tier | High PII in public tier |
| Attribution preserved | Author names present | Attribution lost |
| Schema compliance | Sensitivity fields present | Missing fields |

---

## Unknowns

[UNKNOWN: NOT IN CORPUS] - Comprehensive PII pattern library for all jurisdictions.

[UNKNOWN: NOT IN CORPUS] - Automated redaction tool implementation details.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
