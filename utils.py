from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence


BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
SAMPLE_PDF_DIR = BASE_DIR / "sample_pdfs"
UPLOAD_DIR = SAMPLE_PDF_DIR / "uploads"
MANIFEST_PATH = CHROMA_DIR / "index_manifest.json"
CHROMA_COLLECTION_NAME = "hr_policies"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 180


HR_DOCUMENT_TYPES = [
    "Employee Handbook",
    "Leave Policy",
    "Travel Policy",
    "Benefits Guide",
    "Code of Conduct",
    "Reimbursement Policy",
    "Performance Review Guidelines",
    "Other Policy",
]


def ensure_directories() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_PDF_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "document"


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_metadata_noise(text: str) -> str:
    cleaned_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if stripped.lower().startswith(("source:", "page:", "document type:", "filename:")):
            continue
        cleaned_lines.append(stripped)
    return normalize_whitespace("\n".join(cleaned_lines))


def clean_chunk_text(text: str) -> str:
    return strip_metadata_noise(text)


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(text_length, start + chunk_size)
        segment = text[start:end].strip()
        if segment:
            chunks.append(segment)
        if end >= text_length:
            break
        start = max(0, end - overlap)
    return chunks


def dedupe_citations(citations: Sequence[dict]) -> List[dict]:
    seen = set()
    deduped: List[dict] = []
    for citation in citations:
        key = (
            citation.get("source", ""),
            citation.get("page", ""),
            citation.get("quote", "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(citation)
    return deduped


def slugify_document_type(file_name: str) -> str:
    lowered = file_name.lower()
    mapping = {
        "leave": "Leave Policy",
        "travel": "Travel Policy",
        "benefit": "Benefits Guide",
        "code_of_conduct": "Code of Conduct",
        "conduct": "Code of Conduct",
        "reimbursement": "Reimbursement Policy",
        "performance": "Performance Review Guidelines",
        "review": "Performance Review Guidelines",
        "handbook": "Employee Handbook",
        "employee": "Employee Handbook",
    }
    for needle, doc_type in mapping.items():
        if needle in lowered:
            return doc_type
    return "Other Policy"


def short_document_title(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip().title() or path.name


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


@dataclass
class ChunkCitation:
    source: str
    page: int
    document_type: str
    quote: str

    def as_dict(self) -> dict:
        return asdict(self)


def format_citation_label(source: str, page: int) -> str:
    return f"{source} (page {page})"


def truncate_text(text: str, max_chars: int = 700) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def flatten(iterable: Iterable[Sequence]) -> List:
    flattened: List = []
    for item in iterable:
        flattened.extend(item)
    return flattened
