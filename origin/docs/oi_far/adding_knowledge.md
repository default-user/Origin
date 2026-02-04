# Adding Knowledge to OI-FAR

This guide explains how to expand OI-FAR's knowledge base.

## Overview

OI-FAR's knowledge comes from:
1. **Origin Concept Packs** - Structured YAML files in `knowledge/packs/`
2. **Documents** - Text files ingested via the growth loop
3. **Manual Bricks** - Programmatically added knowledge

## Method 1: Origin Concept Packs (Recommended)

The primary way to add knowledge is through Origin concept packs.

### Pack Structure

```
knowledge/packs/c0024_my_concept/
├── pack.yaml       # Metadata and claims
├── content.mdx     # Detailed content
└── artifacts/      # Supporting files
```

### pack.yaml Format

```yaml
id: C0024
title: My New Concept
summary: Brief description of the concept
authorship:
  created_by: Your Name
  organization: Your Org
provenance:
  basis: Original work
disclosure_tier: public  # public, internal, restricted
sensitivity:
  level: PUBLIC
  pii_risk: false
  contains_personal: false
tags:
  - tag1
  - tag2
created_date: "2025-01-15"
updated_date: "2025-01-15"
status: draft  # draft, active, release

# Relationships
parents: []
children: []
related: []

# Claims (required: minimum 2)
claims:
  - text: "First factual claim about the concept"
    confidence: 1.0
  - text: "Second factual claim"
    confidence: 0.9

# Tests (required: minimum 2)
tests_or_falsifiers:
  - "Test that could verify claim 1"
  - "Test that could verify claim 2"

# Artifacts
artifacts:
  - path: artifacts/diagram.png
    description: System diagram
```

### Adding a Pack

1. Create the directory structure
2. Write pack.yaml with required fields
3. Add content.mdx for detailed documentation
4. Validate: `npm run validate`
5. Build: `npm run build`

The next time OI-FAR runs, it will bootstrap from the updated packs.

## Method 2: Document Ingestion

For adding documents programmatically:

```python
from oi_far import get_runtime
from oi_far.substrate import Document

runtime = get_runtime(".")

# Create document
doc = Document(
    id="doc_my_new_doc",
    title="My Document Title",
    content="Full text content of the document...",
    source_type="text",
    source_path="/path/to/source.txt",
)

# Ingest (compiles to bricks automatically)
bricks_created = runtime.growth_loop.ingest_document(doc)
print(f"Created {bricks_created} bricks")

# Reindex
runtime.growth_loop.reindex()
```

## Method 3: Manual Bricks

For fine-grained control over brick creation:

```python
from oi_far.substrate import BrickStore, Brick, BrickKind, Claim, Provenance

store = BrickStore("./build/oi_far/bricks")

brick = Brick(
    id="brick_custom_001",
    kind=BrickKind.CLAIM,
    title="My Custom Claim",
    summary="Detailed explanation of the claim",
    claims=[
        Claim(
            id="claim_001",
            text="The specific factual assertion",
            confidence=0.95,
        )
    ],
    definitions=[],
    links=[],
    provenance=Provenance(
        source_id="manual",
        source_type="manual",
    ),
    confidence=0.95,
    tags=["custom", "manual"],
)

store.add(brick)
store.rebuild_indexes()
```

## Brick Types

OI-FAR supports different brick kinds:

| Kind | Use Case |
|------|----------|
| `CONCEPT` | Definitions and explanations |
| `CLAIM` | Factual assertions |
| `DEFINITION` | Term definitions |
| `RELATION` | Relationships between concepts |
| `PROCEDURE` | How-to instructions |

## Quality Guidelines

### Good Claims
- Specific and verifiable
- Include confidence scores
- Have clear provenance
- Link to supporting evidence

### Bad Claims
- Vague or opinion-based
- No source attribution
- Overly confident without evidence
- Circular definitions

## Verification

After adding knowledge:

```bash
# Validate structure
npm run validate

# Rebuild indexes
npm run build

# Test a query
python -m oi_far.cli run "your new concept"

# Run eval suite
python -m oi_far.cli eval
```

## Growth Loop Integration

When OI-FAR encounters unknown queries, it tracks:
- Missing knowledge topics
- Needed sources
- Suggested search terms

Access recommendations:
```bash
python -m oi_far.cli growth
```

This shows what knowledge to add to improve coverage.

## Best Practices

1. **Start with packs**: Use Origin packs for structured knowledge
2. **Validate claims**: Ensure claims are verifiable
3. **Set confidence appropriately**: Lower confidence for uncertain claims
4. **Link concepts**: Use parent/child/related relationships
5. **Add tests**: Include tests that could falsify claims
6. **Tag appropriately**: Use consistent tags for discoverability
7. **Document provenance**: Always cite sources
