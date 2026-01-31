// ORIGIN C# Kit
// Demonstrates loading and exploring ORIGIN knowledge packs
//
// Attribution: Ande + Kai (OI) + Whānau (OIs)
//
// To run: dotnet run

using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;

class Program
{
    const string ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)";

    static void Main(string[] args)
    {
        Console.WriteLine("ORIGIN Kit - C#");
        Console.WriteLine("===============");
        Console.WriteLine($"Attribution: {ATTRIBUTION}\n");

        try
        {
            // Load index
            string indexPath = Path.Combine("..", "..", "knowledge", "dist", "packs.index.json");
            string indexContent = File.ReadAllText(indexPath);
            using JsonDocument indexDoc = JsonDocument.Parse(indexContent);

            var packs = indexDoc.RootElement.GetProperty("packs");
            int packCount = packs.GetArrayLength();
            Console.WriteLine($"Loaded {packCount} packs from index.");

            // Load graph
            string graphPath = Path.Combine("..", "..", "knowledge", "dist", "graph.json");
            string graphContent = File.ReadAllText(graphPath);
            using JsonDocument graphDoc = JsonDocument.Parse(graphContent);

            var nodes = graphDoc.RootElement.GetProperty("nodes");
            var edges = graphDoc.RootElement.GetProperty("edges");
            Console.WriteLine($"Loaded graph with {nodes.GetArrayLength()} nodes, {edges.GetArrayLength()} edges.\n");

            // Filter to public tier
            var publicPacks = new List<JsonElement>();
            foreach (var pack in packs.EnumerateArray())
            {
                if (pack.GetProperty("disclosure_tier").GetString() == "public")
                {
                    publicPacks.Add(pack);
                }
            }

            Console.WriteLine($"Public tier packs ({publicPacks.Count}):");
            for (int i = 0; i < Math.Min(3, publicPacks.Count); i++)
            {
                var p = publicPacks[i];
                Console.WriteLine($"  - {p.GetProperty("id")}: {p.GetProperty("title")}");
            }
            if (publicPacks.Count > 3)
            {
                Console.WriteLine($"  ... and {publicPacks.Count - 3} more");
            }

            Console.WriteLine($"\nAttribution: {ATTRIBUTION}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}
