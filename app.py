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

/* ── 波形・範囲選択 ── */
.waveform-box{
    margin-top:16px;
    padding:18px;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:16px;
}
.range-mode{
    display:grid;
    grid-template-columns:repeat(2, 1fr);
    gap:8px;
    margin-top:10px;
}
.range-mode-btn{
    padding:12px;
    font-family:'Orbitron',sans-serif;
    font-size:13px;
    font-weight:700;
    background:var(--panel-light);
    color:var(--dim);
    border:1.5px solid var(--line);
    border-radius:10px;
    cursor:pointer;
    transition:all .18s;
}
.range-mode-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.range-mode-btn:active{transform:scale(.97)}
.range-mode-btn.active{
    border-color:var(--cyan);
    color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 12px rgba(34,211,238,.2);
}
.waveform-wrap{
    position:relative;
    margin-top:14px;
    height:104px;
    background:var(--bg);
    border:1px solid var(--line);
    border-radius:10px;
    overflow:hidden;
    touch-action:none;
    user-select:none;
}
#waveformCanvas{
    width:100%;
    height:100%;
    display:block;
}
.wave-sel{
    position:absolute;
    top:0;
    height:100%;
    background:rgba(34,211,238,.18);
    border-left:2px solid var(--cyan);
    border-right:2px solid var(--cyan);
    pointer-events:none;
    left:0;
    width:100%;
}
.wave-playhead{
    position:absolute;
    top:0;
    width:2px;
    height:100%;
    background:#fbbf24;
    box-shadow:0 0 6px #fbbf24;
    pointer-events:none;
    left:0;
    z-index:4;
    display:none;
}
.wave-player-row{
    display:flex;
    align-items:center;
    gap:8px;
    margin-top:12px;
    flex-wrap:wrap;
}
.wave-play-btn{
    padding:9px 14px;
    border:1.5px solid var(--cyan);
    border-radius:8px;
    background:rgba(34,211,238,.1);
    color:var(--cyan);
    font-family:'Outfit',sans-serif;
    font-size:13px;
    font-weight:600;
    cursor:pointer;
    transition:all .18s;
}
.wave-play-btn:hover{background:rgba(34,211,238,.2)}
.wave-play-btn:active{transform:scale(.96)}
.wave-play-time{
    font-family:'Space Mono','Orbitron',monospace;
    font-size:14px;
    color:var(--cyan-bright);
    margin-left:auto;
}
.set-here-btn{
    width:100%;
    margin-top:6px;
    padding:7px 4px;
    border:1px solid var(--line);
    border-radius:7px;
    background:var(--panel-light);
    color:var(--dim);
    font-family:'Outfit',sans-serif;
    font-size:11px;
    cursor:pointer;
    transition:all .18s;
}
.set-here-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.set-here-btn:active{transform:scale(.97)}
.extract-audio-btn{
    width:100%;
    margin-top:12px;
    padding:12px;
    border:1.5px solid var(--green);
    border-radius:10px;
    background:rgba(34,197,94,.1);
    color:var(--green-bright);
    font-family:'Outfit',sans-serif;
    font-size:13px;
    font-weight:600;
    cursor:pointer;
    transition:all .18s;
}
.extract-audio-btn:hover{background:rgba(34,197,94,.2);box-shadow:0 0 14px rgba(34,197,94,.25)}
.extract-audio-btn:active{transform:scale(.98)}
.extract-audio-btn:disabled{opacity:.5;cursor:not-allowed}
.mov-capture-btn{
    width:100%;
    padding:13px;
    border:1.5px solid #fbbf24;
    border-radius:10px;
    background:rgba(251,191,36,.1);
    color:#fbbf24;
    font-family:'Outfit',sans-serif;
    font-size:13px;
    font-weight:700;
    cursor:pointer;
    transition:all .18s;
}
.mov-capture-btn:hover{background:rgba(251,191,36,.2)}
.mov-capture-btn:active{transform:scale(.98)}
.mov-capture-btn:disabled{opacity:.5;cursor:not-allowed}
.mov-capture-btn-alt{
    margin-top:8px;
    border-color:var(--line);
    background:var(--panel-light);
    color:var(--dim);
}
.mov-capture-btn-alt:hover{border-color:#fbbf24;color:#fbbf24;background:rgba(251,191,36,.08)}
/* ── MOVキャプチャ進行表示 ── */
.mov-progress-wrap{
    height:14px;
    background:var(--panel-light);
    border:1px solid var(--line);
    border-radius:999px;
    overflow:hidden;
}
.mov-progress-bar{
    height:100%;
    background:linear-gradient(90deg, var(--cyan), var(--blue));
    border-radius:999px;
    transition:width .4s linear;
    box-shadow:0 0 8px rgba(34,211,238,.4);
}
.mov-stop-btn{
    flex:2;
    padding:12px;
    border:2px solid #ef4444;
    border-radius:10px;
    background:rgba(239,68,68,.12);
    color:#ef4444;
    font-family:'Outfit',sans-serif;
    font-size:14px;
    font-weight:700;
    cursor:pointer;
    transition:all .18s;
}
.mov-stop-btn:hover{background:rgba(239,68,68,.25);box-shadow:0 0 14px rgba(239,68,68,.3)}
.mov-stop-btn:active{transform:scale(.97)}
.mov-capture-status{
    margin-top:8px;
    padding:10px;
    background:rgba(5,6,13,.5);
    border:1px solid var(--line);
    border-radius:8px;
    font-size:13px;
    color:var(--cyan-bright);
    text-align:center;
    font-family:'Space Mono',monospace;
}
.mov-sub-btn{
    flex:1;
    padding:10px;
    border:1.5px solid var(--line);
    border-radius:8px;
    background:var(--panel-light);
    color:var(--text);
    font-family:'Outfit',sans-serif;
    font-size:13px;
    font-weight:600;
    cursor:pointer;
    transition:all .18s;
}
.mov-sub-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.mov-sub-btn:active{transform:scale(.97)}
.wave-handle{
    position:absolute;
    top:0;
    width:18px;
    height:100%;
    cursor:ew-resize;
    z-index:3;
    display:flex;
    align-items:center;
    justify-content:center;
}
.wave-handle::after{
    content:'';
    width:4px;
    height:40%;
    background:var(--cyan);
    border-radius:2px;
    box-shadow:0 0 8px var(--cyan);
}
.wave-handle-a{left:0;transform:translateX(-9px)}
.wave-handle-b{right:0;transform:translateX(9px)}
.range-time-row{
    display:flex;
    gap:10px;
    margin-top:12px;
}
.range-time-col{flex:1}
.range-time-input{
    width:100%;
    padding:10px;
    border-radius:8px;
    border:1.5px solid var(--line);
    background:var(--panel-light);
    color:var(--text);
    font-family:'Space Mono','Orbitron',monospace;
    font-size:15px;
    text-align:center;
    box-sizing:border-box;
}
.range-time-input:focus{outline:none;border-color:var(--cyan)}
.range-info{
    margin-top:12px;
    text-align:center;
    font-size:13px;
    color:var(--cyan-bright);
    font-family:'Space Mono',monospace;
}

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

/* ── 基準ピッチ合わせ ── */
.pitch-tune-box{
    margin-top:16px;
    padding:18px;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:16px;
}
.tune-row{
    display:flex;
    align-items:flex-end;
    gap:10px;
    margin-top:14px;
}
.tune-col{flex:1}
.tune-label{
    display:block;
    font-size:11px;
    color:var(--dim);
    margin-bottom:6px;
    text-align:center;
}
.tune-select{
    width:100%;
    padding:12px 8px;
    border-radius:10px;
    border:1.5px solid var(--line);
    background:var(--panel-light);
    color:var(--text);
    font-size:15px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    text-align:center;
    cursor:pointer;
}
.tune-select:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,.15)}
.tune-arrow{
    flex:0 0 auto;
    font-size:20px;
    color:var(--cyan);
    padding-bottom:10px;
}
.tune-preview{
    margin-top:14px;
    text-align:center;
    font-family:'Orbitron',sans-serif;
    font-size:14px;
    font-weight:700;
    color:var(--cyan-bright);
}
.tune-apply-btn{
    width:100%;
    margin-top:12px;
    padding:13px;
    border:1.5px solid var(--cyan);
    border-radius:12px;
    background:rgba(34,211,238,.1);
    color:var(--cyan);
    font-family:'Orbitron',sans-serif;
    font-size:14px;
    font-weight:700;
    cursor:pointer;
    transition:all .18s;
}
.tune-apply-btn:hover{
    background:rgba(34,211,238,.2);
    box-shadow:0 0 16px rgba(34,211,238,.3);
}
.tune-apply-btn:active{transform:scale(.98)}

/* ── 自動ピッチ判定 ── */
.detect-btn{
    width:100%;
    margin-top:14px;
    padding:12px;
    border:1.5px dashed var(--line);
    border-radius:10px;
    background:transparent;
    color:var(--dim);
    font-family:'Outfit',sans-serif;
    font-size:13px;
    font-weight:600;
    cursor:pointer;
    transition:all .18s;
}
.detect-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.detect-btn:active{transform:scale(.98)}
.detect-btn:disabled{opacity:.5;cursor:not-allowed}
.detect-result{
    margin-top:10px;
    padding:12px;
    background:rgba(5,6,13,.5);
    border:1px solid var(--line);
    border-radius:10px;
    font-size:13px;
    line-height:1.7;
    color:#cdd6ee;
}
.detect-result .big{
    font-family:'Orbitron',sans-serif;
    font-size:18px;
    font-weight:700;
    color:var(--cyan-bright);
}
.detect-result .note{
    font-size:11px;
    color:var(--dim);
    margin-top:4px;
}
.detect-apply{
    display:block;
    width:100%;
    margin-top:10px;
    padding:10px;
    border:1.5px solid var(--cyan);
    border-radius:8px;
    background:rgba(34,211,238,.1);
    color:var(--cyan);
    font-family:'Outfit',sans-serif;
    font-size:12px;
    font-weight:600;
    cursor:pointer;
    transition:all .18s;
}
.detect-apply:hover{background:rgba(34,211,238,.2)}
.detect-apply:active{transform:scale(.98)}

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

/* ── 通知設定 ── */
.notify-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-top:10px;
}
.notify-label{
    font-size:14px;
    color:var(--text);
    font-weight:500;
}
.notify-toggle{
    display:flex;
    gap:6px;
}
.ntf-btn{
    padding:8px 18px;
    font-size:13px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    background:var(--panel-light);
    color:var(--dim);
    border:1.5px solid var(--line);
    border-radius:8px;
    cursor:pointer;
    transition:all .18s;
}
.ntf-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.ntf-btn:active{transform:scale(.95)}
.ntf-btn.active{
    border-color:var(--cyan);
    color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 12px rgba(34,211,238,.2);
}
.sound-type-buttons{
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    gap:8px;
    margin-top:10px;
}
.snd-btn{
    padding:10px 4px;
    font-size:13px;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    background:var(--panel-light);
    color:var(--dim);
    border:1.5px solid var(--line);
    border-radius:10px;
    cursor:pointer;
    transition:all .18s;
    line-height:1.5;
}
.snd-btn span{font-size:10px;font-weight:400;opacity:.7}
.snd-btn:hover{border-color:var(--cyan);color:var(--cyan)}
.snd-btn:active{transform:scale(.95)}
.snd-btn.active{
    border-color:var(--cyan);
    color:var(--cyan);
    background:rgba(34,211,238,.12);
    box-shadow:0 0 14px rgba(34,211,238,.2);
}

/* ── 変換時間の目安 ── */
.time-guide{
    margin-top:16px;
    padding:14px 16px;
    background:rgba(34,211,238,.06);
    border:1px solid var(--line);
    border-left:3px solid var(--cyan);
    border-radius:12px;
    color:#cdd6ee;
    font-size:13px;
    line-height:1.8;
}
.time-guide strong{color:var(--cyan-bright)}
.warn-note{
    display:block;
    margin-top:8px;
    padding-top:8px;
    border-top:1px solid var(--line);
    color:#fbbf24;
    font-weight:500;
    line-height:1.7;
}
.len-note{
    display:block;
    margin-top:8px;
    color:var(--cyan-bright);
    line-height:1.7;
}
.len-note strong{color:var(--cyan-bright)}

/* ── 変換所要時間の結果表示 ── */
.elapsed-result{
    margin-top:14px;
    padding:16px;
    background:rgba(34,197,94,.08);
    border:1px solid rgba(34,197,94,.35);
    border-left:3px solid var(--green);
    border-radius:12px;
    color:var(--green-bright);
    font-size:15px;
    line-height:1.7;
    text-align:center;
}
.elapsed-result strong{color:var(--green-bright)}

/* ── 完了バナー（画面上部に固定）── */
.done-banner{
    position:fixed;
    top:0;
    left:0;
    right:0;
    z-index:9999;
    padding:16px;
    text-align:center;
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    font-size:16px;
    color:#04101f;
    background:linear-gradient(135deg, var(--green-bright), var(--green));
    box-shadow:0 4px 24px rgba(34,197,94,.5);
    cursor:pointer;
    animation:bannerDrop .5s cubic-bezier(.16,1,.3,1), bannerPulse 1.5s ease-in-out infinite .5s;
}
@keyframes bannerDrop{from{transform:translateY(-100%)}to{transform:translateY(0)}}
@keyframes bannerPulse{0%,100%{box-shadow:0 4px 24px rgba(34,197,94,.5)}50%{box-shadow:0 4px 36px rgba(34,197,94,.85)}}

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

<div id="doneBanner" class="done-banner" style="display:none;" onclick="hideDoneBanner()">
    ✅ 変換が完了しました！　<span style="opacity:.8;font-size:13px">タップで閉じる</span>
</div>

<div class="app-header">
    <img class="app-icon" src="/static/icon.png" alt="AudioShift icon">
    <div>
        <h1>AudioShift HQ</h1>
        <p class="small">高品質移調ツール</p>
    </div>
</div>

<p class="lead">音源または動画を選択し、移調量を半音単位で入力してください。</p>

<p class="small">
音声：MP3 / WAV / M4A / AAC / FLAC / OGG / WebM<br>
動画：MP4 / MOV / WebM / MKV / AVI（音声を自動で抽出して移調します）<br>
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
            <span class="file-sub" id="fileSub">音声・動画ファイル（動画は音声を抽出）</span>
        </span>
    </label>
    <input id="audio" type="file" accept=".mp3,.wav,.m4a,.aac,.flac,.ogg,.webm,.mp4,.mov,.mkv,.avi,.m4v,audio/*,video/*">
</div>

<div class="waveform-box" id="waveformBox" style="display:none;">
    <label class="field-label">✂️ 変換する範囲 / Range</label>
    <div class="range-mode">
        <button type="button" id="rangeFull" class="range-mode-btn active" onclick="setRangeMode('full')">曲全体</button>
        <button type="button" id="rangePart" class="range-mode-btn" onclick="setRangeMode('part')">範囲を選ぶ</button>
    </div>
    <div id="waveformArea" style="display:none;">
        <div class="waveform-wrap" id="waveformWrap">
            <canvas id="waveformCanvas"></canvas>
            <div class="wave-sel" id="waveSel"></div>
            <div class="wave-playhead" id="wavePlayhead"></div>
            <div class="wave-handle wave-handle-a" id="waveHandleA"></div>
            <div class="wave-handle wave-handle-b" id="waveHandleB"></div>
        </div>
        <div id="waveNoDecodeNote" style="display:none;font-size:11px;color:#fbbf24;line-height:1.6;margin-top:8px;padding:8px 10px;background:rgba(251,191,36,0.08);border-radius:8px;">
            ⚠️ この形式（MOVなど）は波形を表示できませんが、下の「再生」で位置を確認しながら範囲を選べます。変換は問題なくできます。
        </div>
        <div id="movCaptureArea" style="display:none;margin-top:10px;">
            <button type="button" id="movCaptureBtnFull" class="mov-capture-btn" onclick="startMovCapture(true)">🎬 最後まで取り込む（途中で止まらない）</button>
            <button type="button" id="movCaptureBtnStop" class="mov-capture-btn mov-capture-btn-alt" onclick="startMovCapture(false)">🎬 途中で止められる取り込み</button>

            <!-- 取り込み中の表示（ボタンを押したら出る） -->
            <div id="movCaptureRunning" style="display:none;margin-top:12px;">
                <!-- 進行状況（時間） -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span id="movCaptureLabel" style="font-size:13px;color:var(--cyan-bright);font-weight:600;">🎵 取り込み中...</span>
                    <span id="movCaptureTime" style="font-family:'Space Mono',monospace;font-size:13px;color:var(--cyan-bright);">0:00 / 0:00</span>
                </div>
                <!-- プログレスバー -->
                <div class="mov-progress-wrap">
                    <div id="movProgressBar" class="mov-progress-bar" style="width:0%;"></div>
                </div>
                <!-- 取り込み中のコントロール -->
                <div style="display:flex;gap:8px;margin-top:10px;">
                    <button type="button" id="movSoundToggle" class="mov-sub-btn" onclick="toggleCaptureSound()">🔇 無音</button>
                    <button type="button" id="movCaptureDone" class="mov-stop-btn" onclick="finishMovCapture()" style="display:none;">⏹ ここまでで確定</button>
                </div>
            </div>

            <div id="movCaptureStatus" class="mov-capture-status" style="display:none;margin-top:8px;"></div>
            <div style="font-size:11px;color:var(--dim);line-height:1.6;margin-top:8px;">
                ※サーバーには送らず、端末内で動画を再生しながら音声を取り込みます（通信量はかかりません）。<br>
                ※「最後まで取り込む」は途中で止まらず、誤操作の心配がありません。前半だけ欲しい時は「途中で止められる取り込み」を選んでください。<br>
                ※取り込み中に音量を変えても、取り込まれる音声には影響しません。<br>
                ⚠️ 取り込み中は、この画面を開いたままにしてください（他のアプリやタブに移ると止まることがあります）。
            </div>
        </div>
        <div class="wave-player-row">
            <button type="button" id="wavePlayBtn" class="wave-play-btn" onclick="toggleWavePlay()">▶ 再生</button>
            <button type="button" id="wavePlayRangeBtn" class="wave-play-btn" onclick="playSelectedRange()">▶ 選択範囲を試聴</button>
            <span id="wavePlayTime" class="wave-play-time">0:00</span>
        </div>
        <button type="button" id="extractAudioBtn" class="extract-audio-btn" onclick="extractAudioOnly()">🎵 この音声をWAVで保存（移調せず抽出）</button>
        <video id="wavePreviewAudio" playsinline style="display:none;width:1px;height:1px;"></video>
        <div class="range-time-row">
            <div class="range-time-col">
                <label class="tune-label">開始</label>
                <input type="text" id="rangeStartInput" class="range-time-input" value="0:00" onblur="onRangeTimeInput()">
                <button type="button" class="set-here-btn" onclick="setRangeFromPlayhead('a')">▶今の位置を開始に</button>
            </div>
            <div class="range-time-col">
                <label class="tune-label">終了</label>
                <input type="text" id="rangeEndInput" class="range-time-input" value="0:00" onblur="onRangeTimeInput()">
                <button type="button" class="set-here-btn" onclick="setRangeFromPlayhead('b')">▶今の位置を終了に</button>
            </div>
        </div>
        <div id="rangeInfo" class="range-info">選択範囲：全体</div>
    </div>
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

<div class="pitch-tune-box">
    <label class="field-label">🎯 基準ピッチ合わせ / Tuning</label>
    <div style="font-size:12px;color:var(--dim);line-height:1.6;margin-top:8px">
        曲の基準ピッチ（A=何Hzか）を「現在」に、合わせたいピッチを「目標」に選んで「適用」を押すと、必要な移調量が自動でセットされます。<br>
        例：455Hzの曲を440Hzにそろえる、442Hzの曲を440Hzにする、など。
    </div>
    <div class="tune-row">
        <div class="tune-col">
            <label class="tune-label">現在のピッチ</label>
            <select id="tuneFrom" class="tune-select"></select>
        </div>
        <div class="tune-arrow">→</div>
        <div class="tune-col">
            <label class="tune-label">目標のピッチ</label>
            <select id="tuneTo" class="tune-select"></select>
        </div>
    </div>

    <button type="button" id="detectBtn" class="detect-btn" onclick="detectPitch()">🔍 曲の基準ピッチを自動判定（参考）</button>
    <div id="detectResult" class="detect-result" style="display:none;"></div>

    <div id="tunePreview" class="tune-preview">必要な移調量：0.00 半音（0 セント）</div>
    <button type="button" id="tuneApplyBtn" class="tune-apply-btn" onclick="applyTuning()">この移調量を適用する</button>
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

<div class="format-box">
    <label class="field-label">完了通知 / Notification</label>
    <div class="notify-row">
        <span class="notify-label">🔔 通知音</span>
        <div class="notify-toggle">
            <button type="button" id="soundOn" class="ntf-btn active" onclick="setSound(true)">ON</button>
            <button type="button" id="soundOff" class="ntf-btn" onclick="setSound(false)">OFF</button>
        </div>
    </div>
    <div id="soundTypeRow" class="sound-type-buttons">
        <button type="button" id="snd_chime" class="snd-btn active" onclick="setSoundType('chime')">チャイム<br><span>♪ 試聴</span></button>
        <button type="button" id="snd_beep" class="snd-btn" onclick="setSoundType('beep')">ビープ<br><span>♪ 試聴</span></button>
        <button type="button" id="snd_bell" class="snd-btn" onclick="setSoundType('bell')">ベル<br><span>♪ 試聴</span></button>
        <button type="button" id="snd_arp" class="snd-btn" onclick="setSoundType('arp')">アルペジオ<br><span>♪ 試聴</span></button>
    </div>
    <div class="notify-row" style="margin-top:12px">
        <span class="notify-label">📳 バイブ</span>
        <div class="notify-toggle">
            <button type="button" id="vibeOn" class="ntf-btn active" onclick="setVibe(true)">ON</button>
            <button type="button" id="vibeOff" class="ntf-btn" onclick="setVibe(false)">OFF</button>
        </div>
    </div>
    <div style="font-size:11px;color:var(--dim);line-height:1.6;margin-top:10px">
        💡 変換完了時に、通知音・振動・画面表示・ブラウザ通知でお知らせします。<br>
        ※変換ボタンを押すと「通知の許可」を聞かれることがあります。許可すると、別の画面を見ていても完了通知が届きやすくなります。<br>
        ※iPhoneは仕様上、振動は動作しません。また画面を長時間離れていると音が鳴らないことがありますが、その場合も画面に戻れば完了表示でお知らせします。
    </div>
</div>

<div class="time-guide">
    ⏱ <strong>変換時間の目安</strong><br>
    5分程度の曲で <strong>およそ6〜8分</strong> かかります。曲が長いほど時間がかかります。<br>
    <span class="len-note">📏 <strong>長さの目安：10分以内を推奨</strong>。10分を超えると処理に失敗することがあります（長尺の動画・音源は、必要な部分だけ切り出してからご利用ください）。</span><br>
    <span style="color:var(--dim)">変換中は、他のアプリに切り替えたり画面を消したりしてもOK。完了時に通知音・画面表示でお知らせします。</span><br>
    <span class="warn-note">⚠️ ただし、この画面を更新（リロード）したりタブを閉じたりすると変換が中止されます。変換が終わるまでこのページは閉じないでください。</span>
</div>

<button id="convertBtn">⚡ 高品質変換する</button>

<div class="progress"><div id="bar" class="bar"></div></div>
<div id="status" class="status">音源を選択してください。</div>

<div id="elapsedResult" class="elapsed-result" style="display:none;"></div>

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

// ─── 通知設定 ───
let soundEnabled = true;
let soundType = "chime";
let vibeEnabled = true;
let notifyAudioCtx = null;
let titleBlinkTimer = null;
let origTitle = document.title;
let notifyPermission = "default"; // ブラウザ通知の許可状態

// 変換ボタンを押した時に呼ぶ：AudioContextを起こして音を鳴らす権利を確保
function primeNotifications(){
    // AudioContextを作成＆resume（iOSはユーザー操作直後でないと音が出せないため）
    try{
        if(!notifyAudioCtx){
            notifyAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if(notifyAudioCtx.state === "suspended"){ notifyAudioCtx.resume(); }
        // 無音を一瞬鳴らしてオーディオを「起こす」
        const osc = notifyAudioCtx.createOscillator();
        const gain = notifyAudioCtx.createGain();
        gain.gain.value = 0.0001;
        osc.connect(gain); gain.connect(notifyAudioCtx.destination);
        osc.start(); osc.stop(notifyAudioCtx.currentTime + 0.02);
    }catch(e){ console.warn("audio prime failed:", e); }

    // ブラウザ通知の許可をリクエスト（まだの場合）
    try{
        if("Notification" in window && Notification.permission === "default"){
            Notification.requestPermission().then(p => { notifyPermission = p; });
        }else if("Notification" in window){
            notifyPermission = Notification.permission;
        }
    }catch(e){ console.warn("notification permission failed:", e); }
}

function setSound(on){
    soundEnabled = on;
    document.getElementById("soundOn").classList.toggle("active", on);
    document.getElementById("soundOff").classList.toggle("active", !on);
    document.getElementById("soundTypeRow").style.display = on ? "grid" : "none";
}
function setSoundType(type){
    soundType = type;
    ["chime","beep","bell","arp"].forEach(t => {
        document.getElementById("snd_" + t).classList.toggle("active", t === type);
    });
    // 選んだ音を試聴
    playNotifySound(type);
}
function setVibe(on){
    vibeEnabled = on;
    document.getElementById("vibeOn").classList.toggle("active", on);
    document.getElementById("vibeOff").classList.toggle("active", !on);
    if(on && navigator.vibrate){ navigator.vibrate(60); }
}

// Web Audio APIで通知音を鳴らす
function playNotifySound(type){
    try{
        if(!notifyAudioCtx){
            notifyAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        const ctx = notifyAudioCtx;
        if(ctx.state === "suspended"){ ctx.resume(); }
        const now = ctx.currentTime;

        // 音色ごとの音符パターン [周波数, 開始秒, 長さ秒]
        let notes;
        if(type === "beep"){
            notes = [[880, 0, 0.12], [880, 0.18, 0.12]];
        }else if(type === "bell"){
            notes = [[1318.5, 0, 0.8]];
        }else if(type === "arp"){
            notes = [[523.25,0,0.12],[659.25,0.12,0.12],[783.99,0.24,0.12],[1046.5,0.36,0.4]];
        }else{ // chime（デフォルト）
            notes = [[783.99, 0, 0.3], [1046.5, 0.18, 0.5]];
        }

        notes.forEach(([freq, start, dur]) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = (type === "bell") ? "triangle" : "sine";
            osc.frequency.value = freq;
            osc.connect(gain);
            gain.connect(ctx.destination);
            const t0 = now + start;
            gain.gain.setValueAtTime(0, t0);
            gain.gain.linearRampToValueAtTime(0.35, t0 + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
            osc.start(t0);
            osc.stop(t0 + dur + 0.05);
        });
    }catch(e){
        console.warn("notify sound failed:", e);
    }
}

// 完了通知（音・バイブ・ブラウザ通知・画面）
function fireCompletionNotify(){
    // 音（AudioContextを復帰させてから鳴らす）
    if(soundEnabled){
        try{ if(notifyAudioCtx && notifyAudioCtx.state === "suspended"){ notifyAudioCtx.resume(); } }catch(e){}
        playNotifySound(soundType);
    }
    // バイブ（対応端末のみ。iOS Safariは非対応）
    if(vibeEnabled && navigator.vibrate){ navigator.vibrate([100, 50, 100, 50, 200]); }
    // ブラウザ通知（許可があれば。画面を裏に回していても出る可能性）
    try{
        if("Notification" in window && Notification.permission === "granted"){
            const n = new Notification("AudioShift HQ", {
                body: "✅ 変換が完了しました！",
                tag: "audioshift-done"
            });
            n.onclick = () => { window.focus(); n.close(); };
        }
    }catch(e){ console.warn("notification failed:", e); }
    // 画面内バナー
    showDoneBanner();
    // タブのタイトルを点滅
    startTitleBlink();
}

// 画面内の完了バナー（戻ってきた時に確実に気づける）
function showDoneBanner(){
    const banner = document.getElementById("doneBanner");
    if(!banner) return;
    banner.style.display = "block";
    banner.classList.add("show");
}
function hideDoneBanner(){
    const banner = document.getElementById("doneBanner");
    if(!banner) return;
    banner.style.display = "none";
    banner.classList.remove("show");
}

function startTitleBlink(){
    stopTitleBlink();
    let on = true;
    document.title = "✅ 変換完了！";
    titleBlinkTimer = setInterval(() => {
        document.title = on ? origTitle : "✅ 変換完了！";
        on = !on;
    }, 800);
    // 画面に戻ってきたら点滅を止める
    const stopOnFocus = () => { stopTitleBlink(); window.removeEventListener("focus", stopOnFocus); document.removeEventListener("visibilitychange", visHandler); };
    const visHandler = () => { if(!document.hidden){ stopOnFocus(); } };
    window.addEventListener("focus", stopOnFocus);
    document.addEventListener("visibilitychange", visHandler);
    // 念のため30秒で自動停止
    setTimeout(stopTitleBlink, 30000);
}
function stopTitleBlink(){
    if(titleBlinkTimer){ clearInterval(titleBlinkTimer); titleBlinkTimer = null; }
    document.title = origTitle;
}

// ─── 経過時間カウンター ───
let elapsedTimer = null;
let elapsedStart = 0;
let lastElapsedSec = 0;  // 直近の変換にかかった秒数（完了後の表示用）

function fmtElapsed(sec){
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    if(m > 0){ return m + "分" + s.toString().padStart(2, "0") + "秒"; }
    return s + "秒";
}

// 変換中にページを離脱しようとしたら確認を出す
function beforeUnloadHandler(e){
    e.preventDefault();
    e.returnValue = "変換中です。このページを離れると変換が中止されます。";
    return e.returnValue;
}

function startElapsed(){
    stopElapsed();
    elapsedStart = Date.now();
    elapsedTimer = setInterval(updateElapsed, 1000);
    updateElapsed();
    window.addEventListener("beforeunload", beforeUnloadHandler);
}
function updateElapsed(){
    const sec = Math.floor((Date.now() - elapsedStart) / 1000);
    const timeStr = fmtElapsed(sec);
    setStatus(
        "🎚 高品質変換中...（Rubber Band R3モード）\\n" +
        "経過時間：" + timeStr + "\\n" +
        "目安：5分の曲でおよそ6〜8分。\\n" +
        "⚠️ この画面は閉じたり更新したりしないでください（変換が中止されます）。他アプリへの切替や画面オフはOKです。",
        70
    );
}
function stopElapsed(){
    // 止める直前に所要時間を確定保存
    if(elapsedTimer && elapsedStart){
        lastElapsedSec = Math.floor((Date.now() - elapsedStart) / 1000);
    }
    if(elapsedTimer){ clearInterval(elapsedTimer); elapsedTimer = null; }
    window.removeEventListener("beforeunload", beforeUnloadHandler);
}

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
        loadWaveform(f);
    }else{
        fileBtn.classList.remove("has-file");
        fileTitle.textContent = "タップして音源を選択";
        fileSub.textContent = "音声・動画ファイル（動画は音声を抽出）";
        document.getElementById("waveformBox").style.display = "none";
    }
});

// ─── 波形表示・範囲選択 ───
let waveAudioDuration = 0;   // 音源の長さ（秒）
let rangeMode = "full";      // 'full' | 'part'
let rangeStart = 0;          // 選択開始（秒）
let rangeEnd = 0;            // 選択終了（秒）
let waveDragging = null;     // 'a' | 'b' | null
let waveDecodedBuf = null;   // デコード済みAudioBuffer（描画用に保持）
let wavePreviewURL = null;   // プレビュー再生用のObjectURL
let wavePlayRAF = null;      // 再生位置更新のアニメーションフレーム

function fmtMMSS(sec){
    sec = Math.max(0, sec);
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return m + ":" + s.toString().padStart(2, "0");
}
function parseMMSS(str){
    // "1:23" or "83" を秒に
    str = (str || "").trim();
    if(str.indexOf(":") >= 0){
        const parts = str.split(":");
        const m = parseInt(parts[0], 10) || 0;
        const s = parseInt(parts[1], 10) || 0;
        return m * 60 + s;
    }
    return parseFloat(str) || 0;
}

async function loadWaveform(file){
    const box = document.getElementById("waveformBox");
    box.style.display = "block";

    // 前回のプレビューURLを解放
    if(wavePreviewURL){ try{ URL.revokeObjectURL(wavePreviewURL); }catch(e){} wavePreviewURL = null; }
    // プレビュー再生用のURLを作成（元ファイルをそのまま再生）
    try{ wavePreviewURL = URL.createObjectURL(file); }catch(e){ wavePreviewURL = null; }
    const prev = document.getElementById("wavePreviewAudio");
    if(prev && wavePreviewURL){ prev.src = wavePreviewURL; }

    setRangeMode("full");
    try{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuf = await file.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(arrayBuf.slice(0));
        try{ ctx.close(); }catch(e){}

        waveDecodedBuf = audioBuf;
        waveAudioDuration = audioBuf.duration;
        rangeStart = 0;
        rangeEnd = waveAudioDuration;
        const note = document.getElementById("waveNoDecodeNote");
        if(note) note.style.display = "none";
        const exBtn = document.getElementById("extractAudioBtn");
        if(exBtn){ exBtn.disabled = false; exBtn.textContent = "🎵 この音声をWAVで保存（移調せず抽出）"; }
        // デコード成功 = 変換できる状態
        convertBtn.disabled = false;
        convertBtn.textContent = "⚡ 高品質変換する";
        updateRangeUI();
    }catch(e){
        console.warn("ブラウザ直接デコード失敗。MOV用の再生キャプチャ方式に切替:", e);
        // MOVなど：サーバーに送らず、ブラウザ内で再生しながら音声をキャプチャする（WaveCut方式）
        showMovCaptureUI(file, prev);
    }
}

// MOV用：再生しながら音声をキャプチャするUIを表示（サーバー不使用・通信量ゼロ）
function showMovCaptureUI(file, prev){
    const note = document.getElementById("waveNoDecodeNote");
    const exBtn = document.getElementById("extractAudioBtn");
    const capArea = document.getElementById("movCaptureArea");

    waveDecodedBuf = null;
    waveAudioDuration = 0;
    if(exBtn){ exBtn.disabled = true; exBtn.textContent = "🎵 音声を準備すると使えます"; }
    if(note){
        note.style.display = "block";
        note.innerHTML = "⚠️ この形式（MOVなど）は、下のボタンで音声を取り込むと波形・範囲選択・抽出が使えます。";
    }
    if(capArea){ capArea.style.display = "block"; }

    // 変換ボタンを無効化（音声取り込みが完了するまで変換不可）
    convertBtn.disabled = true;
    convertBtn.textContent = "⚠️ 先に音声を取り込んでください";

    // video要素から長さだけ先に取得（範囲選択の保険）
    if(prev){
        const onMeta = function(){
            prev.removeEventListener("loadedmetadata", onMeta);
            if(isFinite(prev.duration) && prev.duration > 0 && waveAudioDuration === 0){
                waveAudioDuration = prev.duration;
                rangeStart = 0; rangeEnd = waveAudioDuration;
                updateRangeUI();
            }
        };
        prev.addEventListener("loadedmetadata", onMeta);
    }
}

// 再生キャプチャ実行（ユーザーのタップから呼ぶ）
// MOVキャプチャの状態（ボタン操作から触れるようモジュールレベルに保持）
let movCap = null;  // {ctx, media, source, processor, playGain, chunks, channels, url, finished, finalize}
let movWakeLock = null;  // 画面が消えないようにするWake Lock

async function startMovCapture(canStop){
    const file = (audioInput.files && audioInput.files[0]) ? audioInput.files[0] : null;
    if(!file) return;

    const note = document.getElementById("waveNoDecodeNote");
    const capBtnFull = document.getElementById("movCaptureBtnFull");
    const capBtnStop = document.getElementById("movCaptureBtnStop");
    const capStatus = document.getElementById("movCaptureStatus");
    const capRunning = document.getElementById("movCaptureRunning");
    const soundToggle = document.getElementById("movSoundToggle");
    const doneBtn = document.getElementById("movCaptureDone");
    const progressBar = document.getElementById("movProgressBar");
    const timeLabel = document.getElementById("movCaptureTime");
    const captureLabel = document.getElementById("movCaptureLabel");
    const isAudio = file.type.startsWith("audio/");

    // 両方の取り込みボタンを隠して、進行UIを表示
    if(capBtnFull) capBtnFull.style.display = "none";
    if(capBtnStop) capBtnStop.style.display = "none";
    if(capRunning) capRunning.style.display = "block";
    capStatus.style.display = "none";
    if(soundToggle) soundToggle.textContent = "🔇 無音";
    // 「ここまでで確定」は途中で止められるモードの時だけ表示（誤操作防止）
    if(doneBtn) doneBtn.style.display = canStop ? "block" : "none";
    if(progressBar){ progressBar.style.width = "0%"; }
    if(timeLabel){ timeLabel.textContent = "0:00 / 0:00"; }
    if(captureLabel){ captureLabel.textContent = "🎵 取り込み中..."; }

    // 画面が消えないようにする（Wake Lock。対応端末のみ）
    requestMovWakeLock();

    const url = URL.createObjectURL(file);
    const media = document.createElement(isAudio ? "audio" : "video");
    media.src = url;
    media.preload = "auto";
    media.playsInline = true;
    media.muted = false;

    try{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        if(ctx.state === "suspended"){ await ctx.resume(); }

        await new Promise((resolve, reject) => {
            const channels = 2;
            const chunks = [[], []];
            let source = null, processor = null, playGain = null;
            let finished = false;

            const cleanup = () => {
                try{ if(processor) processor.disconnect(); }catch(e){}
                try{ if(source) source.disconnect(); }catch(e){}
                try{ if(playGain) playGain.disconnect(); }catch(e){}
                try{ media.pause(); }catch(e){}
                try{ URL.revokeObjectURL(url); }catch(e){}
            };

            // 取り込んだチャンクからAudioBufferを組み立てて確定
            const finalize = () => {
                if(finished) return;
                finished = true;
                if(movCap) movCap.finished = true;
                const total = chunks[0].reduce((s,a)=>s+a.length, 0);
                cleanup();
                if(total === 0){ reject(new Error("音声を取り込めませんでした")); return; }
                const buf = ctx.createBuffer(channels, total, ctx.sampleRate);
                for(let ch=0; ch<channels; ch++){
                    const out = buf.getChannelData(ch);
                    let off = 0;
                    for(const arr of chunks[ch]){ out.set(arr, off); off += arr.length; }
                }
                waveDecodedBuf = buf;
                waveAudioDuration = buf.duration;
                rangeStart = 0; rangeEnd = waveAudioDuration;
                resolve();
            };

            media.onerror = () => { if(!finished){ finished = true; cleanup(); reject(new Error("この動画を再生できませんでした")); } };

            media.onloadedmetadata = async () => {
                try{
                    source = ctx.createMediaElementSource(media);
                    processor = ctx.createScriptProcessor(4096, channels, channels);
                    // 再生経路：スピーカーに送る音量（ここだけ切替）。初期は無音。
                    // 録音は onaudioprocess の入力から直接拾うので、この音量を変えても録音には影響しない。
                    playGain = ctx.createGain();
                    playGain.gain.value = 0;

                    source.connect(processor);
                    processor.connect(playGain);   // 再生音量はplayGainで制御
                    playGain.connect(ctx.destination);

                    // モジュールに状態を保存（ボタン操作用）
                    movCap = { ctx, media, source, processor, playGain, chunks, channels, url, finished:false, finalize };

                    processor.onaudioprocess = (ev) => {
                        const input = ev.inputBuffer;
                        // 録音は入力をそのまま保存（フル音量。playGainの値に関係なく完全）
                        for(let ch=0; ch<channels; ch++){
                            const sc = Math.min(ch, input.numberOfChannels - 1);
                            chunks[ch].push(new Float32Array(input.getChannelData(sc)));
                        }
                        // 出力（再生音）には入力をそのままコピー（playGainで音量調整される）
                        for(let ch=0; ch<ev.outputBuffer.numberOfChannels; ch++){
                            const sc = Math.min(ch, input.numberOfChannels - 1);
                            ev.outputBuffer.getChannelData(ch).set(input.getChannelData(sc));
                        }
                        // プログレスバーと時間表示を更新
                        const dur = media.duration;
                        const cur = media.currentTime;
                        if(dur && isFinite(dur) && dur > 0){
                            const pct = Math.min(100, (cur / dur) * 100);
                            if(progressBar) progressBar.style.width = pct + "%";
                            if(timeLabel) timeLabel.textContent = fmtMMSS(cur) + " / " + fmtMMSS(dur);
                            if(captureLabel) captureLabel.textContent = "🎵 取り込み中... " + Math.floor(pct) + "%";
                        }
                    };

                    media.onended = () => { finalize(); };  // 最後まで再生＝全体を確定

                    media.currentTime = 0;
                    await media.play();
                }catch(err){ if(!finished){ finished = true; cleanup(); reject(err); } }
            };
            media.load();
        });

        try{ if(movCap && movCap.ctx) movCap.ctx.close(); }catch(e){}
        movCap = null;
        releaseMovWakeLock();

        // 成功：進行UIを隠して、波形・範囲選択・抽出を有効化
        if(capRunning) capRunning.style.display = "none";
        if(note) note.style.display = "none";
        const capArea = document.getElementById("movCaptureArea");
        if(capArea) capArea.style.display = "none";
        const exBtn = document.getElementById("extractAudioBtn");
        if(exBtn){ exBtn.disabled = false; exBtn.textContent = "🎵 この音声をWAVで保存（移調せず抽出）"; }
        // 変換ボタンを有効化（音声取り込み完了）
        convertBtn.disabled = false;
        convertBtn.textContent = "⚡ 高品質変換する";
        updateRangeUI();
        if(rangeMode === "part"){
            requestAnimationFrame(() => requestAnimationFrame(() => { drawWaveformCanvas(waveDecodedBuf); updateRangeUI(); }));
        }
        capStatus.style.display = "block";
        capStatus.textContent = "✅ 音声の取り込み完了！波形を表示しました。";
    }catch(err){
        console.warn("MOV capture failed:", err);
        movCap = null;
        releaseMovWakeLock();
        if(capRunning) capRunning.style.display = "none";
        capStatus.style.display = "block";
        capStatus.textContent = "❌ 取り込み失敗：" + err.message + "（変換は再生プレビューで範囲指定すれば可能です）";
        // 取り込みボタンを再表示（やり直せるように）
        if(capBtnFull) capBtnFull.style.display = "block";
        if(capBtnStop) capBtnStop.style.display = "block";
    }
}

// ── Wake Lock（取り込み中に画面が消えないように。対応端末のみ）──
async function requestMovWakeLock(){
    try{
        if("wakeLock" in navigator){
            movWakeLock = await navigator.wakeLock.request("screen");
            // 画面が一度消えて復帰した時に取り直す
            document.addEventListener("visibilitychange", reacquireWakeLock);
        }
    }catch(e){ console.warn("wakeLock failed:", e); }
}
async function reacquireWakeLock(){
    try{
        if(movWakeLock !== null && document.visibilityState === "visible" && "wakeLock" in navigator){
            movWakeLock = await navigator.wakeLock.request("screen");
        }
    }catch(e){}
}
function releaseMovWakeLock(){
    try{
        document.removeEventListener("visibilitychange", reacquireWakeLock);
        if(movWakeLock){ movWakeLock.release(); movWakeLock = null; }
    }catch(e){}
}

// 「ここまでで確定」：そこまでに取り込んだぶんで波形を作る
function finishMovCapture(){
    if(movCap && !movCap.finished && movCap.finalize){
        movCap.finalize();
    }
}

// 「🔊聞く / 🔇無音」トグル（再生音量だけ変更。取り込みには影響しない）
function toggleCaptureSound(){
    const btn = document.getElementById("movSoundToggle");
    if(!movCap || !movCap.playGain){ return; }
    const isOn = movCap.playGain.gain.value > 0;
    if(isOn){
        movCap.playGain.gain.value = 0;
        if(btn) btn.textContent = "🔇 無音";
    }else{
        movCap.playGain.gain.value = 1;
        if(btn) btn.textContent = "🔊 聞く";
    }
}

// AudioBufferをWAV Blobに変換（16bit PCM）
function audioBufferToWavBlob(buf){
    const numCh = buf.numberOfChannels;
    const len = buf.length;
    const sampleRate = buf.sampleRate;
    const bytesPerSample = 2;
    const blockAlign = numCh * bytesPerSample;
    const dataSize = len * blockAlign;
    const arrBuf = new ArrayBuffer(44 + dataSize);
    const view = new DataView(arrBuf);
    const writeStr = (off, str) => { for(let i=0;i<str.length;i++) view.setUint8(off+i, str.charCodeAt(i)); };
    writeStr(0, "RIFF");
    view.setUint32(4, 36 + dataSize, true);
    writeStr(8, "WAVE");
    writeStr(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numCh, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, 16, true);
    writeStr(36, "data");
    view.setUint32(40, dataSize, true);
    // チャンネルデータをインターリーブして書き込み
    let offset = 44;
    const channels = [];
    for(let c=0;c<numCh;c++){ channels.push(buf.getChannelData(c)); }
    for(let i=0;i<len;i++){
        for(let c=0;c<numCh;c++){
            let s = Math.max(-1, Math.min(1, channels[c][i] || 0));
            view.setInt16(offset, s < 0 ? s*32768 : s*32767, true);
            offset += 2;
        }
    }
    return new Blob([arrBuf], {type:"audio/wav"});
}

function drawWaveformCanvas(audioBuf){
    const canvas = document.getElementById("waveformCanvas");
    const wrap = document.getElementById("waveformWrap");
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx2 = canvas.getContext("2d");
    ctx2.clearRect(0, 0, w, h);

    const dur = audioBuf.duration;
    const labelBand = 16;  // 上部の時刻ラベル専用帯（px）

    // ── 時刻ラベル帯の背景を敷く ──
    ctx2.fillStyle = "rgba(5,6,13,0.85)";
    ctx2.fillRect(0, 0, w, labelBand);

    // ── タイムライングリッド（時間目盛り）を先に描く ──
    if(dur > 0){
        // 曲の長さに応じて目盛り間隔を決める（5〜10本くらいになるよう）
        let interval;
        if(dur <= 15) interval = 2;
        else if(dur <= 40) interval = 5;
        else if(dur <= 90) interval = 10;
        else if(dur <= 180) interval = 20;
        else if(dur <= 360) interval = 30;
        else if(dur <= 600) interval = 60;
        else interval = 120;

        ctx2.font = "10px 'Space Mono', monospace";
        ctx2.textBaseline = "top";
        for(let t = 0; t <= dur; t += interval){
            const x = (t / dur) * w;
            // 縦のグリッド線（波形領域のみ。ラベル帯の下から）
            ctx2.strokeStyle = "rgba(125,139,181,0.22)";
            ctx2.lineWidth = 1;
            ctx2.beginPath();
            ctx2.moveTo(x, labelBand);
            ctx2.lineTo(x, h);
            ctx2.stroke();
            // ラベル帯の中に短い目盛り線
            ctx2.strokeStyle = "rgba(125,139,181,0.5)";
            ctx2.beginPath();
            ctx2.moveTo(x, labelBand - 4);
            ctx2.lineTo(x, labelBand);
            ctx2.stroke();
            // 時刻ラベル（ラベル帯の中に明るい色で）
            const m = Math.floor(t / 60);
            const s = Math.floor(t % 60);
            const label = m + ":" + s.toString().padStart(2, "0");
            ctx2.fillStyle = "rgba(180,195,230,0.95)";
            // 右端のラベルははみ出さないよう少し左に
            const tx = (x > w - 28) ? x - 26 : x + 3;
            ctx2.fillText(label, tx, 3);
        }
    }

    // ── 波形を描く（ラベル帯の下の領域だけに収める）──
    const data = audioBuf.getChannelData(0);
    const step = Math.floor(data.length / w) || 1;
    const waveTop = labelBand;
    const waveH = h - labelBand;
    const mid = waveTop + waveH / 2;

    ctx2.strokeStyle = "rgba(34,211,238,0.7)";
    ctx2.lineWidth = 1;
    ctx2.beginPath();
    for(let x = 0; x < w; x++){
        let min = 1, max = -1;
        for(let i = 0; i < step; i++){
            const v = data[x * step + i] || 0;
            if(v < min) min = v;
            if(v > max) max = v;
        }
        ctx2.moveTo(x, mid + min * (waveH / 2) * 0.9);
        ctx2.lineTo(x, mid + max * (waveH / 2) * 0.9);
    }
    ctx2.stroke();
}

function setRangeMode(mode){
    rangeMode = mode;
    document.getElementById("rangeFull").classList.toggle("active", mode === "full");
    document.getElementById("rangePart").classList.toggle("active", mode === "part");
    document.getElementById("waveformArea").style.display = (mode === "part") ? "block" : "none";
    if(mode === "full"){
        rangeStart = 0;
        rangeEnd = waveAudioDuration;
    }else{
        // 波形エリアが表示された「後」に描画（隠れた状態だとcanvas幅が0になるため）
        // requestAnimationFrameでレイアウト確定を待ってから描く
        if(waveDecodedBuf){
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    drawWaveformCanvas(waveDecodedBuf);
                    updateRangeUI();
                });
            });
        }
    }
    updateRangeUI();
}

function updateRangeUI(){
    const wrap = document.getElementById("waveformWrap");
    const sel = document.getElementById("waveSel");
    const ha = document.getElementById("waveHandleA");
    const hb = document.getElementById("waveHandleB");
    const info = document.getElementById("rangeInfo");

    if(waveAudioDuration <= 0){
        info.textContent = "選択範囲：全体";
        return;
    }
    const w = wrap.clientWidth;
    const xA = (rangeStart / waveAudioDuration) * w;
    const xB = (rangeEnd / waveAudioDuration) * w;
    sel.style.left = xA + "px";
    sel.style.width = Math.max(0, xB - xA) + "px";
    ha.style.left = xA + "px";
    hb.style.left = xB + "px";

    document.getElementById("rangeStartInput").value = fmtMMSS(rangeStart);
    document.getElementById("rangeEndInput").value = fmtMMSS(rangeEnd);

    if(rangeMode === "part"){
        const dur = rangeEnd - rangeStart;
        info.textContent = "選択範囲：" + fmtMMSS(rangeStart) + " 〜 " + fmtMMSS(rangeEnd) + "（" + fmtMMSS(dur) + "ぶん）";
    }else{
        info.textContent = "選択範囲：全体";
    }
}

function onRangeTimeInput(){
    let s = parseMMSS(document.getElementById("rangeStartInput").value);
    let e = parseMMSS(document.getElementById("rangeEndInput").value);
    s = Math.max(0, Math.min(s, waveAudioDuration));
    e = Math.max(0, Math.min(e, waveAudioDuration));
    if(e < s){ const tmp = s; s = e; e = tmp; }
    rangeStart = s;
    rangeEnd = e;
    updateRangeUI();
}

// 波形上のドラッグで範囲選択
(function initWaveDrag(){
    const wrap = document.getElementById("waveformWrap");
    const ha = document.getElementById("waveHandleA");
    const hb = document.getElementById("waveHandleB");
    if(!wrap) return;

    function xToTime(clientX){
        const rect = wrap.getBoundingClientRect();
        let x = clientX - rect.left;
        x = Math.max(0, Math.min(x, rect.width));
        return (x / rect.width) * waveAudioDuration;
    }
    function startDrag(which){ return (e) => { waveDragging = which; e.preventDefault(); }; }
    ha.addEventListener("mousedown", startDrag("a"));
    hb.addEventListener("mousedown", startDrag("b"));
    ha.addEventListener("touchstart", startDrag("a"), {passive:false});
    hb.addEventListener("touchstart", startDrag("b"), {passive:false});

    function move(clientX){
        if(!waveDragging || waveAudioDuration <= 0) return;
        const t = xToTime(clientX);
        if(waveDragging === "a"){
            rangeStart = Math.min(t, rangeEnd - 0.1);
            if(rangeStart < 0) rangeStart = 0;
        }else{
            rangeEnd = Math.max(t, rangeStart + 0.1);
            if(rangeEnd > waveAudioDuration) rangeEnd = waveAudioDuration;
        }
        updateRangeUI();
    }
    window.addEventListener("mousemove", (e) => move(e.clientX));
    window.addEventListener("touchmove", (e) => { if(waveDragging && e.touches[0]){ move(e.touches[0].clientX); e.preventDefault(); } }, {passive:false});
    window.addEventListener("mouseup", () => { waveDragging = null; });
    window.addEventListener("touchend", () => { waveDragging = null; });
})();

// ─── プレビュー再生・再生位置表示 ───
let wavePlayRangeOnly = false;  // 「選択範囲を試聴」モードか

function getWaveAudio(){ return document.getElementById("wavePreviewAudio"); }

function toggleWavePlay(){
    const audio = getWaveAudio();
    if(!audio || !wavePreviewURL) return;
    if(audio.paused){
        wavePlayRangeOnly = false;
        audio.play();
        document.getElementById("wavePlayBtn").textContent = "⏸ 停止";
        startPlayheadLoop();
    }else{
        audio.pause();
        document.getElementById("wavePlayBtn").textContent = "▶ 再生";
    }
}

function playSelectedRange(){
    const audio = getWaveAudio();
    if(!audio || !wavePreviewURL || waveAudioDuration <= 0) return;
    wavePlayRangeOnly = true;
    audio.currentTime = rangeStart;
    audio.play();
    document.getElementById("wavePlayBtn").textContent = "⏸ 停止";
    startPlayheadLoop();
}

function startPlayheadLoop(){
    const audio = getWaveAudio();
    const playhead = document.getElementById("wavePlayhead");
    const wrap = document.getElementById("waveformWrap");
    const timeLabel = document.getElementById("wavePlayTime");
    if(!audio || !playhead || !wrap) return;

    cancelPlayheadLoop();
    playhead.style.display = "block";

    function loop(){
        const cur = audio.currentTime;
        // 選択範囲試聴モードなら、範囲終端で停止
        if(wavePlayRangeOnly && cur >= rangeEnd){
            audio.pause();
            document.getElementById("wavePlayBtn").textContent = "▶ 再生";
            cancelPlayheadLoop();
            return;
        }
        if(waveAudioDuration > 0){
            const x = (cur / waveAudioDuration) * wrap.clientWidth;
            playhead.style.left = x + "px";
        }
        if(timeLabel){ timeLabel.textContent = fmtMMSS(cur); }
        if(!audio.paused){
            wavePlayRAF = requestAnimationFrame(loop);
        }
    }
    wavePlayRAF = requestAnimationFrame(loop);
}

function cancelPlayheadLoop(){
    if(wavePlayRAF){ cancelAnimationFrame(wavePlayRAF); wavePlayRAF = null; }
}

// 再生終了・一時停止時にボタン表示を戻す
(function initWavePlayerEvents(){
    const audio = document.getElementById("wavePreviewAudio");
    if(!audio) return;
    audio.addEventListener("ended", () => {
        document.getElementById("wavePlayBtn").textContent = "▶ 再生";
        cancelPlayheadLoop();
    });
    audio.addEventListener("pause", () => {
        document.getElementById("wavePlayBtn").textContent = "▶ 再生";
    });
    // 波形をクリック/タップしたらその位置にシーク
    const wrap = document.getElementById("waveformWrap");
    if(wrap){
        wrap.addEventListener("click", (e) => {
            // ハンドルのドラッグ中は無視
            if(waveDragging) return;
            if(waveAudioDuration <= 0 || !wavePreviewURL) return;
            const rect = wrap.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const t = (x / rect.width) * waveAudioDuration;
            audio.currentTime = Math.max(0, Math.min(t, waveAudioDuration));
            const playhead = document.getElementById("wavePlayhead");
            if(playhead){ playhead.style.display = "block"; playhead.style.left = x + "px"; }
            const timeLabel = document.getElementById("wavePlayTime");
            if(timeLabel){ timeLabel.textContent = fmtMMSS(audio.currentTime); }
        });
    }
})();

// 「今の位置を開始/終了に」
function setRangeFromPlayhead(which){
    const audio = getWaveAudio();
    if(!audio || waveAudioDuration <= 0) return;
    const t = audio.currentTime;
    if(which === "a"){
        rangeStart = Math.min(t, rangeEnd - 0.1);
        if(rangeStart < 0) rangeStart = 0;
    }else{
        rangeEnd = Math.max(t, rangeStart + 0.1);
        if(rangeEnd > waveAudioDuration) rangeEnd = waveAudioDuration;
    }
    updateRangeUI();
}

// 音声だけをWAVで保存（移調せず抽出）。範囲選択中ならその区間だけ
function extractAudioOnly(){
    if(!waveDecodedBuf){
        alert("音声データを準備中です。少し待ってからお試しください。\\n（動画によっては音声の読み込みに時間がかかることがあります）");
        return;
    }
    try{
        let bufToSave = waveDecodedBuf;
        // 範囲選択モードなら、その区間だけ切り出す
        if(rangeMode === "part" && waveAudioDuration > 0 && (rangeEnd - rangeStart) > 0.1){
            const sr = waveDecodedBuf.sampleRate;
            const numCh = waveDecodedBuf.numberOfChannels;
            const startSample = Math.floor(rangeStart * sr);
            const endSample = Math.floor(rangeEnd * sr);
            const segLen = endSample - startSample;
            const seg = new AudioBuffer({length: segLen, numberOfChannels: numCh, sampleRate: sr});
            for(let c=0;c<numCh;c++){
                const src = waveDecodedBuf.getChannelData(c);
                const dst = seg.getChannelData(c);
                for(let i=0;i<segLen;i++){ dst[i] = src[startSample + i] || 0; }
            }
            bufToSave = seg;
        }
        const wavBlob = audioBufferToWavBlob(bufToSave);
        const url = URL.createObjectURL(wavBlob);
        const baseName = (audioInput.files[0] ? audioInput.files[0].name : "audio").replace(/\\.[^/.]+$/, "");
        let suffix = "_audio";
        if(rangeMode === "part" && (rangeEnd - rangeStart) > 0.1){
            suffix = "_audio_" + fmtMMSS(rangeStart).replace(":","m") + "-" + fmtMMSS(rangeEnd).replace(":","m");
        }
        const a = document.createElement("a");
        a.href = url;
        a.download = baseName + suffix + ".wav";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }catch(e){
        console.warn("extract audio failed:", e);
        alert("音声の抽出に失敗しました。");
    }
}

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

// ─── 基準ピッチ合わせ ───
// 430〜460Hzのプルダウンを生成し、現在→目標の差から移調量(セント)を計算
(function initTuning(){
    const fromSel = document.getElementById("tuneFrom");
    const toSel = document.getElementById("tuneTo");
    if(!fromSel || !toSel) return;

    for(let hz = 430; hz <= 460; hz++){
        const o1 = document.createElement("option");
        o1.value = hz; o1.textContent = hz + " Hz";
        if(hz === 440) o1.selected = true;
        fromSel.appendChild(o1);

        const o2 = document.createElement("option");
        o2.value = hz; o2.textContent = hz + " Hz";
        if(hz === 440) o2.selected = true;
        toSel.appendChild(o2);
    }

    fromSel.addEventListener("change", updateTunePreview);
    toSel.addEventListener("change", updateTunePreview);
    updateTunePreview();
})();

// 現在→目標の移調量(半音)を計算
function calcTuneSemitones(){
    const from = Number(document.getElementById("tuneFrom").value);
    const to = Number(document.getElementById("tuneTo").value);
    // 周波数比から半音を算出： 12 * log2(to/from)
    return 12 * Math.log2(to / from);
}

function updateTunePreview(){
    const semi = calcTuneSemitones();
    const cents = semi * 100;
    const sign = semi > 0 ? "+" : "";
    document.getElementById("tunePreview").textContent =
        "必要な移調量：" + sign + semi.toFixed(2) + " 半音（" + sign + cents.toFixed(0) + " セント）";
}

// 計算した移調量を移調スライダー/入力に適用
function applyTuning(){
    const semi = calcTuneSemitones();
    const clamped = clampPitch(semi);
    setPitch(clamped);
    const from = document.getElementById("tuneFrom").value;
    const to = document.getElementById("tuneTo").value;
    // ステータスにも反映
    setStatus("🎯 " + from + "Hz → " + to + "Hz の移調量（" + clamped.toFixed(2) + "半音）をセットしました。\\n変換ボタンを押してください。", 0);
}

// ─── 自動ピッチ判定（ブラウザ内・簡易・参考値）───
async function detectPitch(){
    const file = audioInput.files[0];
    const btn = document.getElementById("detectBtn");
    const result = document.getElementById("detectResult");

    if(!file){
        result.style.display = "block";
        result.innerHTML = "先に音源または動画ファイルを選択してください。";
        return;
    }

    btn.disabled = true;
    btn.textContent = "🔍 解析中...";
    result.style.display = "block";
    result.innerHTML = "曲を解析しています...（数秒〜十数秒）";

    try{
        // ファイルをAudioBufferにデコード
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuf = await file.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(arrayBuf.slice(0));
        try{ ctx.close(); }catch(e){}

        // モノラル化（先頭チャンネルを使用）
        const data = audioBuf.getChannelData(0);
        const sampleRate = audioBuf.sampleRate;

        // 解析範囲：曲の中盤を最大60秒ぶん（頭と尾の無音・フェードを避ける）
        const totalLen = data.length;
        const analyzeSec = Math.min(60, audioBuf.duration);
        const startIdx = Math.floor(totalLen * 0.2); // 20%地点から
        const endIdx = Math.min(totalLen, startIdx + Math.floor(analyzeSec * sampleRate));

        // セントずれのヒストグラム（-50〜+49セントを集計）
        const centBins = new Array(100).fill(0);

        const fftSize = 8192;
        const hop = fftSize; // 重ならせず順に
        const re = new Float32Array(fftSize);
        const im = new Float32Array(fftSize);

        let frameCount = 0;
        for(let pos = startIdx; pos + fftSize < endIdx; pos += hop){
            // 窓掛け（Hann）してFFT入力へ
            for(let i = 0; i < fftSize; i++){
                const w = 0.5 * (1 - Math.cos(2 * Math.PI * i / (fftSize - 1)));
                re[i] = data[pos + i] * w;
                im[i] = 0;
            }
            fft(re, im);

            // パワースペクトルから、楽音域（80〜1000Hz）のピークを拾う
            const minBin = Math.floor(80 * fftSize / sampleRate);
            const maxBin = Math.floor(1000 * fftSize / sampleRate);
            // 上位のピークを探す
            for(let b = minBin; b < maxBin; b++){
                const mag = re[b]*re[b] + im[b]*im[b];
                // 局所ピーク（前後より大きい）かつ一定以上の強さ
                if(mag > re[b-1]*re[b-1]+im[b-1]*im[b-1] &&
                   mag > re[b+1]*re[b+1]+im[b+1]*im[b+1] &&
                   mag > 0.0001){
                    const freq = b * sampleRate / fftSize;
                    // 440基準で最も近い半音からのセントずれを計算
                    const midi = 69 + 12 * Math.log2(freq / 440);
                    const nearest = Math.round(midi);
                    const centOff = (midi - nearest) * 100; // -50〜+50
                    let bin = Math.round(centOff) + 50;
                    if(bin >= 0 && bin < 100){ centBins[bin] += Math.sqrt(mag); }
                }
            }
            frameCount++;
            if(frameCount > 200) break; // 安全のため上限
        }

        // ヒストグラムの重心（加重平均）でズレを推定
        let sum = 0, wsum = 0;
        for(let i = 0; i < 100; i++){
            const cent = i - 50;
            sum += centBins[i] * cent;
            wsum += centBins[i];
        }

        if(wsum < 0.0001){
            result.innerHTML = "判定できませんでした。<br><span class='note'>※打楽器中心の曲や無音が多い場合は判定が難しいことがあります。</span>";
            return;
        }

        const avgCent = sum / wsum;
        // 推定基準ピッチ = 440 * 2^(avgCent/1200)
        const estimatedHz = 440 * Math.pow(2, avgCent / 1200);
        const roundedHz = Math.round(estimatedHz);

        const sign = avgCent > 0 ? "+" : "";
        result.innerHTML =
            "推定された基準ピッチ：<span class='big'>約 " + estimatedHz.toFixed(1) + " Hz</span><br>" +
            "（440Hzから " + sign + avgCent.toFixed(1) + " セント）<br>" +
            "<span class='note'>※あくまで参考値です。ドラム中心の曲などは外れることがあります。正確に合わせたい場合はチューナーでの確認をおすすめします。</span><br>" +
            "<button type='button' class='detect-apply' onclick='useDetectedPitch(" + roundedHz + ")'>この値（" + roundedHz + "Hz）を「現在のピッチ」にセット</button>";

    }catch(e){
        console.warn("pitch detect failed:", e);
        result.innerHTML = "解析に失敗しました。<br><span class='note'>※対応していない形式か、ファイルが大きすぎる可能性があります。</span>";
    }finally{
        btn.disabled = false;
        btn.textContent = "🔍 曲の基準ピッチを自動判定（参考）";
    }
}

// 判定結果を「現在のピッチ」プルダウンにセット
function useDetectedPitch(hz){
    const fromSel = document.getElementById("tuneFrom");
    // 範囲内に収める
    const clamped = Math.max(430, Math.min(460, hz));
    fromSel.value = clamped;
    updateTunePreview();
}

// 簡易FFT（Cooley-Tukey, in-place, radix-2）
function fft(re, im){
    const n = re.length;
    for(let i = 1, j = 0; i < n; i++){
        let bit = n >> 1;
        for(; j & bit; bit >>= 1){ j ^= bit; }
        j ^= bit;
        if(i < j){
            [re[i], re[j]] = [re[j], re[i]];
            [im[i], im[j]] = [im[j], im[i]];
        }
    }
    for(let len = 2; len <= n; len <<= 1){
        const ang = -2 * Math.PI / len;
        const wRe = Math.cos(ang), wIm = Math.sin(ang);
        for(let i = 0; i < n; i += len){
            let curRe = 1, curIm = 0;
            for(let k = 0; k < len / 2; k++){
                const uRe = re[i+k], uIm = im[i+k];
                const vRe = re[i+k+len/2]*curRe - im[i+k+len/2]*curIm;
                const vIm = re[i+k+len/2]*curIm + im[i+k+len/2]*curRe;
                re[i+k] = uRe + vRe;
                im[i+k] = uIm + vIm;
                re[i+k+len/2] = uRe - vRe;
                im[i+k+len/2] = uIm - vIm;
                const nRe = curRe*wRe - curIm*wIm;
                curIm = curRe*wIm + curIm*wRe;
                curRe = nRe;
            }
        }
    }
}


convertBtn.addEventListener("click", async () => {
    const file = audioInput.files[0];
    const semitones = semitonesInput.value;

    if(!file){
        setStatus("音源ファイルを選択してください。MP3 / WAV / M4A などに対応しています。", 0);
        return;
    }

    // 動画ファイルで音声が未取り込みの場合は変換不可（重いファイルをそのまま送らせない）
    const isVideoFile = file.type.startsWith("video/") || /\\.(mov|mp4|mkv|avi|m4v|webm)$/i.test(file.name);
    if(isVideoFile && !waveDecodedBuf){
        setStatus("⚠️ 動画ファイルは先に音声を取り込んでから変換してください。\\n「変換する範囲」セクションの取り込みボタンを押してください。", 0);
        // 取り込みエリアを目立たせる
        const capArea = document.getElementById("movCaptureArea");
        if(capArea){
            capArea.style.display = "block";
            capArea.scrollIntoView({behavior:"smooth", block:"center"});
        }
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

    // 通知の準備（ユーザー操作直後にAudioContext起動＆通知許可リクエスト）
    primeNotifications();

    // プレビュー再生を止める
    try{ const pa = document.getElementById("wavePreviewAudio"); if(pa && !pa.paused){ pa.pause(); } cancelPlayheadLoop(); }catch(e){}

    player.style.display = "none";
    downloadLink.style.display = "none";
    document.getElementById("elapsedResult").style.display = "none";
    hideDoneBanner();

    convertBtn.disabled = true;
    convertBtn.textContent = "変換中...";
    setStatus("アップロード準備中...", 10);

    // 送信ファイルを決定：動画などでデコード済み音声があり、WAV化した方が軽ければそれを送る
    let uploadFile = file;
    let uploadName = file.name;
    try{
        if(waveDecodedBuf){
            setStatus("音声を準備中...", 15);
            const wavBlob = audioBufferToWavBlob(waveDecodedBuf);
            // 抽出WAVの方が元ファイルより小さければ、それを送る（アップロード短縮）
            if(wavBlob.size < file.size){
                uploadFile = wavBlob;
                uploadName = file.name.replace(/\\.[^/.]+$/, "") + ".wav";
            }
        }
    }catch(e){
        console.warn("audio extract for upload failed, sending original:", e);
        uploadFile = file;
        uploadName = file.name;
    }

    const formData = new FormData();
    formData.append("audio", uploadFile, uploadName);
    formData.append("semitones", semitones);
    formData.append("format", outFormat);
    formData.append("bitrate", mp3Bitrate);
    // 範囲指定（partモードかつ有効な範囲のときだけ送る）
    if(rangeMode === "part" && waveAudioDuration > 0 && (rangeEnd - rangeStart) > 0.1){
        formData.append("trim_start", rangeStart.toFixed(3));
        formData.append("trim_end", rangeEnd.toFixed(3));
    }

    try{
        setStatus("サーバーへアップロード中...\\n曲が長い場合は少し時間がかかります。\\n目安：5分の曲でおよそ6〜8分。", 30);

        // 経過時間カウンター開始（変換が終わるまで動き続ける）
        startElapsed();

        const response = await fetch("/shift", {
            method: "POST",
            body: formData
        });

        // 変換終了。カウンター停止
        stopElapsed();

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

        // 変換所要時間を専用エリアに表示（音源の長さと混同しないよう明記）
        const doneBox = document.getElementById("elapsedResult");
        doneBox.style.display = "block";
        doneBox.innerHTML = "⏱ <strong>変換作業にかかった時間</strong>：" + fmtElapsed(lastElapsedSec) +
            "<br><span style=\\"font-size:11px;color:var(--dim)\\">※音源の再生時間ではなく、移調処理が完了するまでの所要時間です</span>";

        fireCompletionNotify();

    }catch(error){
        stopElapsed();
        setStatus("エラー：\\n" + error.message, 0);
    }finally{
        stopElapsed();
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
        trim_start = request.form.get("trim_start", "")
        trim_end = request.form.get("trim_end", "")

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

        # 範囲指定の解析（指定があれば切り出し）
        trim_args = []
        try:
            if trim_start != "" and trim_end != "":
                ts = float(trim_start)
                te = float(trim_end)
                if te > ts >= 0 and (te - ts) > 0.05:
                    # -ss（開始）と -t（長さ）で切り出し
                    trim_args = ["-ss", str(ts), "-t", str(te - ts)]
        except ValueError:
            trim_args = []

        uid = str(uuid.uuid4())

        input_path = UPLOAD_DIR / f"{uid}_input"
        wav_path = UPLOAD_DIR / f"{uid}.wav"
        output_path = OUTPUT_DIR / f"{uid}_shifted_hq.wav"

        file.save(input_path)

        # 入力→WAV（範囲指定があれば -ss/-t で切り出し。-i の前に置くと高速）
        ffmpeg_cmd = ["ffmpeg", "-y"]
        ffmpeg_cmd += trim_args
        ffmpeg_cmd += [
            "-i", str(input_path),
            "-vn",
            "-ar", "44100",
            "-ac", "2",
            "-acodec", "pcm_s16le",
            str(wav_path)
        ]
        subprocess.run(ffmpeg_cmd, check=True)

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
