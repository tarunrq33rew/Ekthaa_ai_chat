# Coding Conventions

Patterns and standards used in the Ekthaa AI backend.

## General Patterns
- **Logging**: Every module uses `logging.getLogger(__name__)`. Info logs are used for major events (e.g., `Refining complete`), while Debug logs are used for data inspection.
- **Fail-Safe Logic**: AI-dependent functions (like refinement) should fail gracefully. If the AI call fails, the system should return the best available non-filtered data rather than crashing.
- **Statelessness**: The API is largely stateless, relying on the client to pass necessary context (though basic in-memory usage tracking exists).

## Memory Persistence & Agent Continuity (Ralph Pattern)
- **progress.txt**: Every significant task completion MUST be logged in `progress.txt` under the current date. Include "Learnings for future iterations" to maintain project context.
- **CLAUDE.md**: Root-level instructions MUST be updated when new project-wide patterns (e.g., new auth headers, database schemas) are established.
- **prd.json**: The machine-readable task state must be kept in sync with the human-readable ROADMAP.md.

## Python Style
- **Naming**: Follows PEP 8 (snake_case for functions and variables).
- **Type Hinting**: Used in newer modules (e.g., `data_retrieval_service.py`) for better IDE support.
- **Docstrings**: Essential for major entry points (`app.py`, `rag_service.py`).

## AI Integration Conventions
- **System Prompts**: Centralized in `system_prompt.py`. Logic for building prompts should be separate from logic for calling the AI.
- **Response Format**: Chat responses should be clean strings, while utility AI calls (like refinement) should prefer JSON output.

---
*Last mapped: 2026-04-11*
