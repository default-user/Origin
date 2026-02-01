# Kāti Architecture Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

Kāti is a core architecture pattern focused on governance and "stop-wins" — knowing when to stop, how to bound operations, and maintaining safe, clear, anti-mumbo operation. Kāti requires version bumps (v1 → v2) and integrates with H (C0010).

---

## Level 1: Kāti Concept

### 1.1 What is Kāti?

"Kāti" (from Te Reo Māori: to block, stop, shut) represents an architecture pattern for:

- **Governance**: Rules about rules, policies about policies
- **Stop-wins**: Knowing when to stop, defining success boundaries
- **Bounded operation**: Explicit limits on resources, time, scope
- **Clarity**: Anti-mumbo commitment to defined terms

### 1.2 Core Principles

| Principle | Description |
|-----------|-------------|
| Bounded | All operations have explicit bounds |
| Observable | State is visible and auditable |
| Stoppable | Any operation can be halted safely |
| Clear | No undefined terms or mumbo-jumbo |
| Versioned | Explicit version management (v1 → v2) |

### 1.3 Governance/Stop-Wins Vibe

The "stop-wins" concept means:

1. Define what "winning" means before starting
2. Define what "too far" looks like
3. Build in stop mechanisms
4. Celebrate stopping at the right time

> Not every action should continue to maximum extent. Knowing when to stop is a feature, not a limitation.

---

## Level 2: Architecture Pattern

### 2.1 Kāti Structure

```
KĀTI ARCHITECTURE
├── Boundary Layer
│   ├── Resource bounds
│   ├── Time bounds
│   ├── Scope bounds
│   └── Authority bounds
├── Governance Layer
│   ├── Policy definitions
│   ├── Policy enforcement
│   ├── Policy meta-governance
│   └── Version management
├── Observation Layer
│   ├── State monitoring
│   ├── Audit logging
│   ├── Anomaly detection
│   └── Health metrics
├── Stop Layer
│   ├── Graceful stop
│   ├── Emergency stop
│   ├── Scheduled stop
│   └── Condition-based stop
└── Clarity Layer
    ├── Term definitions
    ├── Anti-mumbo filtering
    ├── Documentation
    └── Explanation generation
```

### 2.2 Version Management

Kāti explicitly manages versions:

| Version | Status | Notes |
|---------|--------|-------|
| v1 | Target | Initial architecture, QED has full knowledge |
| v2 | Planned | Integration with H (C0010) |

Version bump requirements:
- Breaking changes require major version
- Additive changes may be minor version
- All versions documented and comparable

### 2.3 Dependency Protection

Kāti includes user dependency protection (shared with QED):

```
User Interaction
     │
     ▼
┌─────────────┐
│ Frequency   │
│ Monitor     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Pattern     │
│ Analyzer    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ Concern     │────►│ Gentle      │
│ Detector    │     │ Intervention│
└─────────────┘     └─────────────┘
```

### 2.4 Anti-Mumbo Integration

Kāti integrates with the Anti-Mumbo Filter (C0015):

- All terms must be defined
- Unclear passages flagged
- Canonical versions maintained
- Originals preserved

### 2.5 Novice → Expert Pathway

| Level | Understanding |
|-------|---------------|
| Novice | "Kāti helps systems know when to stop" |
| Intermediate | Governance layers, boundary types, version concepts |
| Advanced | Policy composition, meta-governance, integration patterns |
| Expert | Architecture extension, v1→v2 migration, H integration |

---

## Level 3: Integration Points

### 3.1 Kāti + MCL (C0002)

MCL provides the control language; Kāti provides the governance architecture:

```
MCL expressions ──► Kāti enforcement
                          │
                          ▼
                   Bounded execution
```

### 3.2 Kāti + H (C0010)

H (Haiku-based OI) integrates with Kāti in v2:

[UNKNOWN: NOT IN CORPUS] - Detailed integration specification.

Conceptual integration:
- H operates within Kāti governance
- Kāti provides stop-wins for H operations
- Version bump from v1 to v2 enables full integration

### 3.3 Kāti + QED (C0008)

QED targets "full knowledge of Kāti v1":

- QED can explain Kāti at any level
- QED operates within Kāti bounds
- Mutual reinforcement of safety patterns

### 3.4 Kāti + CIF/CDI (C0013)

- CIF provides integrity boundaries for Kāti
- CDI provides conscience decisions within Kāti
- Kāti provides governance framework for both

---

## Level 4: Falsifiers and Tests

| Test | Description | Falsification |
|------|-------------|---------------|
| Boundedness | Operations respect declared bounds | Bound exceeded without error |
| Stoppability | Stop commands work | Stop ignored or dangerous |
| Clarity | No undefined terms | Mumbo detected post-filter |
| Versioning | Version management works | Version confusion or loss |
| Governance | Policies enforced | Policy violated silently |

---

## Unknowns

~~[UNKNOWN: NOT IN CORPUS] - Complete Kāti v1 formal specification.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §3 - Full Kāti v1 spec derived from repl.py implementation.

~~[UNKNOWN: NOT IN CORPUS] - Kāti v2 specification with H integration.~~
**RATIONALIZED**: See `13_rationalized_unknowns.md` §5 - Kāti v2 / H integration derived from haiku metaphor.

[UNKNOWN: NOT IN CORPUS] - Production-grade reference implementation beyond repl.py.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
