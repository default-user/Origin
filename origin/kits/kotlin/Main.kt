/**
 * ORIGIN Kotlin Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 *
 * To run: kotlinc Main.kt -include-runtime -d origin_kit.jar && java -jar origin_kit.jar
 */

import java.io.File

const val ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"

fun countOccurrences(str: String, sub: String): Int {
    var count = 0
    var idx = 0
    while (str.indexOf(sub, idx).also { idx = it } != -1) {
        count++
        idx += sub.length
    }
    return count
}

fun main() {
    println("ORIGIN Kit - Kotlin")
    println("===================")
    println("Attribution: $ATTRIBUTION\n")

    try {
        // Load index
        val indexContent = File("../../knowledge/dist/packs.index.json").readText()
        val packCount = countOccurrences(indexContent, "\"id\":")
        println("Loaded $packCount packs from index.")

        // Load graph
        val graphContent = File("../../knowledge/dist/graph.json").readText()
        val nodeCount = countOccurrences(graphContent, "\"id\":")
        val edgeCount = countOccurrences(graphContent, "\"source\":")
        println("Loaded graph with $nodeCount nodes, $edgeCount edges.\n")

        println("(Full JSON parsing requires kotlinx.serialization or Gson)")
        println("\nAttribution: $ATTRIBUTION")

    } catch (e: Exception) {
        println("Error: ${e.message}")
    }
}
