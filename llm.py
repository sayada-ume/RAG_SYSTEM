from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
except Exception as exc:  # pragma: no cover - import-time guard
    raise RuntimeError("google-genai is required. Install dependencies before running HR Assist Pro.") from exc

from guardrails import answer_is_supported
from utils import dedupe_citations, normalize_whitespace, truncate_text


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")


@dataclass
class ModelResponse:
    answer: str
    relevant_policy_summary: str
    required_employee_actions: str
    citations: List[Dict[str, Any]]
    support_status: str
    unsupported_claims: List[str]
    evidence_gaps: List[str]
    raw_text: str


def get_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_GENAI_API_KEY in the environment.")
    return genai.Client(api_key=api_key)


def _extract_embedding_values(result: Any) -> List[List[float]]:
    embeddings: List[List[float]] = []
    if hasattr(result, "embeddings"):
        for item in result.embeddings:
            vector = getattr(item, "values", None) or getattr(item, "embedding", None)
            if vector is None:
                continue
            embeddings.append(list(vector))
    elif hasattr(result, "embedding"):
        vector = getattr(result.embedding, "values", None) or getattr(result.embedding, "embedding", None)
        if vector is not None:
            embeddings.append(list(vector))
    return embeddings


def _fallback_embedding_vector(text: str, dimensions: int = 384) -> List[float]:
    vector = [0.0] * dimensions
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        weight = 1.0 + (len(token) / 10.0)
        vector[index] += weight

    norm = sum(value * value for value in vector) ** 0.5
    if norm:
        vector = [value / norm for value in vector]
    return vector


def embed_texts(texts: List[str]) -> List[List[float]]:
    cleaned = [truncate_text(normalize_whitespace(text), 7000) for text in texts]
    try:
        client = get_client()
        response = client.models.embed_content(model=GEMINI_EMBED_MODEL, contents=cleaned)
        vectors = _extract_embedding_values(response)
        if not vectors:
            raise RuntimeError("Gemini embedding response did not contain vectors.")
        if len(vectors) == 1 and len(cleaned) > 1:
            return [vectors[0] for _ in cleaned]
        return vectors
    except Exception:
        return [_fallback_embedding_vector(text) for text in cleaned]


def embed_query(text: str) -> List[float]:
    vectors = embed_texts([text])
    return vectors[0]


def build_hr_prompt(question: str, context_blocks: List[Dict[str, Any]]) -> str:
    context_text = []
    for index, block in enumerate(context_blocks, start=1):
        context_text.append(
            f"[CHUNK {index}]\n"
            f"Source: {block['source']}\n"
            f"Page: {block['page']}\n"
            f"Document Type: {block.get('document_type', 'Unknown')}\n"
            f"Text: {block['text']}\n"
        )

    context_blob = "\n".join(context_text)
    return f"""
[SYSTEM ROLE]
You are a Senior HR Business Partner with expertise in company policies and employee relations.
You must answer only using the provided HR documentation.
Do not invent facts, do not reveal chain-of-thought, and do not add unsupported claims.

[CONTEXT FROM HR POLICIES]
{context_blob}

[THOUGHT PROCESS]
Analyze policies internally.
Identify the exact policy applicable.
Determine employee actions.

[ACTIONABLE RESPONSE]
Return valid JSON only using this schema:
{{
  "answer": "direct employee-facing answer",
  "relevant_policy_summary": "2-4 sentence summary",
  "required_employee_actions": "bullet-like sentence or 'Not applicable'",
  "citations": [{{"source": "document name", "page": 1, "quote": "short supporting quote"}}],
  "support_status": "supported" or "unsupported",
  "unsupported_claims": ["list of claim fragments not supported"],
  "evidence_gaps": ["list of missing information if any"]
}}

If there is insufficient evidence, set answer to exactly:
Insufficient information found in company policies.

If any claim cannot be verified from the context, set support_status to unsupported.

[CITATIONS]
List document names and page numbers.

Employee question: {question}
""".strip()


def _extract_json_block(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Empty Gemini response.")

    if text.startswith("{"):
        return json.loads(text)

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Gemini response did not contain JSON.")
    return json.loads(match.group(0))


def parse_model_response(text: str) -> ModelResponse:
    payload = _extract_json_block(text)
    citations = dedupe_citations(payload.get("citations", []))
    return ModelResponse(
        answer=normalize_whitespace(payload.get("answer", "")),
        relevant_policy_summary=normalize_whitespace(payload.get("relevant_policy_summary", "")),
        required_employee_actions=normalize_whitespace(payload.get("required_employee_actions", "")),
        citations=citations,
        support_status=str(payload.get("support_status", "unsupported")).strip().lower(),
        unsupported_claims=[normalize_whitespace(item) for item in payload.get("unsupported_claims", []) if normalize_whitespace(item)],
        evidence_gaps=[normalize_whitespace(item) for item in payload.get("evidence_gaps", []) if normalize_whitespace(item)],
        raw_text=text,
    )


def generate_answer(question: str, context_blocks: List[Dict[str, Any]]) -> ModelResponse:
    client = get_client()
    prompt = build_hr_prompt(question, context_blocks)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    text = getattr(response, "text", None) or ""
    if not text and hasattr(response, "candidates"):
        for candidate in response.candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    text += part_text
    parsed = parse_model_response(text)
    if not parsed.answer:
        parsed.answer = "Insufficient information found in company policies."
        parsed.support_status = "unsupported"
    if not parsed.citations:
        parsed.support_status = "unsupported"
    if not answer_is_supported(parsed.answer, [block["text"] for block in context_blocks]):
        parsed.support_status = "unsupported"
    return parsed


def probe_gemini() -> Tuple[bool, str]:
    try:
        client = get_client()
        client.models.get(model=GEMINI_MODEL)
        return True, "Connected"
    except Exception as exc:
        message = str(exc).lower()
        if "429" in message or "too many requests" in message or "rate limit" in message:
            return False, "Rate limited"
        if "quota" in message:
            return False, "Quota exceeded"
        if "permission" in message or "unauthorized" in message or "forbidden" in message:
            return False, "Auth issue"
        return False, f"Unavailable: {exc.__class__.__name__}"
