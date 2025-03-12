import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import os
from dotenv import load_dotenv
from google.cloud import firestore
import logging
import hashlib
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not set. Cannot initialize Gemini API.")

genai.configure(api_key=API_KEY)

# Configure logging
logger = logging.getLogger(__name__)

# Simple in-memory cache for API responses (reduces API costs during testing)
# In production, consider using Redis or another distributed cache
_response_cache = {}

def serialize_firestore_data(data):
    """Convert Firestore data to JSON serializable format."""
    if not data:
        return {}
        
    processed_data = {}
    for key, value in data.items():
        if hasattr(value, '__class__') and (
            value.__class__.__name__ == 'ServerTimestamp' or 
            isinstance(value, firestore.SERVER_TIMESTAMP.__class__)
        ):
            processed_data[key] = str(time.time())
        elif isinstance(value, firestore.DocumentReference):
            processed_data[key] = str(value.path)
        elif isinstance(value, dict):
            processed_data[key] = serialize_firestore_data(value)
        else:
            processed_data[key] = value
    return processed_data

def create_cache_key(healthcare_data, ingredients):
    """Create a cache key based on input data."""
    combined = json.dumps({
        "health": healthcare_data,
        "ingredients": ingredients
    }, sort_keys=True)
    return hashlib.md5(combined.encode()).hexdigest()

def analyze(healthcare_data, ingredients, use_cache=True, cache_ttl=3600):
    """Analyze product safety based on user's healthcare data and ingredients.
    
    Args:
        healthcare_data (dict): User's healthcare data
        ingredients (list): List of ingredients to analyze
        use_cache (bool): Whether to use caching (default: True)
        cache_ttl (int): Cache time-to-live in seconds (default: 1 hour)
        
    Returns:
        str: Analysis results as formatted text
    """
    # Create cache key if caching is enabled
    cache_key = create_cache_key(healthcare_data, ingredients) if use_cache else None
    
    # Try to get from cache first
    if use_cache and cache_key in _response_cache:
        cache_entry = _response_cache[cache_key]
        if time.time() - cache_entry["timestamp"] < cache_ttl:
            logger.info(f"Using cached analysis result for key {cache_key[:8]}...")
            return cache_entry["result"]
    
    try:
        # Convert Firestore timestamps and references to JSON-serializable format
        serialized_data = serialize_firestore_data(healthcare_data)
        
        # Log input data for debugging (redact in production)
        logger.info(f"Processing analysis for {len(ingredients)} ingredients")
        
        # Create prompt for the AI model
        prompt = (
            "You are an expert dietician. Analyze the following ingredients based on the patient's health data. "
            "Provide a structured response with the following sections:\n\n"
            "1. **Summary:** A brief overview of the analysis.\n"
            "2. **Ingredient Analysis:** For each ingredient, provide:\n"
            "   - **Name:** The ingredient name.\n"
            "   - **Effect:** Whether it is safe or unsafe for the patient.\n"
            "   - **Reason:** A concise explanation of the effect.\n"
            "3. **Warnings:** Any specific warnings or risks based on the patient's health conditions.\n"
            "4. **Recommendations:** Actionable advice for the patient, including portion control, substitutions, or dietary modifications.\n\n"
            "**Patient Data:**\n"
            f"{json.dumps(serialized_data, indent=2)}\n\n"
            "**Ingredients:**\n"
            f"{', '.join(ingredients)}\n\n"
            "Ensure the response is concise, accurate, and tailored to the patient's health conditions."
        )

        # Select the appropriate model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Implement exponential backoff for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt+1}/{max_retries})...")
                result = model.generate_content([prompt])
                
                # Ensure AI output exists before accessing parts
                if result and hasattr(result, 'candidates') and result.candidates and result.candidates[0].content and result.candidates[0].content.parts:
                    response_text = result.candidates[0].content.parts[0].text
                    
                    # Cache the result if caching is enabled
                    if use_cache and cache_key:
                        _response_cache[cache_key] = {
                            "result": response_text,
                            "timestamp": time.time()
                        }
                        
                    return response_text
                else:
                    logger.warning("Received empty response from Gemini API")
                    
            except (PermissionDenied, GoogleAPICallError) as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff with jitter
                    logger.warning(f"API error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error after {max_retries} attempts: {e}")
                    raise
        
        # Fallback response if all retries fail
        return "Unable to generate analysis after multiple attempts. Please try again later."
    
    except Exception as e:
        logger.exception(f"Unexpected error in analysis: {e}")
        return f"Error in generating analysis: {str(e)}"
