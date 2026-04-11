# Testing Strategies

Overview of how to verify the Ekthaa AI backend.

## Automated Testing
The project uses standalone Python scripts for unit testing logic components.

### Unit Tests
- `test_refinement.py`: Verifies the `refine_business_results` function. Checks if irrelevant businesses are successfully filtered out of search results.
- `test_ai.py`: Verifies basic chat completion connectivity and response formatting.

### Running Tests
Execute from the project root:
```bash
python test_refinement.py
python test_ai.py
```

## Manual Testing
- **Chat Tester**: `chat_tester.html` provides a simple UI to interact with the backend API.
- **Health Check**: `GET /api/health` can be used to verify if the server is up and responsive.

## Areas with Low Coverage
- **Appwrite Integration**: Currently relies on real API calls; needs mock-based testing for offline verification.
- **Query Classification**: Needs a comprehensive edge-case test suite for multilingual queries.

---
*Last mapped: 2026-04-11*
