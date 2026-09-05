from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .embeddings import E5EmbeddingModel
from .knowledge import ChunkingConfig, load_and_chunk_knowledge_base
from .schemas import KnowledgeChunk, RetrievedChunk


class RAGDependencyError(RuntimeError):
    """Raised when optional RAG dependencies are unavailable."""


class FaissKnowledgeIndex:
    """Exact cosine retrieval backed by normalized vectors and FAISS IndexFlatIP."""

    INDEX_FILE = "index.faiss"
    CHUNKS_FILE = "chunks.json"
    MANIFEST_FILE = "manifest.json"

    def __init__(self, index: Any, chunks: list[KnowledgeChunk], embedder: E5EmbeddingModel, manifest: dict[str, object]):
        self.index = index
        self.chunks = chunks
        self.embedder = embedder
        self.manifest = manifest

    @classmethod
    def build(
        cls,
        knowledge_dir: Path,
        index_dir: Path,
        *,
        model_name: str = "intfloat/multilingual-e5-small",
        chunking: ChunkingConfig = ChunkingConfig(),
    ) -> FaissKnowledgeIndex:
        faiss = _import_faiss()
        chunks = load_and_chunk_knowledge_base(knowledge_dir, chunking)
        embedder = E5EmbeddingModel(model_name)
        vectors = embedder.embed_documents([chunk.content for chunk in chunks])
        index = faiss.IndexFlatIP(int(vectors.shape[1]))
        index.add(vectors)
        manifest: dict[str, object] = {
            "schema_version": 1,
            "index_type": "IndexFlatIP",
            "similarity": "cosine_via_normalized_inner_product",
            "embedding_model": model_name,
            "embedding_dimension": int(vectors.shape[1]),
            "chunk_size": chunking.chunk_size,
            "chunk_overlap": chunking.chunk_overlap,
            "document_count": len({chunk.document_id for chunk in chunks}),
            "chunk_count": len(chunks),
            "knowledge_sha256": _knowledge_sha256(knowledge_dir),
        }
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(index_dir / cls.INDEX_FILE))
        (index_dir / cls.CHUNKS_FILE).write_text(
            json.dumps([chunk.to_dict() for chunk in chunks], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (index_dir / cls.MANIFEST_FILE).write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        return cls(index=index, chunks=chunks, embedder=embedder, manifest=manifest)

    @classmethod
    def load(cls, index_dir: Path) -> FaissKnowledgeIndex:
        faiss = _import_faiss()
        required = [index_dir / cls.INDEX_FILE, index_dir / cls.CHUNKS_FILE, index_dir / cls.MANIFEST_FILE]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError("RAG index is incomplete; missing: " + ", ".join(missing))
        chunks = [
            KnowledgeChunk.from_dict(item)
            for item in json.loads((index_dir / cls.CHUNKS_FILE).read_text(encoding="utf-8"))
        ]
        manifest = json.loads((index_dir / cls.MANIFEST_FILE).read_text(encoding="utf-8"))
        index = faiss.read_index(str(index_dir / cls.INDEX_FILE))
        if index.ntotal != len(chunks):
            raise ValueError("FAISS vector count does not match chunk metadata count")
        embedder = E5EmbeddingModel(str(manifest["embedding_model"]), local_files_only=True)
        return cls(index=index, chunks=chunks, embedder=embedder, manifest=manifest)

    def search(
        self,
        query: str,
        *,
        top_k: int = 4,
        risk_domain: str | None = None,
        status: str = "active",
        jurisdiction: str = "global",
        effective_at: str | None = None,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query_vector = self.embedder.embed_query(query).reshape(1, -1)
        candidate_count = len(self.chunks)
        scores, indexes = self.index.search(query_vector, candidate_count)
        cutoff_date = effective_at or date.today().isoformat()
        results: list[RetrievedChunk] = []
        for score, index_position in zip(scores[0], indexes[0]):
            if index_position < 0:
                continue
            chunk = self.chunks[int(index_position)]
            if risk_domain is not None and chunk.risk_domain != risk_domain:
                continue
            if status and chunk.status != status:
                continue
            if jurisdiction and chunk.jurisdiction not in {jurisdiction, "global"}:
                continue
            if chunk.effective_from > cutoff_date:
                continue
            if float(score) < min_score:
                continue
            results.append(RetrievedChunk(chunk=chunk, score=float(score)))
            if len(results) == top_k:
                break
        return results


def _import_faiss() -> Any:
    try:
        import faiss
    except ImportError as exc:
        raise RAGDependencyError("faiss-cpu is missing. Install the project with: pip install -e '.[rag]'") from exc
    return faiss


def _knowledge_sha256(knowledge_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(knowledge_dir.rglob("*.md")):
        digest.update(str(path.relative_to(knowledge_dir)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
