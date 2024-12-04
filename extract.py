import json
import os
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPICallError

# Configure the API key
genai.configure(api_key="AIzaSyAu3pz-EwBic5FAb4yfD_S8uwtxlhHZx8w")

# Initialize default variables
patient_data = {}
product_ingredients = []

# Extract patient data
try:
    # Upload the file containing patient data
    patient_file = genai.upload_file("E:\projectx\6230811349543292597.webp")

    # Initialize the model
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generate structured data extraction
    result = model.generate_content([patient_file, "Extract the patient data in key-value pairs as a JSON object."])

    # Check if candidates exist in the response
    if result and result.candidates:
        # Extracting the first candidate's content
        raw_text = result.candidates[0].content.parts[0].text

        # Debugging output for raw text
        print("Raw Extracted Text:")
        print(raw_text)

        # Attempt to convert raw text into a dictionary
        try:
            patient_data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback: Attempt to parse key-value pairs manually
            lines = raw_text.splitlines()
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    patient_data[key.strip()] = value.strip()

        print("\nExtracted Patient Data as Dictionary:")
        print(patient_data)
    else:
        print("No candidates found in the response.")

except PermissionDenied as e:
    print("Permission Denied. Check your API key or access permissions.")
    print(f"Error Details: {e}")
except GoogleAPICallError as e:
    print("An error occurred while calling the Google API.")
    print(f"Error Details: {e}")
except FileNotFoundError:
    print("The specified file was not found. Check the file path.")
except Exception as e:
    print("An unexpected error occurred.")
    print(f"Error Details: {e}")


# Extract ingredients data
try:
    # Upload the image file
    myfile = genai.upload_file("E:\projectx\6230811349999533710.jpg")

    # Initialize the model
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generate text for ingredients extraction
    result = model.generate_content([myfile, "Extract only the ingredients as a list."])

    # Check if candidates exist in the response
    if result and result.candidates:
        # Extracting the first candidate's content
        raw_text = result.candidates[0].content.parts[0].text

        # Print raw extracted text for debugging
        print("Raw Extracted Text:")
        print(raw_text)

        # Clean the output to extract just the ingredients
        if ':' in raw_text:  # Check for key-value style format
            raw_text = raw_text.split(':', 1)[-1]  # Take only the part after the colon
        raw_text = raw_text.replace(" and ", ", ")  # Handle "and" as a delimiter
        product_ingredients = [
            item.strip() for item in raw_text.replace("\n", ",").split(",") if item.strip()
        ]

        print("\nExtracted Ingredients as Clean List:")
        print(product_ingredients)
    else:
        print("No candidates found in the response.")

except PermissionDenied as e:
    print("Permission Denied. Check your API key or access permissions.")
    print(f"Error Details: {e}")
except GoogleAPICallError as e:
    print("An error occurred while calling the Google API.")
    print(f"Error Details: {e}")
except FileNotFoundError:
    print("The specified file was not found. Check the file path.")
except Exception as e:
    print("An unexpected error occurred.")
    print(f"Error Details: {e}")


def get_extracted_data():
    return {
        "product_ingredients": product_ingredients,
        "patient_data": patient_data
}

if __name__ == "__main__":
    extracted_data = get_extracted_data()
    print("Extracted Data:")
    print(extracted_data)
