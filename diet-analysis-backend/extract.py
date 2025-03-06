import json
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Logging setup
logging.basicConfig(filename="extract.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_ingredients(file):
    """ Extract ingredients from image or text file using AI. """
    try:
        logging.info("Uploading ingredient image...")

        # Ensure filename is safe
        safe_filename = file.filename.replace(" ", "_")
        temp_path = os.path.join("/tmp", safe_filename)

        # Save uploaded file temporarily
        file.save(temp_path)  
        logging.info(f"File saved at: {temp_path}")

        # Upload file to Google's AI service
        ingredient_file = genai.upload_file(temp_path)
        logging.info(f"File uploaded successfully: {ingredient_file}")

        # Initialize the AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        logging.info("AI model initialized successfully.")

        # Generate content using the AI model
        prompt = "Extract ingredients as a list. Ensure the output is a comma-separated list of ingredients."
        logging.info(f"Sending prompt to AI model: {prompt}")
        result = model.generate_content([ingredient_file, prompt])

        # Log the AI model response
        if result and result.candidates:
            raw_text = result.candidates[0].content.parts[0].text
            logging.info(f"Raw Ingredients Data: {raw_text}")

            # Ensure clean ingredient extraction
            ingredients = [
                item.strip() for item in raw_text.replace("\n", ",").split(",") if item.strip()
            ]
            logging.info(f"Processed Ingredients: {ingredients}")

            return ingredients
        else:
            logging.warning("No ingredients found in the AI response.")
            return []
    except PermissionDenied as e:
        logging.error(f"Permission denied while accessing Google API: {e}")
        return []
    except GoogleAPICallError as e:
        logging.error(f"Google API call failed: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error extracting ingredients: {e}")
        return []
    finally:
        # Cleanup temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logging.info(f"Deleted temp file: {temp_path}")
