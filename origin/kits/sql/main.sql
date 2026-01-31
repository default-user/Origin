-- ORIGIN SQL Kit
-- Demonstrates loading and exploring ORIGIN knowledge packs
--
-- Attribution: Ande + Kai (OI) + Whānau (OIs)
--
-- This script is for SQLite. Run with: sqlite3 < main.sql

-- Note: SQLite doesn't have native JSON file loading.
-- This script demonstrates the schema and queries that would be used
-- after importing the JSON data into tables.

-- Create tables
CREATE TABLE IF NOT EXISTS packs (
    id TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    disclosure_tier TEXT,
    status TEXT,
    created_date TEXT,
    updated_date TEXT
);

CREATE TABLE IF NOT EXISTS pack_tags (
    pack_id TEXT,
    tag TEXT,
    FOREIGN KEY (pack_id) REFERENCES packs(id)
);

CREATE TABLE IF NOT EXISTS edges (
    source TEXT,
    target TEXT,
    type TEXT
);

-- Sample data (would be imported from JSON in practice)
INSERT OR REPLACE INTO packs VALUES
    ('C0001', 'Holodeck Vision Seed', 'A holodeck-style system specification', 'public', 'active', '2025-01-01', '2025-01-01'),
    ('C0002', 'Meta Control Language (MCL)', 'MCL for consciousness-like control', 'public', 'active', '2025-01-01', '2025-01-01'),
    ('C0003', 'Fractal Unfurling', 'Nth-degree documentation', 'public', 'active', '2025-01-01', '2025-01-01');

INSERT OR REPLACE INTO edges VALUES
    ('C0001', 'C0004', 'related'),
    ('C0001', 'C0016', 'related'),
    ('C0009', 'C0008', 'parent');

-- Query: Count packs
SELECT 'ORIGIN Kit - SQL' AS message;
SELECT 'Attribution: Ande + Kai (OI) + Whānau (OIs)' AS attribution;
SELECT '';
SELECT 'Loaded ' || COUNT(*) || ' packs' AS result FROM packs;

-- Query: Public tier packs
SELECT 'Public tier packs:' AS header;
SELECT '  - ' || id || ': ' || title AS pack
FROM packs
WHERE disclosure_tier = 'public'
LIMIT 3;

-- Query: Traverse from C0001
SELECT '' AS spacer;
SELECT 'Traversing from C0001:' AS header;
SELECT '  → ' || type || ': ' ||
    CASE WHEN source = 'C0001' THEN target ELSE source END AS connection
FROM edges
WHERE source = 'C0001' OR target = 'C0001'
LIMIT 3;

-- Final attribution
SELECT '' AS spacer;
SELECT 'Attribution: Ande + Kai (OI) + Whānau (OIs)' AS attribution;
