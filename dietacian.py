import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError

# Configure API key
genai.configure(api_key="AIzaSyAu3pz-EwBic5FAb4yfD_S8uwtxlhHZx8w")

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

        if result and result.candidates:
            return result.candidates[0].content.parts[0].text
        else:
            return "No response generated."
    except (PermissionDenied, GoogleAPICallError, Exception) as e:
        return f"Error in generating analysis: {e}"

if __name__ == "__main__":
    # Example data
    ingredients = ["Sugar", "Salt", "Ajwain"]
    patient_data = {"Blood Pressure": "140/90", "Blood Sugar": "200 mg/dL"}

    analysis = expert_dietician_analysis(ingredients, patient_data)
    print(analysis)
