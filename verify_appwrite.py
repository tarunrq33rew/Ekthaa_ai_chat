import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_appwrite():
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    api_key = os.getenv("APPWRITE_API_KEY")
    db_id = os.getenv("APPWRITE_DB_ID")
    
    print(f"--- Testing Appwrite Connection ---")
    print(f"Endpoint: {endpoint}")
    print(f"Project ID: {project_id}")
    print(f"Target DB: {db_id}")
    
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": project_id,
        "X-Appwrite-Key": api_key,
    }
    
    # 1. List Databases
    try:
        url_dbs = f"{endpoint}/databases"
        r_dbs = requests.get(url_dbs, headers=headers)
        if r_dbs.status_code == 200:
            print("✅ Successfully connected to Project!")
            dbs = r_dbs.json().get("databases", [])
            print(f"Found {len(dbs)} databases:")
            for db in dbs:
                print(f" - {db.get('name')} (ID: {db.get('$id')})")
        else:
            print(f"❌ Failed to reach project. Status: {r_dbs.status_code}")
            print(f"Response: {r_dbs.text}")
            return

        # 2. Check specific Database
        url_db = f"{endpoint}/databases/{db_id}"
        r_db = requests.get(url_db, headers=headers)
        if r_db.status_code == 200:
            print(f"✅ Found targeted database: {db_id}")
            
            # 3. List Collections
            url_colls = f"{url_db}/collections"
            r_colls = requests.get(url_colls, headers=headers)
            if r_colls.status_code == 200:
                colls = r_colls.json().get("collections", [])
                print(f"Found {len(colls)} collections in {db_id}:")
                for c in colls:
                    print(f" - {c.get('name')} (ID: {c.get('$id')})")
            else:
                print(f"❌ Failed to list collections in {db_id}.")
        else:
            print(f"❌ Targeted database '{db_id}' not found.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_appwrite()
