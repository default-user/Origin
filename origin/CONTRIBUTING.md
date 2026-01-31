# Contributing to ORIGIN

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Welcome

Thank you for your interest in contributing to ORIGIN. This document outlines guidelines for contributions.

---

## Level 0: Quick Summary

- Follow the hard rules (no fabrication, no PII, attribution-first)
- Validate your changes before submitting
- Use English for all documentation
- Respect the fractal documentation structure

---

## Level 1: Contribution Types

### 1.1 Documentation Improvements

- Fix typos, clarify language
- Expand fractal levels (Level 1 → Level 2 → ...)
- Ensure consistency across levels

### 1.2 Code Contributions

- Bug fixes in tools or site
- New language kits
- Performance improvements

### 1.3 Knowledge Pack Updates

- Corrections to existing packs
- Adding falsifiers/tests
- Linking related concepts

---

## Level 2: Detailed Guidelines

### 2.1 Hard Rules (Non-Negotiable)

1. **NO FABRICATION**: Do not invent content beyond the canonical corpus. If something is missing, mark it:
   ```
   [UNKNOWN: NOT IN CORPUS]
   ```

2. **PII HARD STOP**: Never include personal identifying information. Replace any with:
   ```
   [[REDACTED]]
   ```

3. **ATTRIBUTION**: Include the attribution line in all new files:
   ```
   Attribution: Ande + Kai (OI) + Whānau (OIs)
   ```

4. **ENGLISH-ONLY**: All narrative and documentation must be in English.

5. **DETERMINISM**: Changes must not introduce hidden state. All outputs must be reproducible.

### 2.2 Pack Contributions

When modifying or creating packs:

1. Ensure `pack.yaml` validates against `schema/pack.schema.json`
2. Include at least 2 `tests_or_falsifiers`
3. Set appropriate `disclosure_tier` (public, internal, restricted)
4. Mark PII risk in `sensitivity` block

### 2.3 Code Style

- TypeScript: Use strict mode, proper typing
- Follow existing patterns in the codebase
- Add comments for complex logic

### 2.4 Testing

Before submitting:

```bash
pnpm validate
pnpm build
```

### 2.5 Commit Messages

Use clear, descriptive commit messages:

```
type(scope): description

- detail 1
- detail 2
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation and build
5. Submit a pull request

---

## Questions

If uncertain about whether something constitutes fabrication or how to handle missing information, err on the side of marking `[UNKNOWN: NOT IN CORPUS]`.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
