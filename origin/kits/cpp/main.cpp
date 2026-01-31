/**
 * ORIGIN C++ Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 *
 * To compile: g++ -std=c++17 main.cpp -o origin_kit
 * To run: ./origin_kit
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

const std::string ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)";

int countOccurrences(const std::string& str, const std::string& sub) {
    int count = 0;
    size_t pos = 0;
    while ((pos = str.find(sub, pos)) != std::string::npos) {
        count++;
        pos += sub.length();
    }
    return count;
}

std::string readFile(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + path);
    }
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

int main() {
    std::cout << "ORIGIN Kit - C++" << std::endl;
    std::cout << "=================" << std::endl;
    std::cout << "Attribution: " << ATTRIBUTION << std::endl << std::endl;

    try {
        // Load index
        std::string indexContent = readFile("../../knowledge/dist/packs.index.json");
        int packCount = countOccurrences(indexContent, "\"id\":");
        std::cout << "Loaded " << packCount << " packs from index." << std::endl;

        // Load graph
        std::string graphContent = readFile("../../knowledge/dist/graph.json");
        int nodeCount = countOccurrences(graphContent, "\"id\":");
        int edgeCount = countOccurrences(graphContent, "\"source\":");
        std::cout << "Loaded graph with " << nodeCount << " nodes, "
                  << edgeCount << " edges." << std::endl << std::endl;

        std::cout << "(Full JSON parsing requires nlohmann/json or similar library)" << std::endl;
        std::cout << std::endl << "Attribution: " << ATTRIBUTION << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
