from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb

from llm import embed_query
from reranker import FlashRankReranker
from utils import CHROMA_COLLECTION_NAME, CHROMA_DIR, clean_chunk_text, normalize_whitespace, truncate_text


@dataclass
class RetrievalBundle:
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    context_blocks: List[Dict[str, Any]]
    fallback_used: bool = False
    message: str = ""


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _normalize_retrieved_row(text: str, metadata: Dict[str, Any], chunk_id: str, distance: Optional[float] = None) -> Dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "text": clean_chunk_text(text),
        "source": metadata.get("source", "Unknown document"),
        "page": int(metadata.get("page", 0) or 0),
        "document_type": metadata.get("document_type", "Other Policy"),
        "chunk_index": int(metadata.get("chunk_index", 0) or 0),
        "distance": distance,
        "metadata": metadata,
    }


def _lexical_fallback(query: str, collection: chromadb.Collection, top_k: int = 20) -> List[Dict[str, Any]]:
    payload = collection.get(include=["documents", "metadatas"])
    documents = payload.get("documents", []) or []
    metadatas = payload.get("metadatas", []) or []
    ids = payload.get("ids", []) or []
    query_terms = set(normalize_whitespace(query).lower().split())
    ranked: List[Dict[str, Any]] = []

    for doc_text, metadata, chunk_id in zip(documents, metadatas, ids):
        cleaned = clean_chunk_text(doc_text or "")
        lower_text = cleaned.lower()
        overlap = sum(1 for term in query_terms if term and term in lower_text)
        score = overlap + min(len(cleaned) / 1500.0, 1.0)
        ranked.append(_normalize_retrieved_row(cleaned, metadata or {}, chunk_id, distance=1.0 - score))

    ranked.sort(key=lambda row: row.get("distance", 999.0))
    return ranked[:top_k]


def retrieve_chunks(query: str, top_k: int = 20) -> RetrievalBundle:
    collection = get_collection()
    try:
        query_embedding = embed_query(query)
        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0] if response.get("distances") else []

        retrieved: List[Dict[str, Any]] = []
        for index, (doc_text, metadata, chunk_id) in enumerate(zip(documents, metadatas, ids)):
            retrieved.append(_normalize_retrieved_row(doc_text or "", metadata or {}, chunk_id, distances[index] if index < len(distances) else None))
        fallback_used = False
    except Exception as exc:
        retrieved = _lexical_fallback(query, collection, top_k=top_k)
        fallback_used = True
        return RetrievalBundle(query=query, retrieved_chunks=retrieved, reranked_chunks=retrieved[:5], context_blocks=_build_context_blocks(retrieved[:5]), fallback_used=fallback_used, message=f"Fallback retrieval used: {exc.__class__.__name__}")

    reranker = FlashRankReranker()
    reranked = reranker.rerank(query, retrieved, top_k=5)
    return RetrievalBundle(
        query=query,
        retrieved_chunks=retrieved,
        reranked_chunks=reranked,
        context_blocks=_build_context_blocks(reranked),
        fallback_used=fallback_used,
        message="",
    )


def _build_context_blocks(chunks: List[Dict[str, Any]], max_blocks: int = 5, max_chars_each: int = 1200) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for chunk in chunks[:max_blocks]:
        blocks.append(
            {
                "source": chunk.get("source", "Unknown document"),
                "page": chunk.get("page", 0),
                "document_type": chunk.get("document_type", "Other Policy"),
                "text": truncate_text(clean_chunk_text(chunk.get("text", "")), max_chars=max_chars_each),
                "score": chunk.get("score") or chunk.get("distance") or 0.0,
                "chunk_id": chunk.get("chunk_id"),
            }
        )
    return blocks


def format_retrieved_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    for chunk in chunks:
        citations.append(
            {
                "source": chunk.get("source", "Unknown document"),
                "page": chunk.get("page", 0),
                "document_type": chunk.get("document_type", "Other Policy"),
                "score": round(float(chunk.get("score") or 0.0), 4),
                "excerpt": truncate_text(chunk.get("text", ""), 260),
            }
        )
    return citations
