"""BM25 lexical index for deterministic text retrieval."""

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from ..types import Brick, Claim


@dataclass
class LexicalHit:
    """A hit from lexical search."""
    brick_id: str
    score: float
    matched_terms: list[str]
    field: str  # "title", "summary", "claim"
    claim_id: str | None = None


class LexicalIndex:
    """
    BM25-based lexical index for deterministic retrieval.

    This implements the Okapi BM25 ranking function with fixed parameters
    for deterministic scoring.
    """

    # BM25 parameters (fixed for determinism)
    K1 = 1.2
    B = 0.75

    def __init__(self, storage_path: str | None = None):
        """
        Initialize lexical index.

        Args:
            storage_path: Path to persist index. If None, in-memory only.
        """
        self.storage_path = Path(storage_path) if storage_path else None

        # Inverted index: term -> [(brick_id, field, term_freq, claim_id)]
        self._inverted: dict[str, list[tuple[str, str, int, str | None]]] = defaultdict(list)

        # Document lengths: (brick_id, field) -> length
        self._doc_lengths: dict[tuple[str, str], int] = {}

        # Average document length per field
        self._avg_lengths: dict[str, float] = {}

        # Total documents
        self._num_docs = 0

        # IDF cache
        self._idf_cache: dict[str, float] = {}

        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load index from disk."""
        index_path = self.storage_path / "lexical.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)

            self._inverted = defaultdict(list)
            for term, postings in data.get("inverted", {}).items():
                self._inverted[term] = [
                    (p["brick_id"], p["field"], p["tf"], p.get("claim_id"))
                    for p in postings
                ]

            self._doc_lengths = {
                (d["brick_id"], d["field"]): d["length"]
                for d in data.get("doc_lengths", [])
            }
            self._avg_lengths = data.get("avg_lengths", {})
            self._num_docs = data.get("num_docs", 0)
            self._rebuild_idf_cache()

    def _save_to_disk(self) -> None:
        """Save index to disk."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        index_path = self.storage_path / "lexical.json"

        data = {
            "version": "1.0",
            "inverted": {
                term: [
                    {"brick_id": p[0], "field": p[1], "tf": p[2], "claim_id": p[3]}
                    for p in postings
                ]
                for term, postings in self._inverted.items()
            },
            "doc_lengths": [
                {"brick_id": k[0], "field": k[1], "length": v}
                for k, v in self._doc_lengths.items()
            ],
            "avg_lengths": self._avg_lengths,
            "num_docs": self._num_docs,
        }

        with open(index_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into terms.

        Deterministic: same text always produces same tokens in same order.
        """
        # Lowercase
        text = text.lower()

        # Remove punctuation except hyphens within words
        text = re.sub(r"[^\w\s\-]", " ", text)

        # Split on whitespace
        tokens = text.split()

        # Filter short tokens and stopwords
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because",
            "until", "while", "this", "that", "these", "those", "it",
        }

        filtered = [t for t in tokens if len(t) >= 2 and t not in stopwords]
        return filtered

    def _rebuild_idf_cache(self) -> None:
        """Rebuild IDF cache for all terms."""
        self._idf_cache.clear()
        for term in self._inverted:
            df = len(set(p[0] for p in self._inverted[term]))
            self._idf_cache[term] = self._compute_idf(df)

    def _compute_idf(self, df: int) -> float:
        """Compute IDF for a term with document frequency df."""
        if df == 0 or self._num_docs == 0:
            return 0.0
        return math.log((self._num_docs - df + 0.5) / (df + 0.5) + 1.0)

    def _compute_avg_lengths(self) -> None:
        """Compute average document lengths per field."""
        field_totals: dict[str, int] = defaultdict(int)
        field_counts: dict[str, int] = defaultdict(int)

        for (brick_id, field), length in self._doc_lengths.items():
            field_totals[field] += length
            field_counts[field] += 1

        self._avg_lengths = {
            field: field_totals[field] / field_counts[field]
            for field in field_counts
            if field_counts[field] > 0
        }

    def index_brick(self, brick: Brick) -> None:
        """
        Index a brick for lexical search.

        Indexes: title, summary, claims
        """
        # Remove old entries for this brick
        self._remove_brick(brick.id)

        # Index title
        self._index_text(brick.id, "title", brick.title, None)

        # Index summary
        self._index_text(brick.id, "summary", brick.summary, None)

        # Index claims
        for claim in brick.claims:
            self._index_text(brick.id, "claim", claim.text, claim.id)

        self._num_docs += 1
        self._compute_avg_lengths()
        self._rebuild_idf_cache()

    def _index_text(
        self,
        brick_id: str,
        field: str,
        text: str,
        claim_id: str | None,
    ) -> None:
        """Index a single text field."""
        tokens = self._tokenize(text)
        if not tokens:
            return

        # Count term frequencies
        term_counts: dict[str, int] = defaultdict(int)
        for token in tokens:
            term_counts[token] += 1

        # Add to inverted index
        for term, tf in term_counts.items():
            self._inverted[term].append((brick_id, field, tf, claim_id))

        # Record document length
        self._doc_lengths[(brick_id, field)] = len(tokens)

    def _remove_brick(self, brick_id: str) -> None:
        """Remove all entries for a brick."""
        # Remove from inverted index
        for term in list(self._inverted.keys()):
            self._inverted[term] = [
                p for p in self._inverted[term]
                if p[0] != brick_id
            ]
            if not self._inverted[term]:
                del self._inverted[term]

        # Remove from doc lengths
        keys_to_remove = [k for k in self._doc_lengths if k[0] == brick_id]
        for k in keys_to_remove:
            del self._doc_lengths[k]

    def search(
        self,
        query: str,
        top_k: int = 10,
        field_filter: str | None = None,
    ) -> list[LexicalHit]:
        """
        Search for bricks matching query.

        Args:
            query: Search query
            top_k: Maximum results to return
            field_filter: Optional filter by field ("title", "summary", "claim")

        Returns:
            List of LexicalHit sorted by score descending
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Accumulate scores per (brick_id, field, claim_id)
        scores: dict[tuple[str, str, str | None], tuple[float, list[str]]] = {}

        for term in tokens:
            if term not in self._inverted:
                continue

            idf = self._idf_cache.get(term, 0.0)

            for brick_id, field, tf, claim_id in self._inverted[term]:
                if field_filter and field != field_filter:
                    continue

                # Get document length
                doc_len = self._doc_lengths.get((brick_id, field), 1)
                avg_len = self._avg_lengths.get(field, 1.0)

                # BM25 score
                numerator = tf * (self.K1 + 1)
                denominator = tf + self.K1 * (1 - self.B + self.B * doc_len / avg_len)
                score = idf * numerator / denominator

                key = (brick_id, field, claim_id)
                if key not in scores:
                    scores[key] = (0.0, [])

                current_score, matched = scores[key]
                scores[key] = (current_score + score, matched + [term])

        # Convert to hits
        hits = []
        for (brick_id, field, claim_id), (score, matched) in scores.items():
            hits.append(LexicalHit(
                brick_id=brick_id,
                score=score,
                matched_terms=list(set(matched)),
                field=field,
                claim_id=claim_id,
            ))

        # Sort by score descending (deterministic for equal scores)
        hits.sort(key=lambda h: (-h.score, h.brick_id, h.field))

        return hits[:top_k]

    def index_all(self, bricks: Iterator[Brick]) -> int:
        """
        Index all bricks.

        Returns count of bricks indexed.
        """
        count = 0
        for brick in bricks:
            self.index_brick(brick)
            count += 1

        if self.storage_path:
            self._save_to_disk()

        return count

    def clear(self) -> None:
        """Clear the index."""
        self._inverted.clear()
        self._doc_lengths.clear()
        self._avg_lengths.clear()
        self._num_docs = 0
        self._idf_cache.clear()

        if self.storage_path:
            self._save_to_disk()

    def stats(self) -> dict:
        """Get index statistics."""
        return {
            "num_docs": self._num_docs,
            "num_terms": len(self._inverted),
            "num_postings": sum(len(p) for p in self._inverted.values()),
            "avg_lengths": self._avg_lengths,
        }
