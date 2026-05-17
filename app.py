from flask import Flask, request, send_file
import subprocess
import uuid
import os
from pathlib import Path

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AudioShift</title>
<style>
body{
    margin:0;
    font-family:system-ui,sans-serif;
    background:#111827;
    color:white;
    display:flex;
    justify-content:center;
    align-items:center;
    min-height:100vh;
}
.container{
    width:90%;
    max-width:500px;
    background:#1f2937;
    padding:24px;
    border-radius:16px;
}
input,button{
    width:100%;
    margin-top:12px;
    padding:12px;
    border-radius:8px;
    border:none;
}
button{
    background:#2563eb;
    color:white;
    font-weight:bold;
    cursor:pointer;
}
</style>
</head>
<body>
<div class="container">
<h1>AudioShift</h1>

<form action="/shift" method="post" enctype="multipart/form-data">
<input type="file" name="audio" required>

<input type="number" step="0.1" name="semitones" placeholder="移調量（例: 2 or -3）" required>

<button type="submit">変換する</button>
</form>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML

@app.route("/shift", methods=["POST"])
def shift_audio():
    file = request.files["audio"]
    semitones = request.form["semitones"]

    uid = str(uuid.uuid4())

    input_path = UPLOAD_DIR / f"{uid}.mp3"
    wav_path = UPLOAD_DIR / f"{uid}.wav"
    output_path = OUTPUT_DIR / f"{uid}_shifted.wav"

    file.save(input_path)

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        str(wav_path)
    ], check=True)

    subprocess.run([
        "rubberband",
        "-p",
        semitones,
        str(wav_path),
        str(output_path)
    ], check=True)

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
