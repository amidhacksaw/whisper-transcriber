import os
import tempfile
import openai_whisper
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

ALLOWED_PASSWORDS = os.getenv("ALLOWED_PASSWORDS", "").split(",")
API_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    password = data.get("password", "")
    if password in ALLOWED_PASSWORDS:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    file = request.files["audio"]
    format = request.form.get("format", "txt")

    with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
        file.save(temp_audio.name)
        model = openai_whisper.load_model("base")
        result = model.transcribe(temp_audio.name)
        text = result["text"]

    if format == "srt":
        srt_content = ""
        lines = text.split(". ")
        for i, line in enumerate(lines, 1):
            srt_content += f"{i}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{line.strip()}\n\n"
        return send_file(
            tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".srt", encoding="utf-8"),
            mimetype="text/srt",
            as_attachment=True,
            download_name="result.srt"
        )

    return send_file(
        tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt", encoding="utf-8", delete=False),
        mimetype="text/plain",
        as_attachment=True,
        download_name="result.txt"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
