# Architecture Overview

## System Architecture

HR Assist Pro is built as a modular RAG (Retrieval-Augmented Generation) system with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────┐
│                       User Interface Layer                        │
│                    (Streamlit Web Framework)                      │
├─────────────────────────────────────────────────────────────────┤
│                     Application Logic Layer                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐   │
│  │  Employee    │  Admin       │  System      │  Security    │   │
│  │  Portal      │  Dashboard   │  Status      │  Guardrails  │   │
│  └──────────────┴──────────────┴──────────────┴──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      RAG Pipeline Layer                           │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐   │
│  │  Document    │  Retrieval   │  Reranking   │  Generation  │   │
│  │  Ingestion   │  (ChromaDB)  │  (FlashRank) │  (Gemini)    │   │
│  └──────────────┴──────────────┴──────────────┴──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                  Data Storage & Integration Layer                │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐   │
│  │  ChromaDB    │  PDF Files   │  Metadata    │  External    │   │
│  │  (Vectors)   │  (Storage)   │  (Indexing)  │  APIs        │   │
│  └──────────────┴──────────────┴──────────────┴──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Presentation Layer (Streamlit)
- **Location**: `app.py`
- **Responsibilities**:
  - User interface management
  - Session state handling
  - Tab-based navigation
  - Form input/output
- **Technologies**:
  - Streamlit >= 1.36.0
  - Custom CSS styling
  - Dynamic component rendering

### 2. Security Layer (Guardrails)
- **Location**: `guardrails.py`
- **Responsibilities**:
  - Prompt injection detection
  - Harmful request filtering
  - HR question validation
  - Input sanitization
- **Key Functions**:
  - `validate_user_input()` - Input validation
  - `is_hr_question()` - Domain checking
  - `detect_prompt_injection()` - Security check

### 3. Document Ingestion (PDF Processing)
- **Location**: `ingest.py`
- **Responsibilities**:
  - PDF parsing and extraction
  - Document chunking
  - Metadata management
  - Vector embedding
- **Key Functions**:
  - `ingest_uploaded_documents()` - Upload handling
  - `bootstrap_knowledge_base()` - Initialize with samples
  - `list_indexed_documents()` - Document listing

### 4. RAG Pipeline (Core Logic)
- **Location**: `rag_pipeline.py`
- **Responsibilities**:
  - Query embedding
  - Semantic search
  - Chunk retrieval
  - Citation formatting
- **Key Functions**:
  - `retrieve_chunks()` - Semantic search
  - `format_retrieved_citations()` - Citation generation

### 5. Reranking Layer
- **Location**: `reranker.py`
- **Responsibilities**:
  - Result reranking
  - Relevance scoring
  - Quality filtering
- **Key Functions**:
  - `rerank_chunks()` - FlashRank reranking
  - `calculate_relevance_score()` - Scoring

### 6. Language Model Integration
- **Location**: `llm.py`
- **Responsibilities**:
  - API communication
  - Response generation
  - Hallucination detection
  - Fallback handling
- **Key Functions**:
  - `get_gemini_client()` - API initialization
  - `generate_answer()` - Answer generation
  - `verify_output()` - Hallucination check

### 7. Utilities & Configuration
- **Location**: `utils.py`, `config.py`, `logging_config.py`
- **Responsibilities**:
  - Configuration management
  - Logging setup
  - Helper functions
  - File operations

## Data Flow

### Query Processing Flow

```
User Query
    ↓
Input Validation (Guardrails)
    ↓
Embedding Generation
    ↓
ChromaDB Semantic Search (Top-20)
    ↓
FlashRank Reranking (Top-5)
    ↓
Context Preparation
    ↓
Gemini LLM Generation
    ↓
Hallucination Detection
    ↓
Citation Formatting
    ↓
Response Delivery
```

### Document Ingestion Flow

```
PDF Upload
    ↓
PDF Parsing
    ↓
Text Extraction
    ↓
Chunking (500 tokens, 100 overlap)
    ↓
Embedding Generation
    ↓
Metadata Extraction
    ↓
ChromaDB Storage
    ↓
Index Update
    ↓
Status Reporting
```

## Technology Stack

### Frontend
- **Streamlit**: Web framework
- **CSS/HTML**: Custom styling
- **Session State**: Session management

### Backend
- **Python 3.9+**: Core language
- **ChromaDB**: Vector database
- **Google Generative AI**: LLM provider
- **PyPDF**: PDF processing
- **FlashRank**: Reranking engine
- **ReportLab**: PDF generation

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **GitHub Actions**: CI/CD

### Database
- **ChromaDB**: Vector embeddings
- **SQLite**: Metadata storage
- **File System**: PDF storage

## Scalability Considerations

### Horizontal Scaling
- Multiple Streamlit instances behind load balancer
- Shared ChromaDB instance
- Distributed PDF storage

### Vertical Scaling
- Larger vector database
- Batch processing
- Caching layer (Redis)

### Performance Optimization
- Query caching
- Batch embeddings
- Async processing
- Database indexing

## Security Architecture

### Input Security
- Prompt injection detection
- SQL injection prevention
- File upload validation
- Size limits

### Data Security
- API key management via env vars
- Encrypted connections
- Access control
- Audit logging

### API Security
- Rate limiting
- Authentication tokens
- Request validation
- Error handling

## Monitoring & Observability

### Logging
- Application logs in `logs/` directory
- Rotating file handlers
- Console output
- Structured logging

### Metrics
- Document count
- Query count
- Response times
- Error rates
- API usage

### Health Checks
- API connectivity
- Database status
- System resources
- Endpoint availability

## Deployment Architecture

### Development
- Local machine
- Virtual environment
- SQLite storage
- Development API keys

### Staging
- Docker containers
- Persistent volumes
- Test data
- Staging API keys

### Production
- Kubernetes/Docker Swarm
- Load balancing
- Auto-scaling
- Backup strategy
- Monitoring/Alerting

## Configuration Management

Settings stored in `config.py`:
- Chunk size and overlap
- Model parameters
- Feature flags
- Security settings
- Paths and directories

---

**Last Updated:** 2026-06-18
