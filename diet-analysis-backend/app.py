from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from dietician import expert_dietician_analysis  # Import the function

# Load environment variables
load_dotenv()

# Configure Flask app
app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Handles file uploads for patient data and product ingredients.
    Returns extracted data and expert dietician analysis.
    """
    try:
        patient_file = request.files['patient_file']
        ingredient_file = request.files['ingredient_file']

        patient_data = json.load(patient_file)
        product_ingredients = ingredient_file.read().decode().splitlines()

        analysis = expert_dietician_analysis(product_ingredients, patient_data)

        return jsonify({
            "extracted_data": {
                "ingredients": product_ingredients,
                "patient_data": patient_data
            },
            "dietician_analysis": analysis
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)  # Change debug=False in production!
