import requests
import time
import subprocess
import os

print("Starting app in background...")
process = subprocess.Popen(["python", "app.py"], env=os.environ.copy())

try:
    print("Waiting 5 seconds for server to start...")
    time.sleep(5)
    
    print("Testing health endpoint...")
    resp = requests.get("http://localhost:5001/api/health")
    if resp.status_code == 200:
        print("✅ Health check passed!")
        print(resp.json())
    else:
        print(f"❌ Health check failed with status {resp.status_code}")
        
    print("Testing chat endpoint info...")
    resp2 = requests.get("http://localhost:5001/")
    if resp2.status_code == 200:
        print("✅ Index passed!")
        print(resp2.json())
    else:
        print(f"❌ Index failed with status {resp2.status_code}")
        
finally:
    print("Stopping app...")
    process.terminate()
    process.wait()
    print("Done")
