/**
 * ORIGIN Medusa UI - Hub Page
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import Head from "next/head";
import Link from "next/link";
import Layout from "@/components/Layout";
import { getPacks, ATTRIBUTION } from "@/lib/data";

export default function Home() {
  const packs = getPacks();
  const publicCount = packs.filter((p) => p.disclosure_tier === "public").length;
  const activeCount = packs.filter((p) => p.status === "active").length;

  const tendrils = [
    {
      href: "/atlas",
      title: "Atlas",
      description: "Browse, search, and filter all concept packs",
    },
    {
      href: "/graph",
      title: "Graph",
      description: "Interactive visualization of concept relationships",
    },
    {
      href: "/attribution",
      title: "Attribution",
      description: "Authorship and provenance tracking",
    },
    {
      href: "/tiers",
      title: "Tiers",
      description: "Disclosure levels and privacy boundaries",
    },
    {
      href: "/ship",
      title: "Ship",
      description: "Maturity lanes: Draft → Active → Release",
    },
  ];

  return (
    <Layout>
      <Head>
        <title>ORIGIN - Seed for Humanity</title>
        <meta
          name="description"
          content="ORIGIN is a canonical knowledge repository with Medusa-style interface"
        />
      </Head>

      <div className="hero">
        <h1>ORIGIN</h1>
        <p>
          A &quot;seed for humanity&quot; repository — mature, fractalised, branching,
          and documented with a Medusa-style interface for exploration.
        </p>
        <p style={{ fontSize: "0.9rem", marginTop: "1rem" }}>
          <strong>{packs.length}</strong> concepts | <strong>{publicCount}</strong>{" "}
          public | <strong>{activeCount}</strong> active
        </p>
      </div>

      <div className="container">
        <h2 style={{ marginBottom: "1rem", textAlign: "center" }}>
          Explore the Tendrils
        </h2>
        <div className="tendril-grid">
          {tendrils.map((tendril) => (
            <Link
              key={tendril.href}
              href={tendril.href}
              style={{ textDecoration: "none" }}
            >
              <div className="tendril-card">
                <h3>{tendril.title}</h3>
                <p>{tendril.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
