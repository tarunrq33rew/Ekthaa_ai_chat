# Ekthaa AI Assistant Backend

## What This Is

A Python/Flask backend for an AI search and discovery assistant. It utilizes a RAG (Retrieval-Augmented Generation) pipeline to connect users with relevant businesses and services stored in Appwrite, while maintaining strict data isolation for personal user records.

## Core Value

Providing highly relevant, grounded AI responses through specialized data filtering and robust multi-language support.

## Requirements

### Validated

- ✓ **Flask API Server**: Operational routes for health checks and chat interactions.
- ✓ **RAG Implementation**: Semantic search over global business datasets using Google Generative AI embeddings and Numpy vector similarity.
- ✓ **Query Classification**: Automated mapping of user intent to either "product_search" or "out_of_scope" to optimize model usage.
- ✓ **Business Refinement**: Post-search AI filtering layer (Llama 3) that ensures search results precisely match the user's intent.
- ✓ **Multilingual Support**: Intelligent handling of regional languages with clear fallbacks to simple English.

### Active

- [ ] **JWT Authentication**: Move from hardcoded `demo_user` to dynamic user identity extraction from Bearer tokens.
- [ ] **Persistent Usage Tracking**: Transition the message limit counter from in-memory dictionary to a persistent database (Appwrite or similar).
- [ ] **Vector Performance Optimization**: Evaluate moving from Numpy in-memory search to Appwrite's native vector search features if the dataset exceeds memory limits.

### Out of Scope

- [ ] **Web Frontend**: This repository focuses strictly on backend API logic.
- [ ] **Mobile Asset Management**: Content like images or icons for the mobile app are managed outside this service.

## Context

The system is designed for the Indian market, requiring support for code-mixing (Hinglish) and various regional dialects. It relies on Groq for high-speed inference and Gemini for cost-effective embeddings.

## Constraints

- **Tech Stack**: Python/Flask with Appwrite as the BaaS.
- **Security**: Must enforce strict user data isolation in RAG queries.
- **Cost**: Daily message limits (currently 20/day) are enforced to stay within free-tier API quotas.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Groq as Primary Provider | Superior speed/latency for chat interactions compared to native Gemini calls. | ✓ Good |
| In-memory Numpy RAG | Fast implementation for current dataset size without needing a dedicated vector DB. | ✓ Good |
| AI Refinement Layer | RAG alone produced too many "near-miss" results; a secondary LLM filter is needed for precision. | ✓ Good |

---
## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-11 after GSD Initialization*
