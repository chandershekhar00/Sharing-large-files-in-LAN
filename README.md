# 📡 FileDrop v2.0

### Large File Transfer System (LAN + Internet)

FileDrop is a **zero-dependency Python application** that enables fast and reliable transfer of large files (100GB+) between devices using a simple web browser.

No installation. No accounts. No cloud limitations.

---

## 🎥 Demo Video

👉 Watch Demo: **[Add your demo video link here]**

---

## 🚀 Features

* ⚡ Transfer files up to **100GB+**
* 🌐 Works on **LAN and Internet**
* 🧩 Chunk-based upload system (4MB chunks)
* 💻 Browser-based UI (no software needed for sender)
* 📊 Real-time progress (speed, percentage, ETA)
* 📦 Zero dependencies (pure Python standard library)

---

## 🧠 How It Works

FileDrop uses a **3-phase upload protocol**:

### 1. Initialization

* Sender sends file metadata (name, size, chunks)

### 2. Chunk Upload

* File is split into small chunks (4MB each)
* Each chunk is uploaded sequentially

### 3. Completion

* Server assembles chunks into final file
* File becomes available for download

---

## 🏗️ Tech Stack

* **Backend:** Python 3.6+ (HTTPServer)
* **Frontend:** HTML, CSS, JavaScript
* **Protocol:** REST API + Polling
* **Optional:** ngrok (for internet access)

---

## 📂 Project Structure

```
filedrop/
│── server.py        # Entry point
│── handler.py       # Request handling & API
│── config.py        # Configuration settings
│── transfers.py     # Transfer state management
│── utils.py         # Utility functions
│── templates.py     # HTML rendering

templates/
static/
```

---

## ⚡ Quick Start

### 1️⃣ Start Server (Receiver)

```bash
python server.py
```

---

### 2️⃣ Open in Browser

* Sender: `http://<your-ip>:8765/`
* Receiver: `http://<your-ip>:8765/receive`

---

### 3️⃣ Send Files

* Drag & drop files in sender page
* Click **Send Files**
* Monitor progress in real-time
* Download from receiver page

---

## 🌍 Internet Transfer (Optional)

Use ngrok:

```bash
ngrok http 8765
```

Share:

* Sender: `https://xxxx.ngrok.io/`
* Receiver: `https://xxxx.ngrok.io/receive`

---

## 📊 Performance

| Network Type   | Speed                   |
| -------------- | ----------------------- |
| LAN (Ethernet) | ~100 MB/s               |
| Wi-Fi          | 10–60 MB/s              |
| Internet       | Depends on upload speed |

---

## ⚙️ Configuration

Edit `config.py`:

* `CHUNK_SIZE` → Default 4MB
* `MAX_FILE_SIZE` → 100GB
* `PORT` → 8765
* `UPLOAD_DIR` → File storage location

---

## ⚠️ Security Considerations

* ❌ No authentication (yet)
* ❌ No encryption on LAN
* ✅ HTTPS supported via ngrok

---

## 🔮 Future Enhancements

* 🔐 Password protection
* ✅ File checksum verification
* 🔄 Resume interrupted transfers
* 🚀 Parallel chunk uploads
* 📱 QR code sharing

---

## 👨‍💻 Author

**Chandrashekhar Tyagi**
📧 [chandershekhar8433@gmail.com](mailto:chandershekhar8433@gmail.com)
📱 +91 8439443923

---

## 📜 License

This project is created for educational and personal use.
