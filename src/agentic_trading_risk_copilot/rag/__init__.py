"""Policy RAG components with optional third-party dependencies."""

from .agent import PolicyRAGAgent, RAGGenerationError
from .index import FaissKnowledgeIndex, RAGDependencyError
from .knowledge import ChunkingConfig, load_and_chunk_knowledge_base

__all__ = [
    "ChunkingConfig",
    "FaissKnowledgeIndex",
    "PolicyRAGAgent",
    "RAGDependencyError",
    "RAGGenerationError",
    "load_and_chunk_knowledge_base",
]
