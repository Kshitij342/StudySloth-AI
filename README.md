# 🦥 StudySloth AI

> **"Slow and steady wins the race."**  
> A 100% local, private, on-device AI study assistant powered by open-weight models and Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-black.svg)](https://ollama.com/)
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25%20On--Device-success.svg)](#-privacy--the-power-of-open-weight-ai)

---

## 📖 Table of Contents
- [About StudySloth AI](#-about-studysloth-ai)
- [The "Slow and Steady" Learning Philosophy](#-the-slow-and-steady-learning-philosophy)
- [Privacy & The Power of Open-Weight AI](#-privacy--the-power-of-open-weight-ai)
- [Recommended Open-Weight Models & Hardware Matrix](#-recommended-open-weight-models--hardware-matrix)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Prerequisites & Model Setup](#-prerequisites--model-setup)
- [How to Run Version 1: Standalone Streamlit App](#-version-1-standalone-streamlit-app)
- [How to Run Version 2: Web App & Local Bridge](#-version-2-web-app--local-bridge)
- [Vercel Deployment Guide](#-vercel-deployment-guide)
- [Browser Security & Compatibility Matrix](#-browser-security--compatibility-matrix)
- [Offline Verification & Workflow](#-offline-verification--workflow)
- [Known Limitations & Technical Boundaries](#-known-limitations--technical-boundaries)
- [Running the Automated Test Suite](#-running-the-automated-test-suite)
- [Troubleshooting Common Issues](#-troubleshooting-common-issues)
- [Contributing & License](#-contributing--license)

---

## 🌿 About StudySloth AI

Most commercial AI study tools send sensitive lecture notes, unpublished research papers, and school documents across the public internet to cloud APIs—retaining user prompts, tracking usage, and charging recurring subscriptions.

**StudySloth AI** takes an entirely local-first approach:
- It prioritizes **deep, structured comprehension** over hurried skimming.
- It runs **entirely on your own computer** using **open-weight AI models** powered by [Ollama](https://ollama.com).
- **Zero cloud API keys. Zero subscriptions. Zero telemetry. Zero data leaks.**

Whether you are studying biology, preparing for university exams, or reviewing complex documentation, StudySloth transforms raw notes and files into **structured summaries, key concepts, terminology glossaries, active recall flashcards, and multiple-choice quizzes**.

---

## 🦥 The "Slow and Steady" Learning Philosophy

StudySloth is built around the principle that **sustainable comprehension outperforms hurried cramming**:

1. **Cognitive Pacing**: Rather than dumping a single unstructured block of text, StudySloth distills study material into sequential, digestible stages: Executive Summaries → Core Takeaways → Definitions → Active Recall Flashcards → Practice Quizzes.
2. **Local AI Sovereignty**: Running compact open-weight models (1B to 3B parameters) on consumer hardware takes a few seconds longer than massive remote data centers, but the benefit is total privacy, zero dependency on third-party servers, and offline resilience.
3. **Active Recall**: Built-in interactive flashcard flipping and automated quiz grading encourage active memory retrieval rather than passive reading.

---

## 🛡️ Privacy & The Power of Open-Weight AI

### 1. Absolute Data Sovereignty
Commercial cloud AI services reserve the right to log, inspect, and train on user prompts. For students, researchers, and professionals handling:
- Medical case studies or patient notes
- Unpublished academic dissertations
- Proprietary internal manuals
- Personal notes or sensitive records

StudySloth guarantees that **not a single syllable leaves your local machine (`localhost:11434`)**.

### 2. Predictable Costs & No Subscription Fatigue
Cloud APIs charge per token and impose rate limits. StudySloth is free and open-source—no API tokens, no monthly credit cards, and no unexpected overage charges.

### 3. True Offline Resilience
You can study on an airplane, in an underground library, or during a retreat without internet access. Once the model weights are downloaded once, **StudySloth operates 100% offline**.

---

## 🧠 Recommended Open-Weight Models & Hardware Matrix

StudySloth is engineered to run smoothly on everyday consumer laptops without requiring expensive GPUs:

| Model | Parameter Size | Download Size | Minimum RAM | Recommended Hardware | License | Best Suited For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Llama 3.2 1B** *(Recommended Default)* | 1.23 Billion | ~1.3 GB | 4 GB | Any modern Intel/AMD CPU or Apple Silicon | Meta Llama 3.2 Community | Fast summaries, key points, rapid flashcards on budget laptops |
| **Llama 3.2 3B** | 3.21 Billion | ~2.0 GB | 8 GB | 8 GB RAM / 2 GB VRAM | Meta Llama 3.2 Community | Perfect sweet spot for complex quizzes and comprehensive study packs |
| **Phi-3 Mini** | 3.82 Billion | ~2.2 GB | 8 GB | 8 GB RAM / 2-4 GB VRAM | MIT License | High mathematical reasoning, STEM, code explanations |
| **Qwen 2.5 1.5B** | 1.54 Billion | ~1.0 GB | 4 GB | Any modern CPU | Apache 2.0 | Permissive open-source license with high structured JSON compliance |

### Trade-offs:
- **Small Models (1B - 3B)**: Instantaneous startup, minimal RAM footprint, runs on CPU battery power. Bounded context window is handled in StudySloth via automatic text sanitization and safe trimming.
- **Larger Models (7B - 8B)**: Deeper nuance and broader general knowledge, but requires 16 GB RAM or a dedicated GPU and generates slower on CPU.

---

## ✨ Key Features

1. **Sloth-Themed Visual Experience**: Calming forest green palette, clean typography, distraction-free layout, and interactive sloth mascot states.
2. **Flexible Input Handling**:
   - Direct text pasting with real-time character, word, and reading-time counters.
   - Upload `.txt`, `.pdf`, and `.docx` documents up to 10 MB.
3. **6 Specialized Study Aid Formats**:
   - 📝 **Executive Summary**: Structured 3-part overview (Context, Mechanics, Big-Picture Takeaway).
   - 📌 **High-Yield Key Points**: Bolded takeaways organized for rapid exam review.
   - 📖 **Glossary & Definitions**: Unambiguous definitions with contextual applications.
   - 🗂️ **Active Recall Flashcards**: Question & Answer pairs for memory consolidation.
   - 🎯 **Multiple-Choice Quiz**: 4-option questions with correct answer key and explanations.
   - 🌟 **Comprehensive Study Pack**: All formats synthesized into an all-in-one guide.
4. **Interactive Practice Suite**:
   - **Interactive Flashcards**: Flip cards, toggle "Reveal Answer", navigate previous/next.
   - **Interactive Quiz Runner**: Radio button answers, instant automated grading, and live score calculation.
5. **Multi-Format Exporting**:
   - Download as **Markdown (`.md`)**
   - Download as **Plain Text (`.txt`)**
   - Download as **JSON (`.json`)** (ready for import into Anki or spaced repetition software)
   - One-click copy code block
6. **Live Hardware & Server Monitor**:
   - Live health indicator: 🟢 Ollama Online / 🔴 Ollama Offline.
   - Model dropdown automatically detects locally installed models.
   - Built-in fallback demo mode for evaluating UI layouts without waiting for model downloads.
7. **Instant Starter Presets**:
   - One-click sample notes for Biology (Cellular Respiration), Computer Science (Big-O & Data Structures), and World History (The Industrial Revolution).

---

## 🏗️ Architecture & Tech Stack

StudySloth AI provides two distinct interfaces sharing the same secure document processing and local Ollama inference pipeline:

```
[Version 1: Standalone Python App (Streamlit)]
User PC:  Browser (localhost:8501) ──> Streamlit Server (app.py) ──> Ollama (127.0.0.1:11434)

[Version 2: Hosted Web Frontend (Vercel) + Secure Local Bridge]
Public:   https://<your-project>.vercel.app (Static React/Vite on Vercel CDN)
             │  (Local fetch with X-Bridge-Token & W3C PNA headers)
             ▼
User PC:  Local Bridge (127.0.0.1:8765) ──> Ollama (127.0.0.1:11434)

[Version 2 Companion: Universal Local Companion Mode]
User PC:  Browser (http://127.0.0.1:8765) ──> Bridge (serves web/dist) ──> Ollama (127.0.0.1:11434)
```

```
studysloth/
├── app.py                         # Version 1: Streamlit standalone application
├── start_bridge.bat               # Windows one-click launcher for Local Bridge + Companion App
├── start_bridge.ps1               # Windows PowerShell launcher for Local Bridge + Companion App
├── start_bridge.sh                # macOS/Linux launcher for Local Bridge + Companion App
├── requirements-bridge.txt        # Minimal dependencies for bridge (requests, pypdf, python-docx)
├── requirements.txt               # Full dependencies (Streamlit, dev tools, and test suite)
├── bridge/
│   ├── __init__.py
│   ├── bridge.py                  # Hardened local Python bridge (127.0.0.1:8765)
│   └── README.md                  # Detailed bridge security architecture
├── web/                           # Version 2: Vercel-ready React + Vite frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── vercel.json                # Vercel static deployment configuration
│   └── src/
│       ├── App.jsx                # Interactive study workstation UI
│       ├── index.css              # Custom sloth aesthetic styling
│       ├── main.jsx
│       └── samples.js             # Built-in study presets
├── utils/
│   ├── document_processor.py      # Local extraction (TXT, PDF, DOCX) & sanitization
│   ├── ollama_client.py           # Local Ollama REST client & health check
│   ├── prompts.py                 # Structured prompt templates & JSON parsers
│   └── samples.py                 # Built-in study notes
└── tests/
    ├── test_bridge.py             # 18 tests for pairing, CSRF, DNS rebinding, PNA, origins
    ├── test_document_processor.py # 9 tests for document processing
    ├── test_ollama_client.py      # 9 tests for Ollama client & streaming
    └── test_prompts.py            # 10 tests for prompt templates
```

---

## 🚀 Prerequisites & Model Setup

### 1. Install Ollama
Download and install Ollama from [ollama.com/download](https://ollama.com/download) for your operating system (Windows, macOS, or Linux).

### 2. Download the Recommended Model
Open your terminal or PowerShell and run:
```bash
ollama run llama3.2:1b
```
*(Once downloaded, you can close the terminal chat session by typing `/bye`. The Ollama service remains running in the background at `http://127.0.0.1:11434`).*

---

## 🖥️ Version 1: Standalone Streamlit App

If you prefer an all-in-one Python desktop application:

```powershell
# 1. Clone repository and navigate into project directory:
cd studysloth

# 2. Create virtual environment and install full requirements:
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 3. Launch Streamlit app:
.\.venv\Scripts\streamlit run app.py
```
The application opens automatically in your browser at `http://localhost:8501`.

---

## 🌐 Version 2: Web App & Local Bridge

Version 2 separates the presentation layer from the inference engine, allowing the web frontend to be hosted on Vercel while keeping all AI processing on the user's personal machine.

### 1. Start the Local Bridge
The local bridge is a lightweight Python service that securely connects the frontend to your local Ollama:

- **Windows One-Click**: Double-click `start_bridge.bat` (or run `.\start_bridge.ps1` in PowerShell).
- **macOS / Linux One-Click**: Run `chmod +x start_bridge.sh && ./start_bridge.sh`.
- **Manual Command Line**:
  ```bash
  pip install -r requirements-bridge.txt
  python bridge/bridge.py --open
  ```

The bridge prints your terminal session pairing code:
```text
================================================================
 🦥 StudySloth AI Local Bridge Server
 Status: Running on http://127.0.0.1:8765
 🔑 YOUR SESSION PAIRING CODE:  A7B2-C9D4
================================================================
```

### 2. Open the Frontend & Connect
- **Hosted Web App**: Visit your Vercel deployment URL (e.g. `https://your-project.vercel.app`).
- **Or Universal Local Companion**: Running with `--open` opens `http://127.0.0.1:8765` directly in your browser.
- Click **⚡ Connect Local AI** in the top navigation bar.
- Enter your 8-character pairing code from the terminal and click **Connect Local AI**.
- Once connected, you can:
  - Choose your model from the **Ollama Model** selector.
  - Click **🔄 Refresh Models** to discover newly pulled models.
  - Click **🧪 Test Connection** to verify live model inference.
  - Click **🚀 Start Studying →** to transition to the study workstation!

---

## 🚀 Vercel Deployment Guide

> **Important Note on Vercel Hosting**: Hosting the frontend on Vercel serves the static web application. It does **not** host Ollama or AI models in the cloud. Each user connects the web app to their own computer's local bridge (`127.0.0.1:8765`) and local Ollama instance (`127.0.0.1:11434`), guaranteeing that notes never leave their machine.

The `web/` directory is pre-configured for zero-configuration deployment on [Vercel](https://vercel.com):

1. Push your repository branch to GitHub.
2. In the Vercel Dashboard, click **Add New Project** and import your repository.
3. Configure the Project Settings:
   - **Root Directory**: `web` (click Edit, select `web`)
   - **Framework Preset**: `Vite` (auto-detected)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Click **Deploy**.
5. Once Vercel assigns your URL (e.g. `https://your-project.vercel.app`), users can authorize the bridge in any of three convenient ways:
   - **Command Line**: `python bridge/bridge.py --allowed-origin https://your-project.vercel.app`
   - **Environment Variable**: Set `STUDYSLOTH_ALLOWED_ORIGIN=https://your-project.vercel.app`
   - **Companion Mode**: Run `python bridge/bridge.py --open` (runs directly on `127.0.0.1:8765` with zero origin friction!)

---

## 🔒 Browser Security & Compatibility Matrix

When connecting an `https://` website to a local loopback IP (`http://127.0.0.1`), modern browsers apply specific security rules:

| Browser | Hosted HTTPS Site (`*.vercel.app`) | Universal Companion Mode (`127.0.0.1:8765`) |
| :--- | :---: | :---: |
| **Google Chrome / Chromium** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Microsoft Edge** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Brave / Opera** | ✅ Supported (via W3C Private Network Access) | ✅ 100% Supported |
| **Mozilla Firefox** | ⚠️ Blocked by mixed content (HTTPS to HTTP) | ✅ 100% Supported |
| **Apple Safari** | ⚠️ Blocked by mixed content (HTTPS to HTTP) | ✅ 100% Supported |

> 💡 **Universal Local Companion Mode**: If you use Firefox or Safari, launch the bridge with `--open` (or run `start_bridge.bat` / `start_bridge.sh`). The bridge serves the complete production web app locally from `http://127.0.0.1:8765`, completely eliminating mixed content.

---

## 🔌 Offline Verification & Workflow

StudySloth is engineered for local-first autonomy:

1. **Initial Online Setup (Required Once)**:
   - Python dependencies must be installed from PyPI (`pip install -r requirements.txt`).
   - Open-weight model weights must be pulled from the Ollama library (`ollama run llama3.2:1b`).
2. **Offline Verification**:
   - Disconnect your computer from Wi-Fi and Ethernet (or enable Airplane Mode).
   - Launch StudySloth companion: `.\.venv\Scripts\python bridge/bridge.py --open` (or `streamlit run app.py`).
   - Paste study notes or upload a `.txt`, `.pdf`, or `.docx` file.
   - Generate summaries, flashcards, or quizzes.
3. **Observation**:
   - Document extraction, prompt formatting, token generation, and interactive quiz/flashcard features execute completely on-device without an active network connection.

---

## ⚠️ Known Limitations & Technical Boundaries

To maintain technical clarity and realistic expectations:

1. **Scanned PDF Documents**: `pypdf` extracts selectable text. If a PDF is a scanned photocopy or pure image with no OCR text layer, StudySloth will notify the user with an actionable error. Use digital text-based PDFs or run OCR before importing.
2. **Context Window & Safe Trimming**: To ensure local small models (1B to 3B parameters) do not exhaust consumer RAM or hang on CPU inference, text is safely bounded at 75,000 characters (~15,000 words). If a full textbook chapter exceeds this, StudySloth warns the user and processes the first 75k characters.
3. **Inference Latency on CPU**: Unlike massive cloud data centers with liquid-cooled server clusters, local CPU execution takes a few seconds to generate tokens. On typical modern Intel Core i5/i7 or AMD Ryzen laptops, `llama3.2:1b` generates ~15–25 tokens/second.
4. **Initial Download Size**: While ongoing operation is 100% free and offline, downloading Ollama (~300MB) and a model (~1.3GB for `llama3.2:1b`) requires an initial internet connection.

---

## 🧪 Running the Automated Test Suite

StudySloth comes with a test suite covering document validation, error handling, prompt generation, Ollama streaming, and bridge security controls.

Run pytest using your virtual environment:
```powershell
.\.venv\Scripts\pytest -v
```

Expected output:
```text
tests/test_bridge.py::test_create_bridge_handler_scope_regression PASSED [  2%]
tests/test_bridge.py::test_security_manager_pairing_success PASSED       [  4%]
tests/test_bridge.py::test_security_manager_pairing_failure_and_lockout PASSED [  6%]
tests/test_bridge.py::test_security_manager_host_validation PASSED       [  8%]
tests/test_bridge.py::test_security_manager_origin_validation PASSED     [ 10%]
tests/test_bridge.py::test_normalize_origin PASSED                       [ 15%]
tests/test_bridge.py::test_get_configured_origins_env_and_cli PASSED     [ 17%]
tests/test_bridge.py::test_requirements_bridge_is_minimal PASSED         [ 19%]
tests/test_bridge.py::test_launch_scripts_exist PASSED                   [ 21%]
tests/test_bridge.py::test_bridge_options_cors_and_pna PASSED            [ 23%]
tests/test_bridge.py::test_bridge_get_health PASSED                      [ 26%]
tests/test_bridge.py::test_bridge_pairing_and_authorized_extraction PASSED [ 28%]
tests/test_bridge.py::test_bridge_dns_rebinding_rejected PASSED          [ 30%]
tests/test_bridge.py::test_bridge_generate_offline_ollama PASSED         [ 37%]
tests/test_bridge.py::test_bridge_health_session_validation PASSED       [ 39%]
tests/test_bridge.py::test_bridge_test_endpoint_auth_and_offline PASSED  [ 41%]
tests/test_document_processor.py::test_extract_text_from_txt_utf8 PASSED [ 43%]
tests/test_document_processor.py::test_process_uploaded_document_docx PASSED [ 60%]
tests/test_ollama_client.py::test_check_ollama_status_offline PASSED     [ 64%]
tests/test_prompts.py::test_build_prompt_all_types[flashcards] PASSED    [ 89%]
...
============================= 48 passed in 11.80s =============================
```

---

## 🛠️ Troubleshooting Common Issues

### 1. "Ollama is not running locally"
- **Cause**: The Ollama background service has not been started.
- **Fix**: Open your terminal and run `ollama serve` or launch the Ollama desktop application. Verify `http://127.0.0.1:11434` loads in your browser.

### 2. "Model 'llama3.2:1b' not found"
- **Cause**: The model weights have not been downloaded yet.
- **Fix**: Open your terminal and run `ollama pull llama3.2:1b`. You can also select any other model you have installed using the model dropdown.

### 3. "Bridge unreachable at 127.0.0.1:8765"
- **Cause**: The local Python bridge is not running, or your browser is blocking mixed content.
- **Fix**:
  1. Make sure you started `start_bridge.bat` (Windows) or `start_bridge.sh` (macOS/Linux).
  2. If using Firefox or Safari on the hosted HTTPS site, use **Universal Local Companion Mode** by running `python bridge/bridge.py --open`.

### 4. "Invalid pairing code" or "Too many failed attempts"
- **Cause**: The pairing code was typed incorrectly or expired.
- **Fix**: The pairing code is valid for 5 minutes. Check the bridge terminal window for the current 8-character code (e.g. `A7B2-C9D4`). If locked out, wait 60 seconds or restart the bridge.

---

## 📄 Contributing & License

Contributions, bug reports, and suggestions are welcome! Please feel free to open an Issue or submit a Pull Request.

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<p align="center">
  <b>Built with patience and care 🦥 for private, focused learning.</b>
</p>
