/**
 * ORIGIN Medusa UI - Atlas Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import { useState } from "react";
import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getPacks, Pack } from "@/lib/data";

export default function Atlas() {
  const allPacks = getPacks();
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const filteredPacks = allPacks.filter((pack) => {
    const matchesSearch =
      search === "" ||
      pack.title.toLowerCase().includes(search.toLowerCase()) ||
      pack.summary.toLowerCase().includes(search.toLowerCase()) ||
      pack.tags.some((t) => t.includes(search.toLowerCase()));

    const matchesTier = tierFilter === null || pack.disclosure_tier === tierFilter;
    const matchesStatus = statusFilter === null || pack.status === statusFilter;

    return matchesSearch && matchesTier && matchesStatus;
  });

  return (
    <Layout>
      <Head>
        <title>Atlas | ORIGIN</title>
      </Head>

      <div className="container">
        <h1 style={{ marginBottom: "1.5rem" }}>Atlas</h1>

        <input
          type="text"
          className="search-box"
          placeholder="Search concepts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <div className="filters">
          <button
            className={`filter-btn ${tierFilter === null ? "active" : ""}`}
            onClick={() => setTierFilter(null)}
          >
            All Tiers
          </button>
          <button
            className={`filter-btn ${tierFilter === "public" ? "active" : ""}`}
            onClick={() => setTierFilter("public")}
          >
            Public
          </button>
          <button
            className={`filter-btn ${tierFilter === "internal" ? "active" : ""}`}
            onClick={() => setTierFilter("internal")}
          >
            Internal
          </button>
          <button
            className={`filter-btn ${tierFilter === "restricted" ? "active" : ""}`}
            onClick={() => setTierFilter("restricted")}
          >
            Restricted
          </button>
        </div>

        <div className="filters">
          <button
            className={`filter-btn ${statusFilter === null ? "active" : ""}`}
            onClick={() => setStatusFilter(null)}
          >
            All Status
          </button>
          <button
            className={`filter-btn ${statusFilter === "draft" ? "active" : ""}`}
            onClick={() => setStatusFilter("draft")}
          >
            Draft
          </button>
          <button
            className={`filter-btn ${statusFilter === "active" ? "active" : ""}`}
            onClick={() => setStatusFilter("active")}
          >
            Active
          </button>
          <button
            className={`filter-btn ${statusFilter === "release" ? "active" : ""}`}
            onClick={() => setStatusFilter("release")}
          >
            Release
          </button>
        </div>

        <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
          Showing {filteredPacks.length} of {allPacks.length} concepts
        </p>

        <div className="grid">
          {filteredPacks.map((pack) => (
            <Link
              key={pack.id}
              href={`/concept/${pack.id}`}
              style={{ textDecoration: "none" }}
            >
              <div className="card">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "0.5rem",
                  }}
                >
                  <span style={{ fontWeight: "bold" }}>{pack.id}</span>
                  <span className={`status status-${pack.status}`}>
                    {pack.status}
                  </span>
                </div>
                <h2>{pack.title}</h2>
                <p>{pack.summary.slice(0, 150)}...</p>
                <div style={{ marginTop: "0.75rem" }}>
                  {pack.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
