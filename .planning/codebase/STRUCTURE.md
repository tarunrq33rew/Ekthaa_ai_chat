# Project Structure

Ekthaa AI Assistant backend directory layout.

## Root Directory
- `app.py`: Main Flask entry point and API route definitions.
- `requirements.txt`: Python dependencies.
- `data.csv`: Source business data (used for seeding/testing).
- `.env`: Environment variables (API keys, endpoints).
- `chat_tester.html`: UI tool for manual chat verification.

## Core Modules (`/`)
- `ai_service.py`: Interface for Groq LLM calls.
- `rag_service.py`: Vector search logic using Numpy and Appwrite.
- `query_classifier.py`: Rule-based query categorization and normalization.
- `data_retrieval_service.py`: Post-search AI refinement of results.
- `context_builder.py`: Manages user history and conversation state.
- `system_prompt.py`: Prompt engineering templates for different scenarios.

## Documentation & Testing
- `README.md`: Project overview.
- `TESTING_GUIDE.md`: Instructions for running tests.
- `test_refinement.py`: Unit test for the data retrieval service.
- `test_ai.py`: Test for AI response generation.
- `scripts/`: Utility scripts (e.g., seeding data).

## GSD Internal
- `.planning/`: Agentic workflow state (Roadmap, Requirements, etc.).
  - `codebase/`: Technical map of the current state.

---
*Last mapped: 2026-04-11*
