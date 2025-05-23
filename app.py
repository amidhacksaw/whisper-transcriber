import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
openai.api_key = os.getenv("OPENAI_API_KEY", "")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if request.form.get("password") != ADMIN_PASSWORD:
        return "Unauthorized", 401

    audio = request.files.get("audio")
    fmt = request.form.get("format")

    if not audio or not fmt:
        return "Missing audio or format", 400

    filename = secure_filename(audio.filename)
    filepath = os.path.join("/tmp", filename)
    audio.save(filepath)

    try:
        with open(filepath, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)

        content = transcript["text"]

        if fmt == "srt":
            lines = content.split(". ")
            srt = ""
            for i, line in enumerate(lines):
                start = f"00:00:{i*2:02d},000"
                end = f"00:00:{i*2+2:02d},000"
                srt += f"{i+1}\n{start} --> {end}\n{line.strip()}\n\n"
            return srt, 200, {'Content-Type': 'text/plain; charset=utf-8'}

        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
