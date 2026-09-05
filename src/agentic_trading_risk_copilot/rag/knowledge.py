from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schemas import KnowledgeChunk


class KnowledgeBaseError(RuntimeError):
    """Raised when a knowledge document is malformed."""


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 900
    chunk_overlap: int = 120


REQUIRED_METADATA = {
    "document_id",
    "document_type",
    "title",
    "risk_domain",
    "version",
    "effective_from",
    "status",
    "jurisdiction",
    "owner",
    "synthetic",
}


def parse_markdown_document(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise KnowledgeBaseError(f"Missing metadata frontmatter: {path}")
    try:
        closing_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise KnowledgeBaseError(f"Unclosed metadata frontmatter: {path}") from exc

    metadata: dict[str, object] = {}
    for line in lines[1:closing_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise KnowledgeBaseError(f"Invalid frontmatter line in {path}: {line!r}")
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value.lower() in {"true", "false"}:
            metadata[key.strip()] = value.lower() == "true"
        else:
            metadata[key.strip()] = value.strip("\"'")

    missing = REQUIRED_METADATA - set(metadata)
    if missing:
        raise KnowledgeBaseError(f"Missing metadata {sorted(missing)} in {path}")
    if metadata["synthetic"] is not True:
        raise KnowledgeBaseError(f"Demo knowledge must be explicitly marked synthetic: {path}")
    body = "\n".join(lines[closing_index + 1 :]).strip()
    if not body:
        raise KnowledgeBaseError(f"Document body is empty: {path}")
    return metadata, body


def load_and_chunk_knowledge_base(
    knowledge_dir: Path,
    config: ChunkingConfig = ChunkingConfig(),
) -> list[KnowledgeChunk]:
    try:
        from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise KnowledgeBaseError("RAG dependencies are missing. Install the project with: pip install -e '.[rag]'") from exc

    if not knowledge_dir.is_dir():
        raise KnowledgeBaseError(f"Knowledge directory does not exist: {knowledge_dir}")

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "heading_1"), ("##", "heading_2"), ("###", "heading_3")],
        strip_headers=False,
    )
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n\n", "\n", "。", ". ", " ", ""],
    )

    chunks: list[KnowledgeChunk] = []
    for path in sorted(knowledge_dir.rglob("*.md")):
        if path.name == "README.md":
            continue
        metadata, body = parse_markdown_document(path)
        pieces: list[tuple[str, str]] = []
        for section in header_splitter.split_text(body):
            section_name = str(
                section.metadata.get("heading_3")
                or section.metadata.get("heading_2")
                or section.metadata.get("heading_1")
                or metadata["title"]
            )
            split_parts = recursive_splitter.split_text(section.page_content)
            pieces.extend((section_name, part.strip()) for part in split_parts if part.strip())

        for ordinal, (section_name, content) in enumerate(pieces, start=1):
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"{metadata['document_id']}:{ordinal:03d}",
                    document_id=str(metadata["document_id"]),
                    document_type=str(metadata["document_type"]),
                    title=str(metadata["title"]),
                    section=section_name,
                    risk_domain=str(metadata["risk_domain"]),
                    version=str(metadata["version"]),
                    effective_from=str(metadata["effective_from"]),
                    status=str(metadata["status"]),
                    jurisdiction=str(metadata["jurisdiction"]),
                    owner=str(metadata["owner"]),
                    synthetic=bool(metadata["synthetic"]),
                    content=content,
                )
            )
    if not chunks:
        raise KnowledgeBaseError(f"No valid Markdown knowledge documents found under {knowledge_dir}")
    return chunks
