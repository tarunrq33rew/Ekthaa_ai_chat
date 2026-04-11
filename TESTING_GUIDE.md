# Real-World Testing Guide

## Overview
This guide covers comprehensive testing for the product/service discovery chatbot in product-only mode.

---

## 1. Pre-Testing Setup

### Start the Server
```bash
cd "/Users/shiva/Documents/Ekthaa/AI/ chat-bot/backend"
source ../.venv/bin/activate
python3 app.py
```
Server runs on `http://localhost:5001`

### Get JWT Token
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
Save the token from response - you'll use it for all API calls.

---

## 2. Manual Testing via cURL

### Product Query Test
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where can I buy a carpet in Bangalore?",
    "language": "en",
    "conversation_id": "test_conv_1"
  }'
```

**Expected Response:**
- `status`: "success"
- `query_type`: "product_search"
- `reply`: List of nearest carpet retailers with locations

### Out-of-Scope Query Test (Financial)
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my total due?",
    "language": "en",
    "conversation_id": "test_conv_2"
  }'
```

**Expected Response:**
- `status`: "out_of_scope"
- HTTP Status: `400`
- `reply`: "I'm designed to help you find products and services nearby..."
- `query_type`: "out_of_scope"

### Out-of-Scope Query Test (Off-Topic)
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me a joke",
    "language": "en",
    "conversation_id": "test_conv_3"
  }'
```

**Expected Response:**
- `status`: "out_of_scope"
- HTTP Status: `400`
- `reply`: "I'm designed to help you find products and services nearby..."

### Multi-Language Test (Hindi/Hinglish)
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "kahan pe plumber mil sakta hai?",
    "language": "hi",
    "conversation_id": "test_conv_4"
  }'
```

**Expected Response:**
- `status`: "success"
- `query_type`: "product_search"
- `reply`: Results in Hindi/Hinglish with nearest plumbers

---

## 3. Web UI Testing (via chat_tester.html)

1. Open `backend/chat_tester.html` in your browser
2. Enter your JWT token in the input field
3. Select language (English, Hindi, Telugu, Tamil, etc.)
4. Type test messages:
   - Product queries: "Where can I find a doctor?"
   - Financial queries: "Show my spending"
   - Off-topic: "What's the weather?"
5. Verify responses match expected behavior

---

## 4. Test Scenarios

### Scenario A: Product Search (Basic)
| Query | Language | Expected Type | Expected Status |
|-------|----------|---------------|-----------------|
| "Where can I buy a carpet?" | en | product_search | 200 |
| "Find a plumber near me" | en | product_search | 200 |
| "Nearest grocery store" | en | product_search | 200 |
| "Can you get me a pizza?" | en | product_search | 200 |

### Scenario B: Financial Rejection (Strict Block)
| Query | Language | Expected Type | Expected Status | Expected Response |
|-------|----------|---------------|-----------------|-------------------|
| "What do I owe?" | en | out_of_scope | 400 | I'm designed to help with products... |
| "Show my transactions" | en | out_of_scope | 400 | I'm designed to help with products... |
| "What's my balance?" | en | out_of_scope | 400 | I'm designed to help with products... |
| "Can I transfer money?" | en | out_of_scope | 400 | I'm designed to help with products... |

### Scenario C: Off-Topic Rejection
| Query | Language | Expected Type | Expected Status |
|-------|----------|---------------|-----------------|
| "Tell me a joke" | en | out_of_scope | 400 |
| "What's 2+2?" | en | out_of_scope | 400 |
| "How's the weather?" | en | out_of_scope | 400 |
| "Who is the PM?" | en | out_of_scope | 400 |

### Scenario D: Multi-Language Support
| Query | Language | Expected Type | Expected Response Language |
|-------|----------|---------------|---------------------------|
| "kahan pe carpet mil sakta hai?" | hi | product_search | Hinglish |
| "Emundi electronics shops unnai?" | te | product_search | Tenglish |
| "Yeppadi kathai kalaigal pidithaalam?" | ta | product_search | Tanglish |
| "Kahan par ek plumber chahiye?" | en | product_search | English |

### Scenario E: Edge Cases
| Query | Expected Behavior |
|-------|-------------------|
| Empty message | Should handle gracefully |
| Very long query | Should classify correctly |
| Mixed languages | Should detect primary language |
| Special characters | Should not break classifier |
| Spam/gibberish | Should return out_of_scope |

---

## 5. Performance Testing

### Response Time Check
```bash
# Measure response time for product query
time curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Where can I buy a sofa?", "language": "en"}'
```

**Expected:** < 5 seconds for product queries

### Rate Limiting Check
```bash
# Make 21+ requests in quick succession
for i in {1..25}; do
  curl -X POST http://localhost:5001/api/ai/chat \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test query $i\", \"language\": \"en\"}"
  echo "Request $i done"
done
```

**Expected:** After 20 requests → 429 (Too Many Requests) error

---

## 6. Error Handling Tests

### Missing JWT Token
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where can I buy a carpet?", "language": "en"}'
```
**Expected:** 401 Unauthorized

### Invalid JWT Token
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer invalid_token_xyz" \
  -H "Content-Type: application/json" \
  -d '{"message": "Where can I buy a carpet?", "language": "en"}'
```
**Expected:** 401 Unauthorized

### Missing Required Fields
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Where can I buy a carpet?"}'
```
**Expected:** 400 Bad Request (missing `language` field)

---

## 7. Security Testing

### SQL Injection Attempt
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "\" OR 1=1 --", "language": "en"}'
```
**Expected:** Safe handling, treated as out_of_scope

### Cross-Site Scripting (XSS) Attempt
```bash
curl -X POST http://localhost:5001/api/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "<script>alert(\"xss\")</script>", "language": "en"}'
```
**Expected:** Safe handling, treated as out_of_scope

---

## 8. Automated Testing

Run the comprehensive test script:
```bash
python3 test_real_world.py
```

This will execute all test scenarios and generate a report: `test_results_real_world.json`

---

## 9. Demo Flow for Investor

### Step 1: Product Query
```
User: "Where can I buy a carpet in Bangalore?"
Chatbot: [Shows 3-5 nearest retailers with distance, ratings, phone]
```

### Step 2: Financial Query (Shows Product-Only Mode)
```
User: "What do I owe?"
Chatbot: "I'm designed to help you find products and services nearby..."
```

### Step 3: Multi-Language
```
User (Hindi): "kahan pe electrician mil sakta hai?"
Chatbot: [Shows nearest electricians in Hindi response]
```

### Step 4: Cross-Selling
```
User: "I need a plumber"
Chatbot: [Shows plumbers + suggests electricians/repairs adjacent to location]
```

---

## 10. Success Criteria Checklist

- [ ] All product queries return results with retailer info
- [ ] All financial queries return 400 with rejection message
- [ ] All off-topic queries return 400 with rejection message
- [ ] Multi-language responses are in correct language (Hinglish/Tenglish/etc.)
- [ ] Response time < 5 seconds for product queries
- [ ] Rate limiting works (429 after 20 requests)
- [ ] JWT authentication enforced (401 without token)
- [ ] No errors in server logs
- [ ] Web UI (chat_tester.html) works smoothly
- [ ] Security tests pass (no SQL injection/XSS handling)

---

## 11. Troubleshooting

### Server Won't Start
```bash
# Check port availability
lsof -i :5001
# Kill process if needed
kill -9 <PID>
```

### "No businesses found" Response
- Verify business data is populated in Appwrite
- Check `search_businesses()` function in rag_service.py
- Verify embeddings are cached properly

### "Unauthorized" Errors
- Regenerate JWT token with valid credentials
- Check token hasn't expired (default: 24 hours)

### Multi-Language Not Working
- Verify language code is correct (en, hi, te, ta, mr, bn)
- Check `LANGUAGE_MAP` in system_prompt.py
- Ensure transliteration examples are properly configured

---

## 12. Next Steps
1. Run `test_real_world.py` first
2. Fix any failing tests
3. Manual testing via cURL using scenarios above
4. Test via web UI (chat_tester.html)
5. Performance & security testing
6. Demo walkthrough with investor
