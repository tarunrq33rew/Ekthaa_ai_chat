"""
rag_service.py
──────────────
Handles Retrieval Augmented Generation (RAG) for business discovery.
Uses NVIDIA NV-Embed for high-quality semantic search.
"""

import os
import logging
import pickle
from typing import List, Dict, Optional
import numpy as np
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# --- Configuration ---
INDEX_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "businesses_index.pkl")

def _get_nvidia_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY", "")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not set.")
    # Use clean httpx client to avoid environment proxy conflicts
    http_client = httpx.Client(trust_env=False)
    return OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)

# --- Embedding Generation ---
def _generate_embedding(text: str) -> List[float]:
    """Generates an embedding using NVIDIA NV-Embed."""
    client = _get_nvidia_client()
    model = os.getenv("NVIDIA_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
    
    try:
        response = client.embeddings.create(
            input=[text],
            model=model,
            encoding_format="float",
            extra_body={"input_type": "query"}
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"❌ NVIDIA embedding failed: {e}")
        raise

# --- Search Logic ---
def search_businesses(query: str, top_k: int = 5) -> List[Dict]:
    """Search for businesses using semantic similarity."""
    try:
        # Load local index
        if not os.path.exists(INDEX_FILE):
            logger.warning(f"⚠️ Index file {INDEX_FILE} not found.")
            return []
            
        with open(INDEX_FILE, 'rb') as f:
            business_index = pickle.load(f)
            
        if not business_index:
            return []

        # Generate query embedding
        query_vec = np.array(_generate_embedding(query))
        
        # Calculate cosine similarity
        results = []
        for biz in business_index:
            if 'vector' not in biz:
                continue
            biz_vec = np.array(biz['vector'])
            
            # Dot product for normalized vectors
            similarity = np.dot(query_vec, biz_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(biz_vec))
            results.append((similarity, biz))
            
        # Sort by similarity
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top k
        return [res[1] for res in results[:top_k]]
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return []
