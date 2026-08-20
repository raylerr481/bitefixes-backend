"""Vector-store adapters for Bitey's semantic memory and RAG.

The core backend does not require a vector database. FAISS and Qdrant are
optional adapters selected by configuration so Bitey can run locally, use a
managed Qdrant instance, or fall back to its existing structured memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class VectorDocument:
    id: str
    text: str
    metadata: dict[str, Any]


class VectorStoreError(RuntimeError):
    pass


class FAISSVectorStore:
    """Local FAISS store. Requires ``faiss-cpu`` at runtime."""

    def __init__(self, dimension: int, index_path: str | None = None) -> None:
        try:
            import faiss  # type: ignore
        except ImportError as exc:
            raise VectorStoreError("FAISS is not installed; install requirements-ai.txt") from exc
        self._faiss = faiss
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: list[VectorDocument] = []

    def add(self, embeddings: Sequence[Sequence[float]], documents: Sequence[VectorDocument]) -> None:
        if len(embeddings) != len(documents):
            raise ValueError("embeddings and documents must have the same length")
        if not embeddings:
            return
        import numpy as np
        matrix = np.asarray(embeddings, dtype="float32")
        if matrix.ndim != 2 or matrix.shape[1] != self.dimension:
            raise ValueError(f"expected embeddings with dimension {self.dimension}")
        self._faiss.normalize_L2(matrix)
        self.index.add(matrix)
        self.documents.extend(documents)

    def search(self, embedding: Sequence[float], limit: int = 5) -> list[tuple[VectorDocument, float]]:
        import numpy as np
        query = np.asarray([embedding], dtype="float32")
        if query.shape[1] != self.dimension:
            raise ValueError(f"expected embedding dimension {self.dimension}")
        self._faiss.normalize_L2(query)
        scores, ids = self.index.search(query, min(limit, len(self.documents)))
        return [
            (self.documents[i], float(score))
            for i, score in zip(ids[0], scores[0])
            if i >= 0
        ]

    def save(self) -> None:
        if self.index_path:
            self._faiss.write_index(self.index, self.index_path)


class QdrantVectorStore:
    """Qdrant adapter using the official qdrant-client package."""

    def __init__(
        self,
        collection_name: str,
        *,
        url: str | None = None,
        api_key: str | None = None,
        dimension: int,
    ) -> None:
        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.models import Distance, VectorParams  # type: ignore
        except ImportError as exc:
            raise VectorStoreError("Qdrant is not installed; install requirements-ai.txt") from exc

        self.client = QdrantClient(url=url, api_key=api_key) if url else QdrantClient(":memory:")
        self.collection_name = collection_name
        self.dimension = dimension
        self._distance = Distance.COSINE
        self._vector_params = VectorParams(size=dimension, distance=self._distance)

    def ensure_collection(self) -> None:
        from qdrant_client.models import VectorParams  # type: ignore
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=self._distance),
            )

    def add(self, embeddings: Sequence[Sequence[float]], documents: Sequence[VectorDocument]) -> None:
        from qdrant_client.models import PointStruct  # type: ignore
        if len(embeddings) != len(documents):
            raise ValueError("embeddings and documents must have the same length")
        self.ensure_collection()
        points = [
            PointStruct(id=doc.id, vector=list(vector), payload={"text": doc.text, **doc.metadata})
            for vector, doc in zip(embeddings, documents)
        ]
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, embedding: Sequence[float], limit: int = 5) -> list[tuple[VectorDocument, float]]:
        self.ensure_collection()
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=list(embedding),
            limit=limit,
        ).points
        return [
            (
                VectorDocument(
                    id=str(point.id),
                    text=str((point.payload or {}).get("text", "")),
                    metadata={k: v for k, v in (point.payload or {}).items() if k != "text"},
                ),
                float(point.score),
            )
            for point in results
        ]
