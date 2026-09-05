from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class EmbeddingDependencyError(RuntimeError):
    """Raised when sentence-transformers is unavailable."""


class E5EmbeddingModel:
    """Local multilingual E5 encoder using normalized query/passage embeddings."""

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-small",
        model: Any | None = None,
        *,
        local_files_only: bool = False,
    ) -> None:
        self.model_name = model_name
        if model is not None:
            self._model = model
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingDependencyError(
                "sentence-transformers is missing. Install the project with: pip install -e '.[rag]'"
            ) from exc
        self._model = SentenceTransformer(model_name, local_files_only=local_files_only)

    def embed_documents(self, texts: Sequence[str]) -> Any:
        return self._model.encode(
            [f"passage: {text}" for text in texts],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")

    def embed_query(self, text: str) -> Any:
        return self._model.encode(
            [f"query: {text}"],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")[0]
