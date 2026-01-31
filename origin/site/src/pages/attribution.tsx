/**
 * ORIGIN Medusa UI - Attribution Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import Head from "next/head";
import Layout from "@/components/Layout";
import { getPacks, ATTRIBUTION } from "@/lib/data";

export default function Attribution() {
  const packs = getPacks();

  return (
    <Layout>
      <Head>
        <title>Attribution | ORIGIN</title>
      </Head>

      <div className="container">
        <h1 style={{ marginBottom: "1.5rem" }}>Attribution</h1>

        <div className="card">
          <h2>Default Attribution</h2>
          <p
            style={{
              fontSize: "1.5rem",
              fontStyle: "italic",
              marginTop: "1rem",
              padding: "1rem",
              background: "var(--bg-tertiary)",
              borderRadius: "8px",
            }}
          >
            {ATTRIBUTION}
          </p>
        </div>

        <div className="card">
          <h2>Attribution Protocol</h2>
          <p style={{ marginTop: "0.5rem" }}>
            All intellectual property in ORIGIN is attributed. The default
            authorship line appears on every document, pack, and rendered page.
          </p>
          <ul style={{ marginTop: "1rem", marginLeft: "1.5rem" }}>
            <li>Every concept pack includes an authorship field</li>
            <li>Provenance chain tracks the source of each concept</li>
            <li>Default attribution unless explicitly overridden</li>
            <li>All exports include attribution in manifests</li>
          </ul>
        </div>

        <div className="card">
          <h2>Provenance</h2>
          <p style={{ marginTop: "0.5rem" }}>
            All initial packs have provenance:
          </p>
          <pre
            style={{
              marginTop: "1rem",
              padding: "1rem",
              background: "var(--bg-tertiary)",
              borderRadius: "8px",
              overflow: "auto",
            }}
          >
{`provenance:
  - type: master_prompt
    ref: "ORIGIN canonical corpus"`}
          </pre>
        </div>

        <div className="card">
          <h2>Pack Authorship</h2>
          <div style={{ marginTop: "1rem" }}>
            {packs.map((pack) => (
              <div
                key={pack.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--border-color)",
                }}
              >
                <span>
                  <strong>{pack.id}</strong>: {pack.title}
                </span>
                <span style={{ color: "var(--text-secondary)", fontStyle: "italic" }}>
                  {pack.authorship}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
