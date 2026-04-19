import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
API_KEY = os.getenv("APPWRITE_API_KEY")
DB_ID = os.getenv("APPWRITE_DB_ID")
COL_ID = os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")

HEADERS = {
    "X-Appwrite-Project": PROJECT_ID,
    "X-Appwrite-Key": API_KEY,
    "Content-Type": "application/json",
}

def create_attribute(attr_type, key, required=False, size=255, array=False):
    url = f"{ENDPOINT}/databases/{DB_ID}/collections/{COL_ID}/attributes/{attr_type}"
    data = {
        "key": key,
        "required": required,
        "array": array
    }
    if attr_type == "string":
        data["size"] = size
        
    print(f"Creating {attr_type} attribute: {key}")
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code == 201:
        print(f"✅ Created {key}")
    elif resp.status_code == 409:
        print(f"✅ {key} already exists")
    else:
        print(f"❌ Failed to create {key}: {resp.text}")
    time.sleep(0.5)

def main():
    print(f"Setting up attributes for collection: {COL_ID}")
    
    # String attributes
    strings = [
        ("name", 255),
        ("business_type", 100),
        ("category", 100),
        ("subcategory", 100),
        ("address", 1024),
        ("city", 100),
        ("state", 100),
        ("pincode", 20),
        ("phone", 50),
        ("phone_number", 50),
        ("email", 255),
        ("website", 512),
        ("description", 4096)
    ]
    
    for key, size in strings:
        create_attribute("string", key, size=size)
        
    # Float attributes
    create_attribute("float", "latitude")
    create_attribute("float", "longitude")
    
    # Boolean attributes
    create_attribute("boolean", "is_active", required=False)
    
    # Array string attribute
    create_attribute("string", "keywords", size=50, array=True)
    
    print("Done setting up attributes. Waiting a few seconds for Appwrite indices to update...")
    time.sleep(3)

if __name__ == "__main__":
    main()
