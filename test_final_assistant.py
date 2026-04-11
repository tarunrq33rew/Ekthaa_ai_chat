import logging
from system_prompt import build_final_assistant_prompt
from ai_service import call_groq

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_final_assistant():
    print("\n--- Testing Final Assistant Persona ---")
    
    # 1. Test Case: Success
    success_context = "Sharma Carpet Emporium is a Home Decor shop in Chandigarh. It has wool carpets for ₹5000."
    query = "Price of wool carpets at Sharma Carpet?"
    
    print(f"\n[Case 1] Query: {query}")
    prompt = build_final_assistant_prompt(success_context, query, "en")
    response = call_groq(prompt, [], "Answer the question.", language="en")
    print(f"Response: {response.strip()}")
    
    # 2. Test Case: No Data
    fail_context = "Gupta Floorings offers wooden floor tiles. We do NOT sell carpets."
    query = "Where can I buy a space shuttle?"
    
    print(f"\n[Case 2] Query: {query}")
    prompt = build_final_assistant_prompt(fail_context, query, "en")
    response = call_groq(prompt, [], "Answer the question.", language="en")
    print(f"Response: {response.strip()}")
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_final_assistant()
