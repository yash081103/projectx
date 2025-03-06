import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import os
from dotenv import load_dotenv
from google.cloud import firestore

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def serialize_firestore_data(data):
    """ Convert Firestore data to JSON serializable format. """
    for key, value in data.items():
        if isinstance(value, firestore.SERVER_TIMESTAMP.__class__):
            data[key] = value.isoformat()  # Convert Firestore timestamps to ISO format
        elif isinstance(value, firestore.DocumentReference):
            data[key] = str(value.id)  # Convert Firestore DocumentReference to string
    return data

def analyze(healthcare_data, ingredients):
    """ Analyze product safety based on user's healthcare data and ingredients. """
    try:
        # ✅ Convert Firestore timestamps and references to JSON-serializable format
        healthcare_data = serialize_firestore_data(healthcare_data)

        prompt = (
            "You are an expert dietician. Analyze the following:\n\n"
            f"Ingredients:\n{', '.join(ingredients)}\n\n"
            f"Patient Data:\n{json.dumps(healthcare_data, indent=2)}\n\n"
            "Provide warnings if any ingredients conflict with health data and explain potential benefits "
            "or risks for each ingredient using emojis (😊 for benefits, 😢 for risks)."
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([prompt])

        # ✅ Ensure AI output exists before accessing parts
        if result and result.candidates and result.candidates[0].content and result.candidates[0].content.parts:
            return result.candidates[0].content.parts[0].text
        else:
            return "No response generated."
    
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        return f"Error in generating analysis: {e}"
