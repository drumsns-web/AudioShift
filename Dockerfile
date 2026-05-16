import os
import uuid
import shutil
import subprocess
from pathlib import Path
from flask import Flask, request, send_file, jsonify, render_template, after_this_request
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "tmp"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_MB = int(os.environ.get("MAX_UPLOAD_MB", "120"))
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".aiff", ".aif"
}


@app.route("/")
def index():
    return render_template("index.html", max_mb=MAX_MB)


def cleanup_paths(*paths: Path):
    for path in paths:
        try:
            if path and path.exists():
                path.unlink()
        except Exception:
            pass


@app.route("/convert", methods=["POST"])
def convert():
    if "audio" not in request.files:
        return jsonify({"error": "音源ファイルがありません。"}), 400

    file = request.files["audio"]
    if not file.filename:
        return jsonify({"error": "ファイル名が空です。"}), 400

    semitones_raw = request.form.get("semitones", "0")
    quality = request.form.get("quality", "high")

    try:
        semitones = float(semitones_raw)
    except ValueError:
        return jsonify({"error": "移調量が不正です。"}), 400

    if semitones < -12 or semitones > 12:
        return jsonify({"error": "移調量は -12〜+12 半音にしてください。"}), 400

    original_name = secure_filename(file.filename)
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"未対応形式です: {ext}"}), 400

    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}{ext}"
    wav_in_path = UPLOAD_DIR / f"{job_id}_in.wav"
    wav_out_path = UPLOAD_DIR / f"{job_id}_shifted.wav"

    file.save(input_path)

    # rubberbandはWAV入力が安定しやすいため、先にffmpegでWAV化。
    ffmpeg_to_wav = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(wav_in_path),
    ]

    try:
        subprocess.run(
            ffmpeg_to_wav,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=240,
        )
    except subprocess.CalledProcessError as e:
        cleanup_paths(input_path, wav_in_path, wav_out_path)
        return jsonify({"error": "ffmpegで音源を読み込めませんでした。", "detail": e.stderr[-1000:]}), 500
    except subprocess.TimeoutExpired:
        cleanup_paths(input_path, wav_in_path, wav_out_path)
        return jsonify({"error": "音源の読み込み処理がタイムアウトしました。短い音源で試してください。"}), 500

    # Rubber Bandの移調。
    # -p は半音単位のピッチ変更。テンポは基本維持。
    cmd = ["rubberband", "-p", str(semitones)]

    # 品質設定。実環境で軽さを選べるようにする。
    if quality == "fast":
        cmd += ["-F"]
    elif quality == "crisp":
        cmd += ["-c", "4"]
    else:
        # high: より自然寄り。バージョン差で未対応オプションを避けるため保守的。
        cmd += ["-c", "5"]

    cmd += [str(wav_in_path), str(wav_out_path)]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=300,
        )
    except subprocess.CalledProcessError as e:
        cleanup_paths(input_path, wav_in_path, wav_out_path)
        return jsonify({"error": "Rubber Bandで変換できませんでした。", "detail": e.stderr[-1000:]}), 500
    except subprocess.TimeoutExpired:
        cleanup_paths(input_path, wav_in_path, wav_out_path)
        return jsonify({"error": "変換がタイムアウトしました。短い音源で試してください。"}), 500

    download_name = f"{Path(original_name).stem}_pitch_{semitones:+g}.wav"

    @after_this_request
    def remove_files(response):
        cleanup_paths(input_path, wav_in_path, wav_out_path)
        return response

    return send_file(
        wav_out_path,
        mimetype="audio/wav",
        as_attachment=True,
        download_name=download_name,
    )


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": f"ファイルが大きすぎます。最大 {MAX_MB}MB までです。"}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
