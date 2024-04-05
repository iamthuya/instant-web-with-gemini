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
# model = GenerativeModel("gemini-1.0-ultra-vision-001")
model = GenerativeModel("gemini-1.0-pro-vision-001")


def prompt(wireframe_image):
    instructions = (
        f"You are an expert web developer tasked with converting a hand-drawn wireframe into an HTML page."
        f"You may use CSS in <head> tag for styling and layout. Employ placehold.co images as placeholders."
        f"Provide response in pure HTML page without denoting with ```html code block"
    )
    contents = [
        instructions,
        "hand-drawn wireframe:",
        wireframe_image,
        "HTML page:"
    ]
    
    responses = model.generate_content(
        contents=contents,
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 1.0,
            "top_p": 0.8,
            "top_k": 32
        },
        safety_settings={
                generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        stream=True,
    )

    response = ""
    for res in responses:
        try:
            response += res.text.strip()
        except ValueError as e:
            return "<h1> Unable to get a response from the model. Please try again later.</h1>"
    return response


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def write_response(response, folder_name, file_name):
    file_path = os.path.join(folder_name, file_name)
    with open(file_path, "w") as file:
        file.write(response)


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
        uploaded_file = request.files['image-upload']
        wireframe_image = Image.from_bytes(uploaded_file.read())
        response = prompt(wireframe_image)

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
    app.run(debug=True, port=server_port, host='0.0.0.0')