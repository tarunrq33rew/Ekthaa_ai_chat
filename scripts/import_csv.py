import os
import csv
import json
import logging
import time
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load config
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
API_KEY = os.getenv("APPWRITE_API_KEY")
DB_ID = os.getenv("APPWRITE_DB_ID")
COL_ID = os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")

if not all([ENDPOINT, PROJECT_ID, API_KEY, DB_ID]):
    raise ValueError("Missing Appwrite configuration in .env")

HEADERS = {
    "X-Appwrite-Project": PROJECT_ID,
    "X-Appwrite-Key": API_KEY,
    "Content-Type": "application/json",
}

def sanitize_data(row):
    """Clean and format CSV row for Appwrite."""
    # Convert lat/lng
    try:
        row['latitude'] = float(row['latitude']) if row.get('latitude') else 0.0
        row['longitude'] = float(row['longitude']) if row.get('longitude') else 0.0
    except:
        row['latitude'] = 0.0
        row['longitude'] = 0.0

    # Parse keywords
    kw = row.get('keywords', '[]')
    try:
        if kw and isinstance(kw, str) and kw.startswith('['):
            row['keywords'] = json.loads(kw)
        else:
            row['keywords'] = []
    except:
        row['keywords'] = []

    # Filter out internal/empty fields that Appwrite shouldn't receive or can't handle
    valid_fields = [
        'name', 'business_type', 'category', 'subcategory', 'address', 'city', 
        'state', 'pincode', 'phone', 'phone_number', 'email', 'website', 
        'latitude', 'longitude', 'keywords', 'is_active', 'description'
    ]
    
    clean_row = {}
    for f in valid_fields:
        if f in row and row[f] not in (None, 'null', ''):
            clean_row[f] = row[f]
    
    # Defaults
    if 'is_active' in clean_row:
        clean_row['is_active'] = str(clean_row['is_active']).lower() == 'true'
    else:
        clean_row['is_active'] = True

    return clean_row

def upload_row(doc_id, data):
    """Upsert a single business document."""
    url = f"{ENDPOINT}/databases/{DB_ID}/collections/{COL_ID}/documents"
    
    # Try Update first if ID exists
    update_url = f"{url}/{doc_id}"
    try:
        r = requests.patch(update_url, headers=HEADERS, json={"data": data}, timeout=10)
        if r.status_code == 200:
            return "updated"
    except:
        pass

    # Otherwise Create
    payload = {
        "documentId": doc_id,
        "data": data
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    if r.status_code in (200, 201):
        return "created"
    else:
        logger.error(f"Failed to upload {doc_id}: {r.text}")
        return "failed"

def main():
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'data.csv')
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return

    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    total = len(rows)
    logger.info(f"🚀 Starting import of {total} records...")
    
    counts = {"created": 0, "updated": 0, "failed": 0}
    
    for i, row in enumerate(rows):
        doc_id = row.get('$id')
        if not doc_id:
            logger.warning(f"Row {i} has no $id, skipping.")
            continue
            
        clean_data = sanitize_data(row)
        result = upload_row(doc_id, clean_data)
        counts[result] += 1
        
        if (i + 1) % 10 == 0 or (i + 1) == total:
            logger.info(f"Progress: {i+1}/{total} | Created: {counts['created']} | Updated: {counts['updated']} | Failed: {counts['failed']}")
        
        # Rate limit safety
        time.sleep(0.05)

    logger.info("✅ Import complete!")
    print(json.dumps(counts, indent=2))

if __name__ == "__main__":
    main()
