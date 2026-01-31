/**
 * ORIGIN Medusa UI - Concept Detail Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import { useRouter } from "next/router";
import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getPacks, getPackById, getRelatedPacks } from "@/lib/data";

export default function ConceptPage() {
  const router = useRouter();
  const { id } = router.query;

  const pack = id ? getPackById(id as string) : null;
  const relatedPacks = pack ? getRelatedPacks(pack.id) : [];

  if (!pack) {
    return (
      <Layout>
        <div className="container">
          <h1>Concept Not Found</h1>
          <p>The concept {id} was not found.</p>
          <Link href="/atlas">← Back to Atlas</Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <Head>
        <title>{pack.id}: {pack.title} | ORIGIN</title>
      </Head>

      <div className="container">
        <Link href="/atlas" style={{ color: "var(--text-secondary)" }}>
          ← Back to Atlas
        </Link>

        <div style={{ marginTop: "1rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <h1>
              {pack.id}: {pack.title}
            </h1>
            <div>
              <span className={`status status-${pack.status}`}>{pack.status}</span>
              <span
                className={`tier tier-${pack.disclosure_tier}`}
                style={{ marginLeft: "0.5rem" }}
              >
                {pack.disclosure_tier}
              </span>
            </div>
          </div>

          <p
            style={{
              fontSize: "1.1rem",
              marginTop: "1rem",
              color: "var(--text-secondary)",
            }}
          >
            {pack.summary}
          </p>

          <div style={{ marginTop: "1rem" }}>
            {pack.tags.map((tag) => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="grid" style={{ marginTop: "2rem" }}>
          <div>
            <div className="card">
              <h2>Attribution</h2>
              <p style={{ marginTop: "0.5rem", fontStyle: "italic" }}>
                {pack.authorship}
              </p>
            </div>

            <div className="card">
              <h2>Claims</h2>
              <div style={{ marginTop: "0.5rem" }}>
                {pack.claims && pack.claims.length > 0 ? (
                  pack.claims.map((claim, i) => (
                    <div key={i} className="claim">
                      {claim}
                    </div>
                  ))
                ) : (
                  <p style={{ color: "var(--text-secondary)" }}>No claims listed</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2>Falsifiers / Tests</h2>
              <div style={{ marginTop: "0.5rem" }}>
                {pack.tests_or_falsifiers && pack.tests_or_falsifiers.length > 0 ? (
                  pack.tests_or_falsifiers.map((test, i) => (
                    <div key={i} className="falsifier">
                      <h4>{test.name}</h4>
                      <p>{test.description}</p>
                      <p style={{ marginTop: "0.5rem", color: "var(--error)" }}>
                        <strong>Falsification:</strong> {test.falsification_condition}
                      </p>
                    </div>
                  ))
                ) : (
                  <p style={{ color: "var(--text-secondary)" }}>No tests listed</p>
                )}
              </div>
            </div>
          </div>

          <div>
            <div className="card">
              <h2>Metadata</h2>
              <table style={{ width: "100%", marginTop: "0.5rem" }}>
                <tbody>
                  <tr>
                    <td style={{ padding: "0.25rem 0", color: "var(--text-secondary)" }}>
                      Created
                    </td>
                    <td style={{ padding: "0.25rem 0" }}>{pack.created_date}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: "0.25rem 0", color: "var(--text-secondary)" }}>
                      Updated
                    </td>
                    <td style={{ padding: "0.25rem 0" }}>{pack.updated_date}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: "0.25rem 0", color: "var(--text-secondary)" }}>
                      Path
                    </td>
                    <td style={{ padding: "0.25rem 0", fontFamily: "monospace", fontSize: "0.85rem" }}>
                      {pack.path}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="card">
              <h2>Related Concepts</h2>
              <div style={{ marginTop: "0.5rem" }}>
                {relatedPacks.length > 0 ? (
                  relatedPacks.map((related) => (
                    <Link
                      key={related.id}
                      href={`/concept/${related.id}`}
                      style={{ textDecoration: "none" }}
                    >
                      <div
                        style={{
                          padding: "0.5rem",
                          background: "var(--bg-tertiary)",
                          borderRadius: "4px",
                          marginBottom: "0.5rem",
                        }}
                      >
                        <strong>{related.id}</strong>: {related.title}
                      </div>
                    </Link>
                  ))
                ) : (
                  <p style={{ color: "var(--text-secondary)" }}>No related concepts</p>
                )}
              </div>
            </div>

            {pack.parents && pack.parents.length > 0 && (
              <div className="card">
                <h2>Parents</h2>
                <div style={{ marginTop: "0.5rem" }}>
                  {pack.parents.map((parentId) => {
                    const parent = getPackById(parentId);
                    return (
                      <Link
                        key={parentId}
                        href={`/concept/${parentId}`}
                        style={{ textDecoration: "none" }}
                      >
                        <div
                          style={{
                            padding: "0.5rem",
                            background: "var(--bg-tertiary)",
                            borderRadius: "4px",
                            marginBottom: "0.5rem",
                          }}
                        >
                          <strong>{parentId}</strong>: {parent?.title || "Unknown"}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {pack.children && pack.children.length > 0 && (
              <div className="card">
                <h2>Children</h2>
                <div style={{ marginTop: "0.5rem" }}>
                  {pack.children.map((childId) => {
                    const child = getPackById(childId);
                    return (
                      <Link
                        key={childId}
                        href={`/concept/${childId}`}
                        style={{ textDecoration: "none" }}
                      >
                        <div
                          style={{
                            padding: "0.5rem",
                            background: "var(--bg-tertiary)",
                            borderRadius: "4px",
                            marginBottom: "0.5rem",
                          }}
                        >
                          <strong>{childId}</strong>: {child?.title || "Unknown"}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

export async function getStaticPaths() {
  const packs = getPacks();
  const paths = packs.map((pack) => ({
    params: { id: pack.id },
  }));

  return { paths, fallback: false };
}

export async function getStaticProps({ params }: { params: { id: string } }) {
  return { props: {} };
}
