# let's get started
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import extract
import dietician
import os
import logging

# Initialize Firebase
cred = credentials.Certificate("/home/swamyaranjan/Documents/diet-analysis-backend/ServiceAccountKey1.json")  # Update this path
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Flask app
app = Flask(__name__)
CORS(app)

## Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", mode="w"),  # Log to a file (overwrite if exists)
        logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

def get_healthcare_data(uid):
    """
    Fetch healthcare data from Firestore.
    Converts Firestore DocumentReference fields to plain data.
    """
    try:
        logger.info(f"Fetching healthcare data for UID: {uid}")
        user_ref = db.collection("user_info").document(uid)
        user_data = user_ref.get()

        if user_data.exists:
            healthcare_data = user_data.to_dict()

            # Convert Firestore DocumentReference to string
            for key, value in healthcare_data.items():
                if isinstance(value, firestore.DocumentReference):
                    healthcare_data[key] = str(value.id)

            logger.info(f"Healthcare data fetched for UID {uid}: {healthcare_data}")
            return healthcare_data
        else:
            logger.warning(f"User document with UID {uid} does not exist.")
            return None
    except Exception as e:
        logger.error(f"Error fetching healthcare data for UID {uid}: {e}")
        return None


@app.route('/analyze', methods=['POST'])
def analyze_product():
    """
    Analyze product ingredients based on user's healthcare data.
    Expects a UID and an ingredient file (image/PDF) in the request.
    """
    try:
        logger.info("Received request to analyze product.")

        # Get user ID and ingredient file from the request
        uid = request.form.get('uid')
        ingredient_file = request.files.get('ingredient_file')

        # Log request details
        logger.info(f"Request details - UID: {uid}, File: {ingredient_file.filename if ingredient_file else 'No file'}")

        # Validate input
        if not uid or not ingredient_file:
            logger.error("Missing user_id or ingredient file in request.")
            return jsonify({"error": "Missing user_id or ingredient file"}), 400

        # Fetch healthcare data
        logger.info(f"Fetching healthcare data for UID: {uid}")
        healthcare_data = get_healthcare_data(uid)
        if not healthcare_data:
            logger.error(f"No healthcare data found for UID {uid}.")
            return jsonify({"error": "Healthcare data not found for this user"}), 404

        # Extract ingredients from the file
        logger.info("Extracting ingredients from the file...")
        ingredients = extract.extract_ingredients(ingredient_file)
        if not ingredients:
            logger.error("Failed to extract ingredients from the file.")
            return jsonify({"error": "Could not extract ingredients"}), 400
        logger.info(f"Ingredients extracted: {ingredients}")

        # Perform AI analysis
        logger.info("Performing AI analysis...")
        analysis_result = dietician.analyze(healthcare_data, ingredients)
        logger.info(f"Analysis completed for UID {uid}.")

        # Return the result
        logger.info("Returning analysis result to the client.")
        return jsonify({
            "ingredients": ingredients,
            "analysis": analysis_result
        })

    except Exception as e:
        logger.error(f"Error in analyze_product: {e}", exc_info=True)  # Include traceback in logs
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    app.run(debug=True)
