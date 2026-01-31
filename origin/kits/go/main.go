// ORIGIN Go Kit
// Demonstrates loading and exploring ORIGIN knowledge packs
//
// Attribution: Ande + Kai (OI) + Whānau (OIs)

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

const ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"

type Pack struct {
	ID             string   `json:"id"`
	Title          string   `json:"title"`
	DisclosureTier string   `json:"disclosure_tier"`
	Related        []string `json:"related"`
}

type PacksIndex struct {
	Metadata struct {
		PackCount int `json:"pack_count"`
	} `json:"metadata"`
	Packs []Pack `json:"packs"`
}

type GraphEdge struct {
	Source string `json:"source"`
	Target string `json:"target"`
	Type   string `json:"type"`
}

type Graph struct {
	Metadata struct {
		NodeCount int `json:"node_count"`
		EdgeCount int `json:"edge_count"`
	} `json:"metadata"`
	Edges []GraphEdge `json:"edges"`
}

func loadJSON(filename string, v interface{}) error {
	basePath, _ := os.Getwd()
	fullPath := filepath.Join(basePath, "..", "..", "knowledge", "dist", filename)
	data, err := os.ReadFile(fullPath)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, v)
}

func main() {
	fmt.Println("ORIGIN Kit - Go")
	fmt.Println("===============")
	fmt.Printf("Attribution: %s\n\n", ATTRIBUTION)

	// Load index
	var index PacksIndex
	if err := loadJSON("packs.index.json", &index); err != nil {
		fmt.Printf("Error loading index: %v\n", err)
		return
	}

	// Load graph
	var graph Graph
	if err := loadJSON("graph.json", &graph); err != nil {
		fmt.Printf("Error loading graph: %v\n", err)
		return
	}

	fmt.Printf("Loaded %d packs from index.\n", len(index.Packs))
	fmt.Printf("Loaded graph with %d nodes, %d edges.\n\n",
		graph.Metadata.NodeCount, graph.Metadata.EdgeCount)

	// Filter to public tier
	var publicPacks []Pack
	for _, p := range index.Packs {
		if p.DisclosureTier == "public" {
			publicPacks = append(publicPacks, p)
		}
	}

	fmt.Printf("Public tier packs (%d):\n", len(publicPacks))
	for i, p := range publicPacks {
		if i >= 3 {
			fmt.Printf("  ... and %d more\n", len(publicPacks)-3)
			break
		}
		fmt.Printf("  - %s: %s\n", p.ID, p.Title)
	}

	// Traverse from first pack
	if len(index.Packs) > 0 {
		first := index.Packs[0]
		fmt.Printf("\nTraversing from %s (%s):\n", first.ID, first.Title)

		count := 0
		for _, edge := range graph.Edges {
			if edge.Source == first.ID || edge.Target == first.ID {
				otherID := edge.Target
				if edge.Source != first.ID {
					otherID = edge.Source
				}
				fmt.Printf("  → %s: %s\n", edge.Type, otherID)
				count++
				if count >= 3 {
					break
				}
			}
		}
	}

	fmt.Printf("\nAttribution: %s\n", ATTRIBUTION)
}
