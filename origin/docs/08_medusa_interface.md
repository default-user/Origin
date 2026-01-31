# Medusa Interface Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

The Medusa Interface is a UI pattern where a central hub ("head") fans out into multiple exploration tendrils ("snakes"). Each tendril provides a different view of the same corpus: atlas, graph, timeline, build-spec, tests, exports.

---

## Level 1: Core Concept

### 1.1 The Medusa Metaphor

```
                    ┌─────────┐
         ┌──────────┤   HUB   ├──────────┐
         │          │ (HEAD)  │          │
         │          └────┬────┘          │
         │               │               │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │  Atlas  │    │  Graph  │    │Timeline │
    │ Tendril │    │ Tendril │    │ Tendril │
    └─────────┘    └─────────┘    └─────────┘
         │               │               │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │  Tiers  │    │  Ship   │    │ Attrib  │
    │ Tendril │    │ Tendril │    │ Tendril │
    └─────────┘    └─────────┘    └─────────┘
```

### 1.2 Hub (Head)

The central hub provides:
- Overview of ORIGIN
- Navigation to all tendrils
- Key metrics and status
- Entry point for exploration

### 1.3 Tendrils (Snakes)

Each tendril is a specialized explorer:

| Tendril | Purpose |
|---------|---------|
| Atlas | Browse, search, filter packs by tags/tier/status |
| Graph | Interactive node graph visualization |
| Timeline | Temporal view of concept creation/updates |
| Attribution | Authorship and provenance explorer |
| Tiers | Disclosure levels and privacy boundaries |
| Ship | Maturity lanes: Draft → Active → Release |

---

## Level 2: Interface Specification

### 2.1 Page Structure

```
/                    → Hub (index.tsx)
/atlas               → Atlas tendril
/graph               → Graph tendril
/timeline            → Timeline tendril (optional)
/attribution         → Attribution tendril
/tiers               → Tiers tendril
/ship                → Ship tendril
/concept/[id]        → Individual concept view
```

### 2.2 Hub Page (index.tsx)

Content:
- ORIGIN title and tagline
- Attribution line
- Pack count and status summary
- Tendril navigation cards
- Quick search

### 2.3 Atlas Page (atlas.tsx)

Features:
- List/grid view of all packs
- Filter by:
  - Tags
  - Disclosure tier (public, internal, restricted)
  - Status (draft, active, release)
- Search by title, summary, content
- Sort by date, title, status

Data source: `knowledge/dist/packs.index.json`

### 2.4 Graph Page (graph.tsx)

Features:
- Interactive node graph
- Nodes = concepts
- Edges = parent/child/related links
- Click node → concept detail panel
- Zoom, pan, filter

Data source: `knowledge/dist/graph.json`

### 2.5 Attribution Page (attribution.tsx)

Content:
- Default attribution line
- Per-pack attribution overrides (if any)
- Provenance tracking
- Authorship explanation

Data source: `knowledge/dist/packs.index.json` (authorship fields)

### 2.6 Tiers Page (tiers.tsx)

Content:
- Explanation of disclosure tiers
- Tier definitions:
  - **Public**: No restrictions
  - **Internal**: Organization-only
  - **Restricted**: Limited access
- Pack counts per tier
- Privacy boundary explanation
- PII handling policy

### 2.7 Ship Page (ship.tsx)

Content:
- Maturity lane visualization:

```
DRAFT          ACTIVE         RELEASE
┌─────────┐    ┌─────────┐    ┌─────────┐
│ C0001   │    │         │    │         │
│ C0002   │ ──►│ C0003   │ ──►│ C0007   │
│ ...     │    │ C0004   │    │ ...     │
└─────────┘    └─────────┘    └─────────┘
```

- Pack progress checklists:
  - [ ] Schema validates
  - [ ] Falsifiers defined (≥2)
  - [ ] Attribution present
  - [ ] Tier assigned
  - [ ] Content complete

### 2.8 Concept Page (concept/[id].tsx)

Content:
- Pack metadata (from pack.yaml)
- Rendered content (from content.mdx)
- Claims list
- Falsifiers/tests
- Related concepts (links)
- Parent/child navigation
- Attribution

---

## Level 3: Technical Implementation

### 3.1 Technology Stack

```
Next.js 14+
├── TypeScript
├── React 18+
├── Tailwind CSS (optional)
└── Static generation (SSG preferred)
```

### 3.2 Data Flow

```
knowledge/dist/*.json
        │
        ▼
    Site Build
        │
        ▼
   Static Pages
        │
        ▼
    Served UI
```

The UI reads ONLY from `knowledge/dist/*.json` — never directly from pack sources.

### 3.3 Graph Visualization

Options:
- D3.js force-directed graph
- Cytoscape.js
- React Flow

Requirements:
- Responsive
- Interactive (zoom, pan, click)
- Performant with 20+ nodes

### 3.4 Search Implementation

From `knowledge/dist/search.json`:
- Client-side search (no server required)
- Tokenized index
- Fuzzy matching optional

---

## Level 4: Falsifiers

| Test | Description | Falsification |
|------|-------------|---------------|
| Hub reachable | Index page loads | 404 or error |
| All tendrils work | Each tendril page loads | Any tendril fails |
| Graph interactive | Nodes clickable, zoomable | Interaction fails |
| Search functional | Queries return results | Search broken |
| Concept pages render | All concepts viewable | Any concept fails |
| Data consistency | UI matches dist files | Mismatch found |

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
