# Test Scenarios & Expected Results

## Test Case Format
```json
{
  "test_id": "identifier",
  "category": "product_search | out_of_scope | edge_case | security",
  "query": "user message",
  "language": "en | hi | te | ta | mr | bn",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "description"
}
```

---

## Category 1: Product Search - Should Pass (HTTP 200)

### Basic Product Searches
```json
{
  "test_id": "PS001",
  "category": "product_search",
  "query": "Where can I buy a carpet?",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Basic carpet search"
}
```

```json
{
  "test_id": "PS002",
  "category": "product_search",
  "query": "Find a plumber near me",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Service search - plumbing"
}
```

```json
{
  "test_id": "PS003",
  "category": "product_search",
  "query": "Nearest grocery store",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Retail search"
}
```

```json
{
  "test_id": "PS004",
  "category": "product_search",
  "query": "Can you get me a pizza?",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Food delivery intent"
}
```

```json
{
  "test_id": "PS005",
  "category": "product_search",
  "query": "Where is the nearest hospital?",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Healthcare search"
}
```

```json
{
  "test_id": "PS006",
  "category": "product_search",
  "query": "Find an electrician",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Service search - electrical"
}
```

```json
{
  "test_id": "PS007",
  "category": "product_search",
  "query": "Show me nearby restaurants",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Restaurant discovery"
}
```

```json
{
  "test_id": "PS008",
  "category": "product_search",
  "query": "I need a mechanic for my car",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Auto service search"
}
```

### Multi-Language Product Searches

```json
{
  "test_id": "PS301",
  "category": "product_search",
  "query": "kahan pe carpet mil sakta hai?",
  "language": "hi",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Hindi - carpet search"
}
```

```json
{
  "test_id": "PS302",
  "category": "product_search",
  "query": "kahan par ek plumber chahiye?",
  "language": "hi",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Hindi/Hinglish - plumber search"
}
```

```json
{
  "test_id": "PS303",
  "category": "product_search",
  "query": "electrician kaun se khoj rahe ho?",
  "language": "hi",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "Hinglish - electrician search"
}
```

```json
{
  "test_id": "PS304",
  "category": "product_search",
  "query": "Nearby pizza restaurants please",
  "language": "en",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "expected_status": "success",
  "notes": "English - food service"
}
```

---

## Category 2: Out-of-Scope - Financial Queries (HTTP 400)

```json
{
  "test_id": "OOS001",
  "category": "out_of_scope",
  "query": "What do I owe?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - outstanding balance"
}
```

```json
{
  "test_id": "OOS002",
  "category": "out_of_scope",
  "query": "Show my transactions",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - transaction history"
}
```

```json
{
  "test_id": "OOS003",
  "category": "out_of_scope",
  "query": "What's my balance?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - account balance"
}
```

```json
{
  "test_id": "OOS004",
  "category": "out_of_scope",
  "query": "Can I transfer money?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - money transfer"
}
```

```json
{
  "test_id": "OOS005",
  "category": "out_of_scope",
  "query": "Show my spending history",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - spending analytics"
}
```

```json
{
  "test_id": "OOS006",
  "category": "out_of_scope",
  "query": "How much did I spend last month?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - monthly spending"
}
```

```json
{
  "test_id": "OOS007",
  "category": "out_of_scope",
  "query": "What are my payment dues?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - payment dues"
}
```

```json
{
  "test_id": "OOS008",
  "category": "out_of_scope",
  "query": "I need a loan",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Financial - loan request"
}
```

---

## Category 3: Out-of-Scope - Off-Topic Queries (HTTP 400)

```json
{
  "test_id": "OOS101",
  "category": "out_of_scope",
  "query": "Tell me a joke",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Entertainment - joke"
}
```

```json
{
  "test_id": "OOS102",
  "category": "out_of_scope",
  "query": "What's 2+2?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "General knowledge - math"
}
```

```json
{
  "test_id": "OOS103",
  "category": "out_of_scope",
  "query": "How's the weather?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "General knowledge - weather"
}
```

```json
{
  "test_id": "OOS104",
  "category": "out_of_scope",
  "query": "Who is the Prime Minister?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "General knowledge - politics"
}
```

```json
{
  "test_id": "OOS105",
  "category": "out_of_scope",
  "query": "Tell me a story",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Entertainment - story"
}
```

```json
{
  "test_id": "OOS106",
  "category": "out_of_scope",
  "query": "What's your favorite color?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Chit-chat - personal preference"
}
```

```json
{
  "test_id": "OOS107",
  "category": "out_of_scope",
  "query": "Can you sing a song?",
  "language": "en",
  "expected_http_status": 400,
  "expected_query_type": "out_of_scope",
  "expected_status": "out_of_scope",
  "notes": "Entertainment - song request"
}
```

---

## Category 4: Edge Cases

```json
{
  "test_id": "EDG001",
  "category": "edge_case",
  "query": "",
  "language": "en",
  "expected_http_status": 400,
  "notes": "Empty message - should be handled gracefully"
}
```

```json
{
  "test_id": "EDG002",
  "category": "edge_case",
  "query": "   ",
  "language": "en",
  "expected_http_status": 400,
  "notes": "Whitespace only - should be treated as empty"
}
```

```json
{
  "test_id": "EDG003",
  "category": "edge_case",
  "query": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "language": "en",
  "expected_http_status": 400,
  "notes": "Very long gibberish - should be rejected"
}
```

```json
{
  "test_id": "EDG004",
  "category": "edge_case",
  "query": "123456789!@#$%^&*()",
  "language": "en",
  "expected_http_status": 400,
  "notes": "Special characters only - should be rejected"
}
```

```json
{
  "test_id": "EDG005",
  "category": "edge_case",
  "query": "kahan pe carpet in english mixed",
  "language": "hi",
  "expected_http_status": 200,
  "expected_query_type": "product_search",
  "notes": "Mixed language - should detect primary intent"
}
```

---

## Category 5: Security Tests

```json
{
  "test_id": "SEC001",
  "category": "security",
  "query": "\" OR 1=1 --",
  "language": "en",
  "expected_http_status": 400,
  "notes": "SQL Injection attempt - should not execute"
}
```

```json
{
  "test_id": "SEC002",
  "category": "security",
  "query": "<script>alert('xss')</script>",
  "language": "en",
  "expected_http_status": 400,
  "notes": "XSS attempt - should be treated safely"
}
```

```json
{
  "test_id": "SEC003",
  "category": "security",
  "query": "../../../etc/passwd",
  "language": "en",
  "expected_http_status": 400,
  "notes": "Path traversal attempt - should be ignored"
}
```

```json
{
  "test_id": "SEC004",
  "auth": "NONE",
  "category": "security",
  "expected_http_status": 401,
  "notes": "Missing JWT token - should reject request"
}
```

```json
{
  "test_id": "SEC005",
  "auth": "invalid_token",
  "category": "security",
  "expected_http_status": 401,
  "notes": "Invalid JWT token - should reject request"
}
```

---

## Category 6: Rate Limiting

```json
{
  "test_id": "RATE001",
  "category": "rate_limiting",
  "query": "Where can I buy a pen?",
  "language": "en",
  "repeat_count": 25,
  "expected_first_20_http_status": 200,
  "expected_from_21st_http_status": 429,
  "notes": "Rate limit is 20 requests/user/day - should reject 21st"
}
```

---

## Category 7: Performance Benchmarks

| Scenario | Query | Expected Time | Max Time |
|----------|-------|---|---|
| Fast Response | "Find a doctor" | < 2s | 5s |
| Slow Response | "Show all carpets near me with details" | < 4s | 6s |
| Average | "Where to buy pizza?" | < 3s | 5s |

---

## Quick Test Command Reference

### Run all tests
```bash
python3 test_real_world.py
```

### Test single product query
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Where can I buy a carpet?","language":"en","conversation_id":"test1"}'
```

### Test out-of-scope rejection
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What do I owe?","language":"en","conversation_id":"test2"}'
```

### Test without auth (expect 401)
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","language":"en","conversation_id":"test3"}'
```

---

## Success Criteria

For a test to PASS:
1. ✅ HTTP Status Code matches expected
2. ✅ Response JSON includes required fields (status, query_type, reply, etc.)
3. ✅ Response time is within acceptable limits (< 5 seconds)
4. ✅ For product_search: Results include business data (name, location, phone, rating)
5. ✅ For out_of_scope: Reply message is appropriate to rejection reason
6. ✅ Multi-language responses are in correct script (Romanized only, no native scripts)
7. ✅ No authentication bypasses
8. ✅ No SQL injection/XSS issues
9. ✅ Rate limiting enforced correctly

---

## Test Result Template

```json
{
  "test_id": "PS001",
  "status": "PASS | FAIL",
  "expected": {
    "http_status": 200,
    "query_type": "product_search"
  },
  "actual": {
    "http_status": 200,
    "query_type": "product_search",
    "response_time_ms": 1234
  },
  "notes": "Query correctly classified and results returned",
  "timestamp": "2026-04-03T10:30:45.123Z"
}
```
