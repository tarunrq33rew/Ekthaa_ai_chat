import os
import requests
from dotenv import load_dotenv

load_dotenv()

def initialize_appwrite():
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    api_key = os.getenv("APPWRITE_API_KEY")
    db_id = os.getenv("APPWRITE_DB_ID")
    
    collections = [
        os.getenv("APPWRITE_USERS_COLLECTION", "users"),
        os.getenv("APPWRITE_TRANSACTIONS_COLLECTION", "transactions"),
        os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": project_id,
        "X-Appwrite-Key": api_key,
    }
    
    print(f"--- Initializing Appwrite Resources ---")
    
    # 1. Create Database
    print(f"Creating database: {db_id}...")
    db_url = f"{endpoint}/databases"
    db_data = {
        "databaseId": db_id,
        "name": db_id
    }
    
    resp = requests.post(db_url, headers=headers, json=db_data)
    if resp.status_code in [201, 409]: # 409 means already exists
        if resp.status_code == 201:
            print(f"✅ Database '{db_id}' created successfully.")
        else:
            print(f"ℹ️ Database '{db_id}' already exists.")
            
        # 2. Create Collections
        for coll_id in collections:
            print(f"Creating collection: {coll_id}...")
            coll_url = f"{endpoint}/databases/{db_id}/collections"
            coll_data = {
                "collectionId": coll_id,
                "name": coll_id,
                "permissions": [
                    "read(\"any\")",
                    "create(\"any\")",
                    "update(\"any\")",
                    "delete(\"any\")"
                ]
            }
            c_resp = requests.post(coll_url, headers=headers, json=coll_data)
            if c_resp.status_code == 201:
                print(f"✅ Collection '{coll_id}' created successfully.")
            elif c_resp.status_code == 409:
                print(f"ℹ️ Collection '{coll_id}' already exists.")
            else:
                print(f"❌ Failed to create collection '{coll_id}': {c_resp.text}")
    else:
        print(f"❌ Failed to create database: {resp.text}")

if __name__ == "__main__":
    initialize_appwrite()
