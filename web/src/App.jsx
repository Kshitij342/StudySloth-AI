import React, { useState, useEffect, useRef } from 'react';
import { SAMPLE_NOTES } from './samples';

const DEFAULT_BRIDGE_URL = 'http://127.0.0.1:8765';
const DEFAULT_MODEL = 'llama3.2:1b';

export default function App() {
  // Navigation State: 'study' (workstation) | 'connect' (dedicated connection dashboard)
  const [activeNav, setActiveNav] = useState('study');

  // Bridge & Connection State
  const [bridgeUrl, setBridgeUrl] = useState(() => {
    const saved = localStorage.getItem('studysloth_bridge_url');
    if (saved) return saved;
    if (typeof window !== 'undefined' && (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')) {
      return `${window.location.protocol}//${window.location.host}`;
    }
    return DEFAULT_BRIDGE_URL;
  });
  const [sessionToken, setSessionToken] = useState(() => sessionStorage.getItem('studysloth_session_token') || '');
  const [pairingCodeInput, setPairingCodeInput] = useState('');
  const [bridgeStatus, setBridgeStatus] = useState({
    online: false,
    ollamaOnline: false,
    models: [],
    sessionValid: null,
    error: '',
  });
  const [isPairingLoading, setIsPairingLoading] = useState(false);
  const [pairingError, setPairingError] = useState('');

  // Diagnostics & Testing State
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshFeedback, setRefreshFeedback] = useState('');

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
  const abortControllerRef = useRef(null);

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
    checkHealth().catch(() => {});
  }, [bridgeUrl, sessionToken]);

  const checkHealth = async () => {
    try {
      const headers = { Accept: 'application/json' };
      if (sessionToken) {
        headers['X-Bridge-Token'] = sessionToken;
      }
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/health`, {
        method: 'GET',
        headers,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Check session validity if bridge verified token
      if (sessionToken && data.session_valid === false) {
        setSessionToken('');
        sessionStorage.removeItem('studysloth_session_token');
        setPairingError('Previous session has expired or bridge was restarted. Please enter the new pairing code.');
      }

      setBridgeStatus({
        online: true,
        ollamaOnline: data.ollama_online,
        models: data.installed_models || [],
        sessionValid: data.session_valid,
        error: data.ollama_status || '',
      });

      if (data.installed_models?.length > 0 && !data.installed_models.includes(selectedModel)) {
        setSelectedModel(data.installed_models[0]);
      }
      return data;
    } catch (err) {
      setBridgeStatus({
        online: false,
        ollamaOnline: false,
        models: [],
        sessionValid: false,
        error: window.location.protocol === 'https:'
          ? 'Bridge unreachable at 127.0.0.1:8765. (Browser mixed-content restriction on HTTPS. See companion mode below).'
          : 'Bridge unreachable at 127.0.0.1:8765. Make sure start_bridge.bat is running.',
      });
      throw err;
    }
  };

  const handlePair = async (e) => {
    if (e) e.preventDefault();
    if (!pairingCodeInput.trim()) return;
    setIsPairingLoading(true);
    setPairingError('');
    setTestResult(null);
    setTestError('');

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
      setPairingError('');
      await checkHealth();
    } catch (err) {
      setPairingError(err.message);
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
    setTestResult(null);
    setTestError('');
    setRefreshFeedback('');
    setPairingError('');
  };

  const handleRefreshModels = async () => {
    setIsRefreshing(true);
    setRefreshFeedback('');
    try {
      const data = await checkHealth();
      if (data?.installed_models?.length > 0) {
        setRefreshFeedback(`Discovered ${data.installed_models.length} model(s): ${data.installed_models.join(', ')}`);
      } else {
        setRefreshFeedback('Ollama is active, but 0 models were found. Run: ollama pull llama3.2:1b');
      }
    } catch (err) {
      setRefreshFeedback(`Refresh failed: ${err.message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleTestConnection = async () => {
    if (!sessionToken) {
      setTestError('Please connect to the local bridge first.');
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    setTestError('');

    try {
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Bridge-Token': sessionToken,
        },
        body: JSON.stringify({ model: selectedModel }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || `Test failed with status ${res.status}`);
      }
      setTestResult({
        model: data.model,
        latency_ms: data.latency_ms,
        reply: data.reply,
      });
    } catch (err) {
      setTestError(err.message);
    } finally {
      setIsTesting(false);
    }
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

  const handleCancelGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
  };

  const handleGenerate = async () => {
    const trimmedNotes = notes.trim();
    if (!trimmedNotes || trimmedNotes.length < 25) {
      setGenerationError('Please provide at least 25 characters of study notes to generate aids.');
      return;
    }

    if (isGenerating) {
      return; // Prevent duplicate concurrent requests
    }

    setIsGenerating(true);
    setGenerationOutput('');
    setGenerationError('');
    setIsSimulatedResponse(false);
    setActiveResultTab('formatted');
    setQuizAnswers({});
    setQuizSubmitted(false);
    setFlashcardIndex(0);
    setRevealAnswer(false);

    // Fallback: Simulated demo mode if bridge offline and user enabled it
    if (!sessionToken && allowSimulated) {
      setIsSimulatedResponse(true);
      try {
        await generateSimulatedStudyAid(trimmedNotes, selectedFormat);
      } finally {
        setIsGenerating(false);
      }
      return;
    }

    if (!sessionToken) {
      setGenerationError('Local AI Bridge is not connected. Please connect via "Connect Local AI" or enable simulated demo mode.');
      setIsGenerating(false);
      return;
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;
    let reader = null;

    try {
      const res = await fetch(`${bridgeUrl.replace(/\/$/, '')}/api/generate`, {
        method: 'POST',
        signal: controller.signal,
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

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        if (data.output) {
          setGenerationOutput(data.output);
        } else {
          throw new Error('Received empty response from the local bridge.');
        }
        return;
      }

      if (!res.body) {
        throw new Error('Response body is empty. Could not read stream.');
      }

      reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';
      let buffer = '';
      let streamFinished = false;

      while (!streamFinished) {
        const { value, done } = await reader.read();
        if (done) {
          buffer += decoder.decode();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6).trim();
            if (!jsonStr) continue;
            let parsed;
            try {
              parsed = JSON.parse(jsonStr);
            } catch (pErr) {
              continue;
            }

            if (parsed.error) {
              throw new Error(parsed.error);
            }
            if (parsed.chunk) {
              accumulated += parsed.chunk;
              setGenerationOutput(accumulated);
            }
            if (parsed.done) {
              streamFinished = true;
              break;
            }
          }
        }
      }

      // Flush any remaining line in buffer
      if (buffer.trim()) {
        const trimmed = buffer.trim();
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6).trim();
          if (jsonStr) {
            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.error) throw new Error(parsed.error);
              if (parsed.chunk) {
                accumulated += parsed.chunk;
                setGenerationOutput(accumulated);
              }
            } catch (e) {
              if (e.message && e.message.includes('error')) throw e;
            }
          }
        }
      }

      if (!accumulated.trim()) {
        throw new Error('Generation completed, but the AI output was empty. Please check that your Ollama model is functioning.');
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setGenerationError('Generation was stopped.');
      } else {
        setGenerationError(err.message || 'An error occurred during generation.');
      }
    } finally {
      if (reader) {
        try {
          reader.releaseLock();
        } catch (e) {
          // Ignore if already released or closed
        }
      }
      abortControllerRef.current = null;
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

  // Determine actual connection state
  let connectionState = 'disconnected';
  if (isPairingLoading || isTesting) {
    connectionState = 'connecting';
  } else if (sessionToken && bridgeStatus.online && bridgeStatus.sessionValid !== false) {
    if (bridgeStatus.ollamaOnline && bridgeStatus.models.length > 0) {
      connectionState = 'connected';
    } else {
      connectionState = 'error';
    }
  } else if (bridgeStatus.online && !sessionToken) {
    connectionState = 'disconnected';
  } else if (bridgeStatus.error) {
    connectionState = 'disconnected';
  }

  return (
    <div className="container">
      {/* Header */}
      <header className="header-card">
        <div className="brand-wrapper">
          <div className="avatar-badge">🦥</div>
          <div>
            <h1 className="brand-title">StudySloth AI</h1>
            <p className="brand-subtitle">Slow and steady wins the race. 100% Local, Private AI Study Assistant.</p>
            <span className="brand-pill">100% Private • Local Open-Weight AI</span>
          </div>
        </div>

        {/* Navigation & Status Pill */}
        <div className="header-actions">
          <div className="header-nav">
            <button
              className={`nav-btn ${activeNav === 'study' ? 'active' : ''}`}
              onClick={() => setActiveNav('study')}
            >
              ✍️ Study Workstation
            </button>
            <button
              className={`nav-btn ${activeNav === 'connect' ? 'active' : ''}`}
              onClick={() => setActiveNav('connect')}
            >
              ⚡ Connect Local AI
            </button>
          </div>

          <div
            className={`status-pill ${
              connectionState === 'connected'
                ? 'status-online'
                : connectionState === 'connecting'
                ? 'status-warning'
                : connectionState === 'error'
                ? 'status-warning'
                : 'status-offline'
            }`}
            onClick={() => setActiveNav('connect')}
            title="Click to manage local AI connection"
          >
            {connectionState === 'connected' && `🟢 Connected (${selectedModel})`}
            {connectionState === 'connecting' && '🟡 Connecting...'}
            {connectionState === 'error' && (bridgeStatus.online && !bridgeStatus.ollamaOnline ? '🟡 Bridge Ready (Ollama Offline)' : '⚠️ Check Local AI')}
            {connectionState === 'disconnected' && '🔴 Disconnected (Connect AI)'}
          </div>
        </div>
      </header>

      {/* VIEW 1: DEDICATED CONNECT LOCAL AI DASHBOARD */}
      {activeNav === 'connect' && (
        <div className="connect-container">
          {/* Main Connection Status & Action Card */}
          <section className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.8rem', marginBottom: '0.6rem' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', color: 'var(--sloth-dark-green)', fontWeight: 700, margin: 0 }}>
                  ⚡ Connect Your Local AI
                </h2>
                <p style={{ color: 'var(--sloth-text-muted)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
                  StudySloth connects directly to an open-weight AI model on your own machine. Your notes and documents never leave your computer.
                </p>
              </div>
              <div>
                <span className={`status-badge-lg ${connectionState}`}>
                  {connectionState === 'connected' && '🟢 Connected'}
                  {connectionState === 'connecting' && '🟡 Connecting...'}
                  {connectionState === 'error' && '⚠️ Attention Required'}
                  {connectionState === 'disconnected' && '⚪ Disconnected'}
                </span>
              </div>
            </div>

            {/* Metrics Dashboard Grid */}
            <div className="connection-grid">
              <div className="connection-metric-card">
                <div className="connection-metric-label">Local Bridge Service</div>
                <div className="connection-metric-value">
                  {bridgeStatus.online ? '🟢 127.0.0.1:8765 (Active)' : '🔴 Unreachable'}
                </div>
              </div>
              <div className="connection-metric-card">
                <div className="connection-metric-label">Local Ollama Engine</div>
                <div className="connection-metric-value">
                  {bridgeStatus.ollamaOnline ? '🟢 Online (11434)' : '🔴 Offline'}
                </div>
              </div>
              <div className="connection-metric-card">
                <div className="connection-metric-label">Active Model Selected</div>
                <div className="connection-metric-value">
                  {bridgeStatus.models.length > 0 ? `🧠 ${selectedModel}` : '⚠️ None discovered'}
                </div>
              </div>
              <div className="connection-metric-card">
                <div className="connection-metric-label">Session Authentication</div>
                <div className="connection-metric-value">
                  {sessionToken ? '🔒 Authenticated' : '🔓 Not Paired'}
                </div>
              </div>
            </div>

            {/* Interactive Control Box */}
            {!sessionToken ? (
              <div style={{ background: '#f8faf9', border: '1px solid var(--sloth-border)', borderRadius: '10px', padding: '1.2rem', marginTop: '0.8rem' }}>
                <h3 style={{ fontSize: '1.05rem', color: 'var(--sloth-dark-green)', marginBottom: '0.5rem' }}>
                  🔑 Enter Your Session Pairing Code
                </h3>
                <p style={{ fontSize: '0.88rem', color: 'var(--sloth-text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Launch the StudySloth Local Bridge in your terminal (see instructions below). The bridge displays an 8-character code (e.g. <code>A7B2-C9D4</code>). Enter it here to securely pair this browser tab.
                </p>

                <form onSubmit={handlePair}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                        🔑 8-Character Pairing Code
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={pairingCodeInput}
                        onChange={(e) => setPairingCodeInput(e.target.value.toUpperCase())}
                        placeholder="e.g. A7B2-C9D4"
                        maxLength={9}
                        required
                        style={{ fontSize: '1.1rem', letterSpacing: '1px', fontWeight: 600 }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                        🌐 Local Bridge URL
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={bridgeUrl}
                        onChange={(e) => setBridgeUrl(e.target.value)}
                        placeholder="http://127.0.0.1:8765"
                      />
                    </div>
                  </div>

                  {pairingError && (
                    <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                      ❌ {pairingError}
                    </div>
                  )}

                  {!bridgeStatus.online && (
                    <div className="alert alert-warning" style={{ marginBottom: '1rem', fontSize: '0.88rem' }}>
                      ⚠️ <b>Bridge Not Detected on 127.0.0.1:8765:</b><br />
                      Make sure you launched <code>start_bridge.bat</code> (Windows) or <code>./start_bridge.sh</code> (macOS/Linux) and the terminal remains open.
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      style={{ padding: '0.65rem 1.4rem' }}
                      disabled={isPairingLoading || !pairingCodeInput.trim()}
                    >
                      {isPairingLoading ? '⏳ Pairing...' : '⚡ Connect Local AI'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => checkHealth().catch(() => {})}
                    >
                      🔄 Probe Bridge Status
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <div style={{ background: '#f8faf9', border: '1px solid var(--sloth-border)', borderRadius: '10px', padding: '1.2rem', marginTop: '0.8rem' }}>
                <h3 style={{ fontSize: '1.05rem', color: 'var(--sloth-dark-green)', marginBottom: '0.8rem' }}>
                  ⚙️ Active Local AI Controls
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', alignItems: 'end', marginBottom: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem' }}>
                      🧠 Select Ollama Model
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
                        <option value="">No models installed (Run: ollama pull llama3.2:1b)</option>
                      )}
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleRefreshModels}
                      disabled={isRefreshing}
                      title="Discover newly pulled models from Ollama"
                    >
                      {isRefreshing ? '🔄 Refreshing...' : '🔄 Refresh Models'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleTestConnection}
                      disabled={isTesting || bridgeStatus.models.length === 0}
                      title="Send a small test query to verify live inference"
                    >
                      {isTesting ? '🧪 Testing...' : '🧪 Test Connection'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={handleDisconnect}
                    >
                      🔌 Disconnect
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ fontWeight: 700, borderColor: 'var(--sloth-green)', color: 'var(--sloth-dark-green)' }}
                      onClick={() => setActiveNav('study')}
                    >
                      🚀 Start Studying →
                    </button>
                  </div>
                </div>

                {refreshFeedback && (
                  <div className="alert alert-info" style={{ marginTop: '0.6rem', fontSize: '0.85rem' }}>
                    ℹ️ {refreshFeedback}
                  </div>
                )}

                {testResult && (
                  <div className="test-result-box">
                    <div style={{ fontWeight: 700, marginBottom: '0.2rem' }}>
                      ✅ Connection Verified! Model <code>{testResult.model}</code> responded in {testResult.latency_ms}ms:
                    </div>
                    <div style={{ fontStyle: 'italic', background: '#ffffff', padding: '0.5rem 0.8rem', borderRadius: '6px', border: '1px solid #bbf7d0', marginTop: '0.4rem' }}>
                      &quot;{testResult.reply}&quot;
                    </div>
                  </div>
                )}

                {testError && (
                  <div className="test-result-error">
                    ❌ <b>Test Connection Failed:</b> {testError}
                    <div style={{ fontSize: '0.82rem', marginTop: '0.3rem', color: '#7f1d1d' }}>
                      Make sure Ollama is running and model <code>{selectedModel}</code> is downloaded.
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* 7-Step Setup Guide */}
          <section className="card">
            <h3 style={{ fontSize: '1.15rem', color: 'var(--sloth-dark-green)', fontWeight: 700, marginBottom: '0.3rem' }}>
              📚 First-Time User Setup Guide (7 Steps)
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--sloth-text-muted)', marginBottom: '1.2rem' }}>
              Follow these steps to set up private, on-device AI generation. Setup takes only a few minutes.
            </p>

            <div className="step-flow">
              {/* Step 1 */}
              <div className="step-card">
                <div className="step-number">1</div>
                <div className="step-content">
                  <div className="step-title">Install Ollama on Your Computer</div>
                  <div className="step-description">
                    Ollama is the open-source inference engine that runs open-weight AI models directly on your hardware.
                    Download the official installer from{' '}
                    <a
                      href="https://ollama.com/download"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--sloth-green)', fontWeight: 600, textDecoration: 'underline' }}
                    >
                      ollama.com/download ↗
                    </a>.
                    Install it and make sure the Ollama application or background service is running on your machine.
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="step-card">
                <div className="step-number">2</div>
                <div className="step-content">
                  <div className="step-title">Download an AI Model</div>
                  <div className="step-description">
                    Open your PowerShell or Terminal and pull the recommended lightweight model:
                    <div className="code-snippet">ollama pull llama3.2:1b</div>
                    <i>Model recommendations:</i> <code>llama3.2:1b</code> (~1.3 GB) is fast and runs on any CPU. If your machine has 8GB+ RAM, you can also pull <code>llama3.2:3b</code> or <code>phi3:mini</code>.
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="step-card">
                <div className="step-number">3</div>
                <div className="step-content">
                  <div className="step-title">Install & Start the StudySloth Local Bridge</div>
                  <div className="step-description">
                    Because Vercel serves static web assets and cannot start a Python process on a visitor&apos;s computer, you run the lightweight bridge script locally on your machine:
                    <p style={{ margin: '0.4rem 0 0.2rem 0', fontWeight: 600 }}>Windows (One-Click):</p>
                    Double-click <code>start_bridge.bat</code> or run <code>.\start_bridge.ps1</code> in PowerShell.
                    <p style={{ margin: '0.4rem 0 0.2rem 0', fontWeight: 600 }}>macOS / Linux (One-Click):</p>
                    Run <code>chmod +x start_bridge.sh && ./start_bridge.sh</code> in Terminal.
                    <p style={{ margin: '0.4rem 0 0.2rem 0', fontWeight: 600 }}>Manual Command Line:</p>
                    <div className="code-snippet">
                      pip install -r requirements-bridge.txt<br />
                      python bridge/bridge.py --open
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 4 */}
              <div className="step-card">
                <div className="step-number">4</div>
                <div className="step-content">
                  <div className="step-title">Pair the Website with the Bridge</div>
                  <div className="step-description">
                    When the bridge launches, it prints your terminal session pairing code (e.g. <code>A7B2-C9D4</code>).
                    Copy that 8-character code, paste it into the box above, and click <b>Connect Local AI</b>.
                    The code expires after 5 minutes for your security.
                  </div>
                </div>
              </div>

              {/* Step 5 */}
              <div className="step-card">
                <div className="step-number">5</div>
                <div className="step-content">
                  <div className="step-title">Select Your Model</div>
                  <div className="step-description">
                    Once paired, the bridge queries your local Ollama library and populates the dropdown with your installed models.
                    If no models are listed, download one with <code>ollama pull llama3.2:1b</code> and click <b>Refresh Models</b>.
                  </div>
                </div>
              </div>

              {/* Step 6 */}
              <div className="step-card">
                <div className="step-number">6</div>
                <div className="step-content">
                  <div className="step-title">Test the Connection</div>
                  <div className="step-description">
                    Click the <b>Test Connection</b> button above. The website sends a small test prompt to verify end-to-end communication with your local model.
                    When the model responds, you will see its live latency and response text!
                  </div>
                </div>
              </div>

              {/* Step 7 */}
              <div className="step-card">
                <div className="step-number">7</div>
                <div className="step-content">
                  <div className="step-title">Start Studying Privately</div>
                  <div className="step-description">
                    Click <b>Start Studying →</b> to switch to the Study Workstation.
                    Paste notes or upload `.txt`, `.pdf`, or `.docx` files, select your study format, and generate study aids with 100% on-device privacy!
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Browser Compatibility & Companion Callout */}
          <section className="card">
            <h3 style={{ fontSize: '1rem', color: 'var(--sloth-dark-green)', fontWeight: 700, marginBottom: '0.4rem' }}>
              🌐 Browser Compatibility & Mixed Content
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--sloth-text-muted)', lineHeight: 1.5 }}>
              Modern browsers enforce security boundaries when an <code>https://</code> website (such as Vercel) connects to a local loopback address (<code>127.0.0.1</code>):
            </p>
            <ul style={{ margin: '0.5rem 0 0.8rem 1.4rem', fontSize: '0.85rem', color: 'var(--sloth-text-main)', lineHeight: 1.6 }}>
              <li><b>Google Chrome, Microsoft Edge, Brave, & Opera:</b> Fully support connecting from the HTTPS website to your local bridge via W3C Private Network Access.</li>
              <li><b>Mozilla Firefox & Apple Safari:</b> Block HTTPS-to-HTTP mixed content by default.</li>
            </ul>
            <div className="alert alert-info" style={{ fontSize: '0.85rem' }}>
              💡 <b>Universal Local Companion Mode:</b> If you use Firefox or Safari, launch the bridge with:
              <div className="code-snippet">python bridge/bridge.py --open</div>
              This serves the complete web app directly from <code>http://127.0.0.1:8765</code> with zero mixed-content restrictions across all browsers!
            </div>
          </section>
        </div>
      )}

      {/* VIEW 2: STUDY WORKSTATION */}
      {activeNav === 'study' && (
        <main>
          {/* Connection Reminder Banner if Disconnected */}
          {connectionState !== 'connected' && (
            <div
              className="alert alert-info"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.8rem',
                marginBottom: '1.2rem',
              }}
            >
              <div>
                <b>⚡ Connect Local AI for 100% Private Study Aids:</b> Connect your local Ollama instance to generate summaries, flashcards, and quizzes.
              </div>
              <button
                className="btn btn-primary"
                onClick={() => setActiveNav('connect')}
                style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}
              >
                Connect Local AI →
              </button>
            </div>
          )}

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
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1, padding: '0.75rem' }}
                    onClick={handleGenerate}
                    disabled={isGenerating || notes.trim().length < 25}
                  >
                    {isGenerating ? '🦥 Generating Patiently...' : '🦥 Generate with StudySloth'}
                  </button>
                  {isGenerating && (
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.75rem 1rem', whiteSpace: 'nowrap' }}
                      onClick={handleCancelGeneration}
                      title="Stop generating"
                    >
                      ⏹️ Stop
                    </button>
                  )}
                </div>
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

          {/* Errors / Warnings */}
          {generationError && (
            <div className="alert alert-error">
              ❌ {generationError}
            </div>
          )}

          {isSimulatedResponse && (
            <div className="alert alert-warning">
              ⚠️ <b>Notice:</b> This output was generated using Simulated Demo Mode. It was NOT processed by Ollama. Connect your local bridge for real AI generation.
            </div>
          )}

          {/* Results Output Section */}
          {generationOutput && (
            <section className="card">
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
      )}

      {/* Footer */}
      <footer>
        <p>
          🦥 <b>StudySloth AI</b> • Built with React, Python, and Ollama.
        </p>
        <p style={{ marginTop: '0.3rem', fontSize: '0.78rem', color: '#7a9a74' }}>
          100% Open Source • 100% On-Device Inference • Zero Remote Data Tracking
        </p>
      </footer>
    </div>
  );
}
