from flask import Flask, request, jsonify, send_file, render_template_string
import os
import openai
from werkzeug.utils import secure_filename

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/")
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files.get("audio")
    format = request.form.get("format", "txt")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join("/tmp", filename)
    file.save(filepath)

    try:
        with open(filepath, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

        content = transcript["text"]

        if format == "srt":
            lines = content.split(". ")
            srt_output = ""
            for i, line in enumerate(lines):
                srt_output += f"{i+1}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{line.strip()}\n\n"
            with open("result.srt", "w", encoding="utf-8") as f:
                f.write(srt_output)
            return send_file("result.srt", as_attachment=True)
        else:
            with open("result.txt", "w", encoding="utf-8") as f:
                f.write(content)
            return send_file("result.txt", as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
