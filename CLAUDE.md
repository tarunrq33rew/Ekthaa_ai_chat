# Ekthaa AI Backend - Agent Instructions

You are an autonomous coding agent working on the Ekthaa AI Backend.

## Build & Test Commands
- **Run Server**: `python app.py` (requires environment variables)
- **Run Tests**:
  - `python test_refinement.py` (Filters test)
  - `python test_ai.py` (AI connectivity test)
- **Dependency Install**: `pip install -r requirements.txt`

## Project Architecture
- **Framework**: Flask
- **AI Core**: Groq (`llama-3.3-70b-versatile`)
- **Embeddings**: Google Generative AI (`gemini-embedding-001`)
- **Memory/BaaS**: Appwrite (Database IDs in `.env`)

## Task Execution Pattern (Ralph Style)
1. Read `prd.json` to identify the next priority task.
2. Read `progress.txt` for recent learnings and patterns.
3. Implement the story.
4. Run `test_refinement.py` and ensure zero regressions.
5. Update `progress.txt` with what you did and learned.
6. Commit changes with `feat: [Story ID] - [Title]`.
7. Set `passes: true` in `prd.json`.

## Code Style & Conventions
- **Logging**: Use `logging.getLogger(__name__)`. Info logs for flows, Debug for data.
- **Errors**: Return JSON with `error` key and appropriate HTTP status.
- **Fail-Safe**: If AI refinement fails, return raw RAG results (do not crash).
- **Hardcoding**: ABSOLUTELY NO hardcoded API keys. Use `os.getenv`.

---
*Last updated: 2026-04-11*
