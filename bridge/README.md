# 🦥 StudySloth AI Local Bridge

The **StudySloth AI Local Bridge** is a lightweight, secure loopback service that runs on your local computer. It allows the publicly hosted StudySloth web frontend (e.g. on Vercel) or the local companion app to interact with your locally running Ollama instance without ever sending notes, documents, or prompts to any remote cloud server.

---

## 🛡️ Security Architecture

The bridge is designed with strict security constraints:

1. **Loopback Only (`127.0.0.1`)**: Binds exclusively to `127.0.0.1:8765`. It never listens on `0.0.0.0` or public network adapters.
2. **DNS Rebinding Protection**: Validates the `Host` header on every request against an exact loopback list (`127.0.0.1:8765`, `localhost:8765`). External hostnames are rejected with HTTP 400.
3. **Strict Origin Enforcement**: Only requests bearing an approved `Origin` header (such as `https://studysloth-ai.vercel.app` or local development ports) are processed. Malicious third-party websites cannot query the bridge.
4. **Short-Lived Pairing & Session Tokens**:
   - On startup, the bridge displays an 8-character pairing code (e.g., `A7B2-C9D4`) valid for 5 minutes.
   - When entered into the web app, the bridge exchanges it for a cryptographically secure 256-bit bearer token (`X-Bridge-Token`), stored only in the browser's temporary `sessionStorage`.
   - Brute-force rate limiting: 5 failed attempts locks pairing for 60 seconds.
5. **CSRF Immunity**: All data-processing endpoints require the custom header `X-Bridge-Token` and JSON/multipart content types. Standard HTML tags (`<form>`, `<img>`, `<script>`) cannot forge these headers.
6. **No Arbitrary Proxying**: Only `/api/health`, `/api/extract`, `/api/generate`, `/api/pair`, and `/api/unpair` are exposed. Administrative Ollama endpoints (like model deletion or arbitrary shell commands) are strictly unreachable.
7. **Zero Remote Data Storage**: Uploaded files and study notes are processed locally in memory. Nothing is ever written to disk or sent to Vercel.

---

## 🌐 Browser Security & Companion Mode

### The HTTPS-to-Loopback Challenge
Modern web browsers enforce security policies when an `https://` site (like `https://studysloth-ai.vercel.app`) communicates with an `http://127.0.0.1` address:
- **Chromium / Chrome / Edge**: Uses W3C **Private Network Access (PNA)**. The bridge sends `Access-Control-Allow-Private-Network: true` to satisfy this.
- **Firefox & Safari**: Strictly block mixed content (`http://127.0.0.1` from `https://`) unless manually overridden in advanced browser flags.

### 🌟 Universal Solution: Local Companion Mode
To guarantee 100% compatibility across **all browsers** without configuring browser flags:
```powershell
python bridge/bridge.py --open
```
The bridge automatically serves the production frontend build directly from `http://127.0.0.1:8765` and opens it in your default browser. This operates entirely within a first-party local context with zero mixed-content restrictions!

---

## 🚀 How to Run the Bridge

### Windows (PowerShell)
```powershell
# 1. Open PowerShell in the project directory:
cd C:\Users\ADMIN\OneDrive\Desktop\studysloth

# 2. Ensure Ollama is running:
ollama run llama3.2:1b

# 3. Start the bridge:
.\.venv\Scripts\python bridge/bridge.py
```

### macOS / Linux (Terminal)
```bash
# 1. Activate your virtual environment:
source .venv/bin/activate

# 2. Start the bridge:
python bridge/bridge.py
```

### Custom Allowed Origin (for your Vercel URL)
If your Vercel deployment has a custom URL:
```bash
python bridge/bridge.py --allowed-origin https://your-project.vercel.app
```

---

## 🛑 How to Stop the Bridge
Press `Ctrl + C` in the terminal where the bridge is running. The server terminates cleanly and immediately shuts down all active sessions.
