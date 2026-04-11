"""
query_classifier.py
───────────────────
Classifies user queries into categories with query normalization for better RAG matching.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# Keywords that indicate product/service search queries
PRODUCT_SEARCH_KEYWORDS = {
    # English
    "where", "find", "nearest", "closest", "shop", "store", "buy", "purchase", 
    "sell", "rent", "hire", "service", "provider", "available", "have", "stock",
    "location", "address", "contact", "phone", "nearby",
    
    # Hindi/Hinglish
    "kahan", "mile", "dikhao", "kaunsi", "konsi", "dukan", "dukaan", "khareed",
    "kharidna", "kirayaa", "sewaa", "qareeb", "nazdik", "adress", "pata", "number",
    
    # Hindi (transliterated)
    "kaha", "milega", "paas", "lagbhag", "uphar", "ghar", "ghre",
}

# Keywords related to financial transactions/dues
FINANCIAL_KEYWORDS = {
    # English
    "owe", "due", "payment", "bill", "invoice", "outstanding", "balance", "credit",
    "spending", "spent", "paid", "transaction", "history", "wallet", "total", "amount",
    
    # Hindi/Hinglish  
    "baaki", "baakya", "paisa", "paise", "payment", "bill", "kharch", "spend",
    "kharcha", "dena", "lena", "udhar", "kaaj", "lagaan",
}

# Common product categories (helps boost product_search classification)
PRODUCT_CATEGORIES = {
    # Building materials
    "cement", "brick", "steel", "iron", "pipe", "wire", "wood", "concrete", "sand",
    "gravel", "marble", "granite", "tile", "paint", "putty", "adhesive", "glue",
    
    # Furniture & Home
    "carpet", "sofa", "couch", "bed", "table", "chair", "lamp", "curtain", "door",
    "window", "mattress", "pillow", "blanket", "sheets", "cushion", "rug",
    
    # Clothing & Fashion
    "clothes", "dress", "shirt", "pant", "trouser", "skirt", "saree", "suit",
    "jacket", "coat", "shoes", "boot", "slipper", "sock", "hat", "cap", "scarf",
    
    # Electronics & Appliances
    "mobile", "phone", "laptop", "computer", "tv", "television", "refrigerator",
    "fridge", "washing", "machine", "dishwasher", "microwave", "oven", "blender",
    "fan", "cooler", "heater", "ac", "air", "conditioner", "charger", "cable",
    
    # Beauty & Cosmetics
    "beauty", "cosmetics", "makeup", "lipstick", "nail", "polish", "perfume",
    "deodorant", "shampoo", "conditioner", "soap", "lotion", "cream",
    
    # Food & Groceries
    "food", "grocery", "vegetable", "fruit", "rice", "wheat", "flour", "oil",
    "milk", "bread", "butter", "cheese", "egg", "meat", "fish", "chicken",
    "restaurant", "cafe", "bakery", "sweet", "snack",
    
    # Services
    "plumber", "electrician", "mechanic", "carpenter", "painter", "cleaner",
    "repair", "service", "maintenance", "installation", "delivery",
    
    # Automotive
    "bike", "motorcycle", "scooter", "car", "vehicle", "petrol", "diesel",
    "fuel", "gas", "oil", "parts", "tyre", "battery",
    
    # Medical & Health
    "doctor", "hospital", "clinic", "pharmacy", "medicine", "medical",
    "dental", "dentist", "health", "wellness", "vitamin", "supplement",
    
    # Personal Care
    "salon", "hair", "spa", "massage", "barber", "grooming",
    
    # Electronics & IT Services
    "printing", "xerox", "computer", "it", "software", "hardware",
}



def normalize_query(query: str) -> str:
    """
    Clean and normalize query for better RAG semantic search.
    
    Removes:
      - Location filler words (near, nearby, close, paas, lagbhag, etc.)
      - Common politeness fillers (please, can you, i want, i need, etc.)
      - Extra whitespace
    
    Returns cleaned query string for better semantic matching.
    """
    query_lower = query.lower().strip()
    
    # Remove location indicators (DB search already has coordinates)
    location_patterns = [
        r"\b(near|nearby|close|around|paas|lagbhag|qareeb|nazdik|karib)\s+\w+",
        r"\b(mera|mere|mere paas|mere taraf)\b",  # possessive filler
    ]
    for pattern in location_patterns:
        query_lower = re.sub(pattern, "", query_lower, flags=re.IGNORECASE)
    
    # Remove polite filler words
    filler_words = [
        "please", "i want", "i need", "can you", "could you", "do you",
        "can i", "do i", "would you", "thanks", "thankyou", "thank you",
        "aapko", "mujhe", "mera", "kya", "kya aap", "krapya",
    ]
    for word in filler_words:
        query_lower = re.sub(rf"\b{re.escape(word)}\b", "", query_lower, flags=re.IGNORECASE)
    
    # Clean extra spaces
    query_lower = re.sub(r"\s+", " ", query_lower).strip()
    
    # If everything was filler, return original (fallback)
    return query_lower if query_lower else query.lower().strip()


def classify_query(message: str, language: str = "en") -> Tuple[str, float]:
    """
    Classify a user query into a category.
    
    Args:
        message: User's message text
        language: Language code ('en', 'hi', etc.)
    
    Returns:
        (category, confidence)
        category: "product_search" (in scope) or "out_of_scope" (not product/service related)
        confidence: 0.0-1.0 score
    """
    msg_lower = normalize_query(message)  # Normalize for better matching
    
    # Count keyword matches for product search
    product_score = sum(1 for kw in PRODUCT_SEARCH_KEYWORDS if kw in msg_lower)
    category_score = sum(1 for cat in PRODUCT_CATEGORIES if cat in msg_lower)
    
    # Boost product_search if product category is mentioned
    product_score += category_score * 2
    
    # Determine if this is a product search query
    if product_score > 0:
        confidence = min(product_score / 10.0, 1.0)  # Cap at 1.0
        logger.info(f"🏪 Query classified as PRODUCT_SEARCH (confidence: {confidence:.2f}): {message[:60]}")
        return "product_search", confidence
    
    else:
        logger.info(f"❌ Query classified as OUT_OF_SCOPE: {message[:60]}")
        return "out_of_scope", 0.0

# Quick test examples
if __name__ == "__main__":
    test_queries = [
        "Where can I buy a carpet?",
        "Where can I find a good plumber?",
        "Can you please find me a plumber nearby?",
        "What is my total due?",
        "How much have I spent this month?",
        "Tell me about yourself",
        "kahan me carpet mil sakta hai?",
        "Mera total baaki kitna hai?",
    ]
    
    for q in test_queries:
        cat, conf = classify_query(q)
        normalized = normalize_query(q)
        print(f"{q:45} → {cat:15} (conf: {conf:.2f}) | normalized: '{normalized}'")
