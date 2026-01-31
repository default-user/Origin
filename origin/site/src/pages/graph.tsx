/**
 * ORIGIN Medusa UI - Graph Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import { useState } from "react";
import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getGraphNodes, getGraphEdges, getPackById } from "@/lib/data";

export default function Graph() {
  const nodes = getGraphNodes();
  const edges = getGraphEdges();
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const selectedPack = selectedNode ? getPackById(selectedNode) : null;

  const connectedEdges = selectedNode
    ? edges.filter((e) => e.source === selectedNode || e.target === selectedNode)
    : [];

  const connectedNodeIds = new Set(
    connectedEdges.flatMap((e) => [e.source, e.target])
  );

  return (
    <Layout>
      <Head>
        <title>Graph | ORIGIN</title>
      </Head>

      <div className="container">
        <h1 style={{ marginBottom: "1.5rem" }}>Concept Graph</h1>

        <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
          {nodes.length} nodes, {edges.length} edges. Click a node to see details.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "2rem" }}>
          {/* Node Grid */}
          <div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
                gap: "0.5rem",
              }}
            >
              {nodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node.id)}
                  style={{
                    padding: "0.75rem",
                    background:
                      selectedNode === node.id
                        ? "var(--accent-primary)"
                        : connectedNodeIds.has(node.id)
                        ? "var(--bg-tertiary)"
                        : "var(--bg-secondary)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "8px",
                    cursor: "pointer",
                    textAlign: "center",
                    color:
                      selectedNode === node.id ? "#000" : "var(--text-primary)",
                  }}
                >
                  <div style={{ fontWeight: "bold", fontSize: "0.8rem" }}>
                    {node.id}
                  </div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {node.title.split(" ").slice(0, 2).join(" ")}
                  </div>
                </div>
              ))}
            </div>

            {/* Edge List */}
            <h3 style={{ marginTop: "2rem", marginBottom: "1rem" }}>Relationships</h3>
            <div style={{ maxHeight: "300px", overflow: "auto" }}>
              {edges.map((edge, i) => (
                <div
                  key={i}
                  style={{
                    padding: "0.5rem",
                    background:
                      selectedNode &&
                      (edge.source === selectedNode || edge.target === selectedNode)
                        ? "var(--bg-tertiary)"
                        : "transparent",
                    borderRadius: "4px",
                    fontSize: "0.85rem",
                    marginBottom: "0.25rem",
                  }}
                >
                  <span style={{ color: "var(--accent-primary)" }}>
                    {edge.source}
                  </span>
                  <span style={{ margin: "0 0.5rem", color: "var(--text-secondary)" }}>
                    →
                  </span>
                  <span style={{ color: "var(--accent-secondary)" }}>
                    {edge.target}
                  </span>
                  <span
                    style={{
                      marginLeft: "0.5rem",
                      fontSize: "0.75rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    ({edge.type})
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Detail Panel */}
          <div>
            {selectedPack ? (
              <div className="card">
                <h2>{selectedPack.title}</h2>
                <p style={{ marginTop: "0.5rem" }}>{selectedPack.summary}</p>
                <div style={{ marginTop: "1rem" }}>
                  <span className={`status status-${selectedPack.status}`}>
                    {selectedPack.status}
                  </span>
                  <span
                    className={`tier tier-${selectedPack.disclosure_tier}`}
                    style={{ marginLeft: "0.5rem" }}
                  >
                    {selectedPack.disclosure_tier}
                  </span>
                </div>
                <div style={{ marginTop: "1rem" }}>
                  {selectedPack.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
                <Link
                  href={`/concept/${selectedPack.id}`}
                  style={{
                    display: "block",
                    marginTop: "1rem",
                    padding: "0.5rem",
                    background: "var(--accent-primary)",
                    color: "#000",
                    borderRadius: "4px",
                    textAlign: "center",
                  }}
                >
                  View Details →
                </Link>
              </div>
            ) : (
              <div className="card">
                <p style={{ color: "var(--text-secondary)" }}>
                  Click a node to see details
                </p>
              </div>
            )}

            {selectedNode && connectedEdges.length > 0 && (
              <div className="card" style={{ marginTop: "1rem" }}>
                <h3>Connections</h3>
                {connectedEdges.map((edge, i) => {
                  const otherId =
                    edge.source === selectedNode ? edge.target : edge.source;
                  const otherPack = getPackById(otherId);
                  return (
                    <div
                      key={i}
                      style={{
                        padding: "0.5rem 0",
                        borderBottom: "1px solid var(--border-color)",
                      }}
                    >
                      <Link href={`/concept/${otherId}`}>
                        <strong>{otherId}</strong>: {otherPack?.title}
                      </Link>
                      <span
                        style={{
                          marginLeft: "0.5rem",
                          fontSize: "0.75rem",
                          color: "var(--text-secondary)",
                        }}
                      >
                        ({edge.type})
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
