from flask import Flask, request, send_file, jsonify
import subprocess
import uuid
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
    max-width:560px;
    background:#1f2937;
    padding:26px;
    border-radius:18px;
}
input,button{
    width:100%;
    margin-top:14px;
    padding:14px;
    border-radius:10px;
    border:none;
    font-size:16px;
}
button{
    background:#2563eb;
    color:white;
    font-weight:bold;
    cursor:pointer;
}
button:disabled{
    opacity:.55;
    cursor:not-allowed;
}
.status{
    margin-top:18px;
    padding:14px;
    border-radius:10px;
    background:#111827;
    color:#cbd5e1;
    line-height:1.6;
    white-space:pre-wrap;
}
.progress{
    margin-top:14px;
    height:12px;
    background:#374151;
    border-radius:999px;
    overflow:hidden;
}
.bar{
    width:0%;
    height:100%;
    background:#22c55e;
    transition:width .3s;
}
audio{
    width:100%;
    margin-top:16px;
}
a{
    color:#93c5fd;
}
</style>
</head>
<body>
<div class="container">
<h1>AudioShift</h1>
<p>音源を選択し、移調量を半音単位で入力してください。</p>

<input id="audio" type="file" accept="audio/*">

<input id="semitones" type="number" step="0.1" placeholder="移調量 例：2 / -3 / -0.1">

<button id="convertBtn">変換する</button>

<div class="progress"><div id="bar" class="bar"></div></div>
<div id="status" class="status">音源を選択してください。</div>

<audio id="player" controls style="display:none;"></audio>
<a id="downloadLink" style="display:none;" download>変換後WAVをダウンロード</a>
</div>

<script>
const audioInput = document.getElementById("audio");
const semitonesInput = document.getElementById("semitones");
const convertBtn = document.getElementById("convertBtn");
const statusBox = document.getElementById("status");
const bar = document.getElementById("bar");
const player = document.getElementById("player");
const downloadLink = document.getElementById("downloadLink");

let resultUrl = null;

function setStatus(text, percent){
    statusBox.textContent = text;
    bar.style.width = percent + "%";
}

convertBtn.addEventListener("click", async () => {
    const file = audioInput.files[0];
    const semitones = semitonesInput.value;

    if(!file){
        setStatus("音源ファイルを選択してください。", 0);
        return;
    }

    if(semitones === ""){
        setStatus("移調量を入力してください。例：2 / -3 / -0.1", 0);
        return;
    }

    if(resultUrl){
        URL.revokeObjectURL(resultUrl);
        resultUrl = null;
    }

    player.style.display = "none";
    downloadLink.style.display = "none";

    convertBtn.disabled = true;
    convertBtn.textContent = "変換中...";
    setStatus("アップロード準備中...", 10);

    const formData = new FormData();
    formData.append("audio", file);
    formData.append("semitones", semitones);

    try{
        setStatus("サーバーへアップロード中...\\n曲が長い場合は少し時間がかかります。", 30);

        const response = await fetch("/shift", {
            method: "POST",
            body: formData
        });

        setStatus("変換処理中...\\nRubber Bandで移調しています。", 65);

        if(!response.ok){
            const err = await response.json();
            throw new Error(err.error || "変換に失敗しました。");
        }

        const blob = await response.blob();
        resultUrl = URL.createObjectURL(blob);

        player.src = resultUrl;
        player.style.display = "block";

        const baseName = file.name.replace(/\\.[^/.]+$/, "");
        downloadLink.href = resultUrl;
        downloadLink.download = baseName + "_shift_" + semitones + ".wav";
        downloadLink.style.display = "block";

        setStatus("変換完了しました。\\n下のプレイヤーで再生確認できます。\\n必要ならWAVをダウンロードしてください。", 100);

    }catch(error){
        setStatus("エラー：\\n" + error.message, 0);
    }finally{
        convertBtn.disabled = false;
        convertBtn.textContent = "変換する";
    }
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML

@app.route("/shift", methods=["POST"])
def shift_audio():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "音源ファイルがありません。"}), 400

        file = request.files["audio"]
        semitones = request.form.get("semitones", "0")

        uid = str(uuid.uuid4())

        input_path = UPLOAD_DIR / f"{uid}_input"
        wav_path = UPLOAD_DIR / f"{uid}.wav"
        output_path = OUTPUT_DIR / f"{uid}_shifted.wav"

        file.save(input_path)

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ar", "44100",
            "-ac", "2",
            str(wav_path)
        ], check=True)

        subprocess.run([
            "rubberband",
            "-p", semitones,
            str(wav_path),
            str(output_path)
        ], check=True)

        return send_file(output_path, mimetype="audio/wav", as_attachment=False)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "音声変換処理に失敗しました。音源形式または移調量を確認してください。"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
