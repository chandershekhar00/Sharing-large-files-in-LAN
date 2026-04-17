# FileDrop v2.0 📡

Transfer files up to **100 GB** between any two computers — on your local network (LAN) or over the internet. Zero dependencies, pure Python stdlib, runs on Windows / Mac / Linux.

---

## Project Structure

```
filedrop/
├── server.py          ← Entry point — start here
├── config.py          ← All settings in one place
├── handler.py         ← HTTP request router & API logic
├── transfers.py       ← In-memory transfer state manager
├── templates.py       ← HTML template loader
├── utils.py           ← Helpers: IP detection, file assembly, formatting
│
├── templates/
│   ├── sender.html    ← Sender browser UI
│   └── receiver.html  ← Receiver browser UI
│
└── static/
    ├── css/
    │   ├── common.css   ← Shared styles (themes, layout, cards)
    │   ├── sender.css   ← Sender-specific styles
    │   └── receiver.css ← Receiver-specific styles
    └── js/
        ├── common.js    ← Shared utilities (fmtSize, fileIcon, makeFileId)
        ├── sender.js    ← Upload logic, progress UI
        └── receiver.js  ← Polling, transfer card rendering
```

---

## Requirements

- **Python 3.6+** — no pip installs needed (uses stdlib only)
- **ngrok** (optional) — for internet transfers: https://ngrok.com/download

---

## Quick Start

### Step 1 — Start the server (on the receiving machine)

```bash
python server.py
```

Options:
```
--port 8765          Port to listen on (default: 8765)
--dir ./downloads    Where to save received files (default: ./received_files)
--host 0.0.0.0       Bind address (default: all interfaces)
```

### Step 2 — Open in browser

| Role     | URL                                   |
|----------|---------------------------------------|
| Sender   | `http://<receiver-ip>:8765/`          |
| Receiver | `http://<receiver-ip>:8765/receive`   |

The server prints the exact LAN URLs on startup.

---

## Internet Transfer (different networks)

On the receiver machine, open a **second terminal**:

```bash
ngrok http 8765
```

ngrok gives you a public URL like `https://abc123.ngrok.io`. Share:

| Role     | URL                                       |
|----------|-------------------------------------------|
| Sender   | `https://abc123.ngrok.io/`                |
| Receiver | `https://abc123.ngrok.io/receive`         |

**Alternatives to ngrok:** `cloudflared tunnel`, `bore`, `localtunnel`

---

## How It Works

1. Sender selects files via drag-and-drop or file picker
2. Files are split into **4 MB chunks** and uploaded one by one
3. Each chunk is written to disk immediately (no RAM pressure)
4. On completion, chunks are **assembled** into the final file
5. Receiver page auto-refreshes every 2 seconds, showing live progress
6. A **Download** button appears when each file is ready

---

## Customisation

Edit **`config.py`** to change defaults:

```python
Config.CHUNK_SIZE        = 4 * 1024 * 1024   # 4 MB — increase for faster LAN
Config.REFRESH_INTERVAL_MS = 2000             # Receiver poll interval
Config.MAX_FILE_SIZE     = 100 * 1024 ** 3   # 100 GB hard limit
```

---

## Performance Estimates

| Network        | Speed          | 1 GB      | 10 GB      | 100 GB     |
|----------------|----------------|-----------|------------|------------|
| LAN (1 Gbps)   | ~100 MB/s      | ~10 sec   | ~1.5 min   | ~15 min    |
| WiFi 5 GHz     | ~40 MB/s       | ~25 sec   | ~4 min     | ~40 min    |
| Internet (100M)| ~12 MB/s       | ~85 sec   | ~14 min    | ~2.5 hrs   |

---

## Tips

- Use a **wired connection** for maximum LAN speed
- For files over 10 GB, ensure the receiving drive has enough free space
- Received files are stored in `./received_files/<file_id>/<filename>`
- The server can handle **multiple simultaneous transfers**
