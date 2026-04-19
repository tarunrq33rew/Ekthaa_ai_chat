"""
ai_service.py
─────────────
Handles AI model calls via NVIDIA (Meta Llama 3.1 8B) for high-speed replies.
"""

import os
import logging
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

logger = logging.getLogger(__name__)

# ── NVIDIA setup ──────────────────────────────────────────────────────────────
_client = None

def _get_nvidia_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("NVIDIA_API_KEY", "")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is not set in environment variables.")
        # Use a clean httpx client to avoid "proxies" argument conflicts from env vars
        http_client = httpx.Client(trust_env=False)
        _client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
    return _client


# ── Chat call ─────────────────────────────────────────────────────────────────
def call_nvidia(system_prompt: str, history: List[Dict], message: str, language: str = "en") -> str:
    """
    Send a message to NVIDIA Llama 3.1 8B.
    """
    client = _get_nvidia_client()
    model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]

    for turn in history:
        role = turn.get("role", "user")
        if role == "model":
            role = "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})

    messages.append({"role": "user", "content": message})

    logger.info(f"🔗 Calling NVIDIA model: {model}")
    
    # As per user snippet parameters
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=False
    )

    return completion.choices[0].message.content.strip()


# ── Unified call (NVIDIA Primary) ─────────────────────────────────────────────
def call_ai(system_prompt: str, history: List[Dict], message: str, language: str = "en") -> Tuple[str, str]:
    """
    Sends a message to the AI (NVIDIA). Returns the reply and the model used.
    """
    try:
        logger.info(f"🤖 Calling NVIDIA (language={language})...")
        reply = call_nvidia(system_prompt, history, message, language=language)
        logger.info("✅ NVIDIA responded successfully")
        return reply, "nvidia"

    except Exception as e:
        logger.error(f"❌ NVIDIA call failed: {e}")
        raise RuntimeError(
            "The assistant is temporarily unavailable. Please try again in a moment."
        ) from e
