"""
rag_service.py
──────────────
Handles the fast in-memory Numpy vector search for business service discovery.
Ensures strict user data isolation by only querying `GLOBAL_BUSINESS` tagged vectors
for the general search function.
"""

import os
import json
import time
import logging
from typing import List, Dict

import numpy as np
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

logger = logging.getLogger(__name__)

# Global cache for businesses (safe to share across all users because it is global data)
_business_embeddings = {
    "timestamp": 0,
    "vectors": None,
    "biz_list": []
}

CACHE_TTL = 3600  # Reload every hour if needed

def _init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)

def _generate_embedding(text: str) -> List[float]:
    _init_gemini()
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]

def _fetch_all_business_embeddings() -> None:
    """Fetch all GLOBAL_BUSINESS embeddings from Appwrite into memory."""
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    db_id = os.getenv("APPWRITE_DB_ID")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    api_key = os.getenv("APPWRITE_API_KEY")

    if not all([endpoint, db_id, project_id, api_key]):
        logger.warning("❌ Missing Appwrite credentials. RAG service cannot initialize.")
        return

    headers = {
        "X-Appwrite-Project": project_id,
        "X-Appwrite-Key": api_key,
    }

    url = f"{endpoint}/databases/{db_id}/collections/embeddings/documents"
    
    allItems = []
    offset = 0
    # Strict filter: ONLY global businesses
    q_user = json.dumps({"method": "equal", "attribute": "user_id", "values": ["GLOBAL_BUSINESS"]})
    
    while True:
        q_limit = json.dumps({"method": "limit", "values": [100]})
        q_offset = json.dumps({"method": "offset", "values": [offset]})
        
        params = {"queries[]": [q_user, q_limit, q_offset]}
        
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            docs = r.json().get("documents", [])
            logger.debug(f"📥 Appwrite returned {len(docs)} documents at offset {offset}")
            if not docs:
                logger.info(f"📭 No more documents found at offset {offset} — stopping fetch")
                break
            
            for d in docs:
                emb_str = d.get("embedding")
                if not emb_str:
                    logger.debug(f"⚠️  No embedding field for {d.get('business_id')} - available fields: {list(d.keys())}")
                    continue
                    
                try:
                    import ast
                    vec = ast.literal_eval(emb_str)
                    if isinstance(vec, list):
                        vec_len = len(vec)
                        # Accept both Gemini (1536) and OpenAI (3072) embeddings
                        if vec_len not in [1536, 3072]:
                            logger.debug(f"⚠️  Unexpected embedding dimension: {vec_len} (expected 1536 or 3072)")
                            continue
                            
                        meta = {}
                        try:
                            if d.get("metadata"):
                                meta = json.loads(d.get("metadata"))
                        except:
                            pass
                            
                        allItems.append({
                            "id": d.get("business_id"),
                            "vector": vec,
                            "name": meta.get("name", ""),
                            "city": meta.get("city", "")
                        })
                    else:
                        logger.debug(f"⚠️  Embedding is not a list: {type(vec)}")
                except Exception as e:
                    logger.debug(f"⚠️  Parse error for {d.get('business_id')}: {str(e)[:80]}")


                        
            offset += len(docs)
            if len(docs) < 100:
                break
        except Exception as e:
            logger.error(f"❌ Failed to fetch business embeddings: {e}")
            break

    if allItems:
        global _business_embeddings
        _business_embeddings["biz_list"] = allItems
        
        # Pre-convert to numpy array and normalize for fast dot product (Cosine Sim)
        _business_embeddings["vectors"] = np.array([x["vector"] for x in allItems], dtype=np.float32)
        norms = np.linalg.norm(_business_embeddings["vectors"], axis=1, keepdims=True)
        norms[norms == 0] = 1
        _business_embeddings["vectors"] = _business_embeddings["vectors"] / norms
        
        _business_embeddings["timestamp"] = time.time()
        logger.info(f"✅ Loaded {len(allItems)} business embeddings into Numpy memory cache.")
    else:
        logger.warning(f"⚠️  No business embeddings found in Appwrite!")



def search_businesses(query: str, top_k: int = 5) -> List[Dict]:
    """
    Vector-based semantic search for businesses.
    
    Uses Gemini embeddings + Cosine similarity to find semantically relevant businesses.
    Pure vector search — no keyword filtering.
    
    Args:
        query: Search query text
        top_k: Number of results to return
    """
    global _business_embeddings
    
    # Lazy load if empty or expired
    if _business_embeddings["vectors"] is None or (time.time() - _business_embeddings["timestamp"] > CACHE_TTL):
        logger.info(f"📦 Loading business embeddings from Appwrite...")
        _fetch_all_business_embeddings()
        
    if _business_embeddings["vectors"] is None or len(_business_embeddings["biz_list"]) == 0:
        logger.warning(f"⚠️  No businesses loaded! _business_embeddings status: vectors={_business_embeddings['vectors'] is not None}, count={len(_business_embeddings['biz_list'])}")
        return []
        
    try:
        logger.info(f"🔍 Searching {len(_business_embeddings['biz_list'])} businesses for: '{query}'")
        q_vec = _generate_embedding(query)
        q_arr = np.array(q_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm == 0:
            logger.warning(f"⚠️  Query embedding is zero norm")
            return []
        q_arr = q_arr / q_norm
        
        # Fast dot product across all businesses (cosine similarity)
        similarities = np.dot(_business_embeddings["vectors"], q_arr)
        
        # Get top_k results by semantic score
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            biz = _business_embeddings["biz_list"][idx]
            results.append({
                "id": biz["id"],
                "name": biz["name"],
                "city": biz["city"],
                "score": round(score, 3),
            })
            logger.debug(f"  → {biz['name']} (score: {score:.3f})")
        
        logger.info(f"✅ Vector search returned {len(results)} results (top scores: {[r['score'] for r in results]})")
        
        # Enrich results with full business details from businesses collection
        enriched_results = []
        for result in results:
            full_biz = _fetch_business_details(result["id"])
            if full_biz:
                full_biz["score"] = result["score"]
                enriched_results.append(full_biz)
            else:
                enriched_results.append(result)
        
        return enriched_results
    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}", exc_info=True)
        return []

def _fetch_business_details(business_id: str) -> Dict:
    """Fetch full business details from businesses collection."""
    try:
        endpoint = os.getenv("APPWRITE_ENDPOINT")
        db_id = os.getenv("APPWRITE_DB_ID")
        project_id = os.getenv("APPWRITE_PROJECT_ID")
        api_key = os.getenv("APPWRITE_API_KEY")

        if not all([endpoint, db_id, project_id, api_key]):
            return None

        headers = {
            "X-Appwrite-Project": project_id,
            "X-Appwrite-Key": api_key,
        }

        url = f"{endpoint}/databases/{db_id}/collections/businesses/documents/{business_id}"
        r = requests.get(url, headers=headers, timeout=5)
        
        if r.status_code == 200:
            doc = r.json()
            return {
                "id": doc.get("$id", business_id),
                "name": doc.get("name", ""),
                "city": doc.get("city", ""),
                "phone": doc.get("phone", ""),
                "email": doc.get("email", ""),
                "address": doc.get("address", ""),
                "rating": doc.get("rating", 0),
                "reviews": doc.get("reviews_count", 0),
                "latitude": doc.get("latitude"),
                "longitude": doc.get("longitude"),
                "score": 0,  # Will be set by caller
            }
    except Exception as e:
        logger.debug(f"⚠️  Could not fetch full details for {business_id}: {e}")
    
    return None

def search_user_data(query: str, user_id: str, top_k: int = 5) -> List[Dict]:
    """
    Search personal embeddings strictly locked to the authenticated user.
    Does NOT use the global cache. Fetches directly from Appwrite on demand.
    """
    if not user_id:
        return []
        
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    db_id = os.getenv("APPWRITE_DB_ID")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    api_key = os.getenv("APPWRITE_API_KEY")

    headers = {
        "X-Appwrite-Project": project_id,
        "X-Appwrite-Key": api_key,
    }

    url = f"{endpoint}/databases/{db_id}/collections/embeddings/documents"
    
    # Strict filter: ONLY records matching this exact user_id
    q_user = json.dumps({"method": "equal", "attribute": "user_id", "values": [user_id]})
    q_limit = json.dumps({"method": "limit", "values": [100]})
    params = {"queries[]": [q_user, q_limit]}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        r.raise_for_status()
        docs = r.json().get("documents", [])
        if not docs:
            return []
            
        # Parse vectors
        user_items = []
        for d in docs:
            emb_str = d.get("embedding")
            if emb_str:
                try:
                    import ast
                    vec = ast.literal_eval(emb_str)
                    if isinstance(vec, list) and len(vec) == 768:
                        meta = {}
                        try:
                            if d.get("metadata"):
                                meta = json.loads(d.get("metadata"))
                        except:
                            pass
                        user_items.append({
                            "id": d.get("$id"),
                            "content": d.get("content", ""),
                            "metadata": meta,
                            "vector": vec
                        })
                except Exception:
                    pass
                    
        if not user_items:
            return []
            
        # Numpy similarity
        q_vec = _generate_embedding(query)
        q_arr = np.array(q_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm == 0:
            return []
        q_arr = q_arr / q_norm
        
        db_vectors = np.array([x["vector"] for x in user_items], dtype=np.float32)
        norms = np.linalg.norm(db_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        db_vectors = db_vectors / norms
        
        similarities = np.dot(db_vectors, q_arr)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.55: # Relevancy threshold
                item = user_items[idx]
                results.append({
                    "id": item["id"],
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "score": round(score, 3)
                })
                
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"Failed to search private user data: {e}")
        return []
