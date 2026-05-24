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

<link rel="icon" type="image/png" href="/static/icon.png">
<link rel="apple-touch-icon" href="/static/icon.png">

<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Outfit:wght@300;400;500;600;700&display=swap');

:root{
    --bg:#05060d;
    --panel:#0d1326;
    --panel-light:#121a35;
    --line:#1e2a4d;
    --cyan:#22d3ee;
    --cyan-bright:#5eead4;
    --blue:#3b82f6;
    --green:#22c55e;
    --green-bright:#86efac;
    --text:#eaf2ff;
    --dim:#7d8bb5;
    --dimmer:#4a5680;
}

*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}

body{
    font-family:'Outfit',system-ui,sans-serif;
    background:var(--bg);
    color:var(--text);
    min-height:100vh;
    display:flex;
    justify-content:center;
    align-items:flex-start;
    position:relative;
    padding:30px 16px;
}
body::before{
    content:'';
    position:fixed;inset:0;
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(34,211,238,0.15), transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 20%, rgba(59,130,246,0.12), transparent 55%),
        radial-gradient(ellipse 70% 60% at 10% 90%, rgba(94,234,212,0.08), transparent 60%);
    pointer-events:none;z-index:0;
}
body::after{
    content:'';
    position:fixed;inset:0;
    background-image:
        linear-gradient(rgba(34,211,238,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(34,211,238,0.025) 1px, transparent 1px);
    background-size:44px 44px;
    mask-image:radial-gradient(ellipse 100% 80% at 50% 30%, #000 30%, transparent 80%);
    -webkit-mask-image:radial-gradient(ellipse 100% 80% at 50% 30%, #000 30%, transparent 80%);
    pointer-events:none;z-index:0;
}

.container{
    position:relative;z-index:1;
    width:100%;
    max-width:620px;
    background:linear-gradient(180deg, rgba(18,26,53,.7), rgba(13,19,38,.85));
    border:1px solid var(--line);
    padding:26px;
    border-radius:22px;
    backdrop-filter:blur(12px);
    -webkit-backdrop-filter:blur(12px);
    box-shadow:0 8px 40px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.04);
    animation:fadeUp .6s cubic-bezier(.16,1,.3,1) both;
}

.app-header{
    display:flex;
    align-items:center;
    gap:14px;
    margin-bottom:14px;
}
.app-icon{
    width:58px;height:58px;
    border-radius:15px;
    object-fit:cover;
    box-shadow:0 0 22px rgba(34,211,238,.45);
}
h1{
    font-family:'Orbitron',sans-serif;
    font-weight:900;
    font-size:28px;
    letter-spacing:.5px;
    background:linear-gradient(180deg,#eaf6ff 0%, var(--cyan) 75%, var(--blue) 115%);
    -webkit-background-clip:text;background-clip:text;
    -webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 16px rgba(34,211,238,.3));
    line-height:1.1;
}
.small{
    color:var(--dim);
    font-size:13px;
    line-height:1.7;
}
.lead{
    margin:6px 0 4px;
    font-size:15px;
    color:var(--text);
}

/* ── ファイル選択（押せる感を強調）── */
.file-field{
    margin-top:16px;
}
.file-btn{
    display:flex;
    align-items:center;
    gap:14px;
    width:100%;
    padding:18px;
    border-radius:16px;
    border:2px dashed var(--line);
    background:rgba(34,211,238,.02);
    cursor:pointer;
    transition:all .25s ease;
}
.file-btn:hover{
    border-color:var(--cyan);
    background:rgba(34,211,238,.06);
    transform:translateY(-2px);
    box-shadow:0 8px 24px rgba(34,211,238,.18);
}
.file-btn:active{transform:translateY(0) scale(.99)}
.file-btn.has-file{
    border-style:solid;
    border-color:var(--cyan);
    background:rgba(34,211,238,.07);
}
.file-icon{
    flex:0 0 auto;
    width:46px;height:46px;
    display:grid;place-items:center;
    border-radius:13px;
    background:linear-gradient(135deg, var(--cyan), var(--blue));
    box-shadow:0 4px 16px rgba(34,211,238,.4);
    transition:transform .25s;
}
.file-btn:hover .file-icon{transform:scale(1.08) rotate(-3deg)}
.file-icon svg{width:24px;height:24px}
.file-text{flex:1;min-width:0}
.file-title{font-size:15px;font-weight:600;color:var(--text)}
.file-sub{font-size:12px;color:var(--dim);margin-top:2px;word-break:break-all}
#audio{display:none}

/* ── スライダーボックス ── */
.slider-box{
    margin-top:16px;
    padding:18px;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:16px;
}
.field-label{
    font-size:12px;color:var(--dim);
    letter-spacing:1px;text-transform:uppercase;
    font-weight:500;
}
#semitones{
    width:100%;
    margin-top:10px;
    padding:14px;
    border-radius:12px;
    border:1.5px solid var(--line);
    background:var(--panel-light);
    color:var(--text);
    font-size:18px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    text-align:center;
    box-sizing:border-box;
    transition:border-color .2s;
}
#semitones:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,.15)}

input[type="range"]{
    width:100%;
    margin-top:16px;
    -webkit-appearance:none;appearance:none;
    height:8px;border-radius:999px;
    background:linear-gradient(90deg, var(--blue), var(--cyan));
    outline:none;cursor:pointer;
    box-shadow:0 0 12px rgba(34,211,238,.3);
}
input[type="range"]::-webkit-slider-thumb{
    -webkit-appearance:none;appearance:none;
    width:26px;height:26px;border-radius:50%;
    background:radial-gradient(circle at 35% 35%, #fff, var(--cyan));
    border:2px solid #fff;
    box-shadow:0 0 14px var(--cyan), 0 2px 6px rgba(0,0,0,.4);
    cursor:pointer;
}
input[type="range"]::-moz-range-thumb{
    width:26px;height:26px;border-radius:50%;
    background:radial-gradient(circle at 35% 35%, #fff, var(--cyan));
    border:2px solid #fff;
    box-shadow:0 0 14px var(--cyan);
    cursor:pointer;
}

.slider-label{
    display:flex;
    justify-content:space-between;
    color:var(--dim);
    font-size:12px;
    margin-top:10px;
    font-family:'Orbitron',sans-serif;
}
.current-value{
    margin-top:14px;
    font-family:'Orbitron',sans-serif;
    font-size:20px;
    font-weight:700;
    color:var(--green-bright);
    text-align:center;
    filter:drop-shadow(0 0 10px rgba(134,239,172,.3));
}

.quick-buttons{
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    gap:8px;
    margin-top:16px;
}
.quick-buttons button{
    padding:12px 4px;
    font-size:13px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    background:var(--panel-light);
    color:var(--cyan);
    border:1.5px solid var(--line);
    border-radius:10px;
    cursor:pointer;
    transition:all .15s;
}
.quick-buttons button:hover{
    border-color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 14px rgba(34,211,238,.22);
}
.quick-buttons button:active{transform:scale(.94)}

/* ── 形式選択 ── */
.format-box{
    margin-top:16px;
    padding:18px;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:16px;
}
.format-buttons{
    display:grid;
    grid-template-columns:repeat(2, 1fr);
    gap:8px;
    margin-top:10px;
}
.fmt-btn{
    padding:14px;
    font-size:14px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    background:var(--panel-light);
    color:var(--dim);
    border:1.5px solid var(--line);
    border-radius:10px;
    cursor:pointer;
    transition:all .18s;
}
.fmt-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.fmt-btn:active{transform:scale(.97)}
.fmt-btn.active{
    border-color:var(--cyan);
    color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 14px rgba(34,211,238,.22);
}
.bitrate-buttons{
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:8px;
    margin-top:10px;
}
.br-btn{
    padding:10px 4px;
    font-size:14px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    background:var(--panel-light);
    color:var(--dim);
    border:1.5px solid var(--line);
    border-radius:10px;
    cursor:pointer;
    transition:all .18s;
    line-height:1.4;
}
.br-btn span{font-size:10px;font-weight:400;opacity:.8}
.br-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.br-btn:active{transform:scale(.95)}
.br-btn.active{
    border-color:var(--cyan);
    color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 14px rgba(34,211,238,.2);
}

/* ── 情報ボックス ── */
.info{
    margin-top:16px;
    padding:16px;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:14px;
    color:#cdd6ee;
    font-size:14px;
    line-height:1.8;
}
.info strong{color:var(--cyan-bright)}
.example{
    margin-top:14px;
    padding:14px;
    background:rgba(5,6,13,.6);
    border:1px solid var(--line);
    border-radius:12px;
    color:#cdd6ee;
    font-size:13px;
    line-height:1.8;
}
.example strong{color:var(--text)}
.badge{
    display:inline-block;
    padding:5px 10px;
    margin:4px 4px 0 0;
    border-radius:999px;
    background:var(--panel-light);
    border:1px solid var(--line);
    color:var(--cyan);
    font-size:12px;
    font-family:'Orbitron',sans-serif;
}

/* ── 変換ボタン ── */
#convertBtn{
    width:100%;
    margin-top:18px;
    padding:17px;
    border:0;border-radius:14px;
    font-family:'Orbitron',sans-serif;
    font-size:16px;font-weight:700;letter-spacing:1px;
    background:linear-gradient(135deg, var(--cyan) 0%, var(--blue) 100%);
    color:#04101f;
    cursor:pointer;
    box-shadow:0 6px 24px rgba(34,211,238,.35);
    transition:all .2s;
}
#convertBtn:hover:not(:disabled){
    transform:translateY(-2px);
    box-shadow:0 10px 32px rgba(34,211,238,.5);
}
#convertBtn:active:not(:disabled){transform:translateY(0) scale(.99)}
#convertBtn:disabled{opacity:.5;cursor:not-allowed}

.progress{
    margin-top:14px;
    height:10px;
    background:var(--bg);
    border:1px solid var(--line);
    border-radius:999px;
    overflow:hidden;
}
.bar{
    width:0%;height:100%;
    background:linear-gradient(90deg, var(--blue), var(--cyan), var(--cyan-bright));
    box-shadow:0 0 12px var(--cyan);
    transition:width .3s;
}
.status{
    margin-top:14px;
    padding:14px;
    border-radius:12px;
    background:var(--panel);
    border:1px solid var(--line);
    color:#cdd6ee;
    line-height:1.7;
    white-space:pre-wrap;
    font-size:14px;
}
audio{
    width:100%;
    margin-top:16px;
    border-radius:12px;
}
a#downloadLink{
    display:block;
    margin-top:14px;
    padding:15px;
    text-align:center;
    border-radius:14px;
    border:1.5px solid var(--cyan);
    color:var(--cyan);
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    text-decoration:none;
    transition:all .2s;
}
a#downloadLink:hover{
    background:rgba(34,211,238,.1);
    box-shadow:0 0 18px rgba(34,211,238,.25);
}

@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div class="container">

<div class="app-header">
    <img class="app-icon" src="/static/icon.png" alt="AudioShift icon">
    <div>
        <h1>AudioShift HQ</h1>
        <p class="small">高品質移調ツール</p>
    </div>
</div>

<p class="lead">音源を選択し、移調量を半音単位で入力してください。</p>

<p class="small">
対応目安：MP3 / WAV / M4A / AAC / FLAC / OGG / WebM<br>
例：1 = 半音上げ / -1 = 半音下げ / 2 = 全音上げ / 0.01 = 1セント微調整
</p>

<!-- ファイル選択（押せる感を強調したボタン） -->
<div class="file-field">
    <label class="file-btn" id="fileBtn" for="audio">
        <span class="file-icon">
            <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="#04101f" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M5 16v3a1 1 0 001 1h12a1 1 0 001-1v-3" stroke="#04101f" stroke-width="2.2" stroke-linecap="round"/>
            </svg>
        </span>
        <span class="file-text">
            <span class="file-title" id="fileTitle">タップして音源を選択</span>
            <span class="file-sub" id="fileSub">MP3 / WAV / M4A / AAC / FLAC / OGG / WebM</span>
        </span>
    </label>
    <input id="audio" type="file" accept=".mp3,.wav,.m4a,.aac,.flac,.ogg,.webm,audio/*">
</div>

<div class="slider-box">
    <label class="field-label">移調量 / Transpose</label>

    <input id="semitones" type="number" step="0.01" min="-12" max="12" value="0" placeholder="例：2 / -3 / 0.01 / -0.25">

    <input id="semitonesSlider" type="range" min="-12" max="12" step="0.01" value="0">

    <div class="slider-label">
        <span>-12</span>
        <span>0</span>
        <span>+12</span>
    </div>

    <div id="currentValue" class="current-value">現在：0.00 半音 / 0 セント</div>

    <div class="quick-buttons">
        <button type="button" onclick="adjustPitch(-1)">-1</button>
        <button type="button" onclick="adjustPitch(-0.1)">-0.1</button>
        <button type="button" onclick="setPitch(0)">0</button>
        <button type="button" onclick="adjustPitch(0.1)">+0.1</button>
        <button type="button" onclick="adjustPitch(1)">+1</button>
        <button type="button" onclick="adjustPitch(2)">+2</button>
        <button type="button" onclick="adjustPitch(-0.01)">-0.01</button>
        <button type="button" onclick="adjustPitch(0.01)">+0.01</button>
    </div>
</div>

<div id="pitchInfo" class="info">
<strong>移調量の説明</strong><br>
1 = 半音 = 100セント<br>
0.1 = 10セント<br>
0.01 = 1セント<br><br>
A4=440Hzを基準にすると、入力した移調量が何Hz相当になるかをここに表示します。
</div>

<div class="example">
<strong>目安</strong><br>
<span class="badge">0.01 = 1セント</span>
<span class="badge">0.1 = 10セント</span>
<span class="badge">0.5 = 半音の半分</span>
<span class="badge">1 = 半音</span>
<span class="badge">2 = 全音</span>
<br><br>
A4=440Hzの場合：<br>
+0.01 → 約440.25Hz<br>
+0.1 → 約442.55Hz<br>
+0.2 → 約445.11Hz<br>
+1 → 約466.16Hz
</div>

<div class="format-box">
    <label class="field-label">保存形式 / Format</label>
    <div class="format-buttons">
        <button type="button" id="fmtWav" class="fmt-btn active" onclick="setFormat('wav')">WAV（無劣化）</button>
        <button type="button" id="fmtMp3" class="fmt-btn" onclick="setFormat('mp3')">MP3（軽量）</button>
    </div>
    <div id="bitrateRow" style="display:none">
        <label class="field-label" style="margin-top:14px;display:block">MP3音質 / Bitrate</label>
        <div class="bitrate-buttons">
            <button type="button" id="br320" class="br-btn active" onclick="setBitrate('320')">320k<br><span>高音質</span></button>
            <button type="button" id="br192" class="br-btn" onclick="setBitrate('192')">192k<br><span>標準</span></button>
            <button type="button" id="br128" class="br-btn" onclick="setBitrate('128')">128k<br><span>軽量</span></button>
        </div>
    </div>
</div>

<button id="convertBtn">⚡ 高品質変換する</button>

<div class="progress"><div id="bar" class="bar"></div></div>
<div id="status" class="status">音源を選択してください。</div>

<audio id="player" controls style="display:none;"></audio>
<a id="downloadLink" style="display:none;" download>⬇ 変換後ファイルをダウンロード</a>
</div>

<script>
const audioInput = document.getElementById("audio");
const semitonesInput = document.getElementById("semitones");
const semitonesSlider = document.getElementById("semitonesSlider");
const currentValue = document.getElementById("currentValue");
const convertBtn = document.getElementById("convertBtn");
const statusBox = document.getElementById("status");
const bar = document.getElementById("bar");
const player = document.getElementById("player");
const downloadLink = document.getElementById("downloadLink");
const pitchInfo = document.getElementById("pitchInfo");
const fileBtn = document.getElementById("fileBtn");
const fileTitle = document.getElementById("fileTitle");
const fileSub = document.getElementById("fileSub");

let resultUrl = null;
let outFormat = "wav";
let mp3Bitrate = "320";

function setFormat(fmt){
    outFormat = fmt;
    document.getElementById("fmtWav").classList.toggle("active", fmt === "wav");
    document.getElementById("fmtMp3").classList.toggle("active", fmt === "mp3");
    document.getElementById("bitrateRow").style.display = (fmt === "mp3") ? "block" : "none";
}

function setBitrate(br){
    mp3Bitrate = br;
    document.getElementById("br320").classList.toggle("active", br === "320");
    document.getElementById("br192").classList.toggle("active", br === "192");
    document.getElementById("br128").classList.toggle("active", br === "128");
}

function setStatus(text, percent){
    statusBox.textContent = text;
    bar.style.width = percent + "%";
}

function clampPitch(value){
    const num = Number(value);
    if(Number.isNaN(num)){
        return 0;
    }
    return Math.max(-12, Math.min(12, num));
}

function formatPitch(value){
    return Number(value).toFixed(2);
}

function setPitch(value){
    const fixed = formatPitch(clampPitch(value));
    semitonesInput.value = fixed;
    semitonesSlider.value = fixed;
    updatePitchInfo();
}

function adjustPitch(amount){
    const current = clampPitch(semitonesInput.value);
    setPitch(current + amount);
}

function getPracticalLabel(semitones){
    const abs = Math.abs(semitones);

    if(abs === 0){
        return "変化なし";
    }
    if(abs < 0.03){
        return "1〜2セント程度。ごく小さいチューニング補正";
    }
    if(abs < 0.1){
        return "微細なチューニング補正";
    }
    if(abs < 0.3){
        return "微調整。音源のピッチ補正向き";
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
            0.01 = 1セント<br><br>
            A4=440Hzを基準にすると、入力した移調量が何Hz相当になるかをここに表示します。
        `;
        currentValue.textContent = "現在：未入力";
        return;
    }

    const semitones = Number(raw);

    if(Number.isNaN(semitones)){
        pitchInfo.innerHTML = "<strong>数値を入力してください。</strong>";
        currentValue.textContent = "現在：数値エラー";
        return;
    }

    const safeSemitones = clampPitch(semitones);
    const cents = safeSemitones * 100;
    const baseHz = 440;
    const shiftedHz = baseHz * Math.pow(2, safeSemitones / 12);
    const diffHz = shiftedHz - baseHz;
    const percent = ((shiftedHz / baseHz) - 1) * 100;

    const sign = safeSemitones > 0 ? "+" : "";
    const hzSign = diffHz > 0 ? "+" : "";
    const percentSign = percent > 0 ? "+" : "";

    currentValue.textContent = `現在：${sign}${safeSemitones.toFixed(2)} 半音 / ${sign}${cents.toFixed(0)} セント`;

    pitchInfo.innerHTML = `
        <strong>入力値：${sign}${safeSemitones.toFixed(2)} 半音</strong><br>
        セント換算：${sign}${cents.toFixed(1)} セント<br>
        A4=440Hz換算：約 ${shiftedHz.toFixed(2)} Hz<br>
        440Hzとの差：${hzSign}${diffHz.toFixed(2)} Hz<br>
        周波数変化率：${percentSign}${percent.toFixed(2)}%<br>
        目安：${getPracticalLabel(safeSemitones)}
    `;
}

// ファイル選択時の表示更新
audioInput.addEventListener("change", () => {
    const f = audioInput.files[0];
    if(f){
        fileBtn.classList.add("has-file");
        fileTitle.textContent = "🎵 " + f.name;
        fileSub.textContent = "別のファイルを選ぶにはここをタップ";
    }else{
        fileBtn.classList.remove("has-file");
        fileTitle.textContent = "タップして音源を選択";
        fileSub.textContent = "MP3 / WAV / M4A / AAC / FLAC / OGG / WebM";
    }
});

semitonesInput.addEventListener("input", () => {
    const value = clampPitch(semitonesInput.value);
    semitonesSlider.value = value;
    updatePitchInfo();
});

semitonesInput.addEventListener("blur", () => {
    setPitch(semitonesInput.value);
});

semitonesSlider.addEventListener("input", () => {
    semitonesInput.value = formatPitch(semitonesSlider.value);
    updatePitchInfo();
});

updatePitchInfo();

convertBtn.addEventListener("click", async () => {
    const file = audioInput.files[0];
    const semitones = semitonesInput.value;

    if(!file){
        setStatus("音源ファイルを選択してください。MP3 / WAV / M4A などに対応しています。", 0);
        return;
    }

    if(semitones === ""){
        setStatus("移調量を入力してください。例：2 / -3 / -0.01", 0);
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
    formData.append("format", outFormat);
    formData.append("bitrate", mp3Bitrate);

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
        const ext = (outFormat === "mp3") ? "mp3" : "wav";
        downloadLink.href = resultUrl;
        downloadLink.download = baseName + "_shift_" + semitones + "_hq." + ext;
        downloadLink.textContent = "⬇ 変換後" + ext.toUpperCase() + "をダウンロード";
        downloadLink.style.display = "block";

        setStatus("変換完了しました。\\n下のプレイヤーで再生確認できます。\\n必要なら" + ext.toUpperCase() + "をダウンロードしてください。", 100);

    }catch(error){
        setStatus("エラー：\\n" + error.message, 0);
    }finally{
        convertBtn.disabled = false;
        convertBtn.textContent = "⚡ 高品質変換する";
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
        out_format = request.form.get("format", "wav")
        mp3_bitrate = request.form.get("bitrate", "320")

        try:
            semitone_value = float(semitones)
        except ValueError:
            return jsonify({"error": "移調量が数値ではありません。"}), 400

        if semitone_value < -12 or semitone_value > 12:
            return jsonify({"error": "移調量は -12〜+12 の範囲で入力してください。"}), 400

        # 形式・ビットレートの安全確認
        if out_format not in ("wav", "mp3"):
            out_format = "wav"
        if mp3_bitrate not in ("128", "192", "320"):
            mp3_bitrate = "320"

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
            "-p", str(semitone_value),
            str(wav_path),
            str(output_path)
        ], check=True)

        # MP3が指定された場合は、移調後WAVをMP3に変換
        if out_format == "mp3":
            mp3_path = OUTPUT_DIR / f"{uid}_shifted_hq.mp3"
            subprocess.run([
                "ffmpeg",
                "-y",
                "-i", str(output_path),
                "-vn",
                "-acodec", "libmp3lame",
                "-b:a", f"{mp3_bitrate}k",
                str(mp3_path)
            ], check=True)
            return send_file(mp3_path, mimetype="audio/mpeg", as_attachment=False)

        return send_file(output_path, mimetype="audio/wav", as_attachment=False)

    except subprocess.CalledProcessError:
        return jsonify({"error": "音声変換処理に失敗しました。音源形式または移調量を確認してください。"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
