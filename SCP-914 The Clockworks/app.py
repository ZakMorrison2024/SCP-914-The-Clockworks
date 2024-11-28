from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from PIL import Image
import openai
from io import BytesIO
import requests

# Flask App Setup
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# OpenAI API Setup (replace 'your_openai_api_key' with your key)
openai.api_key = ""

# Hugging Face API URL and token (replace 'your_huggingface_api_key' with your key)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HUGGINGFACE_API_TOKEN = ""

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files['file']
    setting = request.form.get('setting')

    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    # Save the uploaded file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Analyze the image with ChatGPT
    image_analysis = analyze_image_with_chatgpt(filepath)

    # Regenerate the image based on the selected setting
    output_path = regenerate_image(filepath, setting, image_analysis)
    if not output_path:
        return jsonify({"success": False, "error": "Failed to process file"}), 500

    return jsonify({"success": True, "output_url": f"/outputs/{os.path.basename(output_path)}"})


def analyze_image_with_chatgpt(filepath):
    """
    Analyze the uploaded image using ChatGPT to describe the content.
    """
    try:
        with open(filepath, "rb") as image_file:
            image_bytes = image_file.read()

        # Send image description prompt to ChatGPT
        response = openai.Image.create_edit(
            image=image_bytes,
            prompt="Describe this image in detail and its key features.",
            n=1,
            size="256x256",
        )

        description = response["choices"][0]["text"]
        print(f"ChatGPT Analysis: {description}")
        return description

    except Exception as e:
        print(f"Error analyzing image with ChatGPT: {e}")
        return "Unknown content."


def regenerate_image(filepath, setting, description):
    """
    Use Hugging Face API (Stable Diffusion) to regenerate the image with modifications
    based on the quality setting and ChatGPT analysis.
    """
    try:
        # Define the prompt for the AI model based on the description and quality setting
        if setting == "rough":
            prompt = f"Generate a heavily abstract version of this image: {description}."
            print(prompt)
        elif setting == "coarse":
            prompt = f"Create a simplified version of this image: {description}."
            print(prompt)
        elif setting == "1:1":
            prompt = f"Generate an identical image with slight variations: {description}."
            print(prompt)
        elif setting == "fine":
            prompt = f"Enhance the details of this image: {description}."
            print(prompt)
        elif setting == "very-fine":
            prompt = f"Generate a highly detailed and polished version of this image: {description}."
            print(prompt)
        else:
            prompt = f"Generate a version of this image: {description}."
            print(prompt)

        # Prepare the request payload for Hugging Face
        with open(filepath, "rb") as f:
            image_bytes = f.read()

        payload = {
            "inputs": prompt,
            "options": {"wait_for_model": True},
        }

        # Send the request to Hugging Face API
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            # Save the output image
            output_filename = f"{setting}_{os.path.basename(filepath)}"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            image.save(output_path)
            return output_path
        else:
            print(f"Error from Hugging Face API: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        print(f"Error regenerating image: {e}")
        return None


@app.route('/outputs/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
