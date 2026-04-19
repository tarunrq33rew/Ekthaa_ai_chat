# Ekthaa AI Assistant — Backend

Conversational AI chatbot for the Ekthaa app. Answers natural-language questions about a user's dues, transactions, and shops using live Appwrite data.

## Stack
- **Flask** — REST API
- **Google Gemini 1.5 Flash** — primary AI model (free: 1,500 req/day)
- **Groq Llama 3.1 8B** — automatic fallback (free: 14,400 req/day)
- **Appwrite** — database (transactions, shops, users)

## Setup

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in your keys in .env
```

Get free API keys:
- **Gemini**: https://aistudio.google.com/app/apikey
- **Groq**: https://console.groq.com

### 3. Run the server
```bash
python app.py
```
Server starts on **port 5001** by default.

---

## API Reference

### `GET /api/health`
No auth required.
```json
{ "status": "ok", "service": "Ekthaa AI Assistant" }
```

### `POST /api/ai/chat`
Requires `Authorization: Bearer <JWT>` header.

**Request:**
```json
{
  "user_id": "abc123",
  "message": "Total due?",
  "language": "en",
  "history": []
}
```
Languages: `en`, `hi`, `te`, `ta`, `mr`, `bn`

**Response:**
```json
{
  "reply": "You owe ₹850 to Sharma Store.",
  "model_used": "gemini",
  "status": "ok"
}
```

### `POST /api/ai/invalidate-cache`
Clears the 5-minute context cache for a user. Call this after recording a new payment.
```json
{ "user_id": "abc123" }
```

---

## File Structure
```
backend/
├── app.py              ← Flask server + routes
├── context_builder.py  ← Fetches & caches Appwrite data
├── system_prompt.py    ← Builds the AI system prompt
├── ai_service.py       ← Gemini + Groq calls
├── requirements.txt
└── .env.example
```

## Rate Limits & Free Tier
| Model | Free Limit | Used For |
|---|---|---|
| Gemini 1.5 Flash | 1,500 req/day | Primary |
| Groq Llama 3.1 8B | 14,400 req/day | Auto-fallback |

A 20 msgs/user/day soft limit is enforced in-app. Appwrite context is cached 5 min per user.

# Ekthaa_ai_chat
