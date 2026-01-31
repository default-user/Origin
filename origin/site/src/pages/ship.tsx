/**
 * ORIGIN Medusa UI - Ship Page (Maturity Lanes)
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getPacks } from "@/lib/data";

export default function Ship() {
  const packs = getPacks();

  const lanes = {
    draft: packs.filter((p) => p.status === "draft"),
    active: packs.filter((p) => p.status === "active"),
    release: packs.filter((p) => p.status === "release"),
  };

  const criteria = [
    { name: "Schema validates", check: (p: any) => true },
    { name: "Falsifiers defined (≥2)", check: (p: any) => (p.tests_or_falsifiers?.length || 0) >= 2 },
    { name: "Attribution present", check: (p: any) => !!p.authorship },
    { name: "Tier assigned", check: (p: any) => !!p.disclosure_tier },
    { name: "Content complete", check: (p: any) => true },
    { name: "Build passes", check: (p: any) => true },
  ];

  return (
    <Layout>
      <Head>
        <title>Ship | ORIGIN</title>
      </Head>

      <div className="container">
        <h1 style={{ marginBottom: "1.5rem" }}>Ship: Maturity Lanes</h1>

        <div className="card">
          <h2>Maturity Journey</h2>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "1rem",
              margin: "2rem 0",
              fontSize: "1.2rem",
            }}
          >
            <span
              style={{
                padding: "0.75rem 1.5rem",
                background: "var(--warning)",
                color: "#000",
                borderRadius: "8px",
              }}
            >
              Draft
            </span>
            <span style={{ color: "var(--text-secondary)" }}>→</span>
            <span
              style={{
                padding: "0.75rem 1.5rem",
                background: "var(--accent-primary)",
                color: "#000",
                borderRadius: "8px",
              }}
            >
              Active
            </span>
            <span style={{ color: "var(--text-secondary)" }}>→</span>
            <span
              style={{
                padding: "0.75rem 1.5rem",
                background: "var(--success)",
                color: "#000",
                borderRadius: "8px",
              }}
            >
              Release
            </span>
          </div>
        </div>

        <div className="lanes" style={{ marginTop: "1.5rem" }}>
          <div className="lane">
            <h3 style={{ background: "var(--warning)", color: "#000" }}>
              Draft ({lanes.draft.length})
            </h3>
            {lanes.draft.length === 0 ? (
              <p style={{ color: "var(--text-secondary)", textAlign: "center" }}>
                No packs in draft
              </p>
            ) : (
              lanes.draft.map((pack) => (
                <Link
                  key={pack.id}
                  href={`/concept/${pack.id}`}
                  style={{ textDecoration: "none" }}
                >
                  <div className="lane-item">
                    <strong>{pack.id}</strong>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {pack.title}
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>

          <div className="lane">
            <h3 style={{ background: "var(--accent-primary)", color: "#000" }}>
              Active ({lanes.active.length})
            </h3>
            {lanes.active.map((pack) => (
              <Link
                key={pack.id}
                href={`/concept/${pack.id}`}
                style={{ textDecoration: "none" }}
              >
                <div className="lane-item">
                  <strong>{pack.id}</strong>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    {pack.title}
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="lane">
            <h3 style={{ background: "var(--success)", color: "#000" }}>
              Release ({lanes.release.length})
            </h3>
            {lanes.release.length === 0 ? (
              <p style={{ color: "var(--text-secondary)", textAlign: "center" }}>
                No packs in release
              </p>
            ) : (
              lanes.release.map((pack) => (
                <Link
                  key={pack.id}
                  href={`/concept/${pack.id}`}
                  style={{ textDecoration: "none" }}
                >
                  <div className="lane-item">
                    <strong>{pack.id}</strong>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {pack.title}
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2>Maturity Criteria</h2>
          <table style={{ width: "100%", marginTop: "1rem" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
                <th style={{ padding: "0.5rem" }}>Criterion</th>
                <th style={{ padding: "0.5rem" }}>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: "0.5rem" }}>Clarity</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  No undefined terms, no mumbo
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Claims</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Explicit, not implied
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Falsifiers</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  At least 2 per concept
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Provenance</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Source documented
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Attribution</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Authorship clear
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Governance</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Tier assigned
                </td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Build/Test</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Passes validation
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
