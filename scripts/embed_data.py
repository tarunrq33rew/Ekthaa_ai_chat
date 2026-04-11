"""
scripts/embed_data.py
─────────────────────
Fetches all businesses from Appwrite, generates Gemini text embeddings (768 dims),
and upserts them to the `embeddings` collection.
Sets strict data isolation tags (user_id="GLOBAL_BUSINESS", document_type="business").
"""

import os
import json
import time
import argparse
from typing import List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import google.generativeai as genai

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
API_KEY = os.getenv("APPWRITE_API_KEY")
DB_ID = os.getenv("APPWRITE_DB_ID")
BIZ_COL = os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")
USERS_COL = os.getenv("APPWRITE_USERS_COLLECTION", "customers")
EMB_COL = "embeddings"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([APPWRITE_ENDPOINT, PROJECT_ID, API_KEY, DB_ID, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables in .env")

genai.configure(api_key=GEMINI_API_KEY)

headers = {
    "X-Appwrite-Project": PROJECT_ID,
    "X-Appwrite-Key": API_KEY,
    "Content-Type": "application/json",
}

def appwrite_get(path: str, params=None) -> dict:
    url = f"{APPWRITE_ENDPOINT}{path}"
    r = session.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def appwrite_post(path: str, payload: dict) -> dict:
    url = f"{APPWRITE_ENDPOINT}{path}"
    r = session.post(url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        print(f"POST Error {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()

def appwrite_delete(path: str) -> None:
    url = f"{APPWRITE_ENDPOINT}{path}"
    r = session.delete(url, headers=headers)
    if r.status_code != 204:
        print(f"DELETE Error {r.status_code}: {r.text}")
    r.raise_for_status()

def get_all_businesses() -> List[dict]:
    all_biz = []
    offset = 0
    print("Fetching businesses...")
    while True:
        limit = 100
        q_limit = json.dumps({"method": "limit", "values": [limit]})
        q_offset = json.dumps({"method": "offset", "values": [offset]})
        data = appwrite_get(f"/databases/{DB_ID}/collections/{BIZ_COL}/documents", params={"queries[]": [q_limit, q_offset]})
        docs = data.get("documents", [])
        if not docs:
            break
        all_biz.extend(docs)
        offset += len(docs)
        if len(docs) < limit:
            break
    print(f"Found {len(all_biz)} businesses.")
    return all_biz

def get_all_customers() -> List[dict]:
    all_cust = []
    offset = 0
    print("Fetching customers...")
    while True:
        limit = 100
        q_limit = json.dumps({"method": "limit", "values": [limit]})
        q_offset = json.dumps({"method": "offset", "values": [offset]})
        data = appwrite_get(f"/databases/{DB_ID}/collections/{USERS_COL}/documents", params={"queries[]": [q_limit, q_offset]})
        docs = data.get("documents", [])
        if not docs:
            break
        all_cust.extend(docs)
        offset += len(docs)
        if len(docs) < limit:
            break
    print(f"Found {len(all_cust)} customers.")
    return all_cust

def wipe_old_embeddings():
    print("Wiping old embeddings...")
    while True:
        q_limit = json.dumps({"method": "limit", "values": [100]})
        data = appwrite_get(f"/databases/{DB_ID}/collections/{EMB_COL}/documents", params={"queries[]": [q_limit]})
        docs = data.get("documents", [])
        if not docs:
            break
        for d in docs:
            doc_id = d["$id"]
            appwrite_delete(f"/databases/{DB_ID}/collections/{EMB_COL}/documents/{doc_id}")
        print(f"Deleted {len(docs)} old embeddings")

def generate_embedding(text: str) -> List[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]

def _build_content_string(biz: dict) -> str:
    parts = []
    if biz.get("name"): parts.append(biz["name"])
    if biz.get("category") or biz.get("business_type"):
        parts.append(biz.get("category") or biz.get("business_type"))
    if biz.get("subcategory"): parts.append(biz["subcategory"])
    
    kw = biz.get("keywords")
    if kw:
        parts.append(", ".join(kw) if isinstance(kw, list) else str(kw))
        
    return " - ".join(parts).strip()

def embed_and_upload(businesses: List[dict]):
    print("Embedding and uploading businesses...")
    for idx, biz in enumerate(businesses):
        biz_id = biz["$id"]
        content_str = _build_content_string(biz)
        if not content_str:
            continue
            
        print(f"[{idx+1}/{len(businesses)}] Embedding Biz: {biz.get('name', 'Unknown')}")
        try:
            vector = generate_embedding(content_str)
            
            payload = {
                "documentId": biz_id,
                "data": {
                    "business_id": biz_id,
                    "content": content_str,
                    "embedding": str(vector),
                    "user_id": "GLOBAL_BUSINESS",
                    "document_type": "business",
                    "metadata": json.dumps({"name": biz.get("name", ""), "city": biz.get("city", "")})
                }
            }
            try:
                url = f"{APPWRITE_ENDPOINT}/databases/{DB_ID}/collections/{EMB_COL}/documents/{biz_id}"
                r = session.patch(url, headers=headers, json={"data": payload["data"]}, timeout=10)
                if r.status_code not in (200, 201):
                    raise ValueError()
            except:
                appwrite_post(f"/databases/{DB_ID}/collections/{EMB_COL}/documents", payload)
            
            time.sleep(0.1) # Gemini rate limit safety
        except Exception as e:
            print(f"Failed to embed {biz_id}: {e}")

def _build_customer_content_string(cust: dict) -> str:
    parts = []
    if cust.get("name"): parts.append(cust["name"])
    if cust.get("phone"): parts.append(f"Phone: {cust['phone']}")
    if cust.get("email"): parts.append(f"Email: {cust['email']}")
    if cust.get("city"): parts.append(f"Lives in {cust['city']}")
    if cust.get("state"): parts.append(cust["state"])
    return " - ".join(parts).strip()

def embed_and_upload_customers(customers: List[dict]):
    print("Embedding and uploading personal customer profiles...")
    for idx, cust in enumerate(customers):
        cust_id = cust["$id"]
        content_str = _build_customer_content_string(cust)
        if not content_str:
            continue
            
        print(f"[{idx+1}/{len(customers)}] Embedding Customer: {cust.get('name', 'Unknown')}")
        try:
            vector = generate_embedding(content_str)
            # Prefix the doc ID so it doesn't collide with businesses
            doc_id = f"cust_{cust_id}"
            
            payload = {
                "documentId": doc_id,
                "data": {
                    "business_id": "",
                    "content": content_str,
                    "embedding": str(vector),
                    "user_id": cust_id, # STRICT ISOLATION: Tagged to exactly one user
                    "document_type": "personal",
                    "metadata": json.dumps({"type": "profile", "name": cust.get("name", "")})
                }
            }
            try:
                url = f"{APPWRITE_ENDPOINT}/databases/{DB_ID}/collections/{EMB_COL}/documents/{doc_id}"
                r = session.patch(url, headers=headers, json={"data": payload["data"]}, timeout=10)
                if r.status_code not in (200, 201):
                    raise ValueError()
            except:
                appwrite_post(f"/databases/{DB_ID}/collections/{EMB_COL}/documents", payload)
            
            time.sleep(0.1)
        except Exception as e:
            print(f"Failed to embed customer {cust_id}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="Wipe all existing embeddings first")
    args = parser.parse_args()
    
    if args.wipe:
        wipe_old_embeddings()
        
    bizs = get_all_businesses()
    embed_and_upload(bizs)
    
    customers = get_all_customers()
    embed_and_upload_customers(customers)
    
    print("Done!")
