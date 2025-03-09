from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import extract
import dietician
import os
import logging
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("/home/swamyaranjan/Documents/diet-analysis/fbdbkey.json")  # Update this path
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Flask app
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_healthcare_data(uid):
    """Fetch healthcare data from Firestore and ensure it's JSON serializable."""
    try:
        logger.info(f"Fetching healthcare data for UID: {uid}")
        user_ref = db.collection("users").document(uid)
        user_data = user_ref.get()

        if user_data.exists:
            healthcare_data = user_data.to_dict()

            # Convert non-serializable types
            for key, value in healthcare_data.items():
                if isinstance(value, firestore.DocumentReference):
                    healthcare_data[key] = str(value.id)
                elif hasattr(value, "isoformat"):  # Handle datetime fields
                    healthcare_data[key] = value.isoformat()

            logger.info(f"Healthcare data fetched for UID {uid}: {healthcare_data}")
            return healthcare_data
        else:
            logger.warning(f"User document with UID {uid} does not exist.")
            return None
    except Exception as e:
        logger.error(f"Error fetching healthcare data for UID {uid}: {e}")
        return None

@app.route('/upload_healthcare_report', methods=['POST'])
def upload_healthcare_report():
    """
    Extracts text from a healthcare report (image/PDF) and updates Firestore.
    """
    try:
        uid = request.form.get('uid')
        report_file = request.files.get('report_file')

        if not uid or not report_file:
            return jsonify({"error": "Missing user_id or report file"}), 400

        logger.info(f"Extracting healthcare report for UID: {uid}")

        # Extract text from the healthcare report using Gemini API
        extracted_data = extract.extract_healthcare_data(report_file)

        if not extracted_data:
            return jsonify({"error": "Failed to extract healthcare data"}), 400

        logger.info(f"Extracted Healthcare Data: {extracted_data}")

        # Update Firestore
        user_ref = db.collection("users").document(uid)
        user_ref.set({"extracted_health_data": extracted_data}, merge=True)

        return jsonify({"message": "Healthcare report processed successfully", "data": extracted_data})

    except Exception as e:
        logger.error(f"Error processing healthcare report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_product():
    """
    Analyzes product ingredients based on user's healthcare data.
    Expects a UID and an ingredient file (image/PDF) in the request.
    """
    try:
        logger.info("Received request to analyze product.")

        uid = request.form.get('uid')
        ingredient_file = request.files.get('ingredient_file')

        logger.info(f"Request details - UID: {uid}, File: {ingredient_file.filename if ingredient_file else 'No file'}")

        if not uid or not ingredient_file:
            logger.error("Missing user_id or ingredient file in request.")
            return jsonify({"error": "Missing user_id or ingredient file"}), 400

        healthcare_data = get_healthcare_data(uid)
        if not healthcare_data:
            logger.error(f"No healthcare data found for UID {uid}.")
            return jsonify({"error": "Healthcare data not found for this user"}), 404

        logger.info("Extracting ingredients from the file...")
        ingredients = extract.extract_ingredients(ingredient_file)

        if not ingredients:
            logger.error("Failed to extract ingredients from the file.")
            return jsonify({"error": "Could not extract ingredients"}), 400

        logger.info(f"Ingredients extracted: {ingredients}")

        logger.info("Performing AI analysis...")
        analysis_result = dietician.analyze(healthcare_data, ingredients)
        logger.info(f"Analysis completed for UID {uid}.")

        # Save analysis results to Firestore
        upload_ref = db.collection("uploads").document()
        upload_ref.set({
            "user_id": uid,
            "ingredients": ingredients,
            "analysis": analysis_result,
            "uploaded_at": firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            "ingredients": ingredients,
            "analysis": analysis_result
        })

    except Exception as e:
        logger.error(f"Error in analyze_product: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    app.run(debug=True)