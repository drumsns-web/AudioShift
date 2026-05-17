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
<title>AudioShift HQ</title>
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
    max-width:620px;
    background:#1f2937;
    padding:26px;
    border-radius:18px;
}
h1{
    margin-top:0;
}
input,button{
    width:100%;
    margin-top:14px;
    padding:14px;
    border-radius:10px;
    border:none;
    font-size:16px;
    box-sizing:border-box;
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
    display:block;
    margin-top:14px;
    color:#93c5fd;
    font-weight:bold;
}
.small{
    color:#9ca3af;
    font-size:13px;
    line-height:1.6;
}
.info{
    margin-top:14px;
    padding:14px;
    background:#111827;
    border-radius:12px;
    color:#d1d5db;
    font-size:14px;
    line-height:1.7;
}
.info strong{
    color:#ffffff;
}
.example{
    margin-top:12px;
    padding:12px;
    background:#0f172a;
    border-radius:10px;
    color:#cbd5e1;
    font-size:13px;
    line-height:1.7;
}
.badge{
    display:inline-block;
    padding:4px 8px;
    margin:4px 4px 0 0;
    border-radius:999px;
    background:#374151;
    color:#e5e7eb;
    font-size:12px;
}
</style>
</head>
<body>
<div class="container">
<h1>AudioShift HQ</h1>

<p>音源を選択し、移調量を半音単位で入力してください。</p>

<p class="small">
例：1 = 半音上げ / -1 = 半音下げ / 2 = 全音上げ / 0.2 = 微調整
</p>

<input id="audio" type="file" accept="audio/*">

<input id="semitones" type="number" step="0.1" placeholder="移調量 例：2 / -3 / -0.1">

<div id="pitchInfo" class="info">
<strong>移調量の説明</strong><br>
1 = 半音 = 100セント<br>
0.1 = 10セント<br>
0.2 = 20セント<br><br>
A4=440Hzを基準にすると、入力した移調量が何Hz相当になるかをここに表示します。
</div>

<div class="example">
<strong>目安</strong><br>
<span class="badge">0.1 = 微調整</span>
<span class="badge">0.5 = 半音の半分</span>
<span class="badge">1 = 半音</span>
<span class="badge">2 = 全音</span>
<br><br>
A4=440Hzの場合：<br>
+0.1 → 約442.55Hz<br>
+0.2 → 約445.11Hz<br>
+1 → 約466.16Hz
</div>

<button id="convertBtn">高品質変換する</button>

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
const pitchInfo = document.getElementById("pitchInfo");

let resultUrl = null;

function setStatus(text, percent){
    statusBox.textContent = text;
    bar.style.width = percent + "%";
}

function getPracticalLabel(semitones){
    const abs = Math.abs(semitones);

    if(abs === 0){
        return "変化なし";
    }
    if(abs < 0.1){
        return "ごく小さい微調整";
    }
    if(abs < 0.3){
        return "微調整。チューニング補正向き";
    }
    if(abs < 0.75){
        return "かなり分かる微調整";
    }
    if(abs < 1.5){
        return "半音前後の移調。歌いやすさが変わりやすい";
    }
    if(abs < 3){
        return "実用的なキー変更範囲";
    }
    if(abs < 6){
        return "大きめの移調。音質変化が目立つ場合あり";
    }
    return "かなり大きい移調。音質劣化が出やすい";
}

function updatePitchInfo(){
    const raw = semitonesInput.value;

    if(raw === ""){
        pitchInfo.innerHTML = `
            <strong>移調量の説明</strong><br>
            1 = 半音 = 100セント<br>
            0.1 = 10セント<br>
            0.2 = 20セント<br><br>
            A4=440Hzを基準にすると、入力した移調量が何Hz相当になるかをここに表示します。
        `;
        return;
    }

    const semitones = Number(raw);

    if(Number.isNaN(semitones)){
        pitchInfo.innerHTML = "<strong>数値を入力してください。</strong>";
        return;
    }

    const cents = semitones * 100;
    const baseHz = 440;
    const shiftedHz = baseHz * Math.pow(2, semitones / 12);
    const diffHz = shiftedHz - baseHz;
    const percent = ((shiftedHz / baseHz) - 1) * 100;

    const sign = semitones > 0 ? "+" : "";
    const hzSign = diffHz > 0 ? "+" : "";
    const percentSign = percent > 0 ? "+" : "";

    pitchInfo.innerHTML = `
        <strong>入力値：${sign}${semitones} 半音</strong><br>
        セント換算：${sign}${cents.toFixed(1)} セント<br>
        A4=440Hz換算：約 ${shiftedHz.toFixed(2)} Hz<br>
        440Hzとの差：${hzSign}${diffHz.toFixed(2)} Hz<br>
        周波数変化率：${percentSign}${percent.toFixed(2)}%<br>
        目安：${getPracticalLabel(semitones)}
    `;
}

semitonesInput.addEventListener("input", updatePitchInfo);

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

        setStatus("高品質変換中...\\nRubber Band R3モードで移調しています。", 65);

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
        downloadLink.download = baseName + "_shift_" + semitones + "_hq.wav";
        downloadLink.style.display = "block";

        setStatus("変換完了しました。\\n下のプレイヤーで再生確認できます。\\n必要ならWAVをダウンロードしてください。", 100);

    }catch(error){
        setStatus("エラー：\\n" + error.message, 0);
    }finally{
        convertBtn.disabled = false;
        convertBtn.textContent = "高品質変換する";
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
        output_path = OUTPUT_DIR / f"{uid}_shifted_hq.wav"

        file.save(input_path)

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-ar", "44100",
            "-ac", "2",
            "-acodec", "pcm_s16le",
            str(wav_path)
        ], check=True)

        subprocess.run([
            "rubberband",
            "-3",
            "-p", semitones,
            str(wav_path),
            str(output_path)
        ], check=True)

        return send_file(output_path, mimetype="audio/wav", as_attachment=False)

    except subprocess.CalledProcessError:
        return jsonify({"error": "音声変換処理に失敗しました。音源形式または移調量を確認してください。"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
