import json
import logging
from data_retrieval_service import build_business_context

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_context_builder():
    print("\n--- Testing Context Builder ---")
    
    # Mock business data
    mock_data = [
        {
            "name": "Sharma Carpet Emporium",
            "category": "Home Decor",
            "subcategory": "Carpets & Rugs",
            "distance_km": 1.2,
            "city": "Chandigarh",
            "rating": 4.5,
            "keywords": "handmade, wool, silk carpets"
        },
        {
            "name": "Gupta Floorings",
            "category": "Construction",
            "subcategory": "Flooring",
            "distance_km": 3.5,
            "city": "Mohali",
            "rating": 4.2,
            "keywords": "carpet tiles, wooden flooring"
        }
    ]
    
    print(f"Input: {len(mock_data)} businesses")
    
    # Call context builder
    context = build_business_context(mock_data)
    
    print("\n--- Structured Context Output ---")
    print(context)
    print("---------------------------------")
    
    if "Sharma Carpet" in context and "Gupta Floorings" in context:
        print("\n✅ Verification SUCCESS: Both businesses present in structured context.")
    else:
        print("\n❌ Verification FAILED: Missing data in output.")

if __name__ == "__main__":
    test_context_builder()
