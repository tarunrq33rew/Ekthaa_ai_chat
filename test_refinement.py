import os
import logging
from data_retrieval_service import refine_business_results

logging.basicConfig(level=logging.INFO)

def test_refinement():
    print("Testing Business Result Refinement...")
    
    # Mock data - some relevant, some not
    mock_query = "Where can I buy a cake?"
    mock_businesses = [
        {
            "id": "1",
            "name": "Cake Palace",
            "city": "Chandigarh",
            "address": "Baker Street, specializing in birthday cakes and pastries."
        },
        {
            "id": "2",
            "name": "Arjun Furniture",
            "city": "Chandigarh",
            "address": "High quality sofas and tables."
        },
        {
            "id": "3",
            "name": "Sweet Delights Bakery",
            "city": "Mohali",
            "address": "Delicious desserts, donuts and custom cakes."
        },
        {
            "id": "4",
            "name": "Royal Steel Traders",
            "city": "Panchkula",
            "address": "Steel bars and construction material."
        }
    ]

    print(f"Original results: {[b['name'] for b in mock_businesses]}")
    
    refined = refine_business_results(mock_query, mock_businesses)
    
    print(f"Refined results: {[b['name'] for b in refined]}")
    
    # Assertions
    relevant_names = ["Cake Palace", "Sweet Delights Bakery"]
    irrelevant_names = ["Arjun Furniture", "Royal Steel Traders"]
    
    success = True
    for b in refined:
        if b['name'] in irrelevant_names:
            print(f"FAILED: Found irrelevant business {b['name']}")
            success = False
            
    for name in relevant_names:
        if not any(b['name'] == name for b in refined):
            print(f"FAILED: Missing relevant business {name}")
            success = False
            
    if success:
        print("✅ SUCCESS: Refinement logic is working as expected.")
    else:
        print("❌ FAILED: Refinement logic did not filter correctly.")

if __name__ == "__main__":
    test_refinement()
