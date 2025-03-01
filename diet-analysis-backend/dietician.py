import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def expert_dietician_analysis(product_ingredients, patient_data):
    """
    Analyze product ingredients and patient healthcare data using Google Generative AI.
    Args:
        product_ingredients (list): List of ingredients.
        patient_data (dict): Patient health data.
    Returns:
        str: Analysis and recommendations.
    """
    try:
        prompt = (
            "You are an expert dietician. Analyze the following:\n\n"
            f"Ingredients:\n{', '.join(product_ingredients)}\n\n"
            f"Patient Data:\n{json.dumps(patient_data, indent=2)}\n\n"
            "Provide warnings if any ingredients conflict with health data and explain potential benefits "
            "or risks for each ingredient using emojis (😊 for benefits, 😢 for risks)."
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([prompt])

        return result.text if hasattr(result, "text") else "No response generated."
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        return f"Error in generating analysis: {e}"
