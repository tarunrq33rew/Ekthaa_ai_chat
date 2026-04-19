"""
app.py
──────
Ekthaa AI Assistant — Flask Backend

Routes:
  GET  /api/health       — health check
  POST /api/ai/chat      — main AI chat endpoint (requires Bearer JWT)
  POST /api/ai/invalidate-cache — clear cached context for a user
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from functools import wraps

import jwt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from services.context_builder import get_user_context, invalidate_cache
from services.system_prompt import build_system_prompt, build_product_discovery_prompt, build_out_of_scope_response, build_final_assistant_prompt
from services.ai_service import call_ai
from services.query_classifier import classify_query
from services.rag_service import search_businesses

# ── Init ──────────────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")

CORS(app, resources={
    r"/*": {
        "origins": "*" if os.getenv("FLASK_ENV") == "development" else [
            "http://localhost:3000",
            "http://localhost:5001",
            "http://localhost:8000",
            "http://localhost:8001",
            "http://localhost:8081",
            "http://localhost:19006",
            "https://ekthaa.com",
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
    }
})

# ── Daily usage tracker (in-memory) ──────────────────────────────────────────
# { user_id: {"date": "YYYY-MM-DD", "count": N} }
_daily_usage: dict = defaultdict(lambda: {"date": "", "count": 0})
MAX_MESSAGES_PER_DAY = 20  # protect free tier


def _check_daily_limit(user_id: str) -> bool:
    """Returns True if user is under their daily limit, False if exceeded."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = _daily_usage[user_id]
    if usage["date"] != today:
        # New day — reset counter
        _daily_usage[user_id] = {"date": today, "count": 0}
    if _daily_usage[user_id]["count"] >= MAX_MESSAGES_PER_DAY:
        return False
    _daily_usage[user_id]["count"] += 1
    return True





# ── Auth Middleware ───────────────────────────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        # Debug fallback if enabled in .env
        if not token and os.getenv("DEBUG_AUTH") == "true":
            logger.info("⚠️  No token provided, falling back to demo_user (DEBUG_AUTH=true)")
            request.user_id = "demo_user"
            return f(*args, **kwargs)

        if not token:
            return jsonify({"error": "Token is missing", "status": "unauthorized"}), 401
        
        try:
            # Note: In production, you would verify this against a public key or Appwrite session
            # For now, we decode using the secret key
            data = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            request.user_id = data.get("sub") or data.get("id") or data.get("userId")
            if not request.user_id:
                raise ValueError("No user_id in token")
        except Exception as e:
            logger.warning(f"❌ Invalid Token: {e}")
            return jsonify({"error": "Invalid or expired token", "status": "unauthorized"}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def index():
    """Friendly index page to show service status."""
    return jsonify({
        "message": "Ekthaa AI Backend is running.",
        "endpoints": {
            "health": "/api/health",
            "chat": "/api/ai/chat",
            "tester": "/chat"
        },
        "status": "online"
    }), 200


@app.route("/chat", methods=["GET"])
def chat_tester():
    """Serve the manual chat tester UI."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), "chat_tester.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check — no auth required."""
    return jsonify({
        "status": "ok",
        "service": "Ekthaa AI Assistant",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


@app.route("/api/ai/chat", methods=["POST"])
@token_required
def ai_chat():
    """Main AI chat endpoint (demo mode - no authentication required).

    Request body (JSON):
    {
        "message"  : "Where can I buy a carpet?",  // User's message (required)
        "language" : "en",                         // en | hi | te | ta | mr | bn (optional)
        "history"  : [                             // Previous conversation turns (optional)
            {"role": "user",  "content": "..."},
            {"role": "model", "content": "..."}
        ]
    }

    Response (JSON):
    {
        "reply"      : "I found these carpet shops near you...",
        "model_used" : "gemini",
        "status"     : "ok"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    message = data.get("message", "").strip()
    language = data.get("language", "en").strip().lower()
    history = data.get("history", [])
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    # Validate optional coords
    try:
        latitude = float(latitude) if latitude is not None else None
        longitude = float(longitude) if longitude is not None else None
    except (ValueError, TypeError):
        latitude = longitude = None

    # ── Validation ────────────────────────────────────────────────────────
    if not message:
        return jsonify({"error": "message is required"}), 400
    if language not in ("en", "hi", "te", "ta", "mr", "bn"):
        language = "en"  # Default to English for unsupported codes

    # ── Authenticated User ────────────────────────────────────────────────
    user_id = request.user_id

    # ── Daily rate limit ──────────────────────────────────────────────────
    if not _check_daily_limit(user_id):
        return jsonify({
            "error": "Daily message limit reached (20 messages/day). Please try again tomorrow.",
            "status": "rate_limited"
        }), 429

    # ── Keep only last 10 turns of history to manage token usage ─────────
    history = history[-10:]

    try:
        # ──────────────────────────────────────────────────────────────────
        # STEP 1: Classify the query to determine intent
        # ──────────────────────────────────────────────────────────────────
        query_type, confidence = classify_query(message, language)
        
        # ──────────────────────────────────────────────────────────────────
        # STEP 2: Route to appropriate handler
        # ──────────────────────────────────────────────────────────────────
        
        if query_type == "out_of_scope":
            # Very short greeting or unrelated — let the AI answer directly without context
            logger.info(f"👋 General/Greeting query handled directly")
            system_prompt = "You are Ekthaa AI, a friendly and smart assistant. You can have a casual chat, answer general questions, and tell jokes. Be concise and friendly."
            reply, model_used = call_ai(system_prompt, history, message, language=language)
            return jsonify({
                "reply": reply,
                "model_used": model_used,
                "query_type": "out_of_scope",
                "status": "ok",
            }), 200
        
        if query_type == "financial":
            # FINANCIAL MODE (Dues, Balances, Transactions)
            logger.info(f"💰 Financial query mode (confidence: {confidence:.2f})")
            
            # Fetch structured financial data from Appwrite
            financial_context = get_user_context(user_id)
            
            # Build system prompt with financial data embedded directly (single AI call)
            system_prompt = build_system_prompt(financial_context, language)
            
        elif query_type == "product_search":
            # PRODUCT SEARCH MODE
            logger.info(f"🏪 Product discovery mode (confidence: {confidence:.2f})")
            
            # Fetch matching businesses from RAG (semantic search)
            businesses = search_businesses(message, top_k=10)
            
            # Build context directly from RAG results (no intermediate AI calls)
            if businesses:
                context_lines = []
                for i, biz in enumerate(businesses, 1):
                    name = biz.get("name", "Unknown")
                    city = biz.get("city", "")
                    address = biz.get("address", "")
                    phone = biz.get("phone_number") or biz.get("phone", "")
                    category = biz.get("category", "")
                    line = f"{i}. {name}"
                    if city and city != "null":
                        line += f" — {city}"
                    if category:
                        line += f" ({category})"
                    if address:
                        line += f"\n   Address: {address}"
                    if phone:
                        line += f"\n   Phone: {phone}"
                    context_lines.append(line)
                structured_context = "\n".join(context_lines)
            else:
                structured_context = ""
            
            # Final Answer (single AI call)
            system_prompt = build_product_discovery_prompt(structured_context, message, language)
        
        else:
            # Fallback (should not happen with classify_query logic)
            system_prompt = build_final_assistant_prompt("No context available.", message, language)
        
        # ──────────────────────────────────────────────────────────────────
        # STEP 3: Call AI (Gemini → Groq fallback)
        # ──────────────────────────────────────────────────────────────────
        reply, model_used = call_ai(system_prompt, history, message, language=language)

        logger.info(f"💬 [{user_id}] [{language}] [{model_used}] [{query_type}] Q: {message[:60]} | A: {reply[:60]}")

        # Include business data in response for product searches
        response_data = {
            "reply": reply,
            "model_used": model_used,
            "query_type": query_type,
            "status": "ok",
        }
        
        if query_type == "product_search" and businesses:
            response_data["businesses"] = businesses

        return jsonify(response_data), 200

    except RuntimeError as e:
        # Both models failed
        return jsonify({"error": str(e), "status": "error"}), 503

    except Exception as e:
        logger.error(f"❌ Unexpected error in ai_chat: {e}", exc_info=True)
        return jsonify({"error": "Something went wrong. Please try again.", "status": "error"}), 500


@app.route("/api/ai/invalidate-cache", methods=["POST"])
def invalidate_user_cache():
    """
    Force-clear the cached financial context for a user.
    Call this after a payment or new transaction is recorded.

    Request body: { "user_id": "abc123" }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    invalidate_cache(user_id)
    return jsonify({"status": "ok", "message": f"Cache cleared for user {user_id}"}), 200


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    # Production default: debug=False
    debug = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    # ── Early Initialization ──────────────────────────────────────────
    logger.info("📦 Pre-initializing RAG business cache...")
    try:
        from services.rag_service import search_businesses
        # This will trigger the global cache load from local .pkl or Appwrite
        search_businesses("init", top_k=1)
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG on startup: {e}")

    logger.info(f"🚀 Starting Ekthaa AI Assistant on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
