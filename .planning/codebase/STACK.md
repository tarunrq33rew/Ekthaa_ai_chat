# Tech Stack

Ekthaa AI Assistant backend.

## Languages & Runtime
- **Python 3.10+**: Core logic and API server.
- **Node.js**: (Inferred) Only used for orchestration tools like `gsd-tools.cjs`.

## Frameworks & Libraries
- **Flask (3.0.0)**: Main web framework for the API.
- **Flask-CORS (4.0.0)**: Handles Cross-Origin Resource Sharing for the web/mobile clients.
- **Numpy**: Used for fast in-memory vector similarity calculations (Cosine Similarity) in the RAG service.
- **PyJWT (2.8.0)**: Handles JSON Web Token signing and verification for authenticated endpoints.
- **python-dotenv**: Manages environment variables from `.env`.

## AI & Machine Learning
- **Groq (0.9.0)**: Primary LLM provider for chat completion (using Llama 3.3 70B).
- **Google Generative AI (0.7.2)**: Used for generating text embeddings (`models/gemini-embedding-001`).

## Data & Storage
- **Appwrite (5.0.2)**: Backend-as-a-Service (BaaS) used as the primary database for business details and pre-calculated embeddings.
- **In-memory cache**: RAG service maintains an in-memory Numpy array of business vectors for high-performance search.

## Configuration
- `.env`: Contains API keys for Groq, Gemini, and Appwrite credentials.
- `requirements.txt`: Standard Python dependency manifest.

---
*Last mapped: 2026-04-11*
