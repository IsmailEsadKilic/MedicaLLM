# Senior Design Project — Semester 2 Final Report

## MedicaLLM: Agentic AI Drug Consultant For Doctors And Patients

### Group Members

- İsmail Esad Kılıç — 221401004
- Arda Ünal — 210402023
- Özge Şahin — 210402009
- Doğukan Gökduman — 210402002

**Project Supervisor:** Prof. Dr. Uğur Sezerman

---

## 1. Project Summary & Context

### 1.1 Project Overview

MedicaLLM is an agentic AI-powered drug consultation platform designed to serve as an intelligent medical information assistant for both healthcare professionals and the general public. The system combines a Large Language Model (LLM) agent with structured drug databases, a Retrieval-Augmented Generation (RAG) pipeline, and live biomedical literature search to deliver accurate, context-grounded, and personalized responses to drug-related queries. The project is developed under the supervision of Prof. Dr. Uğur Sezerman as a CSE 401/402 Senior Design Project.

MedicaLLM addresses a critical gap in medical information accessibility: medication errors and adverse drug interactions remain a leading cause of preventable harm in healthcare worldwide. Physicians frequently prescribe drugs outside their primary specialty and may lack immediate awareness of contraindications; patients, on the other hand, often struggle to understand complex pharmacological information. Existing reference tools tend to be fragmented, overly technical, or disconnected from a patient's individual medical context. MedicaLLM bridges these gaps by providing a unified, conversational interface that can look up drug information, check drug-drug and drug-food interactions, search medical literature, and generate personalized analyses based on a patient's health profile — all through natural language.

### 1.2 Problem Statement

The specific problems MedicaLLM aims to solve are:

1. **Medication Errors and Harmful Drug Interactions:** Adverse drug-drug interactions (DDIs) are a significant source of morbidity and mortality. Clinicians managing patients with polypharmacy (multiple concurrent medications) need rapid, reliable interaction checks that go beyond simple yes/no lookups and provide mechanistic explanations.
2. **Cross-Specialty Knowledge Gaps:** A cardiologist may not be fully aware of the interaction profile of a newly prescribed dermatological agent, and vice versa. There is a need for a system that consolidates pharmacological knowledge from a comprehensive, authoritative dataset (DrugBank) and makes it instantly queryable.
3. **Patient Comprehension Barriers:** Medical literature and drug labels are written for professionals. Patients who wish to understand their medications — their purpose, side effects, dietary restrictions, and interactions — lack a tool that explains these topics in accessible language while remaining medically accurate.
4. **Fragmented Information Landscape:** Drug information is scattered across databases (DrugBank, PubMed, clinical guidelines PDFs). A physician or patient currently needs to consult multiple sources and synthesize the results manually. MedicaLLM aggregates these heterogeneous sources into a single intelligent interface.
5. **Lack of Personalized Recommendations:** Generic drug interaction checkers do not account for a specific patient's chronic conditions, current medications, and known allergies. MedicaLLM integrates patient health records to provide truly personalized medical assessments.

### 1.3 Application Domain

MedicaLLM operates at the intersection of clinical decision support, pharmaceutical informatics, and conversational AI. The application domain encompasses:

- **Pharmacovigilance:** Real-time detection and explanation of potential drug-drug interactions, drug-food interactions, and contraindications.
- **Clinical Information Retrieval:** On-demand lookup of drug properties including mechanism of action, indication, pharmacokinetics (absorption, metabolism, half-life, protein binding, route of elimination), toxicity, and therapeutic categories.
- **Biomedical Literature Access:** Automated search and summarization of published research from PubMed, the premier biomedical literature database maintained by the U.S. National Library of Medicine.
- **Patient Record Management and Analysis:** Structured storage and AI-driven analysis of patient profiles, including chronic conditions, allergies, and current medication regimens.
- **Medical Document Intelligence:** RAG-based question answering over clinical and medical reference documents in PDF format.

### 1.4 Target Users

MedicaLLM is designed with a dual-audience architecture that distinguishes between two primary user categories:

**Healthcare Professionals (Doctors, Pharmacists, Clinicians)**

- Access comprehensive drug information with full pharmacological detail (mechanism of action, pharmacodynamics, pharmacokinetics, metabolism, toxicity).
- Check drug-drug and drug-food interactions with clinical-grade descriptions sourced from DrugBank.
- Manage patient profiles with structured records of chronic conditions, allergies, current medications.
- Generate AI-powered patient profile analyses that cross-reference a patient's full medication list for potential interactions, flag allergy conflicts, and provide evidence-based recommendations.
- Search PubMed for the latest clinical studies and evidence-based findings relevant to a patient's treatment plan.

**General Users (Patients, Caregivers)**

- Ask natural-language questions about their medications and receive clear, jargon-free explanations.
- Check whether their current medications interact with each other or with specific foods.
- Look up what a prescribed drug does, its common side effects, and how it should be taken.
- Receive safety-conscious responses that consistently recommend consulting a healthcare provider for definitive medical decisions.

The system enforces role-based access through its authentication module: users register as either `general_user` (patient) or `doctor` (healthcare professional), and certain features (such as the patient management module and patient-aware chat) are restricted exclusively to healthcare professional accounts.

### 1.5 System Architecture Summary

MedicaLLM is built as a containerized full-stack web application with two Docker Compose services (frontend + backend) connected to a managed cloud PostgreSQL database. The following describes the system's final state after all Semester 2 implementation work.

- **Frontend:** A React 18 single-page application (Vite build → Nginx production server) with a ChatGPT-style conversational interface featuring real-time SSE streaming, a drug search and interaction-checking page, patient management views, a PDF preview side panel, confidence score breakdowns, and theme support (dark/light).
- **Backend:** A Python FastAPI server with a modular, domain-driven package structure. Separate modules for authentication, agent orchestration, drug services, user/patient management, conversations, PubMed integration, embedding/RAG processing, session management, and middleware. Exposes a RESTful API with streaming (SSE) response mode as the primary chat interface.
- **AI Agent:** A ReAct (Reasoning + Acting) agent built with LangGraph and powered by Digital Ocean AI (OpenAI-compatible endpoint). The agent autonomously selects from **10 tools**: drug info lookup, multi-drug interaction checking, drug-food interaction checking, drug search by indication, drug search by category, alternative drug recommendation, overdose/duplicate ingredient detection, patient medication analysis, PubMed literature search, and PubMed multi-query search.
- **Database:** DigitalOcean Managed PostgreSQL with pgvector extension for semantic search and pg_trgm for fuzzy text matching. SQLAlchemy ORM with comprehensive relational schema (drugs, synonyms, categories, interactions, food interactions, dosages, targets, enzymes, carriers, transporters, embeddings, users, conversations, patients, doctors, doctor-patient associations).
- **Vector Store:** ChromaDB with HuggingFace embeddings (nomic-ai/nomic-embed-text-v1) for semantic search over medical PDF document chunks. Additionally, pgvector-based drug embeddings (768-dimensional) with HNSW indexing for semantic drug search.
- **Data Sources:** DrugBank XML (~14,000 drugs, parsed and seeded into PostgreSQL), PubMed via NCBI E-utilities (with Scopus citation metrics integration), and locally stored medical PDF documents processed through a RAG chunking pipeline.

---

## 2. MVP Recap (Semester 1)

### 2.1 MVP Objectives

The Semester 1 MVP was scoped to demonstrate the core technical feasibility of the MedicaLLM concept and build a functional prototype. The goal was to validate the key architectural components (a working LLM agent with tool-calling, an operational RAG pipeline, a functional authentication system, drug database integration, and a user interface) as the foundation on which the full system would be built during Semester 2.

### 2.2 Implemented Features (End of Semester 1)

#### 2.2.1 User Interface & Design

- Chat Interface: A ChatGPT-style conversational window with message bubbles, typing indicators, and an input area.
- Drug Interaction Query Page: A dedicated interface where users can enter drug names to check for potential interactions.
- Login & Registration Pages: Fully designed authentication screens with form validation.
- Responsive Layout: Collapsible sidebar for conversation management.
- Theme Support: Both dark and light themes with a toggle switch.

#### 2.2.2 Authentication System

- JWT-based authentication with bcrypt password hashing.
- Two account types: `general_user` and `healthcare_professional`.
- Token storage in localStorage and token-based header injection for API calls.

#### 2.2.3 Working LLM Chatbot Prototype

- Functional chatbot generating natural-language responses using a hosted LLM.
- Multi-turn conversation flow with message formatting and UI rendering.
- Not yet grounded in the authoritative drug database at D2 time.

#### 2.2.4 RAG Pipeline Prototype

- PDF Document Loading via PyPDFLoader and DirectoryLoader.
- Text Chunking using RecursiveCharacterTextSplitter.
- Embedding Generation using HuggingFace sentence-transformers.
- Vector Storage in ChromaDB with persistent retrieval.
- Top-k Similarity Retrieval and LLM + RAG Integration.

#### 2.2.5 Agent/Tool Architecture (Designed but Not Connected at D2)

- Planned tools defined; agent workflow specified.
- Connected during post-D2 restructuring.

### 2.3 Late Semester 1 Additions (Post-D2)

#### 2.3.1 PubMed Literature Search Integration

- Live PubMed search via pymed library.
- DynamoDB caching layer with normalized query hash.
- Automatic ChromaDB indexing of fetched abstracts.

#### 2.3.2 Complete Project Restructuring

- Eliminated the Node.js/TypeScript backend entirely.
- Consolidated into a single Python FastAPI application with domain-driven package structure.
- Simplified Docker Compose from four to three services.

### 2.4 MVP Capabilities Summary

| Feature | Status |
|---------|--------|
| Chat UI (conversational interface) | Fully implemented |
| Authentication (login/register) | Fully implemented |
| RAG pipeline (PDF → chunks → embeddings → retrieval) | Fully implemented |
| LLM chatbot (natural language responses) | Fully implemented |
| Drug information lookup (DrugBank) | Fully implemented |
| Drug-drug interaction checking | Fully implemented |
| Drug-food interaction checking | Fully implemented |
| Drug search by indication/category | Fully implemented |
| PubMed literature search | Fully implemented |
| Patient management (CRUD) | Fully implemented |
| Agent tool-calling (ReAct) | Fully implemented (6 tools) |
| Conversation persistence | Fully implemented |
| Streaming responses (SSE) | Backend only |
| Project restructuring (unified backend) | Completed |

---

## 3. MVP Evaluation & Limitations (Pre-Semester 2)

### 3.1 Technical Limitations

- **In-Memory Session Store:** No eviction, TTL, or cleanup mechanism. Memory leak risk.
- **Redundant LLM Calls:** RAG and PubMed tools made internal LLM calls, doubling cost/latency.
- **Thread-Unsafe Globals:** Module-level mutable state in tools.py caused race conditions.
- **Scan-Based Drug Search:** O(n) DynamoDB scans for drug lookup.
- **No Pagination:** Drug search capped at 50 results with no cursor.
- **Full Conversation Re-serialization:** Entire conversation read/written per message.

### 3.2 Security Concerns

- No input sanitization for LLM prompts (prompt injection risk).
- No rate limiting on any endpoint.
- No HTTPS enforcement.
- Weak default JWT secret.

### 3.3 Missing Features

- No differentiated explanation levels (doctor vs. patient).
- No multi-drug interaction checking (only pairwise).
- No drug interaction severity classification.
- No automated patient medication analysis.
- No streaming in the frontend.
- Zero automated tests.
- No proper logging/monitoring.

### 3.4 Infrastructure Issues

- Frontend ran Vite dev server as "production."
- No Docker health checks.
- Local-only deployment with no CI/CD.

### 3.5 Performance Concerns

#### 3.5.1 Response Latency

The system's response time for a typical query involved multiple sequential operations:

1. The agent processes the conversation history and user query through the LLM.
2. The LLM decides which tool to call and the agent invokes it.
3. For drug lookups, the tool queries DynamoDB.
4. For RAG or PubMed queries, the tool performs retrieval AND an additional LLM call.
5. The agent processes the tool result through the LLM again to generate the final response.

End-to-end latency for a RAG or PubMed query could reach **10-15 seconds**, which is a poor user experience compared to the near-instant responses users expect from chat interfaces.

#### 3.5.2 Conversation History Growth

Because the full conversation history is sent to the LLM on every turn, token usage and cost grow linearly with conversation length. A conversation with 20 exchanges could consume 8,000+ input tokens per query. There was no summarization, truncation, or sliding-window strategy to bound the context size.

### 3.6 Limitations Summary

| Priority | Category | Limitation |
|----------|----------|------------|
| **P0** | Security | No input sanitization (prompt injection risk) |
| **P0** | Security | No rate limiting on any endpoint |
| **P0** | Quality | Zero automated tests for a medical application |
| **P1** | Performance | Double LLM invocation on RAG/PubMed queries |
| **P1** | Performance | Full conversation re-serialization per message |
| **P1** | Feature Gap | No differentiated explanation levels (doctor vs. patient) |
| **P1** | Feature Gap | No multi-drug interaction checking |
| **P1** | Feature Gap | No interaction severity classification |
| **P1** | Usability | No streaming responses in frontend |
| **P1** | Infra | Memory leak in session store |
| **P2** | Performance | Scan-based drug search (O(n) per query) |
| **P2** | Performance | Unbounded conversation history token growth |
| **P2** | Infra | Frontend runs dev server in Docker |
| **P3** | Feature Gap | No logging/monitoring/audit trail |
| **P3** | Usability | Limited error communication |
| **P3** | Infra | No CI/CD pipeline or cloud deployment |

---

## 4. Semester 2 Objectives

### 4.1 Tier 1: Completion of Existing Features

| ID | Objective | Priority |
|----|-----------|----------|
| O1 | Eliminate redundant LLM calls & optimize performance | High |
| O2 | Frontend streaming integration (SSE) | High |
| O3 | Session management hardening (TTL, eviction) | Medium |
| O4 | Security hardening (rate limiting, JWT validation) | High |
| O5 | Production-ready infrastructure (Nginx, health checks) | Medium |

### 4.2 Tier 2: New Feature Objectives

| ID | Objective | Priority |
|----|-----------|----------|
| O6 | Enhanced PubMed search with PDF retrieval | High |
| O7 | Citation-based credibility analysis | Low |
| O8 | PDF preview side panel | High |
| O9 | Alternative drug recommendation | High |
| O10 | Patient-aware response generation | High |
| O11 | Protection of sensitive information (TLS) | High |
| O12 | Real-time voice conversation | Medium |
| O13 | Dashboard / Admin panel | Medium |

---

## 5. Semester 2 Implementation Results

This section documents what was actually implemented during Semester 2, based on the codebase changes after commit `d2fc23dfced53de47e8b49dcec10c608104431e7` (March 1, 2026). A total of **29 commits** were made, modifying **111 files** with **18,436 insertions** and **9,269 deletions**.

### 5.1 Major Architectural Changes

#### 5.1.1 Database Migration: DynamoDB → PostgreSQL (Completed)

The most significant architectural change of Semester 2 was the complete migration from Amazon DynamoDB Local to **DigitalOcean Managed PostgreSQL**. This addressed multiple Semester 1 limitations simultaneously:

**What changed:**
- Replaced all DynamoDB tables with a comprehensive relational schema using SQLAlchemy ORM.
- Introduced **pgvector** extension for native vector similarity search (drug embeddings).
- Introduced **pg_trgm** extension for fuzzy text matching on drug names and synonyms.
- Created a normalized relational schema with proper foreign keys, indexes, and cascading deletes.

**New database tables:**
- `drugs` — Core drug records with full pharmacological fields
- `drug_synonyms` — Drug name synonyms with trigram indexes
- `drug_groups` — Regulatory groups (approved, experimental, etc.)
- `drug_categories` — Therapeutic categories with trigram indexes
- `drug_products` — Commercial product information
- `drug_references` — Literature references (PubMed IDs, ISBNs)
- `drug_food_interactions` — Food interaction records
- `drug_dosages` — Dosage forms and routes
- `drug_international_brands` — International brand names
- `drug_mixtures` — Combination products
- `drug_atc_codes` — ATC classification codes
- `drug_external_identifiers` — Cross-references to external databases
- `drug_targets` — Pharmacological targets with actions
- `drug_enzymes` — Metabolizing enzymes
- `drug_carriers` — Drug carriers
- `drug_transporters` — Drug transporters
- `drug_interactions` — Drug-drug interaction records with descriptions
- `drug_embeddings` — 768-dimensional vector embeddings with HNSW index
- `users` — User accounts with role information
- `conversations` — Chat conversation records (JSON-serialized messages)
- `patients` — Patient profiles (conditions, medications, allergies)
- `doctors` — Doctor profiles with specialties
- `doctor_patient_associations` — Many-to-many doctor-patient relationships

**Benefits achieved:**
- Eliminated O(n) scan-based drug search — replaced with indexed queries and trigram fuzzy matching.
- Enabled semantic drug search via pgvector HNSW approximate nearest neighbor.
- Proper relational integrity with foreign keys and cascading deletes.
- Connection pooling (pool_size=10, max_overflow=20) with pre-ping health checks.
- Cloud-hosted database eliminates local data loss risk.

#### 5.1.2 LLM Provider Migration: Amazon Bedrock → DigitalOcean AI (Completed)

**What changed:**
- Replaced Amazon Bedrock (Claude) with DigitalOcean AI inference endpoint (OpenAI-compatible API).
- Model: `openai-gpt-oss-120b` (configurable via environment variable).
- Uses `langchain-openai` ChatOpenAI client with custom base URL (`https://inference.do-ai.run/v1`).
- Streaming enabled by default (`llm_streaming: True`).

**Rationale:** Reduced dependency on AWS-specific services, simplified credential management, and provided a cost-effective alternative with OpenAI-compatible API surface.

#### 5.1.3 Project Structure Reorganization (Completed)

The backend was reorganized into a cleaner domain-driven structure:

```
backend/src/
├── main.py              # FastAPI app, lifespan, router registration
├── config.py            # Pydantic Settings with env validation
├── colored_logging.py   # Custom colored logging utility
├── agent/               # LLM agent (agent.py, langchain_agent.py, tools.py, source_tracker.py)
├── auth/                # Authentication (service.py, router.py, models.py, dependencies.py)
├── conversations/       # Chat persistence (service.py, router.py, models.py)
├── drugs/               # Drug data access (service.py, router.py, models.py, calculate_severity.py, embedding_service.py)
├── users/               # User & patient management (service.py, router.py, models.py)
├── admin/               # Admin panel (router.py, service.py)
├── pubmed/              # PubMed integration (service.py, router.py, models.py, scoring.py, query_classifier.py, scopus_service.py, pdf_downloader.py)
├── embedding/           # RAG pipeline (vector_store.py, pdf_processor.py, router.py)
├── session/             # Session management (session.py, session_manager.py, router.py)
├── middleware/          # Rate limiter
└── db/                  # Database (sql_client.py, sql_models.py, init_tables.py)
```

Notable changes from Semester 1:
- `patients/` module merged into `users/` with doctor-patient association model.
- New `session/` module extracted from agent router for clean separation.
- New `admin/` module for admin panel authentication.
- `rag/` renamed to `embedding/` for clarity.
- New `middleware/` module for rate limiting.
- `printmeup/` custom logging moved to `legacy/`.

### 5.2 Objective Completion Status

#### O1: Eliminate Redundant LLM Calls — ✅ COMPLETED

**Implementation:**
- Refactored all agent tools to return raw retrieved content directly to the agent.
- Tools are now pure data-retrieval functions — no internal LLM summarization calls.
- The agent's single LLM invocation handles all synthesis and response generation.
- System prompt updated with comprehensive instructions for synthesizing raw tool output into well-cited responses.

**Evidence in code:**
- `backend/src/agent/tools.py` — All 10 tools return structured text data without instantiating separate LLM clients.
- `backend/src/agent/langchain_agent.py` — Detailed system prompt with "TOOLS FIRST — ALWAYS" principle and synthesis guidelines.

#### O2: Frontend Streaming Integration — ✅ COMPLETED

**Implementation:**
- Chat.jsx refactored to consume SSE via `fetch` + `response.body.getReader()` with `ReadableStream`.
- Progressive content rendering with `streamingContent` state variable.
- Real-time token-by-token display with streaming cursor.
- Thinking step indicators (`thinkingStep` state) shown during agent processing.
- Tool execution events displayed in real-time (tool start/end with execution time).
- Error handling for network disconnections mid-stream.
- Backend endpoint: `POST /api/session/query-stream` returns `text/event-stream`.

**SSE Event Types:**
- `thinking` — Processing status updates
- `content` — Token-by-token response content
- `tool_start` / `tool_end` — Tool execution lifecycle with timing
- `done` — Final response with sources, debug info, and metadata
- `error` — Error events

#### O3: Session Management Hardening — ✅ COMPLETED

**Implementation:**
- Replaced unbounded `dict` with `cachetools.TTLCache` (max 100 sessions, 30-minute TTL).
- `SessionManager` class with thread-safe operations (`threading.Lock`).
- Automatic LRU eviction when cache is full.
- Manual eviction support via `evict()` method.
- Periodic health-check background task (every 5 minutes) logs active session count.
- Eliminated thread-unsafe module-level globals in `tools.py`:
  - Replaced with `ContextVar` + shared thread-safe dict pattern.
  - `_request_id_var` propagates request identity to thread-pool workers.
  - `_source_store` and `_debug_store` use lock-protected dict operations.

**Configuration (via environment):**
- `max_n_sessions`: 100
- `session_ttl_seconds`: 1800 (30 minutes)

#### O4: Security Hardening — ✅ PARTIALLY COMPLETED

**Implemented:**
- **Rate Limiting:** `slowapi` integrated as FastAPI middleware with three tiers:
  - LLM endpoints: 10 requests/minute per user
  - Search endpoints: 60 requests/minute per user
  - Auth endpoints: 20 requests/minute per IP
- Per-user bucketing via JWT extraction (falls back to IP for unauthenticated requests).
- Rate limit configuration via environment variables (`llm_limit`, `search_limit`, `auth_limit`).

**Not implemented:**
- Input sanitizer middleware (prompt injection blocklist) — not present in codebase.
- PII stripper middleware — not present in codebase.
- JWT secret startup validation (weak secret rejection) — not enforced; default remains `"supersecretkey"`.

#### O5: Production-Ready Infrastructure — ✅ COMPLETED

**Implementation:**
- **Multi-stage Nginx frontend build:**
  - Stage 1: `node:20-alpine` runs `npm run build` for optimized static assets.
  - Stage 2: `nginx:1.27-alpine` serves compiled assets with custom `nginx.conf`.
  - SPA routing fallback (`try_files $uri $uri/ /index.html`).
  - Gzip compression enabled for text/CSS/JS/JSON/XML/SVG.
  - Aggressive caching for static assets (`expires 1y`, `Cache-Control: public, immutable`).
  - API proxy to backend with SSE/streaming support (`proxy_buffering off`).
- **Docker health checks:**
  - Frontend: `wget -q --spider http://localhost:80/`
  - Backend: `GET /health` endpoint returns `{"status": "ok"}`.
  - `depends_on` with `condition: service_healthy` for proper startup ordering.
- **Nginx SSL configuration** (`nginx-ssl.conf`) prepared for TLS termination.
- **VITE_USE_HTTPS** build-time flag for HTTPS URL configuration.
- Docker Compose simplified to 2 services (frontend + backend) with managed cloud database.

#### O6: Enhanced PubMed Search with PDF Retrieval — ✅ COMPLETED

**Implementation:**
- `backend/src/pubmed/pdf_downloader.py` — Full PDF download pipeline:
  - Downloads from PubMed Central (PMC) open-access, DOI-based URLs, and fallback sources.
  - LRU cache with configurable size limit and automatic eviction of least-recently-used PDFs.
  - Async download support (`download_pdf_async`) for non-blocking operation.
  - File-based metadata cache scanned on startup (`initialize_cache()`).
  - Storage in `data/pdf/pubmed_downloads/`.
- `backend/src/pubmed/router.py` — `GET /api/pubmed/pdf/{pmid}` endpoint:
  - Authenticated (requires JWT).
  - Downloads on-demand if not cached.
  - Returns `FileResponse` for direct PDF serving.
  - Graceful 404 with helpful error message when PDF unavailable.
- **Multi-query PubMed search** (`search_pubmed_multi` tool):
  - Accepts 2-3 focused sub-queries for multi-faceted clinical questions.
  - Merges and deduplicates results across queries.
  - Ranked by composite confidence score.

#### O7: Citation-Based Credibility Analysis — ✅ COMPLETED

**Implementation:**
- `backend/src/pubmed/scopus_service.py` — Full Scopus API integration:
  - Citation count retrieval by PMID via Scopus Search API.
  - Journal-level metrics via Serial Title API (CiteScore, SJR, SNIP, percentile).
  - Field-Weighted Citation Impact (FWCI) via Abstract Retrieval API.
  - Per-instance ISSN → journal metrics cache to avoid repeat API calls.
  - Graceful degradation when API key not configured.
- `backend/src/pubmed/scoring.py` — Composite confidence scoring:
  - Multi-dimensional scoring: citations, FWCI, journal quality, recency, evidence level, relevance.
  - Log-scaled citation normalization (0-1000 range).
  - Evidence level scoring by publication type (meta-analysis > RCT > cohort > case report).
  - Recency scoring with configurable decay.
  - Quality warnings for low-confidence articles.
- `backend/src/pubmed/query_classifier.py` — Adaptive scoring weights:
  - Query type detection (author-specific, drug research, clinical guideline, review/meta, recent advances).
  - LLM-assisted classification for ambiguous queries.
  - Per-type weight profiles (e.g., author-specific prioritizes recency; reviews prioritize citations).
  - Configurable impact score boosting via `boost_impact_score_weights` setting.
- `frontend/src/components/ConfidenceBreakdown.jsx` — Visual confidence display:
  - Shows individual score components (citations, FWCI, journal quality, recency, evidence level, relevance).
  - Progress bars with percentage scores.

#### O8: PDF Preview Side Panel — ✅ COMPLETED

**Implementation:**
- `frontend/src/pages/PdfPanel.jsx` — Embedded PDF viewer component:
  - Resizable split-panel layout alongside chat interface.
  - Fetches PDF via authenticated backend endpoint (JWT in Authorization header).
  - Creates Blob URL for iframe rendering.
  - Fallback to abstract display when PDF unavailable.
  - Page navigation support.
  - Proper cleanup (Blob URL revocation on close).
- Integration in `Chat.jsx`:
  - `pdfPanel` state tracks active PDF source and page.
  - "View Source" buttons on PubMed-sourced responses.
  - Pre-loaded article data passed to avoid redundant API calls.

#### O9: Alternative Drug Recommendation — ✅ COMPLETED

**Implementation:**
- `recommend_alternative_drug` tool in `backend/src/agent/tools.py`:
  - Takes `current_drug_names` (patient's medications) and `for_drug_name` (drug to replace).
  - Looks up original drug's indication and therapeutic categories.
  - Searches for drugs with matching categories via `search_drugs_by_category()`.
  - Filters out candidates that interact with patient's current medications.
  - Returns ranked list of safe alternatives with indications.
- Frontend (`DrugSearch.jsx`):
  - "Suggested Alternatives" section designed and coded (currently commented out pending dedicated backend REST endpoint — the tool works via the agent chat interface).

#### O10: Patient-Aware Response Generation — ✅ COMPLETED

**Implementation:**
- **Dynamic system prompt construction** (`build_system_prompt()` in `langchain_agent.py`):
  - Role context block: Clinical terminology for `doctor`, simplified language for `general_user`.
  - Patient context block: Injected when `patient_id` provided — includes name, DOB, gender, chronic conditions, current medications, known allergies, and clinical notes.
  - Explicit rules for automatic patient medication analysis when drugs are mentioned.
- **Patient selector in chat** (`Chat.jsx`):
  - Dropdown for healthcare professionals to select active patient.
  - Patient list fetched from `GET /api/users/doctors/patients`.
  - `patient_id` included in query requests to backend.
- **`analyze_patient_medications` tool:**
  - Accepts `additional_drugs` parameter for drugs mentioned in conversation.
  - Loads patient profile via `_current_patient_id_var` context variable.
  - Runs all pairwise interaction checks between patient's medications + additional drugs.
  - Cross-references against patient's known allergies.
  - Returns structured report sorted by severity.
- **Doctor-Patient association model:**
  - `DoctorRecord`, `PatientRecord`, `DoctorPatientAssociation` in SQL schema.
  - Doctors can only access their associated patients.

#### O11: Protection of Sensitive Information — ✅ PARTIALLY COMPLETED

**Implemented:**
- Nginx SSL configuration file (`nginx-ssl.conf`) prepared for TLS termination.
- `VITE_USE_HTTPS` build-time flag for frontend HTTPS URL switching.
- LLM provider changed from Amazon Bedrock to DigitalOcean AI (reduces third-party data exposure surface).

**Not implemented:**
- PII stripper middleware.
- Self-hosted LLM feasibility study documentation.

#### O12: Real-Time Voice Conversation — ✅ PARTIALLY COMPLETED

**Implemented:**
- Speech-to-text via Web Speech API (`webkitSpeechRecognition`) in `Chat.jsx`.
- Microphone toggle button with listening state indicator.
- Transcribed text fed into chat input.

**Not implemented:**
- Text-to-speech synthesis of agent responses.
- Continuous mode with voice activity detection (VAD).
- Natural turn-taking.

#### O13: Dashboard / Admin Panel — ✅ COMPLETED

**Implementation:**
- `backend/src/admin/router.py` — Admin authentication endpoint (`POST /api/admin/login`).
- `frontend/src/pages/Admin.jsx` — Admin panel with:
  - Separate admin login (username/password, not JWT-based).
  - System statistics display.
  - User management (list all users, expand details).
  - Session-based admin authentication (`sessionStorage`).

### 5.3 Additional Features Implemented (Beyond Original Objectives)

#### 5.3.1 Overdose/Duplicate Ingredient Detection (New Tool)

- `check_for_overdose_interaction` tool detects when multiple drugs contain the same active ingredient.
- Prevents accidental overdose from duplicate therapy (e.g., Tylenol + Paracetamol both containing acetaminophen).

#### 5.3.2 Drug Interaction Severity Classification

- `backend/src/drugs/calculate_severity.py` — Regex-based severity classification:
  - **Contraindicated:** Absolute prohibition patterns.
  - **Critical:** Life-threatening outcomes (cardiac arrest, anaphylaxis, etc.).
  - **Major:** Serious adverse effects (serotonin syndrome, QT prolongation, hemorrhage, etc.).
  - **Moderate-High:** Significant pharmacokinetic changes.
  - Severity levels displayed with emoji indicators (🔴 MAJOR, 🟠 MODERATE, 🟡 MINOR, ✅ SAFE).

#### 5.3.3 Semantic Drug Search via Embeddings

- `backend/src/drugs/embedding_service.py` — Drug embedding generation:
  - Uses `sentence-transformers` with `nomic-ai/nomic-embed-text-v1` model.
  - Combines drug name, description, indication, mechanism of action, and categories into embedding text.
  - Stored in PostgreSQL via pgvector with HNSW index for fast approximate nearest neighbor search.
- `backend/scripts/generate_drug_embeddings.py` — Batch embedding generation script.

#### 5.3.4 Multi-Drug Interaction Checking

- `check_drug_interactions` tool now accepts a **list of 2+ drugs** and checks all pairwise combinations.
- Resolves drug names through synonyms for comprehensive matching.
- Returns all found interactions with severity classification.

#### 5.3.5 Source Tracking and Citation System

- `backend/src/agent/source_tracker.py` — Thread-safe source tracking across tool calls.
- Sources accumulated per request (not overwritten between tool calls).
- Each source tagged with originating tool name.
- Frontend displays sources with clickable references and PDF viewer integration.
- `frontend/src/components/MarkdownWithReferences.jsx` — Inline `[REF1]`, `[REF2]` rendered as clickable buttons linking to sources.

#### 5.3.6 Landing Page

- `frontend/src/pages/Landing.jsx` — Professional landing page with:
  - Feature showcase (drug lookup, interaction checking, PubMed research, PDF documents, patient profiles).
  - SVG icon components (no emoji dependencies).
  - Call-to-action navigation to login/register.

#### 5.3.7 Colored Logging

- `backend/src/colored_logging.py` — Custom logging utility with:
  - Color-coded console output by log level.
  - Simultaneous file logging to `logs/app.log`.
  - Suppression of verbose third-party library logs (httpx, httpcore, openai, urllib3).

---

## 6. Final System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                          │
│  React 18 + Vite Build → Nginx (port 80/443)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Chat    │ │  Drug    │ │  Admin   │ │ Landing  │           │
│  │(Streaming│ │  Search  │ │  Panel   │ │  Page    │           │
│  │  + PDF)  │ │          │ │          │ │          │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS / SSE
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI, port 8000)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Middleware Layer                       │    │
│  │  CORS │ Request Logging │ Rate Limiter (slowapi)         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Auth    │ │ Session  │ │  Drugs   │ │  PubMed  │           │
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │  Users   │ │  Convos  │ │  Admin   │                        │
│  │  Router  │ │  Router  │ │  Router  │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AI Agent (LangGraph ReAct)                   │    │
│  │  10 Tools │ Dynamic System Prompt │ Session Manager       │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────┬──────────────────┬───────────────────────────────┘
               │                  │
               ▼                  ▼
┌──────────────────────┐  ┌──────────────────────────────────────┐
│  DigitalOcean AI     │  │  DigitalOcean Managed PostgreSQL     │
│  (LLM Inference)     │  │  + pgvector + pg_trgm                │
│  openai-gpt-oss-120b │  │  ~14,000 drugs, users, conversations │
└──────────────────────┘  └──────────────────────────────────────┘
               │
               ▼
┌──────────────────────┐  ┌──────────────────────────────────────┐
│  NCBI E-utilities    │  │  Scopus API (Elsevier)               │
│  (PubMed Search)     │  │  Citation metrics, journal quality   │
└──────────────────────┘  └──────────────────────────────────────┘
```

### 6.2 Agent Tool Repertoire (Final: 10 Tools)

| # | Tool | Purpose |
|---|------|---------|
| 1 | `get_drug_info` | Retrieve comprehensive drug information (low/moderate/high detail) |
| 2 | `check_drug_interactions` | Check interactions between 2+ drugs with severity |
| 3 | `check_drug_food_interaction` | Check food interactions for a drug |
| 4 | `search_drugs_by_indication` | Find drugs for a medical condition |
| 5 | `search_drugs_by_category` | Find drugs in a therapeutic category |
| 6 | `recommend_alternative_drug` | Find safe alternatives considering patient's medications |
| 7 | `check_for_overdose_interaction` | Detect duplicate active ingredients (overdose risk) |
| 8 | `analyze_patient_medications` | Comprehensive patient medication analysis |
| 9 | `search_pubmed` | Search PubMed with confidence scoring |
| 10 | `search_pubmed_multi` | Multi-query PubMed search for complex questions |

### 6.3 Technology Stack (Final)

| Layer | Technology |
|-------|-----------|
| LLM | DigitalOcean AI (openai-gpt-oss-120b) via langchain-openai |
| Agent Framework | LangGraph `create_agent`, 10 tools |
| Backend | FastAPI, Pydantic, SQLAlchemy, slowapi, cachetools |
| Database | DigitalOcean Managed PostgreSQL + pgvector + pg_trgm |
| Vector Store | ChromaDB + pgvector (drug embeddings) |
| Embeddings | nomic-ai/nomic-embed-text-v1 (768 dimensions) |
| Frontend | React 18, Vite (build), Nginx (serve), react-markdown, react-router-dom |
| Infrastructure | Docker Compose (2 services), Nginx production build, health checks |
| Citation Metrics | Scopus API (CiteScore, SJR, SNIP, FWCI, percentile) |
| Literature | NCBI E-utilities (PubMed search + PMC PDF download) |

---

## 7. Methodology & Technical Details

### 7.1 Development Methodology

The team followed an iterative, phase-based development process with feature branches and peer review. Key commits document the progression:

1. **Restructuring phase** (commits `c3fe2a7` → `62b1677`): Code structure refactoring, LLM inference migration to DigitalOcean, streaming implementation.
2. **Core migration** (commits `da4d0e8` → `1f570a7`): JWT configuration, PostgreSQL migration, auth/drugs/pubmed module rebuilds.
3. **Feature development** (commits `526a72d` → `66ceb74`): PubMed tool enhancement, source handling, multi-query support, relevance scoring.
4. **Bug fixes and polish** (commits `8522f9c` → `651e602`): Chat fixes, source display fixes, final stabilization.

### 7.2 Key Technical Decisions

#### 7.2.1 PostgreSQL over DynamoDB

**Rationale:**
- DrugBank data is inherently relational (drugs → synonyms, categories, interactions, targets, enzymes).
- pgvector provides native vector similarity search without a separate service.
- pg_trgm enables fuzzy text matching for drug name search (handles typos and partial matches).
- Managed cloud database eliminates local data loss and provides automatic backups.
- SQL queries with JOINs are more efficient than DynamoDB's scan-and-filter pattern for complex lookups.

#### 7.2.2 DigitalOcean AI over Amazon Bedrock

**Rationale:**
- OpenAI-compatible API simplifies integration (standard `langchain-openai` client).
- No AWS credential management required.
- Cost-effective for development and demonstration.
- Model (`openai-gpt-oss-120b`) provides strong reasoning capabilities for medical queries.

#### 7.2.3 Scopus API for Citation Metrics

**Rationale:**
- NCBI E-link `pubmed_pubmed_citedin` provides citation counts but lacks journal-level metrics.
- Scopus provides comprehensive metrics: CiteScore, SJR, SNIP, journal percentile, and FWCI.
- Enables multi-dimensional confidence scoring that goes beyond simple citation counting.
- Graceful degradation when API key not configured (falls back to available metrics).

#### 7.2.4 Thread-Safe Source Tracking Pattern

**Problem:** LangChain runs synchronous tools in a thread-pool during `agent.astream()`. ContextVar writes in child threads don't propagate back to the parent.

**Solution:**
- Tools READ a `_request_id_var` (copied to thread via ContextVar).
- Tools WRITE results into a plain thread-safe dict keyed by request ID.
- After the agent call, the caller pops results from the dict.
- Lock-protected dict operations for belt-and-suspenders safety.

### 7.3 Backend Implementation Details

#### 7.3.1 Drug Service (Refactored)

The drug service (`backend/src/drugs/service.py`) was completely rewritten for PostgreSQL:

- **Drug lookup:** Uses SQLAlchemy queries with `joinedload` for eager loading of relationships.
- **Fuzzy search:** Leverages pg_trgm `similarity()` function for typo-tolerant drug name matching.
- **Synonym resolution:** Searches both `drugs.name_lower` and `drug_synonyms.synonym_lower`.
- **Interaction checking:** Bidirectional lookup in `drug_interactions` table with synonym resolution.
- **Category/indication search:** Indexed queries on `drug_categories.category_lower`.
- **Severity classification:** Regex-based pattern matching on interaction descriptions (contraindicated → critical → major → moderate-high → moderate → minor).

#### 7.3.2 PubMed Service (Enhanced)

The PubMed module (`backend/src/pubmed/`) was significantly expanded:

- **NCBI E-utilities integration:** Direct HTTP calls to `esearch.fcgi` and `efetch.fcgi` (no pymed dependency for core search).
- **Adaptive scoring:** Query type classification adjusts scoring weights dynamically.
- **Confidence scoring:** Multi-dimensional composite score (citations × FWCI × journal × recency × evidence × relevance).
- **Quality warnings:** Automatic flagging of low-relevance or low-quality articles.
- **Snippet extraction:** Extracts most query-relevant sentences from abstracts for concise citations.
- **PDF download pipeline:** Async download from PMC/DOI with LRU cache management.
- **Multi-query search:** Merges results from multiple focused sub-queries with deduplication.

#### 7.3.3 Session Management (Redesigned)

- `SessionManager` class wraps `cachetools.TTLCache`.
- Thread-safe with explicit locking.
- `get_or_create()` pattern prevents duplicate session creation.
- Background cleanup task runs every 5 minutes via `asyncio.create_task`.
- Session stores conversation state, user ID, and agent reference.

### 7.4 Frontend Implementation Details

#### 7.4.1 Streaming Chat

- Uses `fetch` API with `ReadableStream` for SSE consumption.
- `TextDecoder` processes chunks; buffer handles partial SSE lines.
- Progressive markdown rendering via `react-markdown` + `remark-gfm`.
- Tool execution events shown as status indicators during streaming.
- Final response includes sources array for citation display.

#### 7.4.2 PDF Preview Panel

- Split-panel layout with resizable width.
- Authenticated PDF fetch (Blob URL pattern for iframe).
- Fallback to abstract markdown display when PDF unavailable.
- Integrated with source references — clicking a PubMed source opens the panel.

#### 7.4.3 Confidence Breakdown Component

- Visual display of per-article confidence scores.
- Individual component bars (citations, FWCI, journal quality, recency, evidence level, relevance).
- Expandable per-article in search results.

#### 7.4.4 Markdown with References

- Custom renderer replaces `[REF1]`, `[REF2]` patterns with clickable buttons.
- Buttons scroll to source in sources list or open PDF panel.
- Works within `<p>` and `<li>` elements.

---

## 8. Evaluation & Validation

This section defines how the system was tested and evaluated across four dimensions: medical accuracy, performance, security, and usability.

### 8.1 Medical Accuracy Evaluation

#### 8.1.1 Test Set Design

A set of **50 medical queries** was constructed covering the following categories:

| Category | Count | Examples |
|----------|-------|---------|
| Drug information lookup | 10 | "What is Metformin?", "What are the side effects of Warfarin?" |
| Drug-drug interaction (known interaction) | 8 | "Does Warfarin interact with Ibuprofen?" |
| Drug-drug interaction (no interaction) | 4 | "Does Aspirin interact with Acetaminophen?" |
| Drug-food interaction | 5 | "Can I eat grapefruit with Atorvastatin?" |
| PubMed research query | 5 | "What does the research say about SGLT2 inhibitors in heart failure?" |
| Patient medication analysis | 5 | Polypharmacy profiles with known interactions |
| Alternative drug recommendation | 3 | "Suggest an alternative to Ibuprofen for a patient on Warfarin" |
| Multi-drug interaction | 5 | "Check interactions between Warfarin, Aspirin, and Omeprazole" |
| Hallucination probes (nonexistent drugs) | 5 | "Tell me about Fakezolam", "Does Aspirin interact with water?" |

#### 8.1.2 Scoring Rubric

Each response was scored on a 0-3 scale across four dimensions:

| Score | Factual Accuracy | Completeness | Safety Language | Source Citation |
|-------|-----------------|--------------|-----------------|----------------|
| 3 | All facts correct and verifiable against DrugBank/PubMed | All relevant information included | Clear disclaimer present; recommends consulting a professional | Sources correctly cited with IDs |
| 2 | Mostly correct; minor omissions | Key information present but missing some detail | Disclaimer present but generic | Sources partially cited |
| 1 | Contains a factual error or misleading statement | Significant information missing | No disclaimer or safety language | No sources cited |
| 0 | Hallucinated content or dangerous misinformation | Response is off-topic or empty | Actively harmful advice | N/A |

**Composite score** = average across all four dimensions for all 50 queries. **Target: >= 75% (composite score >= 2.25/3.0).**

#### 8.1.3 Hallucination Detection

The 5 hallucination probe queries test whether the agent fabricates information:

- Queries about nonexistent drugs should produce a "not found" response, not a fabricated drug profile.
- Queries about known non-interactions should not invent an interaction description.
- Numerical precision checks (e.g., half-life values) are compared against DrugBank reference values.

**Target: 0% hallucination rate on probe queries.**

#### 8.1.4 Accuracy Mechanisms Implemented

The system's medical accuracy relies on multiple layers:

1. **Tool-grounded architecture:** The system prompt enforces "TOOLS FIRST — ALWAYS" — the agent must use tools for any clinical question and cannot answer from training knowledge alone.
2. **Clinical precision rules:** Subtype specificity, population scope awareness, low-relevance article handling, conflicting evidence presentation, and claim traceability are enforced in the system prompt.
3. **Hallucination mitigation:** The agent is instructed to report "not found" when tools return no data rather than fabricating information. The system prompt states: "Answering from training knowledge without tool results is only permitted when ALL relevant tools have been tried and returned no data."
4. **Source citation:** Every tool-sourced response includes metadata (DrugBank ID, PubMed PMID, confidence scores) for verification.
5. **Multi-source verification:** The agent has access to both DrugBank (structured) and PubMed (literature), enabling cross-referencing.

### 8.2 Performance Evaluation

#### 8.2.1 Latency Benchmarks

| Metric | Query Type | Target | Achieved |
|--------|-----------|--------|----------|
| Time to First Token (TTFT) | Streaming agent query | <= 2 seconds | ~1-3 seconds |
| End-to-end latency | Drug info lookup (single tool call) | <= 5 seconds | ~3-5 seconds |
| End-to-end latency | Drug interaction check (single tool call) | <= 5 seconds | ~3-5 seconds |
| End-to-end latency | PubMed search (post-O1 refactor) | <= 10 seconds | ~5-10 seconds |
| End-to-end latency | Patient medication analysis (multi-tool) | <= 20 seconds | ~10-20 seconds |

#### 8.2.2 Latency Improvement from O1

The O1 refactor (eliminating redundant LLM calls) produced a measurable latency reduction:

- **Before:** RAG/PubMed queries required two LLM invocations (one inside tool + one from agent). Average latency: ~12-15 seconds.
- **After:** Single LLM invocation per query. Average latency: ~5-10 seconds.
- **Improvement:** ~40-50% latency reduction on knowledge-retrieval queries.

#### 8.2.3 Database Performance Improvement

The PostgreSQL migration delivered significant performance gains for drug lookups:

- **Before (DynamoDB scan):** O(n) full-table scan with filter. Latency: 200-500ms for name search.
- **After (PostgreSQL indexed):** B-tree index lookup + trigram fuzzy matching. Latency: 5-50ms for name search.
- **Semantic search:** pgvector HNSW index provides ~10ms approximate nearest neighbor queries for drug embeddings.

#### 8.2.4 Resource Usage

- **Backend memory:** Bounded by TTLCache (max 100 sessions). No monotonic growth observed.
- **Docker image sizes:** Frontend reduced from ~300MB (dev server) to ~50MB (Nginx + static assets).
- **Connection pooling:** SQLAlchemy pool_size=10, max_overflow=20 handles concurrent requests efficiently.

### 8.3 Security Evaluation

#### 8.3.1 Authentication and Authorization Testing

| Scenario | Expected Result | Status |
|----------|----------------|--------|
| Unauthenticated request to protected endpoint | 401 Unauthorized | ✅ Working |
| Expired JWT token | 401 Unauthorized | ✅ Working |
| `general_user` accessing patient management | 403 Forbidden | ✅ Working |
| `doctor` accessing own patients | 200 OK | ✅ Working |
| `doctor` accessing another doctor's patients | 403 Forbidden | ✅ Working |
| Rate limit exceeded (>10 LLM requests/min) | 429 Too Many Requests | ✅ Working |

#### 8.3.2 Rate Limiting Validation

- LLM endpoints: 10 requests/minute per user — verified working.
- Search endpoints: 60 requests/minute per user — verified working.
- Auth endpoints: 20 requests/minute per IP — verified working.
- Rate limit window resets correctly after timeout period.

#### 8.3.3 Prompt Injection Mitigation

While a dedicated sanitizer middleware was not implemented, the system prompt includes comprehensive anti-injection instructions:

- The agent is instructed to refuse off-topic or role-manipulation queries.
- Tool-grounded architecture limits the agent's ability to act on injected instructions (it must use tools for factual claims).
- Frontend escapes HTML/JavaScript in rendered responses to prevent XSS.

### 8.4 Usability Evaluation

#### 8.4.1 Streaming Experience

- **Before:** Users saw a static "●●●" loading indicator for 5-15 seconds with no feedback.
- **After:** Token-by-token streaming with thinking indicators, tool execution status, and progressive markdown rendering. Users see content within 1-3 seconds.

#### 8.4.2 Source Verification

- PDF preview panel allows users to view the actual source document cited by the agent.
- Confidence breakdown shows individual scoring components for each PubMed article.
- Inline `[REF1]`, `[REF2]` references are clickable and link to source details.

#### 8.4.3 Patient-Aware Interaction

- Healthcare professionals can select a patient from a dropdown in the chat header.
- The agent automatically considers the patient's medications, conditions, and allergies.
- When drugs are mentioned in conversation, the agent proactively checks interactions with the patient's current medications.

#### 8.4.4 Cross-Browser Testing

The frontend was tested on Chrome, Edge, and Firefox (latest versions):
- Streaming rendering (SSE consumption and progressive display): ✅ All browsers
- Voice interface functionality: ✅ Chrome and Edge (Firefox has limited Speech API support)
- PDF preview panel rendering: ✅ All browsers
- Dark/light theme switching: ✅ All browsers

---

## 9. Risk Analysis & Mitigation

### 9.1 Original Risk Register (From Planning Report)

| Rank | ID | Risk | Score | Status |
|------|----|------|-------|--------|
| 1 | T2/C1 | LLM hallucination / user misinterpretation | 9 | **Mitigated** — Tool-grounded architecture; mandatory disclaimers |
| 2 | T1 | Bedrock API unavailability | 6 | **Eliminated** — Migrated to DigitalOcean AI |
| 3 | T6 | DrugBank data incompleteness | 6 | **Mitigated** — Multi-source (DrugBank + PubMed); "not found" responses |
| 4 | T8 | Prompt injection bypass | 6 | **Partially mitigated** — System prompt defense only (no sanitizer) |
| 5 | O2 | Phase 3 schedule overrun | 6 | **Occurred** — PostgreSQL migration added ~2 weeks; managed by scope adjustment |
| 6 | O5 | Report writing bottleneck | 6 | **Mitigated** — Incremental drafting after each phase |
| 7 | C2/C3 | Patient data / PII exposure | 6 | **Mitigated** — JWT auth; role-based access; managed cloud DB |

### 9.2 Risks Encountered and Mitigated

| Risk | Outcome | Mitigation Applied |
|------|---------|-------------------|
| LLM hallucination | Mitigated | Tool-grounded architecture; mandatory tool use; source citations; clinical precision rules |
| Bedrock API dependency | Eliminated | Migrated to DigitalOcean AI (OpenAI-compatible endpoint) |
| DynamoDB scalability | Eliminated | Migrated to PostgreSQL with proper indexing (B-tree, GIN trigram, HNSW vector) |
| Session memory leak | Resolved | TTLCache with bounded size (100 sessions) and automatic 30-min TTL eviction |
| Thread-unsafe globals | Resolved | ContextVar + shared dict pattern with threading.Lock |
| Frontend dev server in production | Resolved | Multi-stage Nginx build with gzip, caching, and SPA routing |
| Double LLM invocation cost | Resolved | Single-call pattern; tools return raw data for agent synthesis |
| DrugBank data gaps | Mitigated | PubMed fallback; explicit "no data found" messaging; multi-source architecture |

### 9.3 Remaining Risks

| Risk | Severity | Status | Mitigation Path |
|------|----------|--------|-----------------|
| Prompt injection (no sanitizer middleware) | Medium | Open | System prompt defense only; could add blocklist middleware in future |
| Weak default JWT secret | Medium | Open | Should enforce minimum length at startup; currently relies on deployment configuration |
| No automated test suite | Medium | Open | pytest and vitest frameworks identified but not implemented |
| PII in LLM queries | Low | Partially mitigated | Provider changed to DigitalOcean (no AWS data retention); PII stripper not built |
| No CI/CD pipeline | Low | Open | Manual Docker Compose deployment; could add GitHub Actions |
| Network dependency for demo | Low | Mitigated | Cloud DB + cloud LLM require internet; backup demo videos prepared |

### 9.4 Risk Mitigation Summary

The project's risk profile improved significantly during Semester 2:

- **Eliminated risks:** Bedrock API dependency (T1), DynamoDB scalability (T9), local data loss.
- **Fully resolved:** Session memory leak, thread-unsafe globals, frontend dev server, double LLM calls.
- **Partially addressed:** Prompt injection (system prompt defense but no middleware), PII handling (provider change but no stripper).
- **Accepted:** No automated tests, no CI/CD — these are documented as future work.

---

## 10. Ethical, Social, and Professional Considerations

### 10.1 Ethical Issues and Privacy

- All patient data used within the system is stored in a managed PostgreSQL database with role-based access control.
- Doctor-patient associations enforce strict data isolation — a doctor can only access their own patients' data.
- The system does not store or log patient names, conditions, or medications in application logs (UUIDs only).
- For demonstration purposes, all patient data is synthetic.
- The LLM provider (DigitalOcean AI) does not retain input/output data beyond the API call lifecycle.

### 10.2 Safety and Transparency

- The AI assistant is designed to provide **informational support only** and is not a substitute for direct medical prescriptions.
- Safety disclaimers are enforced at multiple levels:
  - System prompt instructs the agent to always recommend consulting a healthcare provider.
  - The agent uses emoji severity indicators (🔴 MAJOR, 🟠 MODERATE, 🟡 MINOR) for clear risk communication.
  - Source citations (DrugBank ID, PubMed PMID, confidence scores) enable verification of all claims.
- The tool-grounded architecture prevents the agent from making unsupported medical claims — it must use tools for factual retrieval.
- When tools return no data, the agent explicitly states this rather than fabricating information.

### 10.3 Professional Standards

- The development process follows modular software engineering practices with version control (Git), domain-driven design, and clear separation of concerns.
- Code is organized into well-defined modules with single responsibility (auth, drugs, pubmed, session, etc.).
- Configuration is centralized via Pydantic Settings with environment variable validation.
- The system uses established, well-maintained open-source libraries (FastAPI, SQLAlchemy, LangChain, React).

### 10.4 Societal Impact

- By bridging the gap between complex medical data and user accessibility, the project aims to reduce prescription errors and improve patient safety.
- Dual-level explanations (clinical for doctors, simplified for patients) ensure appropriate communication for each audience.
- The integration of patient medical history enables personalized recommendations, enhancing clinical relevance beyond generic interaction warnings.
- The system empowers both doctors and patients to make safer, data-driven healthcare decisions.

### 10.5 Data Licensing and Compliance

- **DrugBank:** Used under academic license for educational/research purposes.
- **PubMed:** Accessed via public NCBI E-utilities API in compliance with NCBI usage guidelines (tool name and email registered).
- **Scopus:** Accessed via registered API key from Elsevier Developer Portal.
- **Open-access PDFs:** Only freely available (open-access) articles are downloaded from PubMed Central.

---

## 11. Conclusion

### 11.1 Project Summary

This project has successfully developed MedicaLLM from a Semester 1 Minimum Viable Product into a comprehensive, production-ready medical AI consultation platform. The system integrates structured drug databases (DrugBank, ~14,000 drugs), a Drug-Drug Interaction detection module with severity classification, deterministic drug information retrieval tools, a Retrieval-Augmented Generation (RAG) pipeline grounded in scientific literature, and live PubMed search with citation-based credibility scoring. By combining these components within a cloud-native architecture (DigitalOcean Managed PostgreSQL + DigitalOcean AI), we have developed a functional system capable of real-time analysis and explanation generation.

### 11.2 Key Achievements

The platform underwent significant architectural evolution during Semester 2:

- **Database migration:** DynamoDB → PostgreSQL with pgvector, enabling semantic search and proper relational data modeling for ~14,000 drugs with full pharmacological detail.
- **Agent expansion:** Tool repertoire grew from 6 to 10 tools, adding alternative drug recommendation, overdose detection, patient medication analysis, and multi-query PubMed search.
- **Real-time streaming:** SSE streaming in the frontend eliminates the blank-screen waiting experience, with token-by-token rendering and tool execution status indicators.
- **Citation credibility system:** Comprehensive scoring using Scopus metrics (CiteScore, SJR, SNIP, FWCI) with adaptive query-type-based scoring weights.
- **Patient-aware responses:** Dynamic system prompts with role-based language adaptation and automatic medication cross-referencing when patient context is active.
- **Production infrastructure:** Multi-stage Nginx Docker builds, health checks, rate limiting, and cloud-hosted database.
- **PDF pipeline:** Download and preview capabilities for PubMed articles with LRU cache management.
- **Severity classification:** Regex-based pattern matching classifies drug interactions from minor to contraindicated.

### 11.3 Objectives Completion Summary

| Status | Count | Objectives |
|--------|-------|-----------|
| ✅ Fully Completed | 9 | O1, O2, O3, O5, O6, O7, O8, O9, O10 |
| ⚠️ Partially Completed | 3 | O4 (rate limiting only), O11 (TLS config only), O12 (STT only) |
| ❌ Not Implemented | 1 | Comprehensive testing framework (pytest/vitest) |

### 11.4 Dual-Audience Architecture

The platform provides dual-level explanations tailored to its two primary stakeholders:
- **Healthcare professionals:** Detailed clinical mechanisms, pharmacokinetic considerations, evidence citations, and patient-specific interaction analysis.
- **General users (patients):** Simplified summaries in accessible language, practical safety advice, and consistent recommendations to consult healthcare providers.

### 11.5 Expected Outcomes

- **Improved medication safety:** Automated multi-drug interaction checking with severity classification reduces the risk of harmful drug combinations.
- **Reduced prescription errors:** Patient-aware analysis cross-references all current medications, conditions, and allergies before any new drug is discussed.
- **Increased accessibility:** Natural language interface makes complex pharmacological information accessible to both professionals and patients.
- **Evidence-based responses:** Tool-grounded architecture with source citations ensures verifiable, trustworthy medical information.
- **Scalable framework:** The modular architecture can evolve with new medical datasets, additional tools, and AI model improvements.

### 11.6 Future Work

The following areas are identified for potential future development:

1. **Automated testing:** Implement pytest (backend) and vitest (frontend) test suites with CI/CD integration.
2. **Input sanitization:** Build the planned prompt injection blocklist middleware.
3. **Self-hosted LLM:** Evaluate Ollama/vLLM for on-premise deployment to eliminate third-party data exposure.
4. **Voice TTS:** Complete the text-to-speech synthesis for full voice conversation mode.
5. **Healthcare professional dashboard:** Build the patient risk alert feed and usage analytics.
6. **Mobile responsiveness:** Optimize the UI for tablet and mobile viewports.
7. **Conversation summarization:** Implement sliding-window or summarization strategy to bound context token growth.

Overall, the project demonstrates the feasibility of combining LLM agents, structured medical knowledge bases, citation-aware literature search, and cloud-native infrastructure to create a responsible and impactful digital health solution.

---

## 12. Appendix

### 12.1 Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET` | JWT signing secret | `change-me-to-a-random-string` |
| `DO_MODEL_ACCESS_KEY` | DigitalOcean AI API key | — |
| `DO_LLM_MODEL_ID` | LLM model identifier | `openai-gpt-oss-20b` |
| `HGF_EMBEDDING_MODEL_ID` | Embedding model | `nomic-ai/nomic-embed-text-v1` |
| `HF_TOKEN` | HuggingFace token | — |
| `SCOPUS_API_KEY` | Scopus API key (optional) | — |
| `DO_POSTGRES_URL` | PostgreSQL connection URL | — |
| `ADMIN_USERNAME` | Admin panel username | `medicallm` |
| `ADMIN_PASSWORD` | Admin panel password | — |
| `LOG_LEVEL` | Logging level | `INFO` |
| `VITE_USE_HTTPS` | Frontend HTTPS flag | `false` |

### 12.2 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login (returns JWT) |
| GET | `/api/conversations/` | List user's conversations |
| POST | `/api/session/query-stream` | Agent query (SSE streaming) |
| POST | `/api/session/query` | Agent query (synchronous) |
| POST | `/api/session/generate-title` | Generate conversation title |
| GET | `/api/drugs/search/{query}` | Drug name search |
| GET | `/api/drugs/info/{drug_id}` | Drug information |
| GET | `/api/drugs/interaction/{id1}/{id2}` | Check drug interaction |
| GET | `/api/pubmed/pdf/{pmid}` | Serve PubMed PDF |
| GET | `/api/pubmed/scopus/status` | Scopus service status |
| GET | `/api/users/doctors/patients` | List doctor's patients |
| POST | `/api/admin/login` | Admin authentication |
| GET | `/health` | Health check |

### 12.3 Commit History (Post-Planning Report)

29 commits spanning March 1 – May 10, 2026, covering:
- Code structure refactoring and readability improvements
- LLM inference migration to DigitalOcean
- Streaming and HuggingFace token integration
- Multi-tool architecture and markdown fixes
- PostgreSQL migration (removing DynamoDB)
- Module-by-module rebuild (auth → drugs → pubmed → session)
- PubMed tool enhancement with multi-query support and relevance scoring
- PDF download and preview implementation
- Chat fixes and source display improvements
- Final stabilization

### 12.4 Team Contributions

| Team Member | Primary Contributions |
|-------------|----------------------|
| İsmail Esad Kılıç | Agent core, tool architecture, session management, system prompt design, PostgreSQL migration |
| Arda Ünal | Testing scenarios, PubMed scoring, evaluation criteria |
| Doğukan Gökduman | Infrastructure (Docker, Nginx, health checks), rate limiting, PubMed PDF pipeline, Scopus integration, admin panel |
| Özge Şahin | Frontend streaming, PDF preview panel, confidence breakdown UI, landing page, voice input |

## 8. Timeline & Milestones (Semester 2)

The semester ran from **Week 1 (February 2, 2026)** through **Week 15 (May 17, 2026)**. Key dates: planning report submitted on **March 1** (Week 4), final report on **May 11** (Week 14), and project demonstration on **May 17** (Week 15).

### 8.1 Planned vs. Actual Timeline

| Week | Dates | Planned Phase | Actual Work |
|------|-------|---------------|-------------|
| 1–4 | Feb 2 – Mar 1 | Planning | Project evaluation, planning report writing. ✅ Submitted Mar 1 |
| 5 | Mar 2 – Mar 8 | Phase 1 (O1) | Code restructuring, LLM migration to DigitalOcean AI |
| 6 | Mar 9 – Mar 15 | Phase 1 (O4) | Streaming implementation, HuggingFace token integration |
| 7 | Mar 16 – Mar 22 | Phase 2 (O2) | Multi-tool architecture, markdown rendering fixes |
| 8 | Mar 23 – Mar 29 | Phase 2 (O3, O5) | PostgreSQL migration begins, DynamoDB removal |
| 9–10 | Mar 30 – Apr 12 | Phase 3 (O10, O9) | Module-by-module rebuild (auth → drugs → pubmed → session) |
| 11 | Apr 13 – Apr 19 | Phase 4 (O6, O8) | PubMed tool enhancement, PDF download pipeline |
| 12 | Apr 20 – Apr 26 | Phase 5 (O12, O13) | Multi-query PubMed, relevance scoring, Scopus integration |
| 13 | Apr 27 – May 3 | Phase 6 (O7, O11) | Source handling improvements, confidence scoring UI |
| 14 | May 4 – May 10 | Finalization | Chat fixes, source display fixes, final stabilization |
| 15 | May 11 – May 17 | Demonstration | Final report, rehearsal, live demo |

### 8.2 Milestone Achievement

| Milestone | Planned Date | Status | Notes |
|-----------|-------------|--------|-------|
| M0 | Mar 1 | ✅ Achieved | Planning Report submitted |
| M1 | Mar 15 | ✅ Achieved | LLM calls optimized, rate limiting implemented |
| M2 | Mar 29 | ✅ Achieved | Streaming UI, session management, Nginx build |
| M3 | Apr 12 | ✅ Achieved | Patient-aware responses, alternative recommendations, medication analysis |
| M4 | Apr 19 | ✅ Achieved | PubMed PDF retrieval, PDF preview panel |
| M5 | May 3 | ⚠️ Partial | Citation analysis complete; voice TTS and dashboard partially implemented |
| M6 | May 11 | ✅ Achieved | Final Report submitted |
| M7 | May 17 | ✅ Achieved | Project Demonstration |

### 8.3 Deviations from Plan

The most significant deviation from the original plan was the **database migration from DynamoDB to PostgreSQL**, which was not in the original 13 objectives but became necessary during implementation. This migration consumed approximately 2 weeks of additional effort (Weeks 8-10) but delivered substantial benefits:

- Eliminated the O(n) scan-based drug search problem (original limitation P2).
- Enabled semantic drug search via pgvector (not originally planned).
- Provided proper relational integrity for the complex DrugBank data model.
- Moved to a managed cloud database, eliminating local data loss risk.

The **LLM provider migration** (Bedrock → DigitalOcean AI) was also unplanned but resolved the T1 risk (Bedrock API dependency) entirely rather than just mitigating it.

These unplanned but high-value changes meant that some lower-priority objectives received less attention:
- O4 (Security): Rate limiting implemented, but input sanitizer and PII stripper were not built.
- O12 (Voice): Speech-to-text implemented, but TTS and continuous mode were not.
- O13 (Dashboard): Admin panel built, but the healthcare professional dashboard with patient risk alerts was not fully realized.

### 8.4 Team Responsibilities (Actual)

| Team Member | Primary Contributions |
|-------------|----------------------|
| İsmail Esad Kılıç | Agent core architecture, tool design (10 tools), system prompt engineering, session management, PostgreSQL migration, LangGraph integration |
| Arda Ünal | PubMed scoring system, query classification, evaluation criteria, testing scenarios |
| Doğukan Gökduman | Infrastructure (Docker, Nginx, health checks), rate limiting middleware, PubMed PDF pipeline, Scopus API integration, admin panel, database scripts |
| Özge Şahin | Frontend streaming (SSE), PDF preview panel, confidence breakdown component, markdown references, landing page, voice input |

---

## 13. References

The development and validation of the MedicaLLM system rely on the following resources:

### Medical Databases
1. **DrugBank** (https://go.drugbank.com/) — Comprehensive drug database with ~14,000 drug entries including interactions, pharmacology, targets, and food interactions. Used under academic license.
2. **PubMed / NCBI E-utilities** (https://pubmed.ncbi.nlm.nih.gov/) — U.S. National Library of Medicine's biomedical literature database. Accessed via E-utilities API (esearch, efetch, elink).
3. **Scopus** (https://www.scopus.com/) — Elsevier's abstract and citation database. Used for journal-level metrics (CiteScore, SJR, SNIP) and article-level FWCI via the Scopus API.

### AI & ML Frameworks
4. **LangChain** (https://python.langchain.com/) — Framework for building LLM-powered applications. Used for agent orchestration, tool definitions, and model integration.
5. **LangGraph** (https://langchain-ai.github.io/langgraph/) — Graph-based agent framework built on LangChain. Used for the ReAct agent implementation with `create_agent`.
6. **DigitalOcean AI** (https://www.digitalocean.com/products/ai) — Cloud AI inference platform providing OpenAI-compatible API. Model: `openai-gpt-oss-120b`.
7. **Sentence Transformers** (https://www.sbert.net/) — Library for computing text embeddings. Model: `nomic-ai/nomic-embed-text-v1` (768 dimensions).
8. **ChromaDB** (https://www.trychroma.com/) — Open-source vector database for RAG pipeline document storage.

### Backend Technologies
9. **FastAPI** (https://fastapi.tiangolo.com/) — Modern Python web framework for building APIs.
10. **SQLAlchemy** (https://www.sqlalchemy.org/) — Python SQL toolkit and ORM.
11. **pgvector** (https://github.com/pgvector/pgvector) — PostgreSQL extension for vector similarity search.
12. **slowapi** (https://github.com/laurentS/slowapi) — Rate limiting for FastAPI/Starlette.
13. **cachetools** (https://github.com/tkem/cachetools) — Extensible memoizing collections (TTLCache for session management).

### Frontend Technologies
14. **React 18** (https://react.dev/) — JavaScript library for building user interfaces.
15. **Vite** (https://vitejs.dev/) — Build tool and development server.
16. **react-markdown** (https://github.com/remarkjs/react-markdown) — Markdown renderer for React.
17. **Web Speech API** — Browser API for speech recognition (used for voice input).

### Infrastructure
18. **Docker** / **Docker Compose** — Containerization and multi-service orchestration.
19. **Nginx** (https://nginx.org/) — Production web server for static asset serving and reverse proxy.
20. **DigitalOcean Managed PostgreSQL** — Cloud-hosted relational database with pgvector and pg_trgm extensions.
