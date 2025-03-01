import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Logging setup
logging.basicConfig(
    filename="extract.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_patient_data(file):
    """
    Extract patient data using Google Generative AI.
    Args:
        file: Patient data file (image, text, or document).
    Returns:
        dict: Extracted patient data.
    """
    try:
        logging.info("Uploading patient file...")
        patient_file = genai.upload_file(file)
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([patient_file, "Extract patient data as key-value JSON."])

        if hasattr(result, "text"):
            raw_text = result.text
            logging.info(f"Raw Patient Data: {raw_text}")
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                return {"raw_text": raw_text}
        else:
            logging.warning("No response from API.")
            return {}
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        logging.error(f"Error extracting patient data: {e}")
        return {}

def extract_ingredients(file):
    """
    Extract ingredients using Google Generative AI.
    Args:
        file: Ingredient image or text file.
    Returns:
        list: Extracted ingredients.
    """
    try:
        logging.info("Uploading ingredient image...")
        ingredient_file = genai.upload_file(file)
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([ingredient_file, "Extract ingredients as a list."])

        if hasattr(result, "text"):
            raw_text = result.text
            logging.info(f"Raw Ingredients Data: {raw_text}")
            return [item.strip() for item in raw_text.split(",") if item.strip()]
        else:
            logging.warning("No response from API.")
            return []
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        logging.error(f"Error extracting ingredients: {e}")
        return []
