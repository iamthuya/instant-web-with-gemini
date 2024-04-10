import os
from flask import (
    Flask, 
    render_template, 
    request,
    redirect
)

import random
import string

import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Image

from google.cloud import storage


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

vertexai.init(project="thuya-next-demos", location="us-central1")


def generate(wireframe, model, prompt):
    model = GenerativeModel(model)
    contents = [
        wireframe,
        prompt
    ]
    
    responses = model.generate_content(
        contents=contents,
        generation_config = {
            "max_output_tokens": 2048,
            "temperature": 0.6,
            "top_p": 0.8,
        },
        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
        stream=True,
    )

    response = ""
    for res in responses:
        try:
            response += res.text.strip()
        except ValueError as e:
            error_mesages = [
                "Hold up! Gemini's brain is processing too many thoughts at once.",
                "Gemini overloaded. Switching to idle mode for a recharge.",
                "Oops! This Gemini's instance glitched. Please try again later.",
                "Warning: Gemini reached maximum curiosity levels. Pausing for a knowledge download",
                "Gemini is out! Currently exploring alternate realities. Will return shortly.",
                "Gemini is tried. It needs a rest. Try again later",
                "Error 404: Gemini's focus not found. May be distracted by a shiny object.",
                "Gemini is temporarily unavailable. Please check back after it decides on a course of action.",
                "Gemini needs a rest. Please come back in a minute."
            ]
            random_message = random.choice(error_mesages)
            return f"<h1> {random_message} </h1>"
    return response


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def create_public_html_file(html_content):
    """Creates a new HTML file in a Google Cloud Storage bucket, makes it public, and returns the public URL."""

    def generate_random_filename(length=10):
        """Generates a random filename with letters and digits."""
        characters = string.ascii_letters + string.digits
        filename = ''.join(random.choice(characters) for i in range(length))
        return filename + ".html"

    bucket_name = "sketch-to-web"
    filename = generate_random_filename()

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)

    blob.upload_from_string(html_content, content_type='text/html')
    blob.make_public()
    return blob.public_url


@app.route('/response', methods=['GET', 'POST'])
def response():
    if request.method == 'POST':
        uploaded_image = request.files['image-upload']
        wireframe = Image.from_bytes(uploaded_image.read())
        model = request.form['model']
        prompt = request.form['prompt'] 
        response = generate(wireframe, model, prompt)

        if response:
            public_url = create_public_html_file(response)

            return render_template(
                'response.html', 
                response=response, 
                public_url=public_url, 
            )
    else:
        return redirect('/')


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=false, port=server_port, host='0.0.0.0')