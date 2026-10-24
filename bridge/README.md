# 🦥 StudySloth AI Local Bridge

The **StudySloth AI Local Bridge** is a lightweight, secure loopback service that runs on your personal computer. It enables the publicly hosted StudySloth web application (on Vercel) or the local companion app to connect to your locally running Ollama instance without ever transmitting your study notes, uploaded documents, or prompts to any remote cloud server.

---

## 🏗️ Architecture

```
                                          ┌───────────────────────────────────────────────┐
                                          │            Your Personal Computer             │
┌───────────────────────────────┐         │                                               │
│    Vercel Hosted Frontend     │  CORS   │  ┌─────────────────┐     HTTP     ┌─────────┐ │
│  (https://<app>.vercel.app)   │ ──────> │  │  Local Bridge   │ ───────────> │ Ollama  │ │
│              OR               │   PNA   │  │ 127.0.0.1:8765  │  (loopback)  │ :11434  │ │
│   Local Companion Frontend    │         │  └─────────────────┘              └─────────┘ │
│    (http://127.0.0.1:8765)    │         │                                               │
└───────────────────────────────┘         └───────────────────────────────────────────────┘
```

1. **Vercel Frontend**: Delivers the user interface (React + Vite) statically from CDN. No server-side storage, no backend database.
2. **Local Bridge (`bridge/bridge.py`)**: Runs strictly on `127.0.0.1:8765`, enforcing authentication, DNS rebinding guards, rate limits, and document parsing.
3. **Local Ollama**: Runs the open-weight model (`llama3.2:1b`) directly on your machine's CPU/GPU.

---

## 🛡️ Security Features

- **Loopback Exclusive (`127.0.0.1`)**: Binds only to `127.0.0.1`. It never listens on `0.0.0.0` or external network interfaces.
- **DNS Rebinding Guard**: Validates the HTTP `Host` header on every request against loopback hosts (`127.0.0.1:8765`, `localhost:8765`). Requests from external or spoofed hostnames are rejected with HTTP 400.
- **Strict Origin Enforcement**: Only requests from authorized origins (such as `https://studysloth-ai.vercel.app`, custom Vercel URLs, or local companion ports) are accepted.
- **Ephemeral Pairing Codes**: Generates an 8-character code (`A7B2-C9D4`) with a 5-minute expiry. An attacker cannot guess this without triggering rate-limit lockouts (5 failed attempts locks for 60 seconds).
- **Constant-Time Token Validation**: Validates session tokens using `hmac.compare_digest` to prevent timing attacks.
- **CSRF Immunity**: Requires custom `X-Bridge-Token` headers for all data operations; standard browser cross-origin forms or images cannot forge this.
- **No Disk Logging**: Prompts, notes, and generated study aids are processed exclusively in RAM and never written to disk.

---

## 🌐 Browser Compatibility & Mixed Content

| Browser | Hosted HTTPS App (`*.vercel.app`) | Companion App (`127.0.0.1:8765`) |
| :--- | :---: | :---: |
| **Google Chrome** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Microsoft Edge** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Brave / Opera** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Mozilla Firefox** | ⚠️ Blocked by mixed content (HTTPS to HTTP) | ✅ 100% Supported |
| **Apple Safari** | ⚠️ Blocked by mixed content (HTTPS to HTTP) | ✅ 100% Supported |

> 💡 **Universal Companion Mode**: Firefox and Safari block HTTPS websites from querying HTTP loopback addresses. If you use Firefox or Safari, launch the bridge with `--open` (or use `start_bridge.bat` / `start_bridge.sh`). The bridge serves the complete web app directly from `http://127.0.0.1:8765` with zero mixed-content restrictions.

---

## 🚀 Quick Start for End Users

### Step 1: Install Ollama & Download the Model
1. Download Ollama from [ollama.com](https://ollama.com/download).
2. Open your terminal and pull the recommended lightweight model:
   ```bash
   ollama pull llama3.2:1b
   ```

### Step 2: Start the Bridge

#### Option A: One-Click Launchers (Recommended)
- **Windows**: Double-click `start_bridge.bat` (or right-click `start_bridge.ps1` -> Run with PowerShell).
- **macOS / Linux**: Open Terminal and run:
  ```bash
  chmod +x start_bridge.sh
  ./start_bridge.sh
  ```

#### Option B: Manual Command Line
Using the minimal dependencies (`requirements-bridge.txt`):
```bash
pip install -r requirements-bridge.txt
python bridge/bridge.py --open
```

### Step 3: Connect and Pair
1. The bridge will print your terminal session code:
   ```text
   ================================================================
    🦥 StudySloth AI Local Bridge Server
   ================================================================
    Status:             Running on http://127.0.0.1:8765
    🔑 YOUR SESSION PAIRING CODE:  A7B2-C9D4
   ================================================================
   ```
2. Open the StudySloth web app (on Vercel or at `http://127.0.0.1:8765`).
3. Click **Connect to Local Ollama**, enter the 8-character pairing code, and click **Pair & Connect**.

---

## ⚙️ Configuring Custom Allowed Origins

When hosting your own frontend deployment on Vercel, you can authorize your domain in three ways:

### 1. Command-Line Argument
```bash
python bridge/bridge.py --allowed-origin https://your-project.vercel.app
```
*(You can pass `--allowed-origin` multiple times or comma-separated).*

### 2. Environment Variable
- **PowerShell**:
  ```powershell
  $env:STUDYSLOTH_ALLOWED_ORIGIN="https://your-project.vercel.app"
  python bridge/bridge.py
  ```
- **macOS / Linux**:
  ```bash
  export STUDYSLOTH_ALLOWED_ORIGIN="https://your-project.vercel.app"
  python bridge/bridge.py
  ```

### 3. Local Configuration File (`.bridge_config.json`)
Create a file named `.bridge_config.json` in the project root:
```json
{
  "allowed_origins": [
    "https://your-custom-domain.com",
    "https://your-project.vercel.app"
  ]
}
```

---

## 🛑 Stopping the Bridge
Press `Ctrl + C` in the terminal where the bridge is running. The server terminates cleanly and immediately invalidates all active session tokens.
