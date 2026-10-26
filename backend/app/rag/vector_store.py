from pathlib import Path
import uuid

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

COLLECTION = "knowledge_chunks_multilingual_hybrid_v2"
DENSE_NAME = "dense"
SPARSE_NAME = "bm25"
VECTOR_SIZE = 384
QDRANT_PATH = Path("data/qdrant")
_dense_model: TextEmbedding | None = None
_sparse_model: SparseTextEmbedding | None = None
_client: QdrantClient | None = None


def client() -> QdrantClient:
    global _client
    if _client is None:
        QDRANT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=str(QDRANT_PATH))
        if not _client.collection_exists(COLLECTION):
            _client.create_collection(
                collection_name=COLLECTION,
                vectors_config={DENSE_NAME: models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)},
                sparse_vectors_config={SPARSE_NAME: models.SparseVectorParams()},
            )
    return _client


def dense_embedder() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        _dense_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _dense_model


def sparse_embedder() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return _sparse_model


def chunks(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []
    out, start = [], 0
    while start < len(clean):
        end = min(start + size, len(clean))
        part = clean[start:end].strip()
        if part:
            out.append(part)
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return out


def _sparse_vector(value) -> models.SparseVector:
    return models.SparseVector(indices=value.indices.tolist(), values=value.values.tolist())


def index_document(user_id: uuid.UUID, document_id: uuid.UUID, version_id: uuid.UUID, text: str, source: str) -> int:
    parts = chunks(text)
    if not parts:
        return 0
    dense_vectors = list(dense_embedder().embed([f"passage: {p}" for p in parts]))
    sparse_vectors = list(sparse_embedder().embed(parts))
    points = []
    for i, (part, dense, sparse) in enumerate(zip(parts, dense_vectors, sparse_vectors)):
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector={DENSE_NAME: dense.tolist(), SPARSE_NAME: _sparse_vector(sparse)},
            payload={"user_id": str(user_id), "document_id": str(document_id), "version_id": str(version_id),
                     "chunk_index": i, "source": source, "text": part},
        ))
    client().upsert(collection_name=COLLECTION, points=points, wait=True)
    return len(points)


def delete_document(document_id: uuid.UUID) -> None:
    client().delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key="document_id", match=models.MatchValue(value=str(document_id)))
        ])), wait=True,
    )


def search(user_id: uuid.UUID, query: str, limit: int = 5) -> list[dict]:
    dense = list(dense_embedder().embed([f"query: {query}"]))[0].tolist()
    sparse = list(sparse_embedder().embed([query]))[0]
    user_filter = models.Filter(must=[
        models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user_id)))
    ])
    candidate_limit = min(max(limit * 4, 20), 100)
    result = client().query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=dense, using=DENSE_NAME, filter=user_filter, limit=candidate_limit),
            models.Prefetch(query=_sparse_vector(sparse), using=SPARSE_NAME, filter=user_filter, limit=candidate_limit),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    ).points
    return [{"score": p.score, "retrieval": "hybrid_rrf", **(p.payload or {})} for p in result]
