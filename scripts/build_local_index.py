import os
import csv
import json
import logging
import pickle
import time
from typing import List, Dict
import numpy as np
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load config
load_dotenv()
_client = None

def _get_nvidia_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("NVIDIA_API_KEY")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        if not api_key:
            raise ValueError("Missing NVIDIA_API_KEY in .env")
        
        # Explicitly ignore environment proxies to avoid Client.__init__ errors
        http_client = httpx.Client(trust_env=False)
        _client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
    return _client

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "data", "data.csv")
INDEX_FILE = os.path.join(BASE_DIR, "data", "businesses_index.pkl")

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using NVIDIA NV-Embed."""
    try:
        time.sleep(0.1)  # Small delay to prevent rate limit bursts
        client = _get_nvidia_client()
        model = os.getenv("NVIDIA_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
        response = client.embeddings.create(
            input=[text],
            model=model,
            encoding_format="float",
            extra_body={"input_type": "passage"}
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding failed for text: {text[:50]}... Error: {e}")
        return []

def build_content_string(row: Dict) -> str:
    """Construct a semantic string for embedding."""
    parts = []
    if row.get('name'): parts.append(row['name'])
    if row.get('category'): parts.append(row['category'])
    if row.get('subcategory'): parts.append(row['subcategory'])
    if row.get('business_type'): parts.append(row['business_type'])
    if row.get('description') and row['description'] != 'null': 
        parts.append(row['description'])
    
    # Extract keywords
    kw = row.get('keywords', '[]')
    try:
        if kw.startswith('['):
            kw_list = json.loads(kw)
            parts.append(", ".join(kw_list))
    except:
        pass
        
    return " - ".join(parts).strip()

def main():
    if not os.path.exists(CSV_FILE):
        logger.error(f"File not found: {CSV_FILE}")
        return

    # ALWAYS wipe old index for dimension changes
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
        logger.info(f"Deleted old index to prepare for NVIDIA re-indexing.")

    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    biz_list = []
    new_records = 0
    total = len(rows)
    
    logger.info(f"Processing {total} records from CSV using NVIDIA NV-Embed...")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def process_row(row):
        doc_id = row.get('$id')
        if not doc_id:
            return None
        
        content_str = build_content_string(row)
        if not content_str:
            return None

        vector = generate_embedding(content_str)
        if vector:
            return {
                "id": doc_id,
                "name": row.get('name', ''),
                "category": row.get('category', ''),
                "city": row.get('city', ''),
                "address": row.get('address', ''),
                "phone": row.get('phone_number', '') or row.get('phone', ''),
                "vector": vector,
                "content": content_str
            }
        return None

    # Use 3 workers to balance speed and NVIDIA rate limits (429 Avoidance)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_row, row) for row in rows]
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                biz_list.append(result)
                new_records += 1
            
            if (i + 1) % 50 == 0 or (i + 1) == total:
                with open(INDEX_FILE, 'wb') as f:
                    pickle.dump(biz_list, f)
                logger.info(f"Progress: {i+1}/{total} | Total Index Size: {len(biz_list)}")

    # Final save
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump(biz_list, f)
    
    logger.info(f"✅ Finished! Total records in index: {len(biz_list)} (New: {new_records})")

if __name__ == "__main__":
    main()
