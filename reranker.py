from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


try:
    from flashrank import Ranker, RerankRequest
except Exception:  # pragma: no cover - dependency fallback
    Ranker = None
    RerankRequest = None


@dataclass
class RerankedChunk:
    text: str
    source: str
    page: int
    document_type: str
    score: float
    chunk_id: str
    metadata: Dict[str, Any]


class FlashRankReranker:
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2") -> None:
        self.model_name = model_name
        self._ranker = Ranker(model_name=model_name) if Ranker else None

    def rerank(self, query: str, passages: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not passages:
            return []

        if self._ranker and RerankRequest:
            request = RerankRequest(
                query=query,
                passages=[{"id": item.get("chunk_id"), "text": item.get("text", ""), "meta": item} for item in passages],
            )
            results = self._ranker.rerank(request)
            reranked: List[Dict[str, Any]] = []
            for result in results[:top_k]:
                meta = result.get("meta", {})
                reranked.append(
                    {
                        **meta,
                        "score": float(result.get("score", 0.0)),
                        "text": meta.get("text", ""),
                    }
                )
            return reranked

        query_terms = set(query.lower().split())
        scored: List[Dict[str, Any]] = []
        for item in passages:
            text = item.get("text", "").lower()
            overlap = sum(1 for term in query_terms if term and term in text)
            length_penalty = min(len(text) / 2000.0, 1.0)
            score = overlap + (1.0 - length_penalty)
            scored.append({**item, "score": score})
        scored.sort(key=lambda row: row["score"], reverse=True)
        return scored[:top_k]
