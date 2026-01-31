/**
 * ORIGIN Medusa UI - App Entry
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import type { AppProps } from "next/app";
import "@/styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
