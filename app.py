<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>PitchFlow RubberBand</title>
  <style>
    :root{
      --bg:#0b1020;--card:#111827;--soft:#1f2937;--line:#334155;
      --text:#f8fafc;--muted:#94a3b8;--accent:#38bdf8;--ok:#22c55e;--warn:#fbbf24;--bad:#fb7185;
    }
    *{box-sizing:border-box}
    body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:linear-gradient(160deg,#020617,#0f172a 58%,#111827);color:var(--text);min-height:100vh}
    .wrap{max-width:920px;margin:0 auto;padding:24px 16px 48px}
    header{padding:8px 0 18px}
    h1{margin:0;font-size:32px;letter-spacing:.01em}
    .lead{margin:8px 0 0;color:var(--muted);line-height:1.7;font-size:14px}
    .pill{display:inline-block;margin:10px 6px 0 0;padding:6px 10px;border-radius:999px;background:rgba(56,189,248,.12);border:1px solid rgba(56,189,248,.3);color:#bae6fd;font-size:12px}
    .card{background:rgba(17,24,39,.9);border:1px solid rgba(148,163,184,.18);border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 18px 55px rgba(0,0,0,.25)}
    label{display:block;color:#cbd5e1;font-size:13px;margin-bottom:8px}
    input[type=file],select,input[type=range]{width:100%;font-size:16px}
    input[type=file]{padding:14px;border:1px dashed rgba(148,163,184,.55);border-radius:16px;background:#020617;color:var(--text)}
    select{padding:13px;border-radius:14px;background:#020617;color:var(--text);border:1px solid rgba(148,163,184,.35)}
    input[type=range]{accent-color:var(--accent)}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
    @media(max-width:700px){.grid{grid-template-columns:1fr}}
    .value{font-size:32px;font-weight:850;color:#e0f2fe;margin-top:8px}
    button{width:100%;border:0;border-radius:16px;padding:16px;font-size:16px;font-weight:850;background:linear-gradient(135deg,var(--accent),#7dd3fc);color:#001018;cursor:pointer}
    button:disabled{opacity:.5;cursor:not-allowed}
    .secondary{background:#1f2937;color:var(--text);border:1px solid rgba(148,163,184,.25)}
    .row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1}
    .status{white-space:pre-wrap;color:#cbd5e1;font-size:14px;line-height:1.7}
    .bar{height:10px;background:#020617;border-radius:999px;overflow:hidden;border:1px solid rgba(148,163,184,.22)}
    .bar>div{height:100%;width:0;background:linear-gradient(90deg,var(--accent),var(--ok));transition:width .2s}
    audio{width:100%;margin-top:12px}
    .note{font-size:13px;color:var(--muted);line-height:1.7}.warn{color:#fde68a}.bad{color:#fecaca}
  </style>
</head>
<body>
  <main class="wrap">
    <header>
      <h1>PitchFlow RubberBand</h1>
      <p class="lead">実用品質を狙うため、ブラウザ内の簡易処理ではなく、サーバー側の Rubber Band Library でテンポ維持の移調を行います。</p>
      <span class="pill">Rubber Band Library</span>
      <span class="pill">FFmpeg</span>
      <span class="pill">Tempo Preserve</span>
      <span class="pill">Max {{ max_mb }}MB</span>
    </header>

    <section class="card">
      <label>1. 音源ファイルを選択</label>
      <input id="audio" type="file" accept="audio/*">
      <p class="note">MP3 / WAV / M4A / AAC / FLAC などに対応。まずは1曲未満の短め音源で動作確認してください。</p>
    </section>

    <section class="card grid">
      <div>
        <label>2. 移調量</label>
        <input id="semitones" type="range" min="-12" max="12" step="1" value="0">
        <div class="value"><span id="semiLabel">0</span> 半音</div>
      </div>
      <div>
        <label>3. 変換品質</label>
        <select id="quality">
          <option value="high" selected>High：標準・音楽向け</option>
          <option value="crisp">Crisp：輪郭重視</option>
          <option value="fast">Fast：軽い・確認用</option>
        </select>
      </div>
    </section>

    <section class="card">
      <button id="convert" disabled>高品質変換する</button>
      <div style="height:14px"></div>
      <div class="bar"><div id="progress"></div></div>
      <p id="status" class="status">音源を選択してください。</p>
    </section>

    <section class="card">
      <label>変換後プレビュー</label>
      <audio id="player" controls></audio>
      <div class="row" style="margin-top:12px">
        <a id="downloadLink" style="display:none" download="pitchflow.wav"><button type="button">WAVを保存</button></a>
        <button id="clear" class="secondary" type="button">リセット</button>
      </div>
      <p class="note warn">注意：変換時は音源がサーバーへ一時送信されます。処理後に一時ファイルは削除されます。</p>
      <p class="note bad">著作権のある音源は、権利上問題ない範囲で利用してください。</p>
    </section>
  </main>

<script>
const fileEl = document.getElementById("audio");
const semiEl = document.getElementById("semitones");
const semiLabel = document.getElementById("semiLabel");
const qualityEl = document.getElementById("quality");
const convertBtn = document.getElementById("convert");
const statusEl = document.getElementById("status");
const progress = document.getElementById("progress");
const player = document.getElementById("player");
const downloadLink = document.getElementById("downloadLink");
const clearBtn = document.getElementById("clear");

let resultUrl = null;

function setStatus(text, percent){
  statusEl.textContent = text;
  if(percent !== undefined) progress.style.width = percent + "%";
}

semiEl.addEventListener("input", () => {
  const v = Number(semiEl.value);
  semiLabel.textContent = v > 0 ? "+" + v : String(v);
});

fileEl.addEventListener("change", () => {
  const file = fileEl.files && fileEl.files[0];
  convertBtn.disabled = !file;
  if(file){
    setStatus(`選択中：${file.name}\n${(file.size/1024/1024).toFixed(1)}MB`, 0);
  }
});

convertBtn.addEventListener("click", async () => {
  const file = fileEl.files && fileEl.files[0];
  if(!file) return;

  if(resultUrl) URL.revokeObjectURL(resultUrl);
  resultUrl = null;
  player.removeAttribute("src");
  downloadLink.style.display = "none";

  const form = new FormData();
  form.append("audio", file);
  form.append("semitones", semiEl.value);
  form.append("quality", qualityEl.value);

  convertBtn.disabled = true;
  setStatus("アップロード・変換中です。曲の長さによって時間がかかります。", 25);

  try {
    const res = await fetch("/convert", { method: "POST", body: form });
    if(!res.ok){
      let msg = "変換に失敗しました。";
      try {
        const data = await res.json();
        msg = data.error || msg;
        if(data.detail) msg += "\\n" + data.detail;
      } catch(e) {}
      throw new Error(msg);
    }

    setStatus("変換済み音源を受信中...", 80);
    const blob = await res.blob();
    resultUrl = URL.createObjectURL(blob);
    player.src = resultUrl;

    const semis = Number(semiEl.value);
    const base = file.name.replace(/\.[^.]+$/, "");
    downloadLink.href = resultUrl;
    downloadLink.download = `${base}_pitch_${semis > 0 ? "+" : ""}${semis}.wav`;
    downloadLink.style.display = "block";

    setStatus("変換完了。再生して確認してください。", 100);
  } catch (err) {
    console.error(err);
    setStatus(String(err.message || err), 0);
  } finally {
    convertBtn.disabled = false;
  }
});

clearBtn.addEventListener("click", () => {
  fileEl.value = "";
  semiEl.value = "0";
  semiLabel.textContent = "0";
  convertBtn.disabled = true;
  if(resultUrl) URL.revokeObjectURL(resultUrl);
  resultUrl = null;
  player.removeAttribute("src");
  player.load();
  downloadLink.style.display = "none";
  setStatus("音源を選択してください。", 0);
});
</script>
</body>
</html>
