import os
import random
import string
import base64

import vertexai
import vertexai.preview.generative_models as generative_models
from flask import Flask, redirect, render_template, request
from google.cloud import storage
from tenacity import retry, wait_random, stop_after_attempt
from vertexai.preview.generative_models import GenerativeModel, Part


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB


@retry(wait=wait_random(min=2, max=4), stop=stop_after_attempt(30))
def generate(wireframe, model, prompt):
    model = GenerativeModel(model)
    suffix = "Just provide the code without the explaination."

    contents = [
        wireframe,
        prompt,
        suffix
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
        response += res.text.strip()
    return response


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def generate_random_characters(length=10):
    """Generates a random filename with letters and digits."""
    characters = string.ascii_letters + string.digits
    random_characters = ''.join(random.choice(characters) for i in range(length))
    return random_characters


def create_public_html_file_on_gcs(random_characters, html_content):
    """Creates a new HTML file in a Google Cloud Storage bucket, makes it public, and returns the public URL."""
    filename = f"{GCS_FOLDER_NAME}/web-pages/{random_characters}.html"

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(filename)
    blob.upload_from_string(html_content, content_type='text/html')
    blob.make_public()

    return blob.public_url


def save_wireframe_to_gcs(random_characters, base64_image_string):
    """Store the wireframe in a Google Cloud Storage bucket and returns the g URL."""
    filename = f"{GCS_FOLDER_NAME}/wireframes/{random_characters}.jpeg"
    image_data = base64.b64decode(base64_image_string.replace("data:image/jpeg;base64,", ""))

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    content_type = 'image/jpeg'
    blob = bucket.blob(filename)
    blob.upload_from_string(image_data, content_type=content_type)

    wireframe = Part.from_uri(
        mime_type=content_type,
        uri=f"gs://{GCS_BUCKET_NAME}/{filename}"
    )

    return wireframe

@app.route('/response', methods=['GET', 'POST'])
def response():
    if request.method == 'POST':
        base64_image_string = request.form['capturedImage']
        model = request.form['model']
        prompt = request.form['prompt']
        random_characters = generate_random_characters()

        try:
            wireframe = save_wireframe_to_gcs(random_characters, base64_image_string)
            response = generate(wireframe, model, prompt)
            response = response.replace("```html", "").replace("```", "").strip()

        except ValueError as e:
            error_mesages = [
                "Geminiの脳は一度にたくさんのことを処理しすぎています。少々お待ち下さい。",
                "Geminiは過負荷です。休息のためにアイドルモードに切り替えました。",
                "おっと！Geminiのインスタンスに不具合が発生しました。後でもう一度お試しください。",
                "警告：Geminiは好奇心のレベルが最大に達しました。知識をダウンロードするため一時停止します。",
                "Geminiは退室中！現在、代替現実を探索中。まもなく戻ります。",
                "Geminiは試されています。休息が必要です。後で再挑戦しましょう。",
                "Error 404: Geminiの焦点が定まらない。光るものに気を取られるかもしれない。",
                "Geminiは一時的に利用できません。また後ほどご確認ください。",
                "Geminiには休息が必要です。またあとで試してみてください。"
            ]
            random_message = random.choice(error_mesages)
            response = f"<h1> {random_message} </h1>"

        if response:
            public_url = create_public_html_file_on_gcs(random_characters, response)

            return render_template(
                'response.html',
                response=response,
                public_url=public_url,
            )
    else:
        return redirect('/')


if __name__ == '__main__':
    PORT = os.environ.get('PORT', '8080')
    LOCATION = os.environ.get('LOCATION', "us-central1")
    PROJECT_ID = os.environ.get('PROJECT_ID', "thuya-next-demos")
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', "instant-web-gemini")
    GCS_FOLDER_NAME = os.environ.get('GCS_FOLDER_NAME', "next-tokyo-2024")

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    app.run(debug=False, port=PORT, host='0.0.0.0')
