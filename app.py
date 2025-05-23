from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import whisper
import tempfile
import os
import io

app = Flask(__name__)
CORS(app)

# 環境變數與密碼驗證
from dotenv import load_dotenv
load_dotenv()
ALLOWED_PASSWORDS = os.getenv("ALLOWED_PASSWORDS", "demo123").split(",")

model = whisper.load_model("base")

@app.route("/verify-password", methods=["POST"])
def verify_password():
    password = request.form.get("password", "")
    if password in ALLOWED_PASSWORDS:
        return "ok"
    return "unauthorized", 401

@app.route("/transcribe", methods=["POST"])
def transcribe():
    password = request.form.get("password", "")
    if password not in ALLOWED_PASSWORDS:
        return jsonify({"error": "Unauthorized"}), 401

    audio = request.files.get("audio")
    if not audio:
        return jsonify({"error": "No audio uploaded"}), 400

    format = request.form.get("format", "txt")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        audio.save(tmp.name)
        result = model.transcribe(tmp.name)
        os.unlink(tmp.name)

    if format == "srt":
        from whisper.utils import write_srt
        srt_io = io.StringIO()
        write_srt(result["segments"], file=srt_io)
        srt_io.seek(0)
        return send_file(io.BytesIO(srt_io.read().encode("utf-8")), as_attachment=True, download_name="result.srt", mimetype="text/plain")
    else:
        return jsonify({"text": result["text"]})

if __name__ == "__main__":
    app.run(debug=True)
