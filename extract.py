import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import logging

# Configure API key
genai.configure(api_key="AIzaSyAu3pz-EwBic5FAb4yfD_S8uwtxlhHZx8w")

# Logging setup
logging.basicConfig(
    filename="extract.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_patient_data(file_path):
    """
    Extract patient data using Google Generative AI.
    Args:
        file_path (str): Path to the patient data file.
    Returns:
        dict: Extracted patient data.
    """
    try:
        logging.info("Uploading patient file...")
        patient_file = genai.upload_file(file_path)
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([patient_file, "Extract patient data as key-value JSON."])

        if result and result.candidates:
            raw_text = result.candidates[0].content.parts[0].text
            logging.info(f"Raw Patient Data: {raw_text}")
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                # Fallback parsing
                patient_data = {}
                for line in raw_text.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        patient_data[key.strip()] = value.strip()
                return patient_data
        else:
            logging.warning("No candidates found for patient data.")
            return {}
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        logging.error(f"Error extracting patient data: {e}")
        return {}

def extract_ingredients(file_path):
    """
    Extract ingredients using Google Generative AI.
    Args:
        file_path (str): Path to the ingredient image file.
    Returns:
        list: Extracted ingredients.
    """
    try:
        logging.info("Uploading ingredient image...")
        ingredient_file = genai.upload_file(file_path)
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([ingredient_file, "Extract ingredients as a list."])

        if result and result.candidates:
            raw_text = result.candidates[0].content.parts[0].text
            logging.info(f"Raw Ingredients Data: {raw_text}")
            ingredients = [
                item.strip() for item in raw_text.replace("\n", ",").split(",") if item.strip()
            ]
            return ingredients
        else:
            logging.warning("No candidates found for ingredients.")
            return []
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        logging.error(f"Error extracting ingredients: {e}")
        return []

def get_extracted_data(patient_file_path, ingredient_file_path):
    """
    Combines patient data and ingredient extraction.
    Args:
        patient_file_path (str): Path to the patient data file.
        ingredient_file_path (str): Path to the ingredient image file.
    Returns:
        dict: Combined extracted data.
    """
    return {
        "patient_data": extract_patient_data(patient_file_path),
        "product_ingredients": extract_ingredients(ingredient_file_path),
    }

if __name__ == "__main__":
    # Test with dummy file paths
    patient_file = "/path/to/patient_file.webp"
    ingredient_file = "/path/to/ingredient_image.png"

    data = get_extracted_data(patient_file, ingredient_file)
    print(json.dumps(data, indent=4))
