from __future__ import annotations

import io
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import chromadb
from pypdf import PdfReader

from llm import embed_texts
from utils import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DIR,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MANIFEST_PATH,
    SAMPLE_PDF_DIR,
    UPLOAD_DIR,
    ChunkCitation,
    chunk_text,
    current_timestamp,
    ensure_directories,
    file_sha256,
    normalize_whitespace,
    read_json,
    safe_slug,
    short_document_title,
    slugify_document_type,
    write_json,
)


ensure_directories()


@dataclass
class DocumentManifestEntry:
    source: str
    document_type: str
    file_path: str
    hash: str
    uploaded_at: str
    pages: int
    chunks: int


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def load_manifest() -> Dict[str, Any]:
    return read_json(MANIFEST_PATH, {"documents": {}, "last_indexing_timestamp": None})


def save_manifest(manifest: Dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, manifest)


def _upsert_manifest_entry(entry: DocumentManifestEntry) -> None:
    manifest = load_manifest()
    manifest.setdefault("documents", {})[entry.source] = asdict(entry)
    manifest["last_indexing_timestamp"] = current_timestamp()
    save_manifest(manifest)


def _remove_manifest_entry(source: str) -> None:
    manifest = load_manifest()
    documents = manifest.setdefault("documents", {})
    if source in documents:
        del documents[source]
        manifest["last_indexing_timestamp"] = current_timestamp()
        save_manifest(manifest)


def _extract_pdf_pages(pdf_path: Path) -> List[str]:
    reader = PdfReader(str(pdf_path))
    pages: List[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        pages.append(normalize_whitespace(extracted))
    return pages


def _ensure_sample_pdf(path: Path, title: str, sections: List[str]) -> None:
    if path.exists():
        return

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    margin = 48
    y = height - margin
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, title)
    y -= 28
    c.setFont("Helvetica", 11)

    for section in sections:
        lines = section.split("\n")
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                y -= 10
                continue
            if y < margin + 50:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 11)
            text = c.beginText(margin, y)
            text.textLine(line)
            c.drawText(text)
            y -= 16
        y -= 10

    c.save()


def ensure_sample_pdfs() -> List[Path]:
    ensure_directories()
    samples = [
        (
            SAMPLE_PDF_DIR / "employee_handbook.pdf",
            "Employee Handbook",
            [
                "Welcome to the company handbook. This policy document covers attendance, code of conduct, leave administration, performance review cycles, and employee support services.",
                "Annual leave is accrued monthly. Employees should submit planned leave requests through the HR portal at least five business days in advance unless local law requires a shorter notice period.",
                "Employees may request reimbursements for approved business expenses within 30 calendar days of the expense date. Attach itemized receipts and manager approval where required.",
            ],
        ),
        (
            SAMPLE_PDF_DIR / "leave_policy.pdf",
            "Leave Policy",
            [
                "Annual leave requests must be approved by the line manager. Employees should review team coverage before requesting time off.",
                "Maternity leave is available according to local law and company benefits. Employees should notify HR as early as practical and submit supporting documentation.",
                "Work-from-home arrangements may be approved for eligible roles. Employees must remain reachable during working hours and follow information security guidelines.",
            ],
        ),
        (
            SAMPLE_PDF_DIR / "reimbursement_policy.pdf",
            "Reimbursement Policy",
            [
                "Reimbursable expenses include approved travel, client meals, and other pre-authorized business costs.",
                "Expense claims must be submitted with receipts, business purpose descriptions, and the correct cost center.",
                "Claims are reviewed by Finance and HR operations. Missing receipts may result in rejection unless the policy provides an exception.",
            ],
        ),
        (
            SAMPLE_PDF_DIR / "performance_review_guidelines.pdf",
            "Performance Review Guidelines",
            [
                "The performance review cycle runs twice per year and includes self-review, manager review, calibration, and a final feedback discussion.",
                "Employees should document achievements, goals, and development plans before the review meeting.",
                "Promotion decisions are based on performance evidence, role scope, and business need.",
            ],
        ),
    ]

    created_paths: List[Path] = []
    for pdf_path, title, sections in samples:
        _ensure_sample_pdf(pdf_path, title, sections)
        created_paths.append(pdf_path)
    return created_paths


def _chunk_pages(pages: List[str]) -> List[Dict[str, Any]]:
    chunk_rows: List[Dict[str, Any]] = []
    for page_number, page_text in enumerate(pages, start=1):
        for chunk_index, chunk in enumerate(chunk_text(page_text, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_CHUNK_OVERLAP), start=1):
            cleaned = normalize_whitespace(chunk)
            if not cleaned:
                continue
            chunk_rows.append(
                {
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "text": cleaned,
                }
            )
    return chunk_rows


def ingest_pdf_file(pdf_path: Path, document_type: Optional[str] = None, replace_existing: bool = True, source_name: Optional[str] = None) -> Dict[str, Any]:
    collection = get_collection()
    pages = _extract_pdf_pages(pdf_path)
    chunks = _chunk_pages(pages)
    if not chunks:
        raise ValueError(f"No extractable text found in {pdf_path.name}.")

    source = source_name or pdf_path.name
    document_type = document_type or slugify_document_type(pdf_path.name)
    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    ids = []
    documents = []
    metadatas = []
    for index, chunk in enumerate(chunks):
        chunk_id = f"{safe_slug(source)}-p{chunk['page']}-c{chunk['chunk_index']}-{file_sha256(pdf_path)[:12]}-{index}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append(
            {
                "source": source,
                "page": chunk["page"],
                "document_type": document_type,
                "chunk_index": chunk["chunk_index"],
                "file_hash": file_sha256(pdf_path),
            }
        )

    if replace_existing:
        collection.delete(where={"source": source})

    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    entry = DocumentManifestEntry(
        source=source,
        document_type=document_type,
        file_path=str(pdf_path),
        hash=file_sha256(pdf_path),
        uploaded_at=current_timestamp(),
        pages=len(pages),
        chunks=len(chunks),
    )
    _upsert_manifest_entry(entry)
    return asdict(entry)


def save_uploaded_file(uploaded_file, target_name: Optional[str] = None) -> Path:
    ensure_directories()
    destination = UPLOAD_DIR / (target_name or uploaded_file.name)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def delete_document(source: str) -> bool:
    collection = get_collection()
    payload = collection.get(where={"source": source}, include=["documents"])
    if not payload.get("ids"):
        return False
    collection.delete(where={"source": source})
    _remove_manifest_entry(source)
    return True


def list_indexed_documents() -> List[Dict[str, Any]]:
    manifest = load_manifest()
    documents = list(manifest.get("documents", {}).values())
    documents.sort(key=lambda row: row.get("uploaded_at", ""), reverse=True)
    return documents


def get_database_statistics() -> Dict[str, Any]:
    collection = get_collection()
    manifest = load_manifest()
    docs = list_indexed_documents()
    return {
        "documents_indexed": len(docs),
        "chunks_indexed": collection.count(),
        "last_indexing_timestamp": manifest.get("last_indexing_timestamp"),
        "documents": docs,
    }


def bootstrap_knowledge_base() -> Dict[str, Any]:
    ensure_directories()
    ensure_sample_pdfs()
    collection = get_collection()
    if collection.count() == 0:
        results = []
        for pdf_path in sorted(SAMPLE_PDF_DIR.glob("*.pdf")):
            results.append(ingest_pdf_file(pdf_path, document_type=slugify_document_type(pdf_path.name), replace_existing=True))
        return {"bootstrapped": True, "ingested": results}
    return {"bootstrapped": False, "ingested": []}


def ingest_uploaded_documents(uploaded_files: Iterable[Any], document_type: str, replace_existing: bool = True) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for uploaded_file in uploaded_files:
        saved_path = save_uploaded_file(uploaded_file)
        results.append(ingest_pdf_file(saved_path, document_type=document_type, replace_existing=replace_existing, source_name=uploaded_file.name))
    return results
