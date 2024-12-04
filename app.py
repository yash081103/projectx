from flask import Flask, request, render_template
from dietacian import expert_dietician_analysis
from extract import get_extracted_data
import os

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('food.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    ingredient_file = request.files['ingredient-image']
    health_data_file = request.files['health-data']

    ingredient_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ingredient_file.filename)
    health_data_file_path = os.path.join(app.config['UPLOAD_FOLDER'], health_data_file.filename)

    ingredient_file.save(ingredient_file_path)
    health_data_file.save(health_data_file_path)

    extracted_data = get_extracted_data(health_data_file_path, ingredient_file_path)
    analysis = expert_dietician_analysis(
        extracted_data['product_ingredients'],
        extracted_data['patient_data']
    )

    return render_template('result.html', analysis=analysis)

if __name__ == "__main__":
    app.run(debug=True)
