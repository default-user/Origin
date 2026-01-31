/**
 * ORIGIN Data Loading Utilities
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import packsIndex from "../../../knowledge/dist/packs.index.json";
import graphData from "../../../knowledge/dist/graph.json";

export interface Pack {
  id: string;
  title: string;
  summary: string;
  authorship: string;
  disclosure_tier: string;
  tags: string[];
  created_date: string;
  updated_date: string;
  status: string;
  parents: string[];
  children: string[];
  related: string[];
  claims: string[];
  tests_or_falsifiers: Array<{
    name: string;
    description: string;
    falsification_condition: string;
  }>;
  slug: string;
  path: string;
}

export interface GraphNode {
  id: string;
  title: string;
  summary: string;
  status: string;
  tier: string;
  tags: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "parent" | "child" | "related";
}

export function getPacks(): Pack[] {
  return (packsIndex as any).packs;
}

export function getPackById(id: string): Pack | undefined {
  return getPacks().find((p) => p.id === id);
}

export function getPackBySlug(slug: string): Pack | undefined {
  return getPacks().find((p) => p.slug === slug);
}

export function getGraphNodes(): GraphNode[] {
  return (graphData as any).nodes;
}

export function getGraphEdges(): GraphEdge[] {
  return (graphData as any).edges;
}

export function filterPacksByTier(tier: string): Pack[] {
  return getPacks().filter((p) => p.disclosure_tier === tier);
}

export function filterPacksByStatus(status: string): Pack[] {
  return getPacks().filter((p) => p.status === status);
}

export function filterPacksByTag(tag: string): Pack[] {
  return getPacks().filter((p) => p.tags.includes(tag));
}

export function searchPacks(query: string): Pack[] {
  const lowerQuery = query.toLowerCase();
  return getPacks().filter(
    (p) =>
      p.title.toLowerCase().includes(lowerQuery) ||
      p.summary.toLowerCase().includes(lowerQuery) ||
      p.tags.some((t) => t.includes(lowerQuery))
  );
}

export function getRelatedPacks(packId: string): Pack[] {
  const pack = getPackById(packId);
  if (!pack) return [];

  const relatedIds = [
    ...(pack.parents || []),
    ...(pack.children || []),
    ...(pack.related || []),
  ];

  return relatedIds
    .map((id) => getPackById(id))
    .filter((p): p is Pack => p !== undefined);
}

export const ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)";
