"""StudySloth AI Secure Local Bridge.

Binds exclusively to 127.0.0.1 and acts as a hardened, paired interface between
the StudySloth web frontend (hosted on Vercel or locally) and the user's local Ollama instance.

Security Features:
- Bound only to loopback (127.0.0.1)
- DNS Rebinding protection (Host header validation)
- Strict Origin enforcement with W3C Private Network Access (PNA) preflight support
- Short-lived, rate-limited pairing code generating cryptographically secure session tokens
- Timing-attack safe token comparison (hmac.compare_digest)
- CSRF protection requiring custom headers (X-Bridge-Token)
- Strict schema, length, and size validation
- No document or prompt logging to disk or console
- Dual mode: works via cross-origin web app OR as a local companion app
"""

import argparse
import base64
import hmac
import http.server

import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple, Union

# Reconfigure stdout/stderr on Windows to avoid charmap UnicodeEncodeErrors
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is on sys.path for utils imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.document_processor import (
    process_uploaded_document,
    validate_text_content,
    DocumentProcessingError,
    MAX_FILE_SIZE_BYTES,
    MAX_TEXT_CHARACTERS,
)
from utils.ollama_client import (
    check_ollama_status,
    generate_text_stream,
    generate_text_sync,
    DEFAULT_OLLAMA_URL,
    DEFAULT_MODEL,
    RECOMMENDED_MODELS,
    OllamaClientError,
)
from utils.prompts import build_prompt, SYSTEM_INSTRUCTION

DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"

# Default allowed web origins (production Vercel + local dev)
DEFAULT_ALLOWED_ORIGINS = {
    "https://studysloth-ai.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8765",
    "http://127.0.0.1:8765",
}

# Path to static frontend dist if built
FRONTEND_DIST_DIR = os.path.join(PROJECT_ROOT, "web", "dist")


def normalize_origin(raw_origin: str) -> str:
    """Normalizes an origin string by trimming whitespace, trailing slashes,
    and enforcing lowercase scheme and authority (e.g. 'https://foo.vercel.app').
    """
    if not raw_origin:
        return ""
    origin = raw_origin.strip()
    if not origin:
        return ""
    origin_lower = origin.lower()
    if not origin_lower.startswith("http://") and not origin_lower.startswith("https://"):
        origin = f"https://{origin}"
    parsed = urllib.parse.urlparse(origin)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    return f"{scheme}://{netloc}"


def get_configured_origins(cli_allowed_origins: Optional[List[str]] = None) -> Set[str]:
    """Collects and normalizes allowed origins from defaults, environment variables,
    optional local configuration file (.bridge_config.json), and CLI arguments.
    """
    origins = {normalize_origin(o) for o in DEFAULT_ALLOWED_ORIGINS if o}

    # 1. Environment variable: STUDYSLOTH_ALLOWED_ORIGIN (single or comma-separated)
    env_single = os.getenv("STUDYSLOTH_ALLOWED_ORIGIN")
    if env_single:
        for item in env_single.split(","):
            norm = normalize_origin(item)
            if norm:
                origins.add(norm)

    # 2. Environment variable: STUDYSLOTH_ALLOWED_ORIGINS (comma-separated list)
    env_multi = os.getenv("STUDYSLOTH_ALLOWED_ORIGINS")
    if env_multi:
        for item in env_multi.split(","):
            norm = normalize_origin(item)
            if norm:
                origins.add(norm)

    # 3. Optional local configuration file .bridge_config.json
    config_paths = [
        os.path.join(os.getcwd(), ".bridge_config.json"),
        os.path.join(PROJECT_ROOT, ".bridge_config.json"),
    ]
    for cfg_path in config_paths:
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    cfg_origins = cfg_data.get("allowed_origins", [])
                    if isinstance(cfg_origins, list):
                        for item in cfg_origins:
                            norm = normalize_origin(str(item))
                            if norm:
                                origins.add(norm)
                    elif isinstance(cfg_origins, str):
                        for item in cfg_origins.split(","):
                            norm = normalize_origin(item)
                            if norm:
                                origins.add(norm)
            except Exception:
                pass

    # 4. CLI arguments (list of strings, may contain comma-separated origins)
    if cli_allowed_origins:
        for item in cli_allowed_origins:
            if isinstance(item, str):
                for sub_item in item.split(","):
                    norm = normalize_origin(sub_item)
                    if norm:
                        origins.add(norm)

    return origins


class SessionInfo:
    def __init__(self, token: str, origin: str):
        self.token = token
        self.origin = origin
        self.created_at = time.time()
        self.last_seen = time.time()


class BridgeSecurityManager:
    """Manages pairing codes, active sessions, and security verification."""

    def __init__(self, allowed_origins: Set[str], port: int):
        self.allowed_origins = set(allowed_origins)
        self.port = port
        self.allowed_hosts = {
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            "127.0.0.1",
            "localhost",
        }
        self.lock = threading.Lock()
        
        # Pairing code state
        self.pairing_code = self._generate_pairing_code()
        self.pairing_code_created = time.time()
        self.pairing_code_lifetime = 300.0  # 5 minutes
        self.failed_attempts = 0
        self.lockout_until = 0.0

        # Active session tokens
        self.sessions: Dict[str, SessionInfo] = {}
        self.session_lifetime = 3600.0 * 8  # 8 hours

    def _generate_pairing_code(self) -> str:
        """Generates an 8-character human-readable pairing code, e.g. 'A7B2-C9D4'."""
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        return f"{part1}-{part2}"

    def reset_pairing_code(self) -> str:
        """Regenerates pairing code."""
        with self.lock:
            self.pairing_code = self._generate_pairing_code()
            self.pairing_code_created = time.time()
            self.failed_attempts = 0
            self.lockout_until = 0.0
            return self.pairing_code

    def validate_host(self, host_header: Optional[str]) -> bool:
        """Guards against DNS Rebinding attacks."""
        if not host_header:
            return False
        clean_host = host_header.strip().lower()
        return clean_host in self.allowed_hosts

    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Validates that Origin is in the configured allowlist."""
        if not origin:
            # Same-origin local requests (e.g. companion app served from 127.0.0.1)
            return True
        clean_origin = normalize_origin(origin)
        return clean_origin in self.allowed_origins

    def verify_pairing_attempt(self, candidate_code: str, origin: str) -> Tuple[bool, str, Optional[str]]:
        """Verifies pairing code with rate limiting."""
        now = time.time()
        with self.lock:
            if now < self.lockout_until:
                remaining = int(self.lockout_until - now)
                return False, f"Too many failed attempts. Try again in {remaining}s.", None

            if now - self.pairing_code_created > self.pairing_code_lifetime:
                return False, "Pairing code has expired. Restart bridge or click Refresh Code.", None

            clean_cand = candidate_code.strip().upper()
            if hmac.compare_digest(clean_cand, self.pairing_code):
                # Successful pairing: issue session token
                session_token = secrets.token_hex(32)
                self.sessions[session_token] = SessionInfo(session_token, origin)
                self.failed_attempts = 0
                return True, "Pairing successful.", session_token
            else:
                self.failed_attempts += 1
                if self.failed_attempts >= 5:
                    self.lockout_until = now + 60.0
                    return False, "Too many failed attempts. Locked for 60 seconds.", None
                return False, f"Invalid pairing code. ({5 - self.failed_attempts} attempts remaining)", None

    def validate_session_token(self, token: Optional[str]) -> bool:
        """Validates an active session token in constant time."""
        if not token:
            return False
        now = time.time()
        with self.lock:
            for stored_token, session in list(self.sessions.items()):
                if hmac.compare_digest(token, stored_token):
                    if now - session.last_seen > self.session_lifetime:
                        del self.sessions[stored_token]
                        return False
                    session.last_seen = now
                    return True
            return False

    def revoke_session_token(self, token: Optional[str]):
        """Revokes a session token upon user disconnect."""
        if not token:
            return
        with self.lock:
            for stored_token in list(self.sessions.keys()):
                if hmac.compare_digest(token, stored_token):
                    del self.sessions[stored_token]
                    break


class BridgeHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Hardened HTTP request handler for StudySloth AI local bridge."""

    security_manager: BridgeSecurityManager
    ollama_url: str = DEFAULT_OLLAMA_URL

    # Prevent noisy server header
    server_version = "StudySlothBridge/1.0"
    sys_version = ""

    def log_message(self, format_str, *args):
        """Custom safe logging: never log request body or private study contents."""
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"
        code = args[1] if len(args) > 1 else "-"
        method_path = args[0] if len(args) > 0 else "-"
        # Only log HTTP method, path, and response code
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {client_ip} - {method_path} -> {code}\n")

    def _set_cors_headers(self):
        """Sets strict CORS and W3C Private Network Access (PNA) preflight headers."""
        origin = self.headers.get("Origin")
        if origin and self.security_manager.is_origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        elif not origin:
            # Same-origin request
            pass

        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-Bridge-Token, Accept, Access-Control-Request-Private-Network",
        )
        # Required for Chromium Private Network Access (PNA) specification
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")

        self.send_header("Access-Control-Max-Age", "600")

    def _send_json(self, status_code: int, data: dict):
        """Helper to send JSON response with security headers."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _check_security(self, require_token: bool = True) -> bool:
        """Verifies Host, Origin, and session token."""
        # 1. DNS Rebinding Host Check
        host = self.headers.get("Host")
        if not self.security_manager.validate_host(host):
            self._send_json(400, {"error": "Invalid Host header (DNS rebinding protection)."})
            return False

        # 2. Origin Check
        origin = self.headers.get("Origin")
        if origin and not self.security_manager.is_origin_allowed(origin):
            self._send_json(403, {"error": f"Origin '{origin}' is not authorized by the local bridge."})
            return False

        # 3. Session Token Check (if required)
        if require_token:
            token = self.headers.get("X-Bridge-Token")
            if not self.security_manager.validate_session_token(token):
                self._send_json(401, {"error": "Unauthorized. Invalid or missing X-Bridge-Token."})
                return False

        return True

    def do_OPTIONS(self):
        """Handles CORS and PNA preflight requests."""
        host = self.headers.get("Host")
        if not self.security_manager.validate_host(host):
            self.send_response(400)
            self.end_headers()
            return

        origin = self.headers.get("Origin")
        if origin and not self.security_manager.is_origin_allowed(origin):
            self.send_response(403)
            self.end_headers()
            return

        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handles GET requests (health checks or local static frontend)."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/health":
            if not self._check_security(require_token=False):
                return
            
            # Optional session token validation if client provided one
            token = self.headers.get("X-Bridge-Token")
            session_valid = None
            if token:
                session_valid = self.security_manager.validate_session_token(token)

            # Query local Ollama
            is_online, status_msg, models = check_ollama_status(self.ollama_url, timeout=2.0)
            has_recommended = DEFAULT_MODEL in models
            
            self._send_json(200, {
                "status": "ok",
                "bridge_version": "1.0.0",
                "bridge_online": True,
                "ollama_online": is_online,
                "ollama_status": status_msg,
                "installed_models": models,
                "default_model": DEFAULT_MODEL,
                "default_model_available": has_recommended,
                "recommended_specs": RECOMMENDED_MODELS.get(DEFAULT_MODEL, {}),
                "session_valid": session_valid,
            })
            return

        # Serve static frontend files if local companion app mode is used
        if self._serve_static_frontend(path):
            return

        self._send_json(404, {"error": f"Path '{path}' not found on local bridge."})

    def do_POST(self):
        """Handles POST endpoints: /api/pair, /api/unpair, /api/extract, /api/generate."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Rate limit request payload to 15 MB
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            self._send_json(411, {"error": "Length Required."})
            return

        try:
            content_length = int(content_length_header)
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header."})
            return

        if content_length > MAX_FILE_SIZE_BYTES + (5 * 1024 * 1024):
            self._send_json(413, {"error": "Payload exceeds 15 MB limit."})
            return

        # 1. Pairing endpoint
        if path == "/api/pair":
            if not self._check_security(require_token=False):
                return
            
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "Malformed JSON payload."})
                return

            code = payload.get("pairing_code", "")
            origin = self.headers.get("Origin", "local")
            success, msg, session_token = self.security_manager.verify_pairing_attempt(code, origin)
            
            if success:
                self._send_json(200, {
                    "status": "success",
                    "message": msg,
                    "session_token": session_token,
                })
            else:
                self._send_json(401, {"status": "error", "error": msg})
            return

        # 2. Unpair endpoint
        if path == "/api/unpair":
            if not self._check_security(require_token=False):
                return
            token = self.headers.get("X-Bridge-Token")
            self.security_manager.revoke_session_token(token)
            self._send_json(200, {"status": "success", "message": "Session revoked."})
            return

        # All subsequent endpoints require valid X-Bridge-Token
        if not self._check_security(require_token=True):
            return

        # 3. Document Extraction endpoint
        if path == "/api/extract":
            body_bytes = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")

            filename = "document.txt"
            file_bytes = b""

            if "application/json" in content_type:
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    filename = payload.get("filename", "document.txt")
                    b64_content = payload.get("content_base64", "")
                    file_bytes = base64.b64decode(b64_content)
                except Exception as exc:
                    self._send_json(400, {"error": f"Failed to parse base64 document: {str(exc)}"})
                    return
            else:
                # Direct raw upload with filename in header
                filename = self.headers.get("X-File-Name", "document.txt")
                file_bytes = body_bytes

            try:
                clean_text, meta = process_uploaded_document(filename, file_bytes)
                self._send_json(200, {
                    "status": "success",
                    "text": clean_text,
                    "metadata": meta,
                })
            except DocumentProcessingError as doc_err:
                self._send_json(400, {"error": str(doc_err)})
            except Exception as exc:
                self._send_json(500, {"error": f"Unexpected extraction error: {str(exc)}"})
            return

        # 4. Text Generation endpoint
        if path == "/api/generate":
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "Malformed JSON payload."})
                return

            notes = payload.get("notes", "")
            output_type = payload.get("output_type", "summary")
            model = payload.get("model", DEFAULT_MODEL)
            temperature = float(payload.get("temperature", 0.3))
            stream_mode = bool(payload.get("stream", True))

            is_valid, validation_msg = validate_text_content(notes)
            if not is_valid:
                self._send_json(400, {"error": validation_msg})
                return

            if len(notes) > MAX_TEXT_CHARACTERS:
                notes = notes[:MAX_TEXT_CHARACTERS]

            prompt = build_prompt(output_type, notes)

            # Check Ollama status before invoking
            is_online, _, _ = check_ollama_status(self.ollama_url, timeout=2.0)
            if not is_online:
                self._send_json(503, {
                    "error": "Ollama is not running locally. Please start it with 'ollama serve' or 'ollama run llama3.2:1b'."
                })
                return

            if stream_mode:
                # Stream via Server-Sent Events (SSE)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.send_header("X-Accel-Buffering", "no")
                self._set_cors_headers()
                self.end_headers()
                self.close_connection = True

                try:
                    for chunk in generate_text_stream(
                        prompt=prompt,
                        system_prompt=SYSTEM_INSTRUCTION,
                        model=model,
                        base_url=self.ollama_url,
                        temperature=temperature,
                        timeout=120.0,
                    ):
                        sse_msg = f"data: {json.dumps({'chunk': chunk})}\n\n"
                        self.wfile.write(sse_msg.encode("utf-8"))
                        self.wfile.flush()

                    done_msg = f"data: {json.dumps({'done': True})}\n\n"
                    self.wfile.write(done_msg.encode("utf-8"))
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected or aborted stream
                    return
                except OllamaClientError as err:
                    try:
                        err_msg = f"data: {json.dumps({'error': str(err)})}\n\n"
                        self.wfile.write(err_msg.encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        pass
                except Exception as exc:
                    try:
                        err_msg = f"data: {json.dumps({'error': f'Generation error: {str(exc)}'})}\n\n"
                        self.wfile.write(err_msg.encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        pass
                return
            else:
                # Non-streaming fallback
                try:
                    full_text = []
                    for chunk in generate_text_stream(
                        prompt=prompt,
                        system_prompt=SYSTEM_INSTRUCTION,
                        model=model,
                        base_url=self.ollama_url,
                        temperature=temperature,
                    ):
                        full_text.append(chunk)
                    self._send_json(200, {
                        "status": "success",
                        "output": "".join(full_text),
                    })
                except OllamaClientError as err:
                    self._send_json(500, {"error": str(err)})
                return

        # 5. Live Connection Test endpoint
        if path == "/api/test":
            body_bytes = self.rfile.read(content_length)
            model = DEFAULT_MODEL
            if body_bytes:
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    model = payload.get("model", DEFAULT_MODEL)
                except Exception:
                    pass

            is_online, _, models = check_ollama_status(self.ollama_url, timeout=2.0)
            if not is_online:
                self._send_json(503, {
                    "status": "error",
                    "error": "Ollama is not running locally. Please start it with 'ollama serve' or open the Ollama app."
                })
                return

            if models and model not in models:
                self._send_json(404, {
                    "status": "error",
                    "error": f"Model '{model}' is not installed in your Ollama library. Run 'ollama pull {model}'."
                })
                return

            start_t = time.time()
            try:
                test_prompt = "Hello! In 1 short sentence, confirm that StudySloth local AI is connected."
                res = generate_text_sync(
                    prompt=test_prompt,
                    system_prompt="You are StudySloth AI, a private local study assistant. Respond briefly in one short sentence.",
                    model=model,
                    base_url=self.ollama_url,
                    temperature=0.1,
                    timeout=25.0,
                )
                elapsed_ms = int((time.time() - start_t) * 1000)
                self._send_json(200, {
                    "status": "success",
                    "model": model,
                    "latency_ms": elapsed_ms,
                    "reply": res.strip(),
                })
            except OllamaClientError as err:
                self._send_json(500, {"status": "error", "error": str(err)})
            except Exception as exc:
                self._send_json(500, {"status": "error", "error": f"Test failed: {str(exc)}"})
            return

        self._send_json(404, {"error": f"Endpoint '{path}' not found."})

    def _serve_static_frontend(self, path: str) -> bool:
        """Serves built static web frontend from web/dist for local companion mode."""
        index_file = os.path.join(FRONTEND_DIST_DIR, "index.html")
        if not os.path.isfile(index_file):
            # If web/dist is not built yet, display a helpful diagnostic page rather than a blank 404
            diagnostic_html = (
                "<!DOCTYPE html>"
                "<html><head><meta charset='utf-8'><title>StudySloth AI Local Bridge</title>"
                "<style>"
                "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; "
                "background: #f4f7f4; color: #233d26; padding: 2rem; display: flex; justify-content: center; align-items: center; min-height: 80vh; margin: 0; }"
                ".card { background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); padding: 2rem; max-width: 580px; width: 100%; border: 1px solid #d4ded5; }"
                "h1 { color: #1f4d2b; font-size: 1.4rem; margin-top: 0; display: flex; align-items: center; gap: 0.5rem; }"
                ".badge { display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; margin-bottom: 1rem; }"
                "code { background: #eef3ef; padding: 0.2rem 0.45rem; border-radius: 4px; font-size: 0.9em; color: #1b4d24; font-weight: 600; }"
                ".box { background: #fbfdfb; border: 1px solid #e0eae1; border-radius: 8px; padding: 1rem; margin: 1rem 0; }"
                "</style></head><body>"
                "<div class='card'>"
                "<h1>🦥 StudySloth AI Local Bridge</h1>"
                "<span class='badge'>🟢 Loopback Service Active on 127.0.0.1:8765</span>"
                "<p>Your local AI bridge is active and ready to process notes from your hosted Vercel website or companion app.</p>"
                "<div class='box'>"
                "<p style='margin:0 0 0.5rem 0;font-weight:600;'>To enable the Local Companion App at this URL:</p>"
                "<p style='margin:0 0 0.5rem 0;font-size:0.88rem;color:#555;'>Build the frontend assets once using Node.js:</p>"
                "<code>cd web && npm run build</code>"
                "</div>"
                "<p style='font-size:0.85rem;color:#666;margin-bottom:0;'>If you are using the public website on Vercel, open your Vercel URL and enter your pairing code from the terminal.</p>"
                "</div></body></html>"
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(diagnostic_html)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(diagnostic_html)
            return True

        if path in ("", "/"):
            file_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
        else:
            safe_rel_path = path.lstrip("/")
            file_path = os.path.normpath(os.path.join(FRONTEND_DIST_DIR, safe_rel_path))
            if not file_path.startswith(FRONTEND_DIST_DIR):
                return False

        if not os.path.isfile(file_path):
            # Fallback to index.html for SPA client-side routing
            file_path = os.path.join(FRONTEND_DIST_DIR, "index.html")

        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(content)
                return True
            except Exception:
                return False
        return False


def create_bridge_handler(security_manager: BridgeSecurityManager, ollama_url: str):
    """Factory creating an HTTP request handler configured with security manager and Ollama URL.
    Avoids Python class-scope namespace shadowing.
    """
    class CustomHandler(BridgeHTTPRequestHandler):
        pass

    CustomHandler.security_manager = security_manager
    CustomHandler.ollama_url = ollama_url
    return CustomHandler


def run_bridge(
    port: int = DEFAULT_PORT,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    allowed_origin: Optional[Union[str, List[str]]] = None,
    open_browser: bool = False,
):
    """Starts the StudySloth AI local bridge server."""
    cli_origins: List[str] = []
    if isinstance(allowed_origin, list):
        cli_origins.extend(allowed_origin)
    elif isinstance(allowed_origin, str):
        cli_origins.append(allowed_origin)

    origins = get_configured_origins(cli_origins)

    security = BridgeSecurityManager(origins, port)
    handler_class = create_bridge_handler(security, ollama_url)

    # Bind exclusively to 127.0.0.1
    server_address = (DEFAULT_HOST, port)
    try:
        httpd = http.server.ThreadingHTTPServer(server_address, handler_class)
    except OSError as err:
        sys.stderr.write(f"\n❌ Error binding to {DEFAULT_HOST}:{port}: {err}\n")
        sys.stderr.write("Make sure no other service is using port 8765.\n")
        sys.exit(1)


    print("\n" + "=" * 64)
    print(" 🦥 StudySloth AI Local Bridge Server")
    print("=" * 64)
    print(f" Status:             Running on http://{DEFAULT_HOST}:{port}")
    print(f" Local Ollama URL:   {ollama_url}")
    print(f" Authorized Origins: {', '.join(sorted(origins))}")
    print("-" * 64)
    print(f" 🔑 YOUR SESSION PAIRING CODE:  {security.pairing_code}")
    print(" (Expires in 5 minutes. Enter this code in your StudySloth Web App)")
    print("-" * 64)
    print(" Security Policy:")
    print(" • Bound exclusively to loopback (127.0.0.1)")
    print(" • Protected against DNS Rebinding and CSRF")
    print(" • Zero notes or prompts logged to disk")
    print(" • Press Ctrl+C in this terminal to stop the bridge anytime.")
    print("=" * 64 + "\n")

    if open_browser:
        import webbrowser
        companion_url = f"http://{DEFAULT_HOST}:{port}"
        print(f"🌐 Opening companion app in browser: {companion_url}")
        webbrowser.open(companion_url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🦥 Shutting down StudySloth Local Bridge cleanly...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StudySloth AI Secure Local Bridge")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    parser.add_argument("--ollama-url", type=str, default=DEFAULT_OLLAMA_URL, help="Ollama local URL")
    parser.add_argument(
        "--allowed-origin",
        type=str,
        action="append",
        default=None,
        help="Additional production website origin(s) to allow (can be specified multiple times or comma-separated, or set via STUDYSLOTH_ALLOWED_ORIGIN)",
    )
    parser.add_argument("--open", action="store_true", help="Automatically open browser to local companion app")
    args = parser.parse_args()

    run_bridge(
        port=args.port,
        ollama_url=args.ollama_url,
        allowed_origin=args.allowed_origin,
        open_browser=args.open,
    )
