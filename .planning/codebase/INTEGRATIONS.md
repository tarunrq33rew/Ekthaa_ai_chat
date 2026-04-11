# External Integrations

List of external services and APIs integrated into the Ekthaa AI backend.

## AI Services

### Groq API
- **Purpose**: High-speed LLM inference.
- **Model**: `llama-3.3-70b-versatile`.
- **Primary file**: `ai_service.py`.
- **Key functions**: `call_groq`.

### Google Gemini API
- **Purpose**: Vector embeddings generation.
- **Model**: `models/gemini-embedding-001`.
- **Primary file**: `rag_service.py`.
- **Key functions**: `_generate_embedding`.

## Infrastructure & Platform

### Appwrite (BaaS)
- **Purpose**: Database, document storage, and centralized project management.
- **Collections**:
  - `businesses`: Store full business profile details (name, address, rating, etc.).
  - `embeddings`: Stores pre-calculated vector representations of business data.
- **Primary file**: `rag_service.py`.
- **Integration method**: REST API via `requests` (Appwrite SDK is present in `requirements.txt` but `rag_service.py` currently uses direct HTTP calls).

## Security & Auth

### JWT (Bearer Authentication)
- **Purpose**: Authenticating requests from the frontend/mobile apps.
- **Secret Key**: Managed via `JWT_SECRET_KEY` in env.
- **Primary file**: `app.py`.

---
*Last mapped: 2026-04-11*
