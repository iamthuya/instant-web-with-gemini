import os

from flask import (
    Flask, 
    render_template, 
    request
)

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
import vertexai.preview.generative_models as generative_models

app = Flask(__name__)

vertexai.init(project="thuya-next-demos", location="us-central1")
model = GenerativeModel("gemini-1.0-ultra-vision-001")


def generate(wireframe_image):
    instructions = (
        f"You are an expert web developer. Your are good at creating a webpage from a wireframe." 
        f"Use css framework to beautify the page. Use 'placehold.co' to create dummy images with appropriate size."
    )
    contents = [
        instructions,
        "input wireframe:",
        wireframe_image,
        "your html page:\n <!DOCTYPE html>"
    ]

    responses = model.generate_content(
        contents = contents,
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
        response += res.text


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files['file-upload']
        image_bytes = f.read().decode('utf-8')
        wireframe_image = Image.from_bytes(image_bytes)
        response = generate(wireframe_image)
        return render_template('index.html', response=response)
    else:
        return render_template('index.html')


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
