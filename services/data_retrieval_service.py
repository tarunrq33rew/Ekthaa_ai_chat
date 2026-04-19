import json
import logging
import os
from typing import List, Dict
from services.ai_service import call_ai

logger = logging.getLogger(__name__)

def refine_business_results(user_query: str, businesses: List[Dict]) -> List[Dict]:
    """
    Refines a list of businesses to only include those relevant to the user query.
    Uses AI to perform the semantic filtering.
    """
    if not businesses:
        return []

    # Map input to the format expected by the prompt
    raw_data = json.dumps(businesses, indent=2)
    
    # Prompt template provided by the user
    system_prompt = f"""You are a data retrieval system.

Your task is to identify the user’s intent and extract only the most relevant information from the provided business dataset.

Strict rules:

Focus only on the user’s query
Retrieve only relevant records (dues, transactions, shops, etc.)
Ignore all unrelated data
Do not generate answers
Do not summarize or explain
Do not assume any missing information

User Query:
{user_query}

Available Data:
{raw_data}

Output:
Return only the filtered and relevant data required to answer the query as a valid JSON list of objects.
"""

    try:
        logger.info(f"Refining {len(businesses)} businesses for query: {user_query}")
        
        # We call the model with the system prompt and a simple trigger message
        # history is empty as this is a stateless refinement step
        response, _ = call_ai(system_prompt, [], "Filter the data according to the rules.", language="en")
        
        # Extract JSON list from the response
        json_str = response.strip()
        
        # Handle potential markdown code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        # If the string is empty or just "[", handle it
        if not json_str.startswith("[") and "[" in json_str:
             json_str = json_str[json_str.find("["):]
        if not json_str.endswith("]") and "]" in json_str:
             json_str = json_str[:json_str.rfind("]")+1]

        refined_data = json.loads(json_str)
        
        if not isinstance(refined_data, list):
            logger.warning("AI did not return a list for refinement. Returning original data.")
            return businesses
            
        logger.info(f"Refinement complete. Retained {len(refined_data)}/{len(businesses)} results.")
        return refined_data

    except Exception as e:
        logger.error(f"❌ Error refining business results: {e}")
        # Fail gracefully by returning the original list
        return businesses

def build_semantic_context(raw_data: any) -> str:
    """
    Task 2: Context Building (The Semantic Layer)
    
    Converts raw JSON records (businesses, dues, transactions) into clean, 
    factual sentences for the final AI step.
    """
    # Special handling for city-wise spending in context
    if isinstance(raw_data, dict):
        city_curr = raw_data.get("city_spend_current", {})
        if city_curr:
            city_summaries = [f"This month's spending in {city.capitalize()} is ₹{amt}." for city, amt in city_curr.items()]
            raw_data["city_spend_summary"] = " ".join(city_summaries)

    prompt = f"""You are a context builder.

Your task is to convert the retrieved business or financial data into a clean, simple, and structured format.

Strict rules:
1. Convert raw data (JSON/List/Dict) into short, clear sentences.
2. Keep the information factual and structured.
3. Do not add or assume any extra details.
4. Do not include irrelevant data.
5. Do not answer the user’s question yet.

Retrieved Data:
{raw_data}

Output (Return only the structured context sentences):
"""
    
    # Generic context building using NVIDIA for speed and precision
    try:
        structured_context, _ = call_ai(prompt, [], "Convert data to sentences.")
        return structured_context.strip()
    except Exception as e:
        logger.error(f"Error building semantic context: {e}")
        # Fallback: simple string conversion
        return f"Retrieved Data: {str(raw_data)}"
