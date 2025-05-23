import os
import tempfile
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")
allowed_passwords = os.environ.get("ALLOWED_PASSWORDS", "").split(",")

@app.route("/")
def login():
    return render_template_string(open("index.html", encoding="utf-8").read())

@app.route("/auth", methods=["POST"])
def auth():
    data = request.get_json()
    password = data.get("password", "")
    if password in allowed_passwords:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        file = request.files.get("audio")
        format = request.form.get("format", "txt")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(tempfile.gettempdir(), filename)
        file.save(filepath)

        with open(filepath, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

        content = transcript["text"]

        if format == "srt":
            lines = content.split(". ")
            srt_content = ""
            for i, line in enumerate(lines):
                srt_content += f"{i+1}\n00:00:{i*2:02},000 --> 00:00:{i*2+2:02},000\n{line.strip()}\n\n"
            with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", encoding="utf-8", delete=False) as srt_file:
                srt_file.write(srt_content)
                return send_file(srt_file.name, as_attachment=True)
        else:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as txt_file:
                txt_file.write(content)
                return send_file(txt_file.name, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
