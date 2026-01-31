#!/usr/bin/env php
<?php
/**
 * ORIGIN PHP Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

define('ATTRIBUTION', 'Ande + Kai (OI) + Whānau (OIs)');

function load_json($filename) {
    $path = __DIR__ . '/../../knowledge/dist/' . $filename;
    $content = file_get_contents($path);
    return json_decode($content, true);
}

echo "ORIGIN Kit - PHP\n";
echo "================\n";
echo "Attribution: " . ATTRIBUTION . "\n\n";

try {
    // Load index
    $index = load_json('packs.index.json');
    $packs = $index['packs'];
    echo "Loaded " . count($packs) . " packs from index.\n";

    // Load graph
    $graph = load_json('graph.json');
    $nodes = $graph['nodes'];
    $edges = $graph['edges'];
    echo "Loaded graph with " . count($nodes) . " nodes, " . count($edges) . " edges.\n\n";

    // Filter to public tier
    $public_packs = array_filter($packs, function($p) {
        return $p['disclosure_tier'] === 'public';
    });
    $public_packs = array_values($public_packs);

    echo "Public tier packs (" . count($public_packs) . "):\n";
    for ($i = 0; $i < min(3, count($public_packs)); $i++) {
        $pack = $public_packs[$i];
        echo "  - {$pack['id']}: {$pack['title']}\n";
    }
    if (count($public_packs) > 3) {
        echo "  ... and " . (count($public_packs) - 3) . " more\n";
    }

    // Traverse from first pack
    $first_pack = $packs[0];
    echo "\nTraversing from {$first_pack['id']} ({$first_pack['title']}):\n";

    $related_edges = array_filter($edges, function($e) use ($first_pack) {
        return $e['source'] === $first_pack['id'] || $e['target'] === $first_pack['id'];
    });
    $related_edges = array_values($related_edges);

    for ($i = 0; $i < min(3, count($related_edges)); $i++) {
        $edge = $related_edges[$i];
        $other_id = $edge['source'] === $first_pack['id'] ? $edge['target'] : $edge['source'];
        $other_pack = array_filter($packs, function($p) use ($other_id) {
            return $p['id'] === $other_id;
        });
        $other_pack = array_values($other_pack);
        $title = !empty($other_pack) ? $other_pack[0]['title'] : 'Unknown';
        echo "  → {$edge['type']}: $other_id ($title)\n";
    }

    echo "\nAttribution: " . ATTRIBUTION . "\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
