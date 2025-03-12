from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import extract
import dietician
import os
import logging
from functools import wraps
from dotenv import load_dotenv
import requests
import time
from io import BytesIO
import sys  # For log flushing

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
PRIVATE_KEY_PATH = os.getenv("FIREBASE_PRIVATE_KEY_PATH")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", mode="a"),
        logging.StreamHandler(sys.stdout)  # Force logs to show immediately
    ]
)
logger = logging.getLogger(__name__)

# --- Initialize Firebase ---
try:
    cred = credentials.Certificate(PRIVATE_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Firebase initialization failed: {e}", exc_info=True)
    raise RuntimeError("Firebase initialization failed. Check your credentials path.")

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Helper Functions ---
def download_file(url, max_size=5 * 1024 * 1024):  # 5 MB limit
    if not url.startswith("https://"):
        raise ValueError("Insecure URL detected. Only HTTPS URLs are allowed.")

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        total_size = 0
        file_data = bytearray()
        for chunk in response.iter_content(1024):
            total_size += len(chunk)
            if total_size > max_size:
                raise ValueError("File size exceeds 5 MB limit.")
            file_data.extend(chunk)

        return BytesIO(file_data)
    except requests.exceptions.RequestException as e:
        logger.error(f"File download error: {e}")
        raise ValueError(f"Failed to download file: {str(e)}")

# --- Authentication Decorator ---
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        logger.info(f"Received request with auth header: {bool(auth_header)}")
        
        if not auth_header:
            return jsonify({"success": False, "error": "Authorization header is missing"}), 401
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Invalid authorization format. Use 'Bearer <token>'"}), 401

        try:
            id_token = auth_header.split("Bearer ")[1].strip()
            
            # For development/testing environment only
            if os.environ.get('FLASK_ENV') == 'development':
                # Special case for test tokens
                if id_token.startswith("eyJ") and "test_user_123" in id_token:
                    logger.info("Using test custom token authentication")
                    uid = "test_user_123"
                    kwargs['uid'] = uid
                    return f(*args, **kwargs)
            
            # Normal ID token verification for production
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            logger.info(f"Authenticated request for UID: {uid}")
            kwargs['uid'] = uid
            
        except IndexError:
            return jsonify({"success": False, "error": "Invalid token format"}), 401
        except auth.InvalidIdTokenError:
            logger.error(f"Invalid ID token: {id_token[:20]}...")
            return jsonify({"success": False, "error": "Invalid ID token"}), 401
        except Exception as e:
            logger.error(f"Token verification error: {e}", exc_info=True)
            return jsonify({"success": False, "error": "Authentication error"}), 401

        return f(*args, **kwargs)
    return decorated

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for testing connectivity"""
    return jsonify({
        "status": "healthy",
        "firebase": "connected", 
        "timestamp": time.time()
    }), 200

# --- API Routes ---
@app.route('/upload_healthcare_report', methods=['POST'])
@requires_auth
def upload_healthcare_report(uid):
    logger.info(f"Processing healthcare report upload for UID: {uid}")
    try:
        report_file_url = request.form.get('report_file')
        
        if not report_file_url:
            return jsonify({"success": False, "error": "Missing report file URL"}), 400
            
        logger.info(f"Downloading file from URL for processing")
        file_data = download_file(report_file_url)
        
        logger.info("Extracting healthcare data from file")
        extracted_data = extract.extract_healthcare_data(file_data)
        
        if not extracted_data:
            logger.warning("No healthcare data extracted from file")
            return jsonify({"success": False, "error": "Failed to extract healthcare data"}), 422
        
        logger.info(f"Saving healthcare data to Firestore for UID: {uid}")
        db.collection("users").document(uid).set(
            {"extracted_health_data": extracted_data}, merge=True
        )
        
        return jsonify({
            "success": True,
            "message": "Healthcare report processed successfully",
            "data": extracted_data
        }), 200
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error processing healthcare report")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@app.route('/analyze', methods=['POST'])
@requires_auth
def analyze_product(uid):
    logger.info(f"Processing product analysis for UID: {uid}")
    try:
        ingredient_file_url = request.form.get('ingredient_file')
        
        if not ingredient_file_url:
            return jsonify({"success": False, "error": "Missing ingredient file URL"}), 400
        
        # Get user's healthcare data
        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            return jsonify({
                "success": False, 
                "error": "User data not found. Please upload healthcare report first."
            }), 404
            
        user_data = user_doc.to_dict()
        healthcare_data = user_data.get('extracted_health_data')
        if not healthcare_data:
            return jsonify({
                "success": False, 
                "error": "Healthcare data not found. Please upload healthcare report first."
            }), 404
        
        logger.info(f"Downloading ingredient file from URL")
        file_data = download_file(ingredient_file_url)
        
        logger.info(f"Extracting ingredients from file")
        ingredients = extract.extract_ingredients(file_data)
        
        if not ingredients:
            logger.warning("No ingredients extracted from file")
            return jsonify({"success": False, "error": "Could not extract ingredients"}), 422
        
        logger.info(f"Ingredients extracted: {ingredients}")
        analysis_result = dietician.analyze(healthcare_data, ingredients)
        
        # Store analysis results
        upload_ref = db.collection("uploads").document()
        upload_data = {
            "user_id": uid,
            "image_url": ingredient_file_url,
            "ingredients": ingredients,
            "analysis": analysis_result,
            "uploaded_at": firestore.SERVER_TIMESTAMP
        }
        upload_ref.set(upload_data)
        logger.info(f"Analysis stored with document ID: {upload_ref.id}")
        
        return jsonify({
            "success": True,
            "document_id": upload_ref.id,
            "ingredients": ingredients,
            "analysis": analysis_result
        }), 200
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in analyze_product")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

# --- Generate Test Token Endpoint (FOR TESTING ONLY) ---
@app.route('/generate_test_token', methods=['GET'])
def generate_test_token():
    """Generate a test token for API testing.
    THIS SHOULD BE REMOVED IN PRODUCTION.
    """
    try:
        # Only allow in development environment
        if os.environ.get('FLASK_ENV') != 'development':
            return jsonify({"error": "This endpoint is only available in development mode"}), 403
            
        # Create a custom token for testing
        test_uid = "test_user_123"
        custom_token = auth.create_custom_token(test_uid)
        token_string = custom_token.decode('utf-8')
        
        return jsonify({
            "custom_token": token_string,
            "note": "IMPORTANT: This is a custom token for testing purposes only",
            "curl_example": f"curl -X POST http://localhost:5000/upload_healthcare_report \\\n-H \"Authorization: Bearer {token_string}\" \\\n-H \"Content-Type: multipart/form-data\" \\\n-F \"report_file=@/path/to/your/file.png\""
        }), 200
    except Exception as e:
        logger.exception("Error generating test token")
        return jsonify({"error": str(e)}), 500

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"success": False, "error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    logger.info(f"Starting app on port {port}, debug mode: {debug_mode}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
