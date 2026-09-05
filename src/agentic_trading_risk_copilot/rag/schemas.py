from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    document_type: str
    title: str
    section: str
    risk_domain: str
    version: str
    effective_from: str
    status: str
    jurisdiction: str
    owner: str
    synthetic: bool
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> KnowledgeChunk:
        return cls(**value)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float

    def trace_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "document_id": self.chunk.document_id,
            "title": self.chunk.title,
            "section": self.chunk.section,
            "risk_domain": self.chunk.risk_domain,
            "score": round(self.score, 6),
        }
