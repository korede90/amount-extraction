from flask import Flask, render_template, request, redirect, url_for, jsonify
from google.cloud import vision
import os
import pickle
import pytesseract
import re
import cv2
import json
import logging

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True, mode=0o755)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Set Tesseract path based on the operating system
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:  # Linux/Mac
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


def extract_amount(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    amounts = []
    for text in texts:
        if re.match(r'\d{1,3}(?:,\d{3})*', text.description):
            amounts.append(text.description)
    return amounts if amounts else ['No amount found']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file and extract amounts."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        # Validate file type
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({'error': 'Invalid file type. Please upload a PNG, JPG, or JPEG image.'})

        # Save the file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Extract amounts
        amounts = extract_amount(filepath)

        # Handle errors in extraction
        if 'error' in amounts:
            return jsonify(amounts)

        # Redirect to result page with JSON encoded amounts
        return redirect(url_for('result', image_path=file.filename, amounts=json.dumps(amounts)))

@app.route('/result')
def result():
    """Display extracted amounts."""
    image_path = request.args.get('image_path', None)
    amounts_json = request.args.get('amounts', '[]')
    extracted_amounts = json.loads(amounts_json)  # Correctly parse the JSON list

    return render_template('result.html', image_path='/' + os.path.join(app.config['UPLOAD_FOLDER'], image_path),
                           extracted_amounts=extracted_amounts)

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')