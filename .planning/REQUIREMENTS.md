# Requirements: Ekthaa AI Assistant Backend

**Defined:** 2026-04-11
**Core Value:** Providing highly relevant, grounded AI responses through specialized data filtering and robust multi-language support.

## v1 Requirements

### Foundation & Refinement
- [x] **BASE-01**: Flask API setup with health and chat endpoints.
- [x] **BASE-02**: RAG pipeline connecting Appwrite business data to AI prompts.
- [x] **BASE-03**: AI Refinement layer using Llama 3 to filter search results for precision.
- [x] **BASE-04**: Multi-language detection and English fallback for regional languages.

### Authentication & Identity
- [ ] **AUTH-01**: System extracts `user_id` from Bearer JWT in the request header.
- [ ] **AUTH-02**: System provides error response for missing or invalid tokens.
- [ ] **AUTH-03**: RAG queries are dynamically filtered by the extracted `user_id` to ensure data privacy.

### Scaling & Observability
- [ ] **SCALE-01**: Message usage is tracked per user in a persistent database (Appwrite).
- [ ] **SCALE-02**: Users are limited to 20 messages per day (survives restarts).
- [ ] **OBSV-01**: AI request latency and status are logged for production monitoring.

## Out of Scope

| Feature | Reason |
|---------|--------|
| User Registration | Handled by Appwrite directly or via a separate auth service. |
| Vector Management UI | Managed through the Appwrite console or standalone scripts. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BASE-01 | Phase 1 | Complete |
| BASE-02 | Phase 1 | Complete |
| BASE-03 | Phase 1 | Complete |
| BASE-04 | Phase 1 | Complete |
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 2 | Pending |
| SCALE-01 | Phase 3 | Pending |
| SCALE-02 | Phase 3 | Pending |
| OBSV-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-11*
*Last updated: 2026-04-11 after initial definition*
