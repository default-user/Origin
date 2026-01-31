/**
 * ORIGIN Java Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 *
 * To run: javac Main.java && java Main
 * (Requires org.json or similar for full JSON parsing)
 */

import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    private static final String ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)";

    public static void main(String[] args) {
        System.out.println("ORIGIN Kit - Java");
        System.out.println("=================");
        System.out.println("Attribution: " + ATTRIBUTION + "\n");

        try {
            // Load index
            String indexPath = "../../knowledge/dist/packs.index.json";
            String indexContent = new String(Files.readAllBytes(Paths.get(indexPath)));

            // Simple count (full parsing requires org.json or Jackson)
            int packCount = countOccurrences(indexContent, "\"id\":");
            System.out.println("Loaded " + packCount + " packs from index.");

            // Load graph
            String graphPath = "../../knowledge/dist/graph.json";
            String graphContent = new String(Files.readAllBytes(Paths.get(graphPath)));

            int nodeCount = countOccurrences(graphContent, "\"id\":");
            int edgeCount = countOccurrences(graphContent, "\"source\":");
            System.out.println("Loaded graph with " + nodeCount + " nodes, " + edgeCount + " edges.\n");

            System.out.println("(Full implementation requires JSON library like org.json or Jackson)");
            System.out.println("\nAttribution: " + ATTRIBUTION);

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }
    }

    private static int countOccurrences(String str, String sub) {
        int count = 0;
        int idx = 0;
        while ((idx = str.indexOf(sub, idx)) != -1) {
            count++;
            idx += sub.length();
        }
        return count;
    }
}
