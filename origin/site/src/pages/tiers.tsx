/**
 * ORIGIN Medusa UI - Tiers Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getPacks } from "@/lib/data";

export default function Tiers() {
  const packs = getPacks();

  const tierGroups = {
    public: packs.filter((p) => p.disclosure_tier === "public"),
    internal: packs.filter((p) => p.disclosure_tier === "internal"),
    restricted: packs.filter((p) => p.disclosure_tier === "restricted"),
  };

  return (
    <Layout>
      <Head>
        <title>Tiers | ORIGIN</title>
      </Head>

      <div className="container">
        <h1 style={{ marginBottom: "1.5rem" }}>Disclosure Tiers</h1>

        <div className="card">
          <h2>Privacy Boundary</h2>
          <p style={{ marginTop: "0.5rem" }}>
            ORIGIN encodes knowledge while strictly excluding &quot;personal personal
            data&quot; (PII). Any accidental personal identifiers are replaced with{" "}
            <code>[[REDACTED]]</code> tokens.
          </p>
        </div>

        <div className="grid" style={{ marginTop: "1.5rem" }}>
          <div className="card">
            <h2>
              <span className="tier tier-public">Public</span>
            </h2>
            <p style={{ margin: "1rem 0" }}>
              <strong>No restrictions.</strong> Content is freely accessible and
              contains no sensitive information.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              {tierGroups.public.length} packs
            </p>
          </div>

          <div className="card">
            <h2>
              <span className="tier tier-internal">Internal</span>
            </h2>
            <p style={{ margin: "1rem 0" }}>
              <strong>Organization-only.</strong> Content is available within the
              organization but not for public distribution.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              {tierGroups.internal.length} packs
            </p>
          </div>

          <div className="card">
            <h2>
              <span className="tier tier-restricted">Restricted</span>
            </h2>
            <p style={{ margin: "1rem 0" }}>
              <strong>Limited access.</strong> Content may reference individuals
              (redacted) or contain sensitive concepts.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              {tierGroups.restricted.length} packs
            </p>
          </div>
        </div>

        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2>Public Tier Packs</h2>
          <div style={{ marginTop: "1rem" }}>
            {tierGroups.public.map((pack) => (
              <Link
                key={pack.id}
                href={`/concept/${pack.id}`}
                style={{ textDecoration: "none" }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "0.75rem",
                    background: "var(--bg-tertiary)",
                    borderRadius: "4px",
                    marginBottom: "0.5rem",
                  }}
                >
                  <span>
                    <strong>{pack.id}</strong>: {pack.title}
                  </span>
                  <span className={`status status-${pack.status}`}>
                    {pack.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2>PII Handling</h2>
          <table style={{ width: "100%", marginTop: "1rem" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
                <th style={{ padding: "0.5rem" }}>Type</th>
                <th style={{ padding: "0.5rem" }}>Examples</th>
                <th style={{ padding: "0.5rem" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: "0.5rem" }}>Private names</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Home addresses, personal phones
                </td>
                <td style={{ padding: "0.5rem", color: "var(--error)" }}>EXCLUDE</td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Identifiers</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  SSN, passport, license numbers
                </td>
                <td style={{ padding: "0.5rem", color: "var(--error)" }}>EXCLUDE</td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Health/Financial</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  Medical records, bank accounts
                </td>
                <td style={{ padding: "0.5rem", color: "var(--error)" }}>EXCLUDE</td>
              </tr>
              <tr>
                <td style={{ padding: "0.5rem" }}>Attribution names</td>
                <td style={{ padding: "0.5rem", color: "var(--text-secondary)" }}>
                  &quot;Ande&quot;, &quot;Kai (OI)&quot;
                </td>
                <td style={{ padding: "0.5rem", color: "var(--success)" }}>INCLUDE</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
