from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://amidhacksaw.github.io"], supports_credentials=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
allowed_passwords = os.getenv("ALLOWED_PASSWORDS", "").split(",")

@app.route("/")
def home():
    return "Whisper Transcriber API is running."

@app.route("/admin", methods=["POST"])
def check_password():
    data = request.get_json()
    password = data.get("password", "")
    if password in allowed_passwords:
        return jsonify({"success": True})
    return jsonify({"success": False}), 403

@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files.get("audio")
    format = request.form.get("format", "txt")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        file.save(temp_audio.name)
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            content = transcript

        if format == "srt":
            lines = content.strip().split('.')
            srt = ""
            for i, line in enumerate(lines, 1):
                start = f"00:00:{(i-1)*3:02},000"
                end = f"00:00:{i*3:02},000"
                srt += f"{i}\n{start} --> {end}\n{line.strip()}\n\n"
            srt_path = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".srt", encoding="utf-8").name
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt)
            return send_file(srt_path, as_attachment=True, download_name="result.srt")

        else:
            txt_path = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt", encoding="utf-8").name
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            return send_file(txt_path, as_attachment=True, download_name="result.txt")

    except Exception as e:
        print("❌ Transcribe error:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
