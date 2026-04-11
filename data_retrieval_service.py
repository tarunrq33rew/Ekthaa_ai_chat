import json
import logging
import os
from typing import List, Dict
from ai_service import call_groq

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
        response = call_groq(system_prompt, [], "Filter the data according to the rules.", language="en")
        
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
