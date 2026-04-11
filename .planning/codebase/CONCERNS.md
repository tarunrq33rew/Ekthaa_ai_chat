# Technical Concerns & Debt

Current limitations and areas for improvement in the Ekthaa AI backend.

## Security & Privacy
- **Hardcoded Demo User**: Currently, the `/api/ai/chat` endpoint uses a fixed `demo_user` ID. This must be replaced with dynamic ID extraction from the JWT payload.
- **Exposure of `businesses` details**: Full business addresses and phone numbers are sent to the AI in the prompt; ensure this conforms to privacy requirements.

## Performance & Scalability
- **Latency**: The addition of the `refinement` layer adds 1-2 seconds of latency per search request. Consider running search and initial prompt evaluation in parallel if possible.
- **In-Memory State**: `_daily_usage` (usage tracking) and `_business_embeddings` (RAG cache) are in-memory. This data will be lost on server restart and is not synchronized across multi-instance deployments.
- **Appwrite Sequential Fetch**: `rag_service.py` fetches businesses sequentially with 100-limit paging. For large datasets, this initialization will be slow.

## Code Quality & Maintainability
- **Implicit Dependencies**: The system relies on the `GLOBAL_BUSINESS` tag in Appwrite. If this tag is changed or deleted, RAG will break silently.
- **Environment Variance**: Many configurations are hardcoded (like `MAX_MESSAGES_PER_DAY`). These should be moved to a configuration service or `config.json`.

---
*Last mapped: 2026-04-11*
