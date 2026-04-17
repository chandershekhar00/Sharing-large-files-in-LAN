/**
 * FileDrop v2.0 — sender.js
 * Handles: file selection, drag-and-drop, chunked upload, progress display.
 * Depends on: common.js (fmtSize, fileIcon, makeFileId)
 * CHUNK_SIZE is injected by the HTML template from server config.
 */

// ── State ─────────────────────────────────────────────────────────────────────
let filesToSend   = [];
let transferring  = false;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const dropZone  = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList  = document.getElementById('file-list');
const sendBtn   = document.getElementById('send-btn');

// ── Drag & drop ───────────────────────────────────────────────────────────────
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  addFiles([...e.dataTransfer.files]);
});
fileInput.addEventListener('change', () => {
  addFiles([...fileInput.files]);
  fileInput.value = '';
});

// ── File management ───────────────────────────────────────────────────────────
function addFiles(files) {
  files.forEach(f => {
    // Deduplicate by name + size
    if (filesToSend.find(x => x.name === f.name && x.size === f.size)) return;
    const idx = filesToSend.length;
    filesToSend.push(f);

    const el = document.createElement('div');
    el.className = 'file-item';
    el.innerHTML = `
      <div class="file-icon">${fileIcon(f.name)}</div>
      <div class="file-info">
        <div class="file-name">${escHtml(f.name)}</div>
        <div class="file-size">${fmtSize(f.size)}</div>
      </div>
      <button class="file-remove" title="Remove" onclick="removeFile(${idx}, this.closest('.file-item'))">✕</button>`;
    fileList.appendChild(el);
  });
  refreshSendBtn();
}

function removeFile(idx, el) {
  filesToSend.splice(idx, 1);
  el.remove();
  refreshSendBtn();
}

function refreshSendBtn() {
  sendBtn.disabled = filesToSend.length === 0 || transferring;
}

// ── Message helpers ───────────────────────────────────────────────────────────
function showMsg(type, text = '') {
  ['success', 'error', 'info'].forEach(t => {
    document.getElementById('msg-' + t).style.display = t === type ? 'block' : 'none';
  });
  if (type === 'error') document.getElementById('err-text').textContent  = text;
  if (type === 'info')  document.getElementById('info-text').textContent = text;
}

function hideAllMsgs() {
  showMsg(null);
}

// ── Transfer orchestration ────────────────────────────────────────────────────
async function startTransfer() {
  if (transferring || filesToSend.length === 0) return;
  transferring = true;
  sendBtn.disabled = true;
  document.getElementById('progress-wrap').style.display = 'block';
  hideAllMsgs();
  showMsg('info', 'Starting transfer…');

  try {
    for (const file of filesToSend) {
      await uploadFile(file);
    }
    showMsg('success');
    // Show completed card
    document.getElementById('completed-card').style.display = 'block';
    filesToSend = [];
    fileList.innerHTML = '';
  } catch (err) {
    showMsg('error', err.message || 'Transfer failed. Please try again.');
  } finally {
    transferring = false;
    refreshSendBtn();
  }
}

// ── Single-file upload (chunked) ──────────────────────────────────────────────
async function uploadFile(file) {
  const fileId      = makeFileId();
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

  // Set progress UI
  document.getElementById('progress-filename').textContent = file.name;
  setProgress(0, file.size, 0, '—', '—');

  // ── INIT ──────────────────────────────────────────────────────────────────
  const initRes = await fetch('/api/upload/init', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, filename: file.name, size: file.size, total_chunks: totalChunks }),
  });
  if (!initRes.ok) throw new Error('Server rejected transfer initialisation');

  // ── CHUNKS ────────────────────────────────────────────────────────────────
  let bytesUploaded = 0;
  let speedSamples  = [];
  let lastTs        = Date.now();
  let lastBytes     = 0;

  for (let i = 0; i < totalChunks; i++) {
    const start     = i * CHUNK_SIZE;
    const end       = Math.min(start + CHUNK_SIZE, file.size);
    const chunkBlob = file.slice(start, end);

    const fd = new FormData();
    fd.append('file_id',     fileId);
    fd.append('chunk_index', i);
    fd.append('chunk',       chunkBlob);

    const res = await fetch('/api/upload/chunk', { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`Chunk ${i + 1}/${totalChunks} failed (HTTP ${res.status})`);

    bytesUploaded += end - start;

    // Speed / ETA every ~500ms
    const now     = Date.now();
    const elapsed = (now - lastTs) / 1000;
    if (elapsed >= 0.5) {
      const speed = (bytesUploaded - lastBytes) / elapsed;
      speedSamples.push(speed);
      if (speedSamples.length > 8) speedSamples.shift();
      const avgSpeed = speedSamples.reduce((a, b) => a + b, 0) / speedSamples.length;
      const eta      = (file.size - bytesUploaded) / avgSpeed;
      const etaStr   = eta < 60 ? Math.round(eta) + 's' : Math.round(eta / 60) + 'm';
      setProgress(bytesUploaded, file.size, avgSpeed, etaStr, file.name);
      lastTs    = now;
      lastBytes = bytesUploaded;
    }
  }

  // Ensure 100%
  setProgress(file.size, file.size, 0, '0s', file.name);

  // ── COMPLETE ──────────────────────────────────────────────────────────────
  const completeRes = await fetch('/api/upload/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, filename: file.name }),
  });
  if (!completeRes.ok) throw new Error('Server failed to assemble the file');

  // Add to completed card
  const li = document.createElement('div');
  li.className = 'completed-item';
  li.innerHTML = `
    <div class="completed-dot"></div>
    <span>${escHtml(file.name)}</span>
    <span style="margin-left:auto;color:var(--muted);font-size:0.7rem;font-family:var(--mono)">${fmtSize(file.size)}</span>`;
  document.getElementById('completed-list').appendChild(li);
}

// ── Progress helpers ──────────────────────────────────────────────────────────
function setProgress(received, total, speedBps, eta, name) {
  const pct = total > 0 ? (received / total * 100).toFixed(1) : '0.0';
  document.getElementById('progress-fill').style.width     = pct + '%';
  document.getElementById('progress-pct').textContent      = pct + '%';
  document.getElementById('stat-sent').textContent         = fmtSize(received);
  if (speedBps > 0)
    document.getElementById('stat-speed').textContent      = fmtSize(speedBps) + '/s';
  if (eta !== '—')
    document.getElementById('stat-eta').textContent        = eta;
  if (name)
    document.getElementById('progress-filename').textContent = name;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
