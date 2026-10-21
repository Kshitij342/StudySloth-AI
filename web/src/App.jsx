import React, { useState, useEffect, useRef } from 'react';
import { SAMPLE_NOTES } from './samples';

const DEFAULT_BRIDGE_URL = 'http://127.0.0.1:8765';
const DEFAULT_MODEL = 'llama3.2:1b';

export default function App() {
  // Bridge & Connection State
  const [bridgeUrl, setBridgeUrl] = useState(() => localStorage.getItem('studysloth_bridge_url') || DEFAULT_BRIDGE_URL);
  const [sessionToken, setSessionToken] = useState(() => sessionStorage.getItem('studysloth_session_token') || '');
  const [pairingCodeInput, setPairingCodeInput] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [bridgeStatus, setBridgeStatus] = useState({ online: false, ollamaOnline: false, models: [], error: '' });
  const [isPairingLoading, setIsPairingLoading] = useState(false);

  // Study Content State
  const [notes, setNotes] = useState('');
  const [activeInputTab, setActiveInputTab] = useState('paste'); // 'paste' | 'upload'
  const [selectedFormat, setSelectedFormat] = useState('summary');
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [temperature, setTemperature] = useState(0.3);
  const [allowSimulated, setAllowSimulated] = useState(false);

  // Uploaded Document State
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMeta, setUploadMeta] = useState(null);
  const [uploadError, setUploadError] = useState('');

  // Generation State
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationOutput, setGenerationOutput] = useState('');
  const [generationError, setGenerationError] = useState('');
  const [isSimulatedResponse, setIsSimulatedResponse] = useState(false);

  // Interactive Practice State
  const [activeResultTab, setActiveResultTab] = useState('formatted'); // 'formatted' | 'interactive'
  const [flashcardIndex, setFlashcardIndex] = useState(0);
  const [revealAnswer, setRevealAnswer] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  const fileInputRef = useRef(null);

  // Check bridge health on mount or when bridgeUrl changes
  useEffect(() => {
    checkHealth();
  }, [bridgeUrl, sessionToken]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setBridgeStatus({
        online: true,
        ollamaOnline: data.ollama_online,
        models: data.installed_models || [],
        error: data.ollama_status || '',
      });
      if (data.installed_models?.length > 0 && !data.installed_models.includes(selectedModel)) {
        setSelectedModel(data.installed_models[0]);
      }
    } catch (err) {
      setBridgeStatus({
        online: false,
        ollamaOnline: false,
        models: [],
        error: 'Bridge unreachable at 127.0.0.1:8765',
      });
    }
  };

  const handlePair = async (e) => {
    e.preventDefault();
    if (!pairingCodeInput.trim()) return;
    setIsPairingLoading(true);
    setGenerationError('');

    try {
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/pair`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ pairing_code: pairingCodeInput.trim().toUpperCase() }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Pairing failed');
      }

      const token = data.session_token;
      setSessionToken(token);
      sessionStorage.setItem('studysloth_session_token', token);
      localStorage.setItem('studysloth_bridge_url', bridgeUrl);
      setPairingCodeInput('');
      setIsModalOpen(false);
      await checkHealth();
    } catch (err) {
      alert(`❌ Pairing Error: ${err.message}`);
    } finally {
      setIsPairingLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (sessionToken) {
      try {
        await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/unpair`, {
          method: 'POST',
          headers: {
            'X-Bridge-Token': sessionToken,
            'Content-Type': 'application/json',
          },
        });
      } catch (err) {
        // Ignore unpair network errors
      }
    }
    setSessionToken('');
    sessionStorage.removeItem('studysloth_session_token');
    setIsModalOpen(false);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!sessionToken && !allowSimulated) {
      setUploadError('Please connect to your Local Bridge first to process documents locally.');
      return;
    }

    setUploadLoading(true);
    setUploadError('');

    try {
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Data = reader.result.split(',')[1];
        if (!sessionToken && allowSimulated) {
          // Client-side plain text preview if TXT
          if (file.name.endsWith('.txt')) {
            const textContent = atob(base64Data);
            setNotes(textContent);
            setUploadMeta({ filename: file.name, word_count: textContent.split(/\s+/).length, character_count: textContent.length });
          } else {
            setUploadError('Simulated mode can only preview .txt files directly without the bridge. Start the local bridge for PDF and DOCX parsing.');
          }
          setUploadLoading(false);
          return;
        }

        try {
          const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/extract`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Bridge-Token': sessionToken,
            },
            body: JSON.stringify({
              filename: file.name,
              content_base64: base64Data,
            }),
          });

          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Failed to extract text');

          setNotes(data.text);
          setUploadMeta(data.metadata);
          setActiveInputTab('paste'); // Switch to notes view to review
        } catch (fetchErr) {
          setUploadError(`Document extraction error: ${fetchErr.message}`);
        } finally {
          setUploadLoading(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (err) {
      setUploadError(`File read error: ${err.message}`);
      setUploadLoading(false);
    }
  };

  const handleGenerate = async () => {
    const trimmedNotes = notes.trim();
    if (!trimmedNotes || trimmedNotes.length < 25) {
      alert('Please provide at least 25 characters of study notes.');
      return;
    }

    setGenerationError('');
    setIsGenerating(true);
    setGenerationOutput('');
    setFlashcardIndex(0);
    setRevealAnswer(false);
    setQuizSubmitted(false);
    setQuizAnswers({});

    // Check if we should use Simulated Demo Mode
    const isBridgeReady = bridgeStatus.online && bridgeStatus.ollamaOnline && sessionToken;

    if (!isBridgeReady && allowSimulated) {
      setIsSimulatedResponse(true);
      await generateSimulatedStudyAid(trimmedNotes, selectedFormat);
      setIsGenerating(false);
      return;
    }

    if (!isBridgeReady) {
      setIsGenerating(false);
      setIsModalOpen(true);
      return;
    }

    setIsSimulatedResponse(false);

    try {
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Bridge-Token': sessionToken,
        },
        body: JSON.stringify({
          notes: trimmedNotes,
          output_type: selectedFormat,
          model: selectedModel,
          temperature: parseFloat(temperature),
          stream: true,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `Generation failed (HTTP ${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;
            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.chunk) {
                accumulated += parsed.chunk;
                setGenerationOutput(accumulated);
              }
              if (parsed.error) {
                throw new Error(parsed.error);
              }
            } catch (pErr) {
              // Ignore line parse edge cases
            }
          }
        }
      }
    } catch (err) {
      setGenerationError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateSimulatedStudyAid = async (text, format) => {
    // Deterministic simulation with clear disclaimer
    const firstLines = text.split('\n').filter(l => l.trim()).slice(0, 3).join(' ');
    let simText = `[SIMULATED - DEMO ONLY]\n\n`;

    if (format === 'summary') {
      simText += `## 🦥 Executive Summary\nThese study notes provide a thorough exploration of the core concepts:\n> ${firstLines}\n\nThrough structured review, the material establishes foundational principles and operational mechanisms.\n\n## 🎯 Core Themes & Mechanics\n- **Systemic Interactions**: How initial inputs transform into useful outputs.\n- **Sequential Logic**: Step-by-step progressions governing this topic.\n\n## 💡 Big Picture Takeaway\nMastery relies on understanding that each discrete stage builds directly on preceding products.`;
    } else if (format === 'key_points') {
      simText += `## 📌 High-Yield Key Points\n- **Primary Driver**: Core mechanisms form the bedrock of the entire subject.\n- **Energy/Resource Transfer**: Critical phase transitions dictate stability.\n- **Exam Favorite**: Pay careful attention to terminology, sequences, and structural boundaries.`;
    } else if (format === 'definitions') {
      simText += `## 📖 Key Terminology & Definitions\n- **Primary Entity**: The foundational subject or substrate in the provided notes.\n  *Context*: Serves as the starting element for subsequent reactions.\n- **Catalyst / Accelerator**: Any agent or condition that speeds up the transformation rate.\n- **Terminal Acceptor**: Concluding element that finalizes the system flow.`;
    } else if (format === 'flashcards') {
      simText += `### Flashcard 1\n**Q**: What is the primary purpose of the system described in the notes?\n**A**: To break down initial substrates and generate usable outputs.\n\n### Flashcard 2\n**Q**: Where does the initial phase take place?\n**A**: In the foundational environment prior to specialized processing.\n\n\`\`\`json\n[\n  {"id": 1, "question": "What is the primary purpose of the system described in the notes?", "answer": "To break down initial substrates and generate usable energy/outputs efficiently."},\n  {"id": 2, "question": "Where does the initial phase take place?", "answer": "In the foundational baseline environment prior to specialized processing."}\n]\n\`\`\``;
    } else if (format === 'quiz') {
      simText += `### Question 1\nWhat is the foundational role of the process described in the notes?\n- A) Rapid destruction without recovery\n- B) Systematic transformation into usable outputs\n- C) Static storage without change\n- D) Random uncoordinated events\n\n**Correct Answer**: B\n**Explanation**: The notes emphasize systematic transformation over uncoordinated destruction.\n\n\`\`\`json\n[\n  {\n    "id": 1,\n    "question": "What is the foundational role of the process described in the notes?",\n    "options": {"A": "Rapid destruction without recovery", "B": "Systematic transformation into usable outputs", "C": "Static storage without change", "D": "Random uncoordinated events"},\n    "answer": "B",\n    "explanation": "The notes emphasize systematic transformation over uncoordinated destruction."\n  }\n]\n\`\`\``;
    } else {
      simText += `# 🦥 Comprehensive Study Pack\n\n## 1. Executive Summary\n${firstLines}\n\n## 2. Key Points\n- Sequential logic and structured transformation.\n\n## 3. Active Recall Flashcards\n**Q**: What is the core mechanism?\n**A**: Step-by-step execution described in the text.`;
    }

    // Simulate streaming delay
    const chunks = simText.split(' ');
    let acc = '';
    for (const ch of chunks) {
      acc += ch + ' ';
      setGenerationOutput(acc);
      await new Promise(r => setTimeout(r, 20));
    }
  };

  // Extract structured JSON for interactive mode
  const parseJsonBlock = (text) => {
    if (!text) return null;
    const fenced = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
    if (fenced) {
      try {
        const parsed = JSON.parse(fenced[1].trim());
        if (Array.isArray(parsed)) return parsed;
        if (typeof parsed === 'object') {
          for (const k of ['flashcards', 'quiz', 'questions']) {
            if (Array.isArray(parsed[k])) return parsed[k];
          }
        }
      } catch (e) {}
    }
    const arr = text.match(/(\[\s*\{[\s\S]*\}\s*\])/);
    if (arr) {
      try {
        return JSON.parse(arr[1].trim());
      } catch (e) {}
    }
    return null;
  };

  const parsedPracticeData = parseJsonBlock(generationOutput);

  // Download Helpers
  const downloadFile = (filename, content, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generationOutput);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // Metrics
  const wordCount = notes.trim() ? notes.trim().split(/\s+/).length : 0;
  const charCount = notes.trim().length;
  const readMin = Math.max(1, Math.round(wordCount / 200));

  return (
    <div className="container">
      {/* Header */}
      <header className="header-card">
        <div className="brand-wrapper">
          <div className="avatar-badge">🦥</div>
          <div>
            <h1 className="brand-title">StudySloth AI</h1>
            <p className="brand-subtitle">Slow and steady wins the race. 100% Local, Private AI Study Assistant.</p>
            <span className="hacktoberfest-pill">Hacktoberfest 2026 • Week 3: Slow and Steady</span>
          </div>
        </div>

        {/* Status Pill */}
        <div
          className={`status-pill ${
            sessionToken && bridgeStatus.ollamaOnline
              ? 'status-online'
              : sessionToken && bridgeStatus.online
              ? 'status-warning'
              : 'status-offline'
          }`}
          onClick={() => setIsModalOpen(true)}
          title="Click to manage local bridge connection"
        >
          {sessionToken && bridgeStatus.ollamaOnline && '🟢 Connected to Local Ollama'}
          {sessionToken && bridgeStatus.online && !bridgeStatus.ollamaOnline && '🟡 Bridge Ready (Ollama Offline)'}
          {!sessionToken && '🔴 Disconnected (Click to Connect)'}
        </div>
      </header>

      {/* Main Study Workstation */}
      <main>
        {/* Presets */}
        <section className="card">
          <h3 style={{ fontSize: '1rem', marginBottom: '0.6rem', color: 'var(--sloth-dark-green)' }}>
            🚀 Instant Starters (Load Sample Notes)
          </h3>
          <div className="preset-group">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setNotes(SAMPLE_NOTES['Biology: Cellular Respiration & Energy']);
                setActiveInputTab('paste');
              }}
            >
              🔬 Biology: Respiration
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setNotes(SAMPLE_NOTES['Computer Science: Big-O & Data Structures']);
                setActiveInputTab('paste');
              }}
            >
              💻 CS: Big-O & Data Structures
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setNotes(SAMPLE_NOTES['World History: The Industrial Revolution']);
                setActiveInputTab('paste');
              }}
            >
              📜 History: Industrial Rev
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setNotes('');
                setGenerationOutput('');
                setUploadMeta(null);
              }}
            >
              🧹 Clear
            </button>
          </div>

          {/* Input Tabs */}
          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeInputTab === 'paste' ? 'active' : ''}`}
              onClick={() => setActiveInputTab('paste')}
            >
              ✍️ Paste / Edit Notes
            </button>
            <button
              className={`tab-btn ${activeInputTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveInputTab('upload')}
            >
              📁 Upload Document (.txt, .pdf, .docx)
            </button>
          </div>

          {activeInputTab === 'paste' ? (
            <div>
              <textarea
                className="form-control"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Paste lecture notes, textbook excerpts, or article content here..."
              />
              <div style={{ marginTop: '0.4rem' }}>
                <span className="stat-badge">📊 {wordCount.toLocaleString()} words</span>
                <span className="stat-badge">🔤 {charCount.toLocaleString()} characters</span>
                <span className="stat-badge">⏱️ ~{readMin} min read</span>
                {uploadMeta && (
                  <span className="stat-badge" style={{ background: '#eaf3eb' }}>
                    📄 Loaded from: {uploadMeta.filename}
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div style={{ padding: '1rem 0' }}>
              <p style={{ fontSize: '0.9rem', color: 'var(--sloth-text-muted)', marginBottom: '0.8rem' }}>
                Upload study files up to 10 MB. All document parsing happens strictly locally on your computer via the bridge;
                files are never transmitted to Vercel.
              </p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".txt,.pdf,.docx"
                style={{ display: 'block', marginBottom: '0.8rem' }}
              />
              {uploadLoading && <div className="alert alert-info">🦥 Extracting text locally on your device...</div>}
              {uploadError && <div className="alert alert-error">{uploadError}</div>}
            </div>
          )}
        </section>

        {/* Study Options & Generation */}
        <section className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', alignItems: 'end' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                🎯 Study Aid Format
              </label>
              <select
                className="form-control"
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
              >
                <option value="summary">📝 Executive Summary (Deep & Structured)</option>
                <option value="key_points">📌 High-Yield Key Points & Takeaways</option>
                <option value="definitions">📖 Key Terminology & Definitions</option>
                <option value="flashcards">🗂️ Active Recall Flashcards (Q&A)</option>
                <option value="quiz">🎯 Multiple-Choice Comprehension Quiz</option>
                <option value="comprehensive">🌟 All-in-One Comprehensive Study Pack</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                🧠 Local AI Model
              </label>
              <select
                className="form-control"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={bridgeStatus.models.length === 0}
              >
                {bridgeStatus.models.length > 0 ? (
                  bridgeStatus.models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))
                ) : (
                  <option value={DEFAULT_MODEL}>{DEFAULT_MODEL} (Connect bridge to list)</option>
                )}
              </select>
            </div>

            <div>
              <button
                className="btn btn-primary"
                style={{ width: '100%', padding: '0.75rem' }}
                onClick={handleGenerate}
                disabled={isGenerating || notes.trim().length < 25}
              >
                {isGenerating ? '🦥 Generating Patiently...' : '🦥 Generate with StudySloth'}
              </button>
            </div>
          </div>

          <div style={{ marginTop: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--sloth-text-muted)' }}>
              Study Rigor (Temperature: {temperature}):{' '}
              <input
                type="range"
                min="0.1"
                max="0.7"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                style={{ verticalAlign: 'middle', width: '120px' }}
              />
            </label>

            <label style={{ fontSize: '0.85rem', color: 'var(--sloth-text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={allowSimulated}
                onChange={(e) => setAllowSimulated(e.target.checked)}
                style={{ marginRight: '0.4rem' }}
              />
              Enable Simulated Demo Mode (if Ollama offline)
            </label>
          </div>
        </section>

        {/* Generation Feedback / Loading */}
        {isGenerating && (
          <div className="alert alert-info">
            🦥 StudySloth is carefully distilling your notes via local Ollama (127.0.0.1)...
          </div>
        )}

        {generationError && (
          <div className="alert alert-error">
            ❌ {generationError}
          </div>
        )}

        {/* Results Area */}
        {generationOutput && (
          <section className="card">
            {isSimulatedResponse && (
              <div className="alert alert-warning" style={{ fontWeight: 600 }}>
                ⚠️ SIMULATED DEMO MODE: This response was generated by a local deterministic template because Ollama is offline or disconnected. It was NOT produced by an AI model.
              </div>
            )}

            <div className="tabs-nav">
              <button
                className={`tab-btn ${activeResultTab === 'formatted' ? 'active' : ''}`}
                onClick={() => setActiveResultTab('formatted')}
              >
                📄 Formatted Study Aid
              </button>
              {parsedPracticeData && (
                <button
                  className={`tab-btn ${activeResultTab === 'interactive' ? 'active' : ''}`}
                  onClick={() => setActiveResultTab('interactive')}
                >
                  🎮 Interactive Practice Mode
                </button>
              )}
            </div>

            {activeResultTab === 'formatted' ? (
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, padding: '0.5rem 0' }}>
                {generationOutput}
              </div>
            ) : (
              <div>
                {/* Interactive Flashcards */}
                {parsedPracticeData && parsedPracticeData[0]?.question && !parsedPracticeData[0]?.options && (
                  <div>
                    <h4 style={{ color: 'var(--sloth-dark-green)', marginBottom: '0.5rem' }}>
                      🗂️ Interactive Flashcards (Card {flashcardIndex + 1} of {parsedPracticeData.length})
                    </h4>
                    <div className="flashcard-box">
                      <div className="flashcard-q">
                        ❓ {parsedPracticeData[flashcardIndex]?.question}
                      </div>
                      {revealAnswer ? (
                        <div className="flashcard-a">
                          💡 {parsedPracticeData[flashcardIndex]?.answer}
                        </div>
                      ) : (
                        <div style={{ color: '#888', fontStyle: 'italic' }}>
                          Click &quot;Reveal Answer&quot; to test your memory
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setFlashcardIndex((prev) => (prev - 1 + parsedPracticeData.length) % parsedPracticeData.length);
                          setRevealAnswer(false);
                        }}
                      >
                        ⬅️ Previous
                      </button>
                      <button
                        className="btn btn-primary"
                        onClick={() => setRevealAnswer(!revealAnswer)}
                      >
                        {revealAnswer ? '🙈 Hide Answer' : '👁️ Reveal Answer'}
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setFlashcardIndex((prev) => (prev + 1) % parsedPracticeData.length);
                          setRevealAnswer(false);
                        }}
                      >
                        Next ➡️
                      </button>
                    </div>
                  </div>
                )}

                {/* Interactive Quiz */}
                {parsedPracticeData && parsedPracticeData[0]?.options && (
                  <div>
                    <h4 style={{ color: 'var(--sloth-dark-green)', marginBottom: '1rem' }}>
                      🎯 Multiple-Choice Comprehension Quiz
                    </h4>
                    {parsedPracticeData.map((q, idx) => {
                      const qid = q.id || idx + 1;
                      const userChoice = quizAnswers[qid];
                      const correctAns = (q.answer || '').trim().toUpperCase();

                      // Handle options whether object or array
                      let optionsList = [];
                      if (typeof q.options === 'object' && !Array.isArray(q.options)) {
                        optionsList = Object.entries(q.options).map(([k, v]) => `${k}) ${v}`);
                      } else if (Array.isArray(q.options)) {
                        const letters = ['A', 'B', 'C', 'D'];
                        optionsList = q.options.map((opt, oIdx) => {
                          const s = String(opt).trim();
                          return s.match(/^[A-D]\)/i) ? s : `${letters[oIdx] || oIdx + 1}) ${s}`;
                        });
                      }

                      return (
                        <div key={qid} className="quiz-item">
                          <p style={{ fontWeight: 600 }}>Q{idx + 1}: {q.question}</p>
                          {optionsList.map((opt) => {
                            const optLetter = opt.charAt(0).toUpperCase();
                            const isSelected = userChoice === optLetter;

                            return (
                              <div
                                key={opt}
                                className={`quiz-option ${isSelected ? 'selected' : ''}`}
                                onClick={() => !quizSubmitted && setQuizAnswers({ ...quizAnswers, [qid]: optLetter })}
                              >
                                <input
                                  type="radio"
                                  name={`quiz_${qid}`}
                                  checked={isSelected}
                                  onChange={() => {}}
                                />
                                <span>{opt}</span>
                              </div>
                            );
                          })}

                          {quizSubmitted && (
                            <div className={`explanation-box ${userChoice === correctAns ? 'explanation-correct' : 'explanation-incorrect'}`}>
                              {userChoice === correctAns ? '✅ Correct! ' : `❌ You chose ${userChoice || 'none'}. Correct answer is ${correctAns}. `}
                              {q.explanation}
                            </div>
                          )}
                        </div>
                      );
                    })}

                    <div style={{ marginTop: '1rem' }}>
                      {!quizSubmitted ? (
                        <button
                          className="btn btn-primary"
                          onClick={() => setQuizSubmitted(true)}
                        >
                          📝 Submit Quiz Answers
                        </button>
                      ) : (
                        <button
                          className="btn btn-secondary"
                          onClick={() => {
                            setQuizSubmitted(false);
                            setQuizAnswers({});
                          }}
                        >
                          🔄 Retake Quiz
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Export Bar */}
            <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--sloth-border)', display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary"
                onClick={() => downloadFile(`studysloth_${selectedFormat}.md`, generationOutput, 'text/markdown')}
              >
                ⬇️ Download Markdown (.md)
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => downloadFile(`studysloth_${selectedFormat}.txt`, generationOutput, 'text/plain')}
              >
                ⬇️ Download Text (.txt)
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  const data = parsedPracticeData ? JSON.stringify(parsedPracticeData, null, 2) : JSON.stringify({ content: generationOutput }, null, 2);
                  downloadFile(`studysloth_${selectedFormat}.json`, data, 'application/json');
                }}
              >
                ⬇️ Download JSON (Anki)
              </button>
              <button className="btn btn-secondary" onClick={handleCopy}>
                {copySuccess ? '✅ Copied!' : '📋 Copy to Clipboard'}
              </button>
            </div>
          </section>
        )}
      </main>

      {/* Bridge Connection Modal / Drawer */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ color: 'var(--sloth-dark-green)', fontSize: '1.2rem' }}>
                🦥 Connect to Local Ollama Bridge
              </h3>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>✕</button>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--sloth-text-muted)', marginBottom: '1rem' }}>
              To ensure 100% privacy, your study notes are processed entirely on your personal machine.
              Start the lightweight local bridge on your computer, then enter your session pairing code.
            </p>

            <form onSubmit={handlePair}>
              <div style={{ marginBottom: '0.8rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                  Local Bridge URL
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={bridgeUrl}
                  onChange={(e) => setBridgeUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8765"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                  🔑 Session Pairing Code
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={pairingCodeInput}
                  onChange={(e) => setPairingCodeInput(e.target.value.toUpperCase())}
                  placeholder="e.g. A7B2-C9D4"
                  maxLength={9}
                  required
                />
                <span style={{ fontSize: '0.75rem', color: '#666' }}>
                  Displayed in your terminal when running the bridge.
                </span>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.2rem' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={isPairingLoading}
                >
                  {isPairingLoading ? 'Pairing...' : 'Pair & Connect'}
                </button>
                {sessionToken && (
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={handleDisconnect}
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </form>

            <div style={{ borderTop: '1px solid var(--sloth-border)', paddingTop: '1rem' }}>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem', color: 'var(--sloth-dark-green)' }}>
                💻 How to Start the Bridge on Your Computer:
              </h4>

              <p style={{ fontSize: '0.8rem', fontWeight: 600, marginTop: '0.4rem' }}>Windows (PowerShell):</p>
              <div className="code-snippet">
                cd studysloth<br />
                .\.venv\Scripts\python bridge/bridge.py
              </div>

              <p style={{ fontSize: '0.8rem', fontWeight: 600, marginTop: '0.4rem' }}>macOS / Linux (Terminal):</p>
              <div className="code-snippet">
                cd studysloth<br />
                python3 bridge/bridge.py
              </div>

              <div className="alert alert-info" style={{ marginTop: '0.8rem', fontSize: '0.8rem' }}>
                💡 <b>Universal Local Companion App:</b> If your browser blocks HTTPS-to-localhost connections (e.g. Safari or Firefox mixed content), run:
                <br />
                <code>python bridge/bridge.py --open</code>
                <br />
                This serves the web app directly from 127.0.0.1 with zero browser restrictions!
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer>
        <p>
          🦥 <b>StudySloth AI</b> • Built with React, Python, and Ollama for <b>Hacktoberfest 2026: Slow and Steady</b>.
        </p>
        <p style={{ marginTop: '0.3rem', fontSize: '0.78rem', color: '#7a9a74' }}>
          100% Open Source • 100% On-Device Inference • Zero Remote Data Tracking
        </p>
      </footer>
    </div>
  );
}
