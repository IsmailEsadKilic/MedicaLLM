# MedicaLLM — Comprehensive Audit Report

**Date:** May 14, 2026  
**Scope:** Full codebase analysis — backend, frontend, agent, PubMed search, infrastructure

---

## Table of Contents

1. [PubMed Search Issues (Presentation Focus)](#part-1-pubmed-search-issues)
2. [Agent System Issues](#part-2-agent-system-issues)
3. [Security Issues](#part-3-security-issues)
4. [Infrastructure & Deployment Issues](#part-4-infrastructure--deployment-issues)
5. [Frontend Issues](#part-5-frontend-issues)
6. [Presentation-Day Risk Summary](#presentation-day-risk-summary)

---

## PART 1: PubMed Search Issues

### Critical PubMed Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **P1** | **HIGH** | `backend/src/agent/tools.py:1258` | `fetch_count = max(num_articles, 15)` — always fetches **15 articles minimum** even if user asks for 3. Wastes API calls, adds latency. `MAX_CONTEXT_ARTICLES` then caps output at the requested count, so extra articles are fetched and scored for nothing. |
| **P2** | **HIGH** | `backend/src/pubmed/service.py:313-318` | **DOI parsing `break` bug** — if PMC ID appears before DOI in the XML, the `break` inside the PMC case exits the loop before DOI is captured. Articles may end up with no DOI, breaking enrichment and PDF downloads. |
| **P3** | **HIGH** | `tools.py:1269` vs `service.py:94` | **`min_confidence` mismatch** — service default is `35.0`, but the tool hardcodes `45.0`. The service-level default is dead code; the tool always overrides it. Not configurable. |
| **P4** | **MEDIUM** | `scoring.py:327-334` vs `query_classifier.py:33-42` | **Two separate `DEFAULT_WEIGHTS`** — `scoring.py` has one set (`relevance=0.25`), `query_classifier.py` has another (`relevance=0.35`). The scoring.py defaults are only used as fallback; the classifier weights always win. Maintenance hazard. |
| **P5** | **MEDIUM** | `backend/src/pubmed/router.py` | **No REST endpoint for PubMed search** — search is only accessible through the LLM agent tool. No way to test or demo PubMed search independently of the agent. |
| **P6** | **MEDIUM** | `backend/src/pubmed/router.py:83-90` | `check_pdf_availability` **always returns `available: True`** regardless of actual availability. Misleading to the frontend. |
| **P7** | **MEDIUM** | `backend/src/config.py:65` | `pubmed_max_results: int = 15` is **defined but never used** anywhere. The tool hardcodes its own value. Dead config. |
| **P8** | **MEDIUM** | `backend/src/config.py:59-60` | `pubmed_citation_ttl_seconds` and `pubmed_search_cache_ttl_seconds` — **no caching layer exists**. Every query hits NCBI API fresh. These config values are dead. |
| **P9** | **MEDIUM** | `backend/src/pubmed/service.py:132-137` | `_empty_esearch` retries 3 times on 0 results, adding ~1.2s delay. **Valid "no results" searches are treated as failures** and retried unnecessarily. |
| **P10** | **MEDIUM** | `backend/src/agent/tools.py:1240-1243` | Non-English detection **only checks Turkish characters**. French, German, Arabic, Chinese queries pass through. Also gives false positives on valid English terms like "Ménière's disease". |

### PubMed Scoring & Classification Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **P11** | **MEDIUM** | `backend/src/pubmed/scoring.py:399` | `breakdown` dict uses different key names than `DEFAULT_WEIGHTS` — `"journal_quality"` vs `"journal"`, `"evidence_level"` vs `"evidence"`. Confusing when consuming externally. |
| **P12** | **MEDIUM** | `backend/src/pubmed/query_classifier.py:114` | Drug pattern too broad — the word `"treatment"` matches most medical queries, biasing classification towards `DRUG_RESEARCH`. |
| **P13** | **MEDIUM** | `backend/src/pubmed/query_classifier.py:150-200` | Classification is **fixed priority order** (AUTHOR→REVIEW→GUIDELINE→RECENT→DRUG→DISEASE→GENERAL). No multi-label support. A "recent systematic review of diabetes drug therapy" always matches `REVIEW_META` first. |
| **P14** | **LOW** | `backend/src/pubmed/service.py:107` | `get_adaptive_weights(query, llm=None)` — always `None`, making the LLM classification fallback in `classify_query` **dead code**. |

### PubMed External API Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **P15** | **MEDIUM** | `backend/src/pubmed/scopus_service.py:441-444` | Scopus API key sent as **URL query parameter** instead of header (`X-ELS-APIKey`). Appears in logs and error messages. |
| **P16** | **MEDIUM** | `backend/src/pubmed/openalex_service.py:100` | OpenAlex filter expects bare numeric PMIDs. If a PMID is passed with `"PMID:"` prefix or leading zeros, the filter **silently returns 0 results**. |
| **P17** | **LOW** | `backend/src/pubmed/scopus_service.py:450` | `timeout=2` for Scopus single-article search — very short, causes frequent timeouts with no retry. |
| **P18** | **LOW** | `backend/src/pubmed/fulltext_service.py:174` | No max size guard on full-text XML download. Malformed response could consume several MB. |

### PubMed Timing & Performance

| # | Severity | File | Issue |
|---|----------|------|-------|
| **P19** | **LOW** | `backend/src/pubmed/service.py:477-485` | Enrichment timing variables don't actually measure per-future execution time — they measure wall-clock after `.result()`. |
| **P20** | **LOW** | `backend/src/pubmed/service.py:469-475` | `_batch_enrich_articles` creates nested `ThreadPoolExecutor`s (3 × 3 = up to 9 threads) per single search. |

---

## PART 2: Agent System Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **A1** | **HIGH** | `backend/src/session/session.py:250` | `self.agent.invoke()` is **synchronous** called from `async def` — **blocks the entire event loop** during agent execution. Should use `await self.agent.ainvoke()`. |
| **A2** | **HIGH** | `backend/src/agent/agent.py:1-8` | Imports from `langchain.agents.middleware.types` — **private internal types** (`_InputAgentState`, `_OutputAgentState`) that may not exist in the installed langchain version. Fragile. |
| **A3** | **HIGH** | `backend/src/agent/tools.py:369-399` | `get_drug_info` only registers a source citation for `detail="high"`. **Low/moderate detail queries return no citation**, violating the system prompt rule "every clinical claim MUST have citations." |
| **A4** | **MEDIUM** | `backend/src/agent/source_tracker.py` | **Entire file is dead code** — parallel unused source tracking system with incompatible types vs what `tools.py` actually uses. |
| **A5** | **MEDIUM** | `backend/src/agent/langchain_agent.py:300-330` | `max_iterations` parameter accepted but **never passed** to `create_agent()`. Actual recursion limit is hardcoded to 50 in session.py. |
| **A6** | **MEDIUM** | `backend/src/agent/tools.py:175-191` | REF counter fallback path (non-streaming) can produce **duplicate reference IDs**. |
| **A7** | **MEDIUM** | `backend/src/agent/tools.py:111-135` | **Memory leak** — `_ref_counter`, `_source_store`, `_debug_store` are never cleaned up on exceptions. No TTL, no max-size guard. |
| **A8** | **MEDIUM** | `backend/src/session/session.py:489-494` | Title generation passes through the **full agent with all tools**. LLM might call a tool accidentally. Should use plain `model.invoke()`. |
| **A9** | **MEDIUM** | `backend/src/agent/tools.py:1464` | `_build_pubmed_response` hardcodes `MAX_CONTEXT = 15` in multi-query mode, ignoring user's requested article count. |
| **A10** | **MEDIUM** | `backend/src/agent/tools.py:503,616` | Error messages return raw `str(e)` to the LLM — may leak database URLs, file paths, internal stack details. |
| **A11** | **MEDIUM** | `backend/src/agent/tools.py:873-876` | `recommend_alternative_drug` — no guard for when all drug name resolutions fail (`current_drug_ids = []`). |
| **A12** | **LOW** | `backend/src/agent/tools.py:632,1049` | Mutable default arguments `[]` on `food_items` and `additional_drugs`. |
| **A13** | **LOW** | `backend/src/agent/tools.py:1186-1205` | Dead code: local `_extract_relevant_snippet` function is never called. |

---

## PART 3: Security Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **S1** | **CRITICAL** | `backend/src/config.py:48` | **Hardcoded admin password**: `"sezeristan000"` in plaintext in source code. |
| **S2** | **CRITICAL** | `backend/src/config.py:12` | **Weak JWT secret default**: `"supersecretkey"` — trivially guessable, allows token forgery. |
| **S3** | **HIGH** | `backend/src/admin/router.py:17-22` | Admin login returns `{"success": True}` with **no auth token** — subsequent admin requests have no authentication. |
| **S4** | **HIGH** | `backend/src/pubmed/pdf_downloader.py:41-46` | **Path traversal risk** — `pmid` is not sanitized before being used in file path construction. A malicious PMID like `../../etc/passwd` could write outside the intended directory. |
| **S5** | **HIGH** | `backend/src/pubmed/router.py:20` | No validation on PMID path parameter (no regex constraint to digits only). |
| **S6** | **HIGH** | `backend/src/drugs/router.py` | **No authentication** on any drug endpoint. Any unauthenticated client can query the full database. |
| **S7** | **HIGH** | `backend/src/users/router.py:138-153` | `assign_doctor_to_patient` / `remove_doctor_from_patient` have **no admin authorization check** (TODO comment). |
| **S8** | **MEDIUM** | `backend/src/auth/router.py:48` | Verification codes use non-cryptographic `random.randint()` instead of `secrets`. |
| **S9** | **MEDIUM** | `backend/src/auth/router.py:30-33` | Verification codes stored in **memory with no expiry**. Codes never expire, lost on restart, not shared across workers. |
| **S10** | **MEDIUM** | `frontend/src/components/MarkdownWithReferences.jsx:4` | `rehype-raw` renders raw HTML in Markdown — **XSS vector** if LLM output is poisoned (prompt injection). |
| **S11** | **MEDIUM** | `backend/src/conversations/router.py:37` | Error detail leakage: `HTTPException(detail=str(e))` returns raw exceptions to clients across 7 endpoints. |

---

## PART 4: Infrastructure & Deployment Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **I1** | **HIGH** | `backend/Dockerfile:24-28` | `USER appuser` but `appuser` is **never created** with `adduser`. Container build will fail. |
| **I2** | **HIGH** | `compose.yml:12` | **Env var name mismatch**: Docker sets `MODEL_ACCESS_KEY` / `DO_AI_MODEL` but config expects `do_model_access_key` / `do_llm_model_id`. LLM API key won't load. |
| **I3** | **HIGH** | `compose.yml:7` | **Postgres env mismatch**: Docker sets `POSTGRES_URL` but config expects field `do_postgres_url` → env var `DO_POSTGRES_URL`. |
| **I4** | **HIGH** | `backend/src/embedding/vector_store.py:10-11` | **Broken imports**: references `..rag.pdf_processor` and `..printmeup` which don't exist. File crashes on import. |
| **I5** | **MEDIUM** | `compose.yml:38-40` | Frontend depends on `service_healthy` but backend has **no healthcheck defined** in compose. Will hang forever. |
| **I6** | **MEDIUM** | `backend/src/main.py:140-148` | **Hardcoded CORS origins** — only localhost. Production with real domains will be blocked. |
| **I7** | **MEDIUM** | `backend/src/main.py:188` | Health endpoint **always returns OK** (`if True:`) regardless of actual system state. |
| **I8** | **MEDIUM** | `backend/src/db/sql_models.py:305` | All timestamps stored as `String(50)` instead of `DateTime` — prevents DB-level date operations. |
| **I9** | **MEDIUM** | `backend/src/config.py:108` | Deprecated `class Config` inner class instead of Pydantic v2 `model_config = SettingsConfigDict(...)`. May not load `.env` files correctly. |
| **I10** | **MEDIUM** | `backend/src/db/sql_client.py:38` | If `do_postgres_url` is empty (the default), `create_engine("")` will raise a confusing error. No validation. |
| **I11** | **MEDIUM** | `backend/src/db/sql_models.py:316` | Messages stored as single JSON text blob (`Text, default="[]"`). Grows unbounded, performance bottleneck for long conversations. |
| **I12** | **LOW** | `backend/src/config.py:44` | `log_level: str = "DEBUG"` in production default. Should be INFO; DEBUG generates excessive logs. |
| **I13** | **LOW** | `backend/pyproject.toml:8` | Requires Python >=3.13 — very restrictive, many deployment environments may not have it. |
| **I14** | **LOW** | `backend/Dockerfile:19` | No lockfile pinning: `uv pip install` without a lockfile makes builds non-reproducible. |
| **I15** | **LOW** | `backend/src/auth/service.py:75` | Timestamp-based user IDs (`user_{ms_timestamp}`) — not guaranteed unique under concurrent registrations. Should use UUID. |
| **I16** | **LOW** | `backend/src/conversations/service.py` | No pagination on `get_conversations()` — loads ALL conversations for a user with no limit/offset. |
| **I17** | **LOW** | `backend/src/drugs/router.py:92-100` | GET endpoint with request body (`/interactions`). Non-standard; many proxies strip GET bodies. Should be POST. |
| **I18** | **LOW** | `backend/src/embedding/pdf_processor.py:1` | Debugging import left in: `from pdb import pm`. Unused, confusing. |
| **I19** | **LOW** | `backend/src/conversations/router.py:93` | Returns stale title after update — returns `conversation.title` (old value) instead of `body.title`. |

---

## PART 5: Frontend Issues

| # | Severity | File | Issue |
|---|----------|------|-------|
| **F1** | **HIGH** | `frontend/src/App.jsx:51-54` | **React Hooks violation** — `useEffect` called after conditional early return. Breaks Rules of Hooks. Potential runtime errors. |
| **F2** | **MEDIUM** | `frontend/src/App.jsx` (entire) | **Entirely dead code** — never referenced by the router in `main.jsx`. Still gets bundled. |
| **F3** | **MEDIUM** | `frontend/src/pages/Chat.jsx:325-327` | SSE buffer may **lose the final event** if stream ends without trailing `\n\n`. |
| **F4** | **MEDIUM** | `frontend/src/main.jsx:14-26` | **No route protection** — `/chat`, `/admin`, `/patients` are open. Each page checks auth independently and inconsistently. |
| **F5** | **MEDIUM** | Multiple files | Token stored in `localStorage` with **no expiry/refresh handling**. 401 responses show generic errors instead of redirecting to login. |
| **F6** | **MEDIUM** | `frontend/src/Auth.jsx:41-43` | Registration flow broken — shows alert to "check the Register page" but provides no navigation. User is stuck. Legacy component. |
| **F7** | **LOW** | `frontend/src/pages/PatientAnalysis.jsx:87` | Analysis rendered as raw text instead of Markdown. Backend may return markdown-formatted content. |
| **F8** | **LOW** | Multiple files | Extensive `console.log` debug statements left in production code. Leaks potentially sensitive info in browser console. |
| **F9** | **LOW** | `frontend/src/pages/DrugSearch.jsx:40-41` | Every page component independently manages `user` and `theme` state from localStorage. No shared context provider. |
| **F10** | **LOW** | `frontend/src/pages/Chat.jsx:72-96` | `loadConversations` doesn't handle 401 responses — no redirect to login on expired token. |
| **F11** | **LOW** | `frontend/src/pages/PatientAnalysis.jsx:22-32` | Missing `response.ok` check before parsing JSON. HTTP errors may cause unexpected behavior. |

---

## Presentation-Day Risk Summary

### Highest-Impact Risks for PubMed Demo

1. **P2 (DOI break bug)** — articles may appear with missing DOIs, breaking "View PDF" links
2. **P5 (no REST endpoint)** — PubMed search can only be demoed through the chat agent, not directly
3. **P9 (false retries)** — queries with genuinely 0 results take ~1.2s extra for useless retries
4. **P1 (over-fetching)** — always fetches 15 articles minimum, adding latency even for small requests
5. **A1 (sync invoke blocks event loop)** — entire server freezes during agent execution; if LLM is slow, frontend appears hung
6. **P6 (PDF availability lie)** — if you demo "View PDF," it always says available even when it isn't

### What to Avoid Demoing (Landmines)

- **Don't query with Turkish characters** — you'll get a hard rejection even for valid medical terms
- **Don't try admin features** — auth is broken (no token returned)
- **Don't try to open PDFs for articles that only have PMC IDs but no DOIs** — the DOI break bug may hit
- **Don't push a large number of simultaneous requests** — sync invoke blocks the event loop

---

## Issue Count Summary

| Severity | Count |
|----------|-------|
| **CRITICAL** | 2 |
| **HIGH** | 14 |
| **MEDIUM** | 30 |
| **LOW** | 19 |
| **Total** | **65** |
