import os
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import openai

app = Flask(__name__)
CORS(app)

# 讀取密碼與 OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")
allowed_passwords = os.environ.get("ALLOWED_PASSWORDS", "").split(",")

# 驗證密碼
@app.route("/auth", methods=["POST"])
def auth():
    data = request.get_json()
    password = data.get("password", "")
    if password in allowed_passwords:
        return jsonify({"success": True})
    return jsonify({"error": "Unauthorized"}), 401

# Whisper 語音轉文字
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "Missing audio file"}), 400

    audio = request.files["audio"]
    format = request.form.get("format", "txt")

    filename = secure_filename(audio.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        audio.save(temp_audio.name)
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
            content = transcript["text"]

        if format == "srt":
            lines = content.split(". ")
            srt = ""
            for i, line in enumerate(lines):
                srt += f"{i+1}\n00:00:{i:02},000 --> 00:00:{i+1:02},000\n{line.strip()}\n\n"
            output = srt
            out_name = "result.srt"
        else:
            output = content
            out_name = "result.txt"

        output_path = os.path.join(tempfile.gettempdir(), out_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# 測試入口（Render不一定用得到）
@app.route("/")
def hello():
    return "Whisper Transcriber API is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
