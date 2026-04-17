/**
 * FileDrop v2.0 — common.js
 * Shared utility functions used by both sender.js and receiver.js
 */

/**
 * Format bytes into a human-readable string.
 * @param {number} b - bytes
 * @returns {string}
 */
function fmtSize(b) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
  return b.toFixed(1) + ' ' + units[i];
}

/**
 * Return an emoji icon for a given filename based on extension.
 * @param {string} name
 * @returns {string}
 */
function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const map = {
    mp4: '🎬', mkv: '🎬', avi: '🎬', mov: '🎬', webm: '🎬',
    zip: '📦', tar: '📦', gz:  '📦', rar: '📦', '7z': '📦',
    pdf: '📄',
    doc: '📝', docx: '📝', txt: '📝', md:  '📝',
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️',
    iso: '💿', dmg: '💿',
    exe: '⚙️', msi: '⚙️', apk: '📱',
    mp3: '🎵', wav: '🎵', flac: '🎵', aac: '🎵',
    py:  '🐍', js:  '📜', ts:  '📜', html: '🌐', css: '🎨',
  };
  return map[ext] || '📁';
}

/**
 * Generate a short random ID for a file transfer.
 * @returns {string}
 */
function makeFileId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}
