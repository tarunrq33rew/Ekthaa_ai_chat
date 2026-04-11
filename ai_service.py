"""
ai_service.py
─────────────
Handles AI model calls via Groq (Llama 3.3 70B).

Model : Groq Llama 3.3 70B (primary)
"""

import os
import logging
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # Ensure .env is loaded even when module is imported standalone

logger = logging.getLogger(__name__)

# ── Groq setup ────────────────────────────────────────────────────────────────
def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")
    return Groq(api_key=api_key)


# ── Groq call ─────────────────────────────────────────────────────────────────
def call_groq(system_prompt: str, history: List[Dict], message: str, language: str = "en") -> str:
    """
    Send a message to Groq.
    For languages Groq handles confidently (en, hi), it enforces the language.
    For regional languages it can't do well (te, ta, mr, bn), it responds in
    English so the user gets a clear, correct answer instead of broken transliteration.
    """
    client = _get_groq_client()

    # Languages Groq handles well enough to enforce
    GROQ_CONFIDENT_LANGUAGES = {"en", "hi"}

    if language in GROQ_CONFIDENT_LANGUAGES:
        lang_note = ""  # trust the system_prompt language instruction
    else:
        # Override: don't force broken regional language — respond in clear English
        lang_note = (
            "\n\nNOTE: The user's preferred language is not one you handle fluently. "
            "Please respond in clear, simple English instead of attempting broken "
            "transliteration. Keep the tone warm and friendly."
        )

    # Build messages array (OpenAI-compatible format)
    messages = [{"role": "system", "content": system_prompt + lang_note}]

    for turn in history:
        role = turn.get("role", "user")
        if role == "model":
            role = "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Unified call (Groq only) ──────────────────────────────────────────────────
def call_ai(system_prompt: str, history: List[Dict], message: str, language: str = "en") -> Tuple[str, str]:
    """
    Sends a message to the AI (Groq). Returns the reply and the model used.
    """
    try:
        logger.info(f"🤖 Calling Groq (language={language})...")
        reply = call_groq(system_prompt, history, message, language=language)
        logger.info("✅ Groq responded successfully")
        return reply, "groq"

    except Exception as e:
        logger.error(f"❌ Groq call failed: {e}")
        raise RuntimeError(
            "The AI assistant is temporarily unavailable. Please try again in a moment."
        ) from e
