# HR Assist Pro

Enterprise-grade HR Retrieval-Augmented Generation workflow application built with Streamlit, ChromaDB, FlashRank, and the latest Google GenAI SDK.

## Features

- Employee-facing HR question answering with structured policy responses.
- PDF ingestion with page-level parsing, chunking, embedding, and ChromaDB persistence.
- Delete and update workflows using document metadata.
- Two-stage retrieval: top-20 Chroma retrieval followed by FlashRank reranking to top-5.
- Guardrails for prompt injection, harmful requests, and non-HR questions.
- Output verification with hallucination warnings and Gemini failover.
- Automatic sample HR PDFs so the app runs immediately after setup.

## Project Structure

```text
hr-assist-pro/
├── app.py
├── ingest.py
├── rag_pipeline.py
├── reranker.py
├── guardrails.py
├── llm.py
├── utils.py
├── requirements.txt
├── chroma_db/
├── sample_pdfs/
└── README.md
```

## Setup

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure `.env` contains `GOOGLE_GENAI_API_KEY`.
4. Start the app:

```bash
streamlit run app.py
```

## Notes

- The app bootstraps sample HR PDFs automatically into ChromaDB if the index is empty.
- Uploaded PDFs are stored under `sample_pdfs/uploads/` and indexed with source/page metadata.
- Gemini failures do not stop the app; the UI falls back to retrieved policy excerpts.
