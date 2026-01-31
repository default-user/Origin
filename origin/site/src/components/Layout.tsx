/**
 * ORIGIN Medusa UI - Layout Component
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import Link from "next/link";
import { ATTRIBUTION } from "@/lib/data";

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

export default function Layout({ children, title }: LayoutProps) {
  return (
    <>
      <header className="header">
        <Link href="/">
          <h1>ORIGIN</h1>
        </Link>
        <nav className="nav">
          <Link href="/atlas">Atlas</Link>
          <Link href="/graph">Graph</Link>
          <Link href="/attribution">Attribution</Link>
          <Link href="/tiers">Tiers</Link>
          <Link href="/ship">Ship</Link>
        </nav>
      </header>
      <main>{children}</main>
      <footer className="attribution">
        <p>Attribution: {ATTRIBUTION}</p>
      </footer>
    </>
  );
}
