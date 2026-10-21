# 🦥 StudySloth AI

> **"Slow and steady wins the race."**  
> A 100% local, private, and open-weight AI study companion built for the **Hacktoberfest 2026 DEV Challenge — Week 3: Slow and Steady**.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-black.svg)](https://ollama.com/)
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25%20On--Device-success.svg)](#privacy--the-power-of-open-weight-ai)

---

## 📖 Table of Contents
- [About StudySloth AI](#-about-studysloth-ai)
- [Why "Slow and Steady"?](#-why-slow-and-steady)
- [Privacy & The Power of Open-Weight AI](#-privacy--the-power-of-open-weight-ai)
- [Recommended Open-Weight Models & Hardware Matrix](#-recommended-open-weight-models--hardware-matrix)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Quick Start Guide (Windows / macOS / Linux)](#-quick-start-guide)
- [Offline Verification & Workflow](#-offline-verification--workflow)
- [Running the Test Suite](#-running-the-test-suite)
- [DEV Challenge Submission Checklist](#-dev-challenge-submission-checklist)
- [Contributing & License](#-contributing--license)

---

## 🌿 About StudySloth AI

Modern study tools rush learners through hurried, superficial summaries while sending sensitive lecture notes, unpublished research papers, and proprietary school documents across the public internet to commercial AI APIs.

**StudySloth AI** takes the opposite philosophy: **Slow and Steady**.
- It prioritizes **deep, structured comprehension** over frantic skimming.
- It runs **entirely on your local computer** using **open-weight AI models** powered by [Ollama](https://ollama.com).
- **Zero cloud API keys. Zero external subscriptions. Zero telemetry. Zero data leaks.**

Whether you are studying high school biology, preparing for university exams, or memorizing algorithms, StudySloth transforms raw notes and documents into tailored **summaries, high-yield takeaways, glossaries, interactive flashcards, and practice quizzes**.

---

## 🦥 Why "Slow and Steady"?

The theme of Week 3 of the Hacktoberfest 2026 DEV Challenge is **Slow and Steady**. StudySloth embodies this in three core dimensions:

1. **Cognitive Pacing**: Instead of dumping wall-of-text responses, StudySloth distills information into digestible stages: High-Yield Summaries → Key Concepts → Terminology → Active Recall Flashcards → Verification Quizzes.
2. **Patience over Premature Optimization**: Running smaller open-weight models (1B to 3B parameters) directly on consumer laptops may take a few seconds longer than massive trillion-parameter server farms, but the reward is total sovereignty, silence, and reliability.
3. **Sustainable Learning**: High-retention active recall and spaced repetition flashcards out-perform overnight cramming every time.

---

## 🛡️ Privacy & The Power of Open-Weight AI

Open-weight models represent a seismic shift toward accessible, ethical, and privacy-preserving education.

### 1. Absolute Data Sovereignty
Commercial cloud AI services reserve the right to log, inspect, and train on user prompts. For students, researchers, and professionals handling:
- Medical case studies or patient notes
- Unpublished academic dissertations
- Proprietary internal company training manuals
- Personal learning difficulties or sensitive school records

StudySloth guarantees that **not a single syllable leaves `localhost:11434`**. 

### 2. Predictable Costs & Zero Subscription Fatigue
Cloud APIs charge per token and impose strict rate limits. StudySloth is free forever—no API tokens, no monthly credit cards, and no unexpected overage charges.

### 3. True Offline Resilience
You can study on an airplane, in an underground library, or during a remote retreat without internet. Once the model weights are downloaded once, **StudySloth operates 100% offline**.

---

## 🧠 Recommended Open-Weight Models & Hardware Matrix

StudySloth is built to run effortlessly on everyday consumer laptops without requiring expensive GPUs. Below is our benchmarked model matrix:

| Model | Parameter Size | Download Size | Minimum RAM | Recommended Hardware | License | Best Suited For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Llama 3.2 1B** *(Recommended Default)* | 1.23 Billion | ~1.3 GB | 4 GB | Any modern Intel/AMD CPU or Apple Silicon | Meta Llama 3.2 Community | Ultra-fast summaries, key points, rapid flashcards on budget laptops |
| **Llama 3.2 3B** | 3.21 Billion | ~2.0 GB | 8 GB | 8 GB RAM / 2 GB VRAM | Meta Llama 3.2 Community | Perfect sweet spot for complex quizzes and comprehensive study packs |
| **Phi-3 Mini** | 3.82 Billion | ~2.2 GB | 8 GB | 8 GB RAM / 2-4 GB VRAM | MIT License | High mathematical reasoning, STEM, code explanations |
| **Qwen 2.5 1.5B** | 1.54 Billion | ~1.0 GB | 4 GB | Any modern CPU | Apache 2.0 | Fully permissive open-source license with high structured JSON compliance |

### Trade-offs:
- **Small Models (1B - 3B)**: Instantaneous startup, minimal RAM footprint, runs on CPU battery power. Trade-off: Slightly shorter context window (optimized in StudySloth via automatic note sanitization and trimming).
- **Larger Models (7B - 8B)**: Deeper nuance and broader general knowledge. Trade-off: Requires 16 GB RAM or dedicated GPU; slower generation on CPU.

---

## ✨ Key Features

1. **Cute, Calming Sloth Theme**: Nature-inspired forest green aesthetic, sloth mascots, clean typography, and a distraction-free layout.
2. **Flexible Input Channels**:
   - Direct text pasting with live character, word, and reading-time counters.
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
   - **Interactive Quiz Runner**: Radio button answers, instant automated grading, score percentage, and celebratory balloons!
5. **Multi-Format Exporting**:
   - Download as **Markdown (`.md`)**
   - Download as **Plain Text (`.txt`)**
   - Download as **JSON (`.json`)** (ready for import into Anki or flashcard apps)
   - One-click copy code block
6. **Live Hardware & Server Monitor**:
   - Live health indicator: 🟢 Ollama Online / 🔴 Ollama Offline.
   - Model dropdown automatically detects locally pulled models.
   - Built-in fallback demo mode for testing UI without waiting for downloads.
7. **Instant Starter Presets**:
   - One-click sample notes for Biology (Cellular Respiration), Computer Science (Big-O & Data Structures), and World History (The Industrial Revolution).

---

## 🏗️ Architecture & Deployment Modes

StudySloth AI supports two distinct deployment modes while preserving 100% on-device AI inference:

```
[Mode A: Standalone Desktop App (Streamlit)]
User PC:  Browser (localhost:8501) ──> Streamlit Server ──> Ollama (127.0.0.1:11434)

[Mode B: Hosted Web Frontend (Vercel) + Secure Local Bridge]
Public:   https://studysloth-ai.vercel.app (Static React/Vite on Vercel CDN)
             │  (Loopback fetch with X-Bridge-Token & PNA headers)
             ▼
User PC:  Bridge (127.0.0.1:8765) ──> Ollama (127.0.0.1:11434)

[Mode C: Universal Local Companion App (Zero Browser Restrictions)]
User PC:  Browser (http://127.0.0.1:8765) ──> Bridge (serves web/dist) ──> Ollama (127.0.0.1:11434)
```

```
studysloth/
├── app.py                         # Streamlit standalone application
├── bridge/
│   ├── __init__.py
│   ├── bridge.py                  # Hardened local Python bridge (127.0.0.1:8765)
│   └── README.md                  # Detailed bridge security architecture
├── web/                           # Vercel-ready React + Vite frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── vercel.json                # Vercel static deployment configuration
│   └── src/
│       ├── App.jsx                # Interactive study workstation UI
│       ├── index.css              # Custom sloth aesthetic styling
│       ├── main.jsx
│       └── samples.js             # Biology, CS, History study presets
├── utils/
│   ├── document_processor.py      # Local extraction (TXT, PDF, DOCX) & sanitization
│   ├── ollama_client.py           # Local Ollama REST client & health check
│   ├── prompts.py                 # "Slow and Steady" prompt templates & JSON parsers
│   └── samples.py                 # Built-in study notes
└── tests/
    ├── test_bridge.py             # 13 tests for pairing, CSRF, DNS rebinding, PNA
    ├── test_document_processor.py # 9 tests for document processing
    ├── test_ollama_client.py      # 9 tests for Ollama client & streaming
    └── test_prompts.py            # 10 tests for prompt templates
```

---

## 🚀 Quick Start Guide

### Step 1: Install Ollama (Local AI Engine)
1. Download Ollama from [ollama.com/download](https://ollama.com/download).
2. Open PowerShell or Terminal and pull your model:
   ```powershell
   ollama run llama3.2:1b
   ```

---

### Option 1: Run the Standalone Streamlit App (Mode A)
```powershell
# In PowerShell:
.\.venv\Scripts\streamlit run app.py
```
Opens in your browser at `http://localhost:8501`.

---

### Option 2: Run the Web App with Local Bridge (Mode B / C)

#### 1. Start the Secure Local Bridge
```powershell
# In PowerShell:
.\.venv\Scripts\python bridge/bridge.py
```
The terminal displays:
```
================================================================
 🦥 StudySloth AI Local Bridge Server
 Status: Running on http://127.0.0.1:8765
 🔑 YOUR SESSION PAIRING CODE:  A7B2-C9D4
================================================================
```

#### 2. Open the Frontend
- **On Vercel**: Visit your deployed URL (e.g. `https://studysloth-ai.vercel.app`).
- **Or via Universal Local Companion Mode**:
  ```powershell
  .\.venv\Scripts\python bridge/bridge.py --open
  ```
  *(Serves the production build directly from `http://127.0.0.1:8765` with zero mixed-content restrictions across Chrome, Edge, Firefox, and Safari!)*

#### 3. Connect & Pair
Click the status pill in the top-right corner of the web page, enter your 8-character pairing code (e.g. `A7B2-C9D4`), and click **Pair & Connect**.

---

## 🌐 Deploying the Web Frontend to Vercel

The `web/` directory is 100% ready for zero-configuration deployment on [Vercel](https://vercel.com):

1. Push your repository to GitHub.
2. In the Vercel Dashboard, click **Add New Project** and select your `studysloth` repository.
3. Configure the Project Settings:
   - **Root Directory**: `web`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Click **Deploy**.
5. Once deployed, run your local bridge with your specific Vercel URL:
   ```powershell
   python bridge/bridge.py --allowed-origin https://your-project.vercel.app
   ```

---

## 🔒 Security & Browser Compatibility

| Browser | HTTPS-to-Loopback (Vercel) | Universal Companion Mode (`--open`) |
| :--- | :--- | :--- |
| **Google Chrome / MS Edge** | Supported via W3C Private Network Access (PNA) | ✅ 100% Supported |
| **Mozilla Firefox** | Blocks Mixed Content by default | ✅ 100% Supported |
| **Apple Safari** | Blocks Mixed Content by default | ✅ 100% Supported |

> **Recommendation**: For universal, zero-friction usage across all browsers, use **Universal Local Companion Mode** (`python bridge/bridge.py --open`).

---

## 🔌 Offline Verification & Workflow

StudySloth is engineered for local-first autonomy with clear, verifiable boundaries:

1. **Initial Online Setup (Required Once)**:
   - Python dependencies must be installed from PyPI (`pip install -r requirements.txt`).
   - Open-weight model weights must be pulled from the Ollama library (`ollama run llama3.2:1b`).
2. **True Offline Verification**:
   - Disconnect your computer from Wi-Fi and Ethernet (or toggle Airplane Mode).
   - Launch StudySloth companion: `.\.venv\Scripts\python bridge/bridge.py --open` (or `.\.venv\Scripts\streamlit run app.py`).
   - Paste study notes or upload a `.txt`, `.pdf`, or `.docx` document.
   - Click **🦥 Generate with StudySloth**.
3. **Observation**:
   - The document extraction, prompt formatting, token generation, and interactive quiz/flashcard features execute completely on-device without any active network connection.

---

## ⚠️ Known Limitations & Design Trade-Offs

To maintain honesty and technical integrity for judges and users:

1. **Scanned PDF Documents**: `pypdf` extracts selectable text. If a PDF is a scanned photocopy or pure image with no OCR text layer, StudySloth will notify the user with an actionable error. Use digital text-based PDFs or run OCR before importing.
2. **Context Window & Safe Trimming**: To ensure local small models (1B to 3B parameters) do not crash consumer RAM or hang on CPU inference, text is safely bounded at 75,000 characters (~15,000 words). If a full textbook chapter exceeds this, StudySloth warns the user and processes the first 75k characters.
3. **Inference Latency on CPU**: Unlike massive cloud data centers with liquid-cooled H100 clusters, local CPU execution takes a few seconds to think and stream ("Slow and Steady"). On typical Intel Core i5/i7 or AMD Ryzen laptops, `llama3.2:1b` generates ~15-25 tokens/second.
4. **Initial Download Size**: While ongoing operation is 100% free and offline, downloading Ollama (~300MB) and a model (~1.3GB for `llama3.2:1b`) requires an initial high-speed internet connection.

---

## 🧪 Running the Test Suite

StudySloth comes with an automated test suite covering document validation, error handling, prompt generation, Ollama streaming, and bridge security controls.

Run pytest using your virtual environment:
```powershell
.\.venv\Scripts\pytest -v
```

Expected output:
```
tests/test_bridge.py::test_security_manager_pairing_success PASSED       [  2%]
tests/test_bridge.py::test_security_manager_pairing_failure_and_lockout PASSED [  4%]
tests/test_bridge.py::test_security_manager_host_validation PASSED       [  7%]
tests/test_bridge.py::test_security_manager_origin_validation PASSED     [  9%]
tests/test_bridge.py::test_bridge_options_cors_and_pna PASSED            [ 14%]
tests/test_bridge.py::test_bridge_pairing_and_authorized_extraction PASSED [ 19%]
tests/test_bridge.py::test_bridge_dns_rebinding_rejected PASSED          [ 21%]
tests/test_bridge.py::test_bridge_static_frontend_serving PASSED         [ 29%]
tests/test_document_processor.py::test_extract_text_from_txt_utf8 PASSED [ 34%]
tests/test_document_processor.py::test_process_uploaded_document_docx PASSED [ 53%]
tests/test_ollama_client.py::test_extract_json_block_fenced PASSED       [ 60%]
tests/test_prompts.py::test_build_prompt_all_types[flashcards] PASSED    [ 87%]
...
============================= 41 passed in 6.81s ==============================
```


---

## 📝 DEV Challenge Submission Checklist

When writing your **DEV.to** post for the **Hacktoberfest 2026 Week 3: Slow and Steady** challenge, follow this submission checklist:

- [ ] **Title**: e.g., `StudySloth AI: Slow and Steady Learning with 100% Local Open-Weight AI`
- [ ] **Tags**: `#hacktoberfest`, `#devchallenge`, `#python`, `#ai`
- [ ] **Challenge Theme Alignment**:
  - Explain why you chose the "Slow and Steady" theme (thoughtful learning, local AI sovereignty, patient active recall).
- [ ] **Demo Screenshots / GIFs**:
  - Screenshot 1: The sloth-themed header and quick starter sample buttons.
  - Screenshot 2: Sidebar showing the green "🟢 Ollama Online" badge and model selection.
  - Screenshot 3: Active generation streaming tokens into the formatted study guide.
  - Screenshot 4: The interactive flashcard flip cards and quiz runner with live scoring.
- [ ] **Open-Weight AI Discussion**:
  - Highlight why running Llama 3.2 locally protects student data and eliminates cloud API costs.
- [ ] **Open Source Repo Link**:
  - Include your GitHub repository link and confirm the MIT license is present.
- [ ] **Installation Steps**:
  - Provide the simple 3-step setup commands so judges and readers can run it themselves.

---

## 📄 Contributing & License

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue to suggest new features, additional document formats, or new study templates.

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<p align="center">
  <b>Built with patience and care 🦥 for Hacktoberfest 2026.</b>
</p>
