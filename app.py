import os
import random
import string

import vertexai
import vertexai.preview.generative_models as generative_models
from flask import Flask, redirect, render_template, request
from google.cloud import storage
from tenacity import retry, stop_after_attempt
from vertexai.preview.generative_models import GenerativeModel, Image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@retry(stop=stop_after_attempt(5))
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
        response += res.text.strip()
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
        wireframe = request.form['capturedImage']
        model = request.form['model']
        prompt = request.form['prompt']

        try:
            response = generate(wireframe, model, prompt)

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
    location = os.environ.get('LOCATION', "us-central1")
    project_id = os.environ.get('PROJECT_ID', "thuya-next-demos")
    vertexai.init(project=project_id, location=location)

    app.run(debug=True, port=server_port, host='0.0.0.0')
