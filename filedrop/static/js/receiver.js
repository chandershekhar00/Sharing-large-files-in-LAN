/**
 * FileDrop v2.0 — receiver.js
 * Polls /api/status and renders live transfer cards with progress.
 * Depends on: common.js (fmtSize, fileIcon)
 * REFRESH_INTERVAL is injected by the HTML template from server config.
 */

// ── State ─────────────────────────────────────────────────────────────────────
const knownIds = new Set();

// ── DOM refs ──────────────────────────────────────────────────────────────────
const container  = document.getElementById('transfers-container');
const emptyState = document.getElementById('empty-state');

// ── Poll loop ─────────────────────────────────────────────────────────────────
async function refresh() {
  try {
    const res  = await fetch('/api/status');
    if (!res.ok) return;
    const data = await res.json();

    const all = [
      ...(data.active    || []),
      ...(data.completed || []),
    ];

    if (all.length > 0 && emptyState) {
      emptyState.style.display = 'none';
    }

    all.forEach(renderTransfer);
  } catch (e) {
    // Silently ignore network errors (server may be temporarily busy)
    console.warn('[FileDrop] Refresh error:', e);
  }
}

// ── Render a single transfer card ─────────────────────────────────────────────
function renderTransfer(t) {
  const done = t.status === 'complete';
  const pct  = t.size > 0 ? Math.round(t.received / t.size * 100) : 0;

  if (!knownIds.has(t.file_id)) {
    // ── Create new card ──────────────────────────────────────────────────────
    knownIds.add(t.file_id);

    const card = document.createElement('div');
    card.className = 'transfer-card';
    card.id        = 'tc-' + t.file_id;
    card.innerHTML = buildCardHTML(t, pct, done);

    // Insert newest at top
    const firstCard = container.querySelector('.transfer-card');
    if (firstCard) container.insertBefore(card, firstCard);
    else           container.appendChild(card);

  } else {
    // ── Update existing card ─────────────────────────────────────────────────
    updateCard(t.file_id, t, pct, done);
  }
}

function buildCardHTML(t, pct, done) {
  return `
    <div class="transfer-top">
      <div class="t-icon">${fileIcon(t.filename)}</div>
      <div style="flex:1;min-width:0">
        <div class="t-name">${escHtml(t.filename)}</div>
        <div class="t-size">${fmtSize(t.size)}</div>
      </div>
      <span class="t-badge ${done ? '' : 'inprog'}" id="badge-${t.file_id}">
        ${done ? 'Complete' : 'Receiving…'}
      </span>
    </div>
    <div class="pbar-bg">
      <div class="pbar-fill" id="pf-${t.file_id}" style="width:${pct}%"></div>
    </div>
    <div class="t-stats">
      <span><span class="sv" id="pr-${t.file_id}">${fmtSize(t.received)}</span> / ${fmtSize(t.size)}</span>
      <span><span class="sv" id="pp-${t.file_id}">${pct}%</span></span>
    </div>
    <div id="dl-${t.file_id}">
      ${done ? dlButton(t.file_id) : ''}
    </div>`;
}

function updateCard(fileId, t, pct, done) {
  const fill  = document.getElementById('pf-'    + fileId);
  const prEl  = document.getElementById('pr-'    + fileId);
  const ppEl  = document.getElementById('pp-'    + fileId);
  const badge = document.getElementById('badge-' + fileId);
  const dlEl  = document.getElementById('dl-'    + fileId);

  if (fill)  fill.style.width  = pct + '%';
  if (prEl)  prEl.textContent  = fmtSize(t.received);
  if (ppEl)  ppEl.textContent  = pct + '%';

  if (done && badge) {
    badge.textContent = 'Complete';
    badge.classList.remove('inprog');
  }

  if (done && dlEl && !dlEl.innerHTML.trim()) {
    dlEl.innerHTML = dlButton(fileId);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function dlButton(fileId) {
  return `<a class="dl-btn" href="/download/${fileId}">⬇ Download</a>`;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Boot ──────────────────────────────────────────────────────────────────────
refresh();
setInterval(refresh, typeof REFRESH_INTERVAL !== 'undefined' ? REFRESH_INTERVAL : 2000);
