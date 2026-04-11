# Roadmap: Ekthaa AI Assistant Backend

## Overview
This roadmap outlines the journey from the current baseline (demo mode with RAG) to a production-ready AI backend with secure authentication, persistent state management, and optimized vector performance.

## Phases

- [x] **Phase 1: Foundation & Refinement** - Mapping codebase and adding AI refinement logic.
- [ ] **Phase 2: Authentication & Identity** - Transition from demo mode to secure JWT-based user session handling.
- [ ] **Phase 3: Persistent Usage Tracking** - Implementing database-backed message limiting to prevent abuse.
- [ ] **Phase 4: Production Observability** - Adding structured logging and monitoring for AI latency.

## Phase Details

### Phase 1: Foundation & Refinement
**Goal**: Establish a baseline understanding of the codebase and improve result precision.
**Status**: Complete
**Success Criteria**:
  1. Base code is mapped into `.planning/codebase/`.
  2. `data_retrieval_service.py` successfully filters semantic search results.
**Plans**: 1 plan (Complete)

### Phase 2: Authentication & Identity
**Goal**: Secure the API using JWT and isolate user data via dynamic ID extraction.
**Depends on**: Phase 1
**Requirements**: 
  - REQ-AUTH-01: Extract `user_id` from Bearer JWT in `app.py`.
  - REQ-AUTH-02: Remove `demo_user` hardcoded logic.
**Success Criteria**:
  1. API returns 401/403 for invalid or missing tokens.
  2. Queries are correctly isolated to the user's personal scope in Appwrite.
**Plans**: 2 plans

Plans:
- [ ] 02-01: Implement JWT middleware for user identity extraction.
- [ ] 02-02: Refactor `ai_chat` and `rag_service` to use dynamic user context.

### Phase 3: Persistent Usage Tracking
**Goal**: move usage limits from memory to a persistent store.
**Depends on**: Phase 2
**Requirements**:
  - REQ-SCALE-01: Store daily message counts in Appwrite.
  - REQ-SCALE-02: Atomic increments for usage counters.
**Success Criteria**:
  1. User usage limits survive server restarts.
  2. Limits are enforced correctly across multiple parallel requests.
**Plans**: 1 plan

### Phase 4: Production Observability
**Goal**: Improve monitoring and error handling for production scale.
**Depends on**: Phase 3
**Success Criteria**:
  1. AI latency is tracked and logged per request.
  2. Service degradation (e.g., Groq downtime) is handled gracefully with clear user feedback.
**Plans**: 1 plan

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | Complete | 2026-04-11 |
| 2. Auth & Identity | 0/2 | Not started | - |
| 3. Usage Tracking | 0/1 | Not started | - |
| 4. Observability | 0/1 | Not started | - |

---
*Last updated: 2026-04-11 after GSD Initialization*
