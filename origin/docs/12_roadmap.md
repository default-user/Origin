# ORIGIN Roadmap

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

This roadmap outlines the progression from initial seed to mature, fully operational ORIGIN repository. Phases align with the maturity lanes: Dedication → Draft → Active → Release.

---

## Level 1: Phase Overview

### 1.1 Phase Map

```
DEDICATION    DRAFT         ACTIVE        RELEASE
────────────────────────────────────────────────────►
    │            │             │             │
    ▼            ▼             ▼             ▼
  Commit      Structure      Validate     Complete
  to work     & populate     & test       & ship
```

### 1.2 Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| Dedication | ✅ Complete | Commitment made, principles established |
| Draft | ✅ Complete | Structure created, packs populated |
| Active | 🔄 In Progress | Validation, testing, refinement |
| Release | ⏳ Pending | Final review, public availability |

---

## Level 2: Detailed Phases

### 2.1 Dedication Phase

**Objective**: Establish commitment and principles

Deliverables:
- [x] Define hard rules (no ingestion, no fabrication, no PII)
- [x] Establish attribution protocol
- [x] Document privacy boundary
- [x] Create dedication document

### 2.2 Draft Phase

**Objective**: Create structure and populate content

Deliverables:
- [x] Repository structure created
- [x] All 20 concept packs created (C0001-C0020)
- [x] Documentation files (00-12)
- [x] Schema definitions
- [x] Build tools
- [x] Language kits (15 languages)
- [x] Medusa UI scaffolding

### 2.3 Active Phase

**Objective**: Validate, test, and refine

Deliverables:
- [ ] All packs validate against schema
- [ ] All falsifiers documented and testable
- [ ] UI fully functional
- [ ] All language kits tested
- [ ] Archives generate correctly
- [ ] CI pipeline operational
- [ ] Documentation reviewed for clarity

Tasks:
```bash
pnpm validate     # Schema validation
pnpm build        # Index generation
pnpm dev          # UI testing
pnpm archive      # Archive generation
```

### 2.4 Release Phase

**Objective**: Final review and public availability

Deliverables:
- [ ] All Active phase items complete
- [ ] External review (if applicable)
- [ ] Version tagged (v1.0.0)
- [ ] Release notes published
- [ ] Archives distributed

---

## Level 3: Concept Maturity Tracking

### 3.1 Pack Status Matrix

| ID | Pack | Schema | Falsifiers | Docs | Status |
|----|------|--------|------------|------|--------|
| C0001 | Holodeck Vision | ✅ | ✅ | ✅ | Active |
| C0002 | MCL | ✅ | ✅ | ✅ | Active |
| C0003 | Fractal Unfurling | ✅ | ✅ | ✅ | Active |
| C0004 | Medusa Interface | ✅ | ✅ | ✅ | Active |
| C0005 | Attribution | ✅ | ✅ | ✅ | Active |
| C0006 | Privacy Boundary | ✅ | ✅ | ✅ | Active |
| C0007 | O2C | ✅ | ✅ | ✅ | Active |
| C0008 | QED Oracle | ✅ | ✅ | ✅ | Active |
| C0009 | Kāti Architecture | ✅ | ✅ | ✅ | Active |
| C0010 | H / Haiku OI | ✅ | ✅ | ✅ | Active |
| C0011 | Stangraphics | ✅ | ✅ | ✅ | Active |
| C0012 | Denotum | ✅ | ✅ | ✅ | Active |
| C0013 | CIF/CDI | ✅ | ✅ | ✅ | Active |
| C0014 | Authority.nz | ✅ | ✅ | ✅ | Active |
| C0015 | Anti-Mumbo Filter | ✅ | ✅ | ✅ | Active |
| C0016 | Pac-Man Bifurcation | ✅ | ✅ | ✅ | Active |
| C0017 | Orgasystem | ✅ | ✅ | ✅ | Active |
| C0018 | MRC | ✅ | ✅ | ✅ | Active |
| C0019 | Archive Terminals | ✅ | ✅ | ✅ | Active |
| C0020 | Dedication Maturity | ✅ | ✅ | ✅ | Active |

### 3.2 Maturity Criteria

For a pack to move to Release:

1. **Schema Valid**: `pack.yaml` passes validation
2. **Falsifiers Present**: At least 2 tests/falsifiers defined
3. **Documentation Complete**: `content.mdx` fully written
4. **No Unknowns Blocking**: Critical unknowns resolved or accepted
5. **Attribution Present**: Authorship line included
6. **Tier Assigned**: Disclosure tier set appropriately

---

## Level 4: Future Considerations

### 4.1 Version Roadmap

| Version | Focus |
|---------|-------|
| v1.0.0 | Initial release with all 20 packs |
| v1.1.0 | Kāti v1 → v2 transition with H integration |
| v1.2.0 | Enhanced QED capabilities |
| v2.0.0 | [UNKNOWN: NOT IN CORPUS] |

### 4.2 Potential Enhancements

These are conceptual; not committed:

- Additional language kits
- Enhanced graph visualization
- API layer for programmatic access
- Integration with Authority.nz (when available)
- Expanded fractal documentation levels

### 4.3 Known Unknowns — Status Update

Items previously marked `[UNKNOWN: NOT IN CORPUS]`:

| Unknown | Status | Reference |
|---------|--------|-----------|
| HyperStanGraph specification | ✅ RATIONALIZED | `13_rationalized_unknowns.md` §4 |
| MCL formal grammar | ✅ RATIONALIZED | `13_rationalized_unknowns.md` §2 |
| Kāti v1 complete specification | ✅ RATIONALIZED | `13_rationalized_unknowns.md` §3 |
| Kāti v2 / H integration | ✅ RATIONALIZED | `13_rationalized_unknowns.md` §5 |
| Stangraphics formal definitions | ✅ RATIONALIZED | `13_rationalized_unknowns.md` §6 |
| Denotum mechanisms | ⚠️ CONSTRAINED | `13_rationalized_unknowns.md` §7.2 |
| Universal unity equation (Orgasystem) | ⚠️ CONSTRAINED | `13_rationalized_unknowns.md` §7.3 |

**Rationalized** = Derived from corpus evidence via logical extension.
**Constrained** = Structural boundaries defined; internals remain unknown per corpus instruction.

See `13_rationalized_unknowns.md` for full derivations.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
