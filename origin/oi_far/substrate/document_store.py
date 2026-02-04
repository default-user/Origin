"""Document store for raw documents and extracted text."""

import hashlib
import json
import os
from pathlib import Path
from typing import Iterator
import yaml

from .types import Document


class DocumentStore:
    """
    Store for raw documents and extracted text.

    Documents are the raw inputs to the knowledge substrate.
    They are compiled into bricks for structured retrieval.
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize document store.

        Args:
            storage_path: Path to persist documents. If None, in-memory only.
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self._documents: dict[str, Document] = {}
        self._by_hash: dict[str, str] = {}  # content_hash -> doc_id

        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load documents from disk storage."""
        index_path = self.storage_path / "documents.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)
            for doc_data in data.get("documents", []):
                doc = Document.from_dict(doc_data)
                self._documents[doc.id] = doc
                if doc.content_hash:
                    self._by_hash[doc.content_hash] = doc.id

    def _save_to_disk(self) -> None:
        """Save documents to disk storage."""
        if not self.storage_path:
            return
        self.storage_path.mkdir(parents=True, exist_ok=True)
        index_path = self.storage_path / "documents.json"
        data = {
            "version": "1.0",
            "documents": [doc.to_dict() for doc in self._documents.values()],
        }
        with open(index_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def add(self, document: Document) -> str:
        """
        Add a document to the store.

        Returns:
            Document ID
        """
        # Compute hash if not set
        if not document.content_hash:
            document.compute_hash()

        # Check for duplicates by hash
        if document.content_hash in self._by_hash:
            existing_id = self._by_hash[document.content_hash]
            # Return existing ID if content matches
            return existing_id

        self._documents[document.id] = document
        self._by_hash[document.content_hash] = document.id

        if self.storage_path:
            self._save_to_disk()

        return document.id

    def get(self, doc_id: str) -> Document | None:
        """Get document by ID."""
        return self._documents.get(doc_id)

    def get_by_hash(self, content_hash: str) -> Document | None:
        """Get document by content hash."""
        doc_id = self._by_hash.get(content_hash)
        if doc_id:
            return self._documents.get(doc_id)
        return None

    def remove(self, doc_id: str) -> bool:
        """Remove document by ID."""
        if doc_id in self._documents:
            doc = self._documents.pop(doc_id)
            if doc.content_hash in self._by_hash:
                del self._by_hash[doc.content_hash]
            if self.storage_path:
                self._save_to_disk()
            return True
        return False

    def list_all(self) -> list[Document]:
        """List all documents."""
        return list(self._documents.values())

    def count(self) -> int:
        """Count documents in store."""
        return len(self._documents)

    def iterate(self) -> Iterator[Document]:
        """Iterate over all documents."""
        yield from self._documents.values()

    def ingest_file(self, path: str | Path, doc_id: str | None = None) -> Document:
        """
        Ingest a file into the document store.

        Supports: .txt, .md, .yaml, .json
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8")
        extracted = content

        # Extract text based on file type
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            try:
                data = yaml.safe_load(content)
                extracted = self._extract_yaml_text(data)
            except yaml.YAMLError:
                extracted = content
        elif suffix == ".json":
            try:
                data = json.loads(content)
                extracted = self._extract_json_text(data)
            except json.JSONDecodeError:
                extracted = content

        if doc_id is None:
            doc_id = f"doc_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"

        doc = Document(
            id=doc_id,
            title=path.stem,
            source_path=str(path),
            source_type="file",
            content=content,
            extracted_text=extracted,
        )
        doc.compute_hash()

        self.add(doc)
        return doc

    def ingest_pack(self, pack_path: str | Path) -> Document:
        """
        Ingest an Origin concept pack.

        Extracts structured content from pack.yaml and content.mdx
        """
        pack_path = Path(pack_path)

        # Load pack.yaml
        pack_yaml = pack_path / "pack.yaml"
        if not pack_yaml.exists():
            raise FileNotFoundError(f"pack.yaml not found in {pack_path}")

        with open(pack_yaml) as f:
            pack_data = yaml.safe_load(f)

        # Extract text from pack
        extracted_parts = []

        # Title and summary
        extracted_parts.append(f"# {pack_data.get('title', 'Untitled')}")
        if pack_data.get("summary"):
            extracted_parts.append(pack_data["summary"])

        # Claims
        for claim in pack_data.get("claims", []):
            if isinstance(claim, dict):
                extracted_parts.append(f"- {claim.get('text', str(claim))}")
            else:
                extracted_parts.append(f"- {claim}")

        # Load content.mdx if exists
        content_mdx = pack_path / "content.mdx"
        if content_mdx.exists():
            extracted_parts.append(content_mdx.read_text(encoding="utf-8"))

        content = yaml.dump(pack_data, default_flow_style=False)
        extracted = "\n\n".join(extracted_parts)

        doc = Document(
            id=f"pack_{pack_data.get('id', pack_path.name)}",
            title=pack_data.get("title", pack_path.name),
            source_path=str(pack_path),
            source_type="pack",
            content=content,
            extracted_text=extracted,
            metadata=pack_data,
        )
        doc.compute_hash()

        self.add(doc)
        return doc

    def _extract_yaml_text(self, data: dict | list, prefix: str = "") -> str:
        """Recursively extract text from YAML data."""
        parts = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    parts.append(f"{key}: {value}")
                elif isinstance(value, (dict, list)):
                    parts.append(self._extract_yaml_text(value, f"{prefix}{key}."))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    parts.append(f"- {item}")
                elif isinstance(item, dict):
                    parts.append(self._extract_yaml_text(item, prefix))
        return "\n".join(parts)

    def _extract_json_text(self, data: dict | list) -> str:
        """Extract text from JSON data."""
        return self._extract_yaml_text(data)

    def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._by_hash.clear()
        if self.storage_path:
            self._save_to_disk()
