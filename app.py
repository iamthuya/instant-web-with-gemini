import os

from flask import (
    Flask, 
    render_template, 
    request,
    url_for,
    redirect
)

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
import vertexai.preview.generative_models as generative_models

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

vertexai.init(project="thuya-next-demos", location="us-central1")
# model = GenerativeModel("gemini-1.0-ultra-vision-001")
model = GenerativeModel("gemini-1.0-pro-vision-001")


def generate(wireframe_image):
    instructions = (
        f"You are an expert web developer. Your are good at creating webpages from hand-drawn wireframes." 
        f"You use 'placehold.co' to create dummy images with appropriate size."
    )
    contents = [
        instructions,
        "input wireframe:",
        wireframe_image,
        "\nyour html page:\n<div>"
    ]
    
    responses = model.generate_content(
        contents=contents,
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0.4,
            "top_p": 1,
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
        response += res.text.strip()
    return response


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        uploaded_file = request.files['file-upload']
        wireframe_image = Image.from_bytes(uploaded_file.read())
        response = generate(wireframe_image)
        return response
    else:
        return render_template('generate.html')


# @app.route('/response')
# def response(response):
#     return render_template('response.html', response=response)


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
