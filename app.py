from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st

from guardrails import GuardrailResult, validate_user_input
from ingest import bootstrap_knowledge_base, delete_document, get_database_statistics, ingest_uploaded_documents, list_indexed_documents
from llm import generate_answer, probe_gemini
from rag_pipeline import format_retrieved_citations, retrieve_chunks
from utils import HR_DOCUMENT_TYPES, ensure_directories, normalize_whitespace, truncate_text


ensure_directories()


st.set_page_config(
    page_title="HR Assist Pro",
    page_icon="HR",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_CSS = """
<style>
    :root {
        --bg: #07111f;
        --bg-soft: #0d1a2b;
        --panel: rgba(10, 20, 35, 0.76);
        --panel-strong: rgba(17, 33, 57, 0.95);
        --accent: #63d2ff;
        --accent-2: #34d399;
        --accent-3: #a78bfa;
        --text: #eef4fb;
        --muted: #9db0c8;
        --warn: #f59e0b;
        --danger: #ef4444;
        --border: rgba(148, 163, 184, 0.18);
        --shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", "Aptos", "Helvetica Neue", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, rgba(99, 210, 255, 0.16), transparent 24%),
            radial-gradient(circle at 18% 18%, rgba(167, 139, 250, 0.10), transparent 18%),
            radial-gradient(circle at left center, rgba(52, 211, 153, 0.10), transparent 22%),
            linear-gradient(180deg, #07111f 0%, #0b1728 100%);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        right: 1rem;
        top: 0.5rem;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1240px;
    }

    .hero {
        padding: 1.4rem 1.5rem 1.2rem;
        border: 1px solid var(--border);
        border-radius: 24px;
        background:
            linear-gradient(145deg, rgba(17, 33, 57, 0.95), rgba(10, 20, 35, 0.92)),
            radial-gradient(circle at top right, rgba(99, 210, 255, 0.18), transparent 26%);
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        letter-spacing: -0.03em;
        line-height: 1.05;
    }

    .hero p {
        margin: 0.55rem 0 0;
        color: var(--muted);
        font-size: 0.98rem;
        max-width: 72ch;
    }

    .panel {
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1rem 1.05rem;
        background: var(--panel);
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.14);
        backdrop-filter: blur(14px);
    }

    .metric-card {
        border: 1px solid var(--border);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(22, 50, 82, 0.96), rgba(12, 22, 39, 0.96));
        padding: 0.9rem 1rem;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text);
        margin-top: 0.25rem;
    }

    .section-title {
        margin-top: 0;
        margin-bottom: 0.65rem;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }

    .small-muted {
        color: var(--muted);
        font-size: 0.92rem;
    }

    .pill-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.95rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.7rem;
        border-radius: 999px;
        border: 1px solid rgba(99, 210, 255, 0.22);
        background: rgba(99, 210, 255, 0.08);
        color: var(--text);
        font-size: 0.82rem;
        line-height: 1;
    }

    .panel-heading {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 0.35rem;
    }

    .panel-heading h2 {
        margin: 0;
        font-size: 1.1rem;
        letter-spacing: -0.02em;
    }

    .panel-heading p {
        margin: 0.2rem 0 0;
        color: var(--muted);
        font-size: 0.92rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        border: 1px solid rgba(52, 211, 153, 0.24);
        background: rgba(52, 211, 153, 0.08);
        color: #d7faea;
        font-size: 0.8rem;
        white-space: nowrap;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(8, 16, 29, 0.88) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
        border-radius: 14px !important;
    }

    .stTextArea textarea {
        min-height: 120px;
        padding-top: 0.9rem !important;
    }

    .stButton button {
        border-radius: 14px;
        font-weight: 700;
        padding-top: 0.72rem;
        padding-bottom: 0.72rem;
        border: 1px solid rgba(99, 210, 255, 0.25);
        box-shadow: 0 10px 24px rgba(99, 210, 255, 0.12);
    }

    .stButton button:hover {
        border-color: rgba(99, 210, 255, 0.5);
    }

    .stExpander {
        border: 1px solid var(--border);
        border-radius: 16px;
        background: rgba(10, 20, 35, 0.45);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        background: rgba(8, 16, 29, 0.42);
        padding: 0.35rem;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 14px;
        padding: 0.65rem 1rem;
        color: var(--muted);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 210, 255, 0.18), rgba(52, 211, 153, 0.14));
        color: var(--text);
    }

    .warning-box {
        border-left: 4px solid var(--warn);
        background: rgba(245, 158, 11, 0.12);
        padding: 0.85rem 1rem;
        border-radius: 12px;
        color: var(--text);
        margin: 0.5rem 0 1rem;
    }

    .danger-box {
        border-left: 4px solid var(--danger);
        background: rgba(239, 68, 68, 0.12);
        padding: 0.85rem 1rem;
        border-radius: 12px;
        color: var(--text);
        margin: 0.5rem 0 1rem;
    }

    .surface-card {
        border: 1px solid var(--border);
        border-radius: 20px;
        background: var(--panel-strong);
        padding: 1rem;
        box-shadow: var(--shadow);
    }

    .section-card {
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 18px;
        background: rgba(10, 20, 35, 0.62);
        padding: 0.95rem 1rem;
        margin-bottom: 0.85rem;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: 1.6fr 0.85fr;
        gap: 1rem;
        align-items: stretch;
        margin-bottom: 0.9rem;
    }

    .hero-stat {
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(22, 50, 82, 0.9), rgba(11, 20, 35, 0.92));
        padding: 1rem;
    }

    .hero-stat .label {
        color: var(--muted);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .hero-stat .value {
        margin-top: 0.25rem;
        font-size: 1.3rem;
        font-weight: 700;
    }
</style>
"""


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="badge">Enterprise HR RAG</div>
                    <h1>HR Assist Pro</h1>
                    <p>Intelligent HR workflow assistant for policy retrieval, answer generation, citations, and administrator-controlled indexing.</p>
                    <div class="pill-row">
                        <span class="pill">Policy Q&A</span>
                        <span class="pill">ChromaDB</span>
                        <span class="pill">FlashRank Reranking</span>
                        <span class="pill">Gemini LLM</span>
                    </div>
                </div>
                <div class="hero-stat">
                    <div class="label">Workflow</div>
                    <div class="value">Search → Rerank → Verify → Respond</div>
                    <p class="small-muted">Built for policy guidance, not casual chat.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: Any) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=180)
def cached_gemini_status() -> Dict[str, Any]:
    ok, message = probe_gemini()
    return {"ok": ok, "message": message}


def show_guardrail_banner(result: GuardrailResult) -> None:
    if result.category == "greeting":
        st.info(result.message)
    else:
        st.markdown(f'<div class="danger-box">{result.message}</div>', unsafe_allow_html=True)


def render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        st.info("No citations available.")
        return
    for citation in citations:
        st.markdown(
            f"- **{citation.get('source', 'Unknown document')}** | Page {citation.get('page', 0)} | {citation.get('document_type', 'Other Policy')}"
        )
        quote = citation.get("quote") or citation.get("excerpt")
        if quote:
            st.caption(truncate_text(str(quote), 240))


def answer_question(question: str) -> None:
    guardrail = validate_user_input(question)
    if not guardrail.allowed:
        show_guardrail_banner(guardrail)
        return

    with st.spinner("Searching the HR knowledge base and reranking relevant policy chunks..."):
        bundle = retrieve_chunks(question, top_k=20)

    if bundle.message:
        st.warning(bundle.message)

    retrieved_citations = format_retrieved_citations(bundle.retrieved_chunks)

    try:
        response = generate_answer(question, bundle.context_blocks)
        if response.support_status != "supported":
            st.warning(
                "⚠ Hallucination Warning:\nThe generated response contains statements that cannot be verified using the indexed HR documentation."
            )
            if response.answer != "Insufficient information found in company policies.":
                response.answer = "Insufficient information found in company policies."

        st.subheader("Answer")
        st.write(response.answer)

        st.subheader("Relevant Policy Summary")
        st.write(response.relevant_policy_summary or "Insufficient information found in company policies.")

        st.subheader("Required Employee Actions")
        st.write(response.required_employee_actions or "Not applicable")

        st.subheader("Policy Citations")
        render_citations(response.citations or retrieved_citations[:5])

    except Exception:
        st.warning("⚠ System Degradation Warning\nGemini is temporarily unavailable. Showing retrieved HR policy excerpts instead.")
        st.subheader("Top 5 Reranked Policy Chunks")
        for chunk in bundle.reranked_chunks[:5]:
            st.markdown(
                f"**{chunk.get('source', 'Unknown document')}** | Page {chunk.get('page', 0)} | {chunk.get('document_type', 'Other Policy')}"
            )
            st.caption(truncate_text(chunk.get("text", ""), 380))

        st.subheader("Policy Citations")
        render_citations(retrieved_citations[:5])

    with st.expander("Retrieved Citations and Evidence", expanded=False):
        st.caption("Top 20 retrieved chunks before reranking and the final top 5 evidence set.")
        st.markdown("**Top 20 Retrieved Chunks**")
        for index, chunk in enumerate(bundle.retrieved_chunks, start=1):
            st.markdown(
                f"{index}. **{chunk.get('source', 'Unknown document')}** | Page {chunk.get('page', 0)} | {chunk.get('document_type', 'Other Policy')}"
            )
            st.caption(truncate_text(chunk.get("text", ""), 280))
        st.markdown("**Top 5 Reranked Chunks**")
        for index, chunk in enumerate(bundle.reranked_chunks, start=1):
            st.markdown(
                f"{index}. **{chunk.get('source', 'Unknown document')}** | Page {chunk.get('page', 0)} | Score: {round(float(chunk.get('score') or 0.0), 4)}"
            )
            st.caption(truncate_text(chunk.get("text", ""), 280))


def render_employee_portal() -> None:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-heading">
                <div>
                    <h2>Employee Portal</h2>
                    <p>Ask an HR policy question and receive a structured, citation-backed answer.</p>
                </div>
                <span class="badge">Employee-facing</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        question = st.text_area(
            "Ask HR a question",
            placeholder="How many annual leave days do I have? What is the reimbursement process?",
            height=140,
            label_visibility="collapsed",
        )
        action_col, hint_col = st.columns([1, 2])
        with action_col:
            pressed = st.button("Get HR Answer", type="primary", use_container_width=True)
        with hint_col:
            st.caption("Examples: leave policy, maternity leave, reimbursement, work-from-home, performance review.")
        if pressed:
            if question.strip():
                answer_question(question.strip())
            else:
                st.warning("Please enter an HR question.")


def render_admin_panel() -> None:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-heading">
                <div>
                    <h2>HR Administrator Panel</h2>
                    <p>Manage policy document ingestion, replacement, and deletion.</p>
                </div>
                <span class="badge">Admin</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.2, 0.8], gap="large")
    with left_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload HR policy PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload policy versions to append or replace indexed documents.",
        )
        document_type = st.selectbox("Document type", HR_DOCUMENT_TYPES, index=0)
        replace_existing = st.checkbox("Replace existing document with the same filename", value=True)

        if uploaded_files and st.button("Ingest Uploaded PDFs", use_container_width=True):
            try:
                results = ingest_uploaded_documents(uploaded_files, document_type=document_type, replace_existing=replace_existing)
                st.success(f"Indexed {len(results)} document(s) successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to ingest uploaded PDFs: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        docs = list_indexed_documents()
        if docs:
            sources = [doc["source"] for doc in docs]
            selected_source = st.selectbox("Select document to delete", sources)
            if st.button("Delete Document", use_container_width=True):
                if delete_document(selected_source):
                    st.success(f"Deleted {selected_source}.")
                    st.rerun()
                else:
                    st.warning("Document not found in the index.")
        else:
            st.info("No indexed documents yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    docs = list_indexed_documents()
    if docs:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Indexed Documents")
        for doc in docs:
            st.markdown(
                f"- **{doc['source']}** | {doc['document_type']} | {doc['pages']} page(s) | {doc['chunks']} chunk(s) | Updated: {doc['uploaded_at']}"
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_system_status() -> None:
    stats = get_database_statistics()
    gemini = cached_gemini_status()
    st.markdown(
        """
        <div class="panel">
            <div class="panel-heading">
                <div>
                    <h2>System Status Panel</h2>
                    <p>Live operational snapshot of the knowledge base and Gemini connectivity.</p>
                </div>
                <span class="badge">Live status</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        render_metric("Indexed Documents", stats["documents_indexed"])
    with col2:
        render_metric("Indexed Chunks", stats["chunks_indexed"])
    with col3:
        render_metric("Last Indexing", stats.get("last_indexing_timestamp") or "Not indexed yet")
    with col4:
        status_text = f"Connected" if gemini["ok"] else gemini["message"]
        render_metric("Gemini Status", status_text)


def render_sidebar(stats: Dict[str, Any]) -> None:
    st.sidebar.markdown("## HR Assist Pro")
    st.sidebar.caption("Enterprise HR policy retrieval and workflow automation")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Snapshot**")
    st.sidebar.metric("Documents", stats.get("documents_indexed", 0))
    st.sidebar.metric("Chunks", stats.get("chunks_indexed", 0))
    st.sidebar.metric("Last Indexing", stats.get("last_indexing_timestamp") or "Not indexed")
    gemini = cached_gemini_status()
    st.sidebar.metric("Gemini", "Connected" if gemini["ok"] else gemini["message"])
    st.sidebar.caption(gemini["message"])


def main() -> None:
    bootstrap_result = {"bootstrapped": False, "ingested": []}
    try:
        bootstrap_result = bootstrap_knowledge_base()
    except Exception as exc:
        st.warning(f"Sample knowledge base bootstrap was skipped: {exc}")
    stats = get_database_statistics()
    render_sidebar(stats)
    st.markdown(APP_CSS, unsafe_allow_html=True)
    render_hero()

    if bootstrap_result.get("bootstrapped"):
        st.info("The sample HR policy library was indexed automatically for immediate use.")

    tab_employee, tab_admin, tab_status = st.tabs(["Employee Portal", "HR Administrator Panel", "System Status"])

    with tab_employee:
        render_employee_portal()

    with tab_admin:
        render_admin_panel()

    with tab_status:
        render_system_status()


if __name__ == "__main__":
    main()
