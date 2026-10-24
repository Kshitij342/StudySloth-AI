"""Unit and integration tests for StudySloth AI local bridge."""

import base64
import json
import threading
import time
import urllib.error
import urllib.request
import pytest

from bridge.bridge import (
    BridgeSecurityManager,
    BridgeHTTPRequestHandler,
    create_bridge_handler,
    normalize_origin,
    get_configured_origins,
    DEFAULT_PORT,
    DEFAULT_HOST,
)


@pytest.fixture
def security_manager():
    allowed_origins = {
        "https://studysloth-ai.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
    return BridgeSecurityManager(allowed_origins, port=8765)


def test_create_bridge_handler_scope_regression():
    """Regression test ensuring create_bridge_handler correctly binds parameters without NameError."""
    security = BridgeSecurityManager({"http://localhost:3000"}, port=8765)
    test_ollama_url = "http://127.0.0.1:11434"
    handler_class = create_bridge_handler(security, test_ollama_url)
    assert handler_class.security_manager is security
    assert handler_class.ollama_url == test_ollama_url
    assert issubclass(handler_class, BridgeHTTPRequestHandler)



def test_security_manager_pairing_success(security_manager):
    code = security_manager.pairing_code
    success, msg, token = security_manager.verify_pairing_attempt(code, "https://studysloth-ai.vercel.app")
    assert success is True
    assert token is not None
    assert len(token) == 64
    assert security_manager.validate_session_token(token) is True


def test_security_manager_pairing_failure_and_lockout(security_manager):
    # 4 invalid attempts
    for _ in range(4):
        success, msg, token = security_manager.verify_pairing_attempt("WRONG-CODE", "https://studysloth-ai.vercel.app")
        assert success is False
        assert token is None
        assert "Invalid pairing code" in msg

    # 5th invalid attempt triggers lockout
    success, msg, token = security_manager.verify_pairing_attempt("WRONG-CODE", "https://studysloth-ai.vercel.app")
    assert success is False
    assert "Locked for 60 seconds" in msg

    # Subsequent attempt within lockout window is rejected immediately
    success, msg, token = security_manager.verify_pairing_attempt("ANY-CODE", "https://studysloth-ai.vercel.app")
    assert success is False
    assert "Too many failed attempts" in msg


def test_security_manager_host_validation(security_manager):
    assert security_manager.validate_host("127.0.0.1:8765") is True
    assert security_manager.validate_host("localhost:8765") is True
    assert security_manager.validate_host("127.0.0.1") is True
    assert security_manager.validate_host("localhost") is True

    # Malicious hosts (DNS Rebinding)
    assert security_manager.validate_host("attacker.com") is False
    assert security_manager.validate_host("evil.com:8765") is False
    assert security_manager.validate_host("") is False
    assert security_manager.validate_host(None) is False


def test_security_manager_origin_validation(security_manager):
    assert security_manager.is_origin_allowed("https://studysloth-ai.vercel.app") is True
    assert security_manager.is_origin_allowed("http://localhost:3000") is True
    assert security_manager.is_origin_allowed(None) is True  # Same-origin

    # Untrusted origins
    assert security_manager.is_origin_allowed("https://malicious-site.com") is False
    assert security_manager.is_origin_allowed("http://phishing.org") is False


def test_security_manager_session_revocation(security_manager):
    code = security_manager.pairing_code
    _, _, token = security_manager.verify_pairing_attempt(code, "https://studysloth-ai.vercel.app")
    assert security_manager.validate_session_token(token) is True

    security_manager.revoke_session_token(token)
    assert security_manager.validate_session_token(token) is False


def test_normalize_origin():
    assert normalize_origin("https://studysloth-ai.vercel.app/") == "https://studysloth-ai.vercel.app"
    assert normalize_origin("http://localhost:3000///") == "http://localhost:3000"
    assert normalize_origin("  HTTPS://CUSTOM-DOMAIN.COM/  ") == "https://custom-domain.com"
    assert normalize_origin("my-app.vercel.app") == "https://my-app.vercel.app"
    assert normalize_origin("") == ""


def test_get_configured_origins_env_and_cli(monkeypatch):
    monkeypatch.setenv("STUDYSLOTH_ALLOWED_ORIGIN", "https://single-origin.vercel.app/")
    monkeypatch.setenv("STUDYSLOTH_ALLOWED_ORIGINS", "https://multi1.com,https://multi2.org/")

    origins = get_configured_origins(["https://cli-origin.vercel.app", "https://cli2.com,https://cli3.com"])
    assert "https://single-origin.vercel.app" in origins
    assert "https://multi1.com" in origins
    assert "https://multi2.org" in origins
    assert "https://cli-origin.vercel.app" in origins
    assert "https://cli2.com" in origins
    assert "https://cli3.com" in origins
    assert "https://studysloth-ai.vercel.app" in origins


def test_requirements_bridge_is_minimal():
    import os
    bridge_req_path = os.path.join(os.path.dirname(__file__), "..", "requirements-bridge.txt")
    assert os.path.isfile(bridge_req_path)
    with open(bridge_req_path, "r", encoding="utf-8") as f:
        lines = [line.strip().lower() for line in f if line.strip() and not line.strip().startswith("#")]
    assert any("requests" in l for l in lines)
    assert any("pypdf" in l for l in lines)
    assert any("python-docx" in l for l in lines)
    # Crucial: Streamlit and dev dependencies must NOT be in minimal bridge requirements
    assert not any("streamlit" in l for l in lines)
    assert not any("pytest" in l for l in lines)


def test_launch_scripts_exist():
    import os
    root = os.path.join(os.path.dirname(__file__), "..")
    bat = os.path.join(root, "start_bridge.bat")
    ps1 = os.path.join(root, "start_bridge.ps1")
    sh = os.path.join(root, "start_bridge.sh")

    assert os.path.isfile(bat)
    assert os.path.isfile(ps1)
    assert os.path.isfile(sh)

    with open(bat, "r", encoding="utf-8") as f:
        assert "bridge.py" in f.read()
    with open(ps1, "r", encoding="utf-8") as f:
        assert "bridge.py" in f.read()
    with open(sh, "r", encoding="utf-8") as f:
        assert "bridge.py" in f.read()


# --- INTEGRATION TESTS WITH LIVE THREADED SERVER ---

@pytest.fixture(scope="module")
def live_bridge_server():
    """Runs a test bridge server on port 8799."""
    test_port = 8799
    allowed_origins = {
        "https://studysloth-ai.vercel.app",
        "http://localhost:3000",
    }
    security = BridgeSecurityManager(allowed_origins, port=test_port)
    handler_class = create_bridge_handler(security, "http://127.0.0.1:54321")

    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer(("127.0.0.1", test_port), handler_class)

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    yield {
        "port": test_port,
        "base_url": f"http://127.0.0.1:{test_port}",
        "security": security,
    }

    server.shutdown()
    server.server_close()


def test_bridge_options_cors_and_pna(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/api/health"
    req = urllib.request.Request(url, method="OPTIONS")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://studysloth-ai.vercel.app")
    req.add_header("Access-Control-Request-Private-Network", "true")

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 204
        headers = dict(resp.headers)
        assert headers.get("Access-Control-Allow-Origin") == "https://studysloth-ai.vercel.app"
        assert headers.get("Access-Control-Allow-Private-Network") == "true"


def test_bridge_get_health(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/api/health"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://studysloth-ai.vercel.app")

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["bridge_online"] is True
        assert data["ollama_online"] is False  # Dummy port


def test_bridge_pairing_and_authorized_extraction(live_bridge_server):
    base = live_bridge_server["base_url"]
    sec = live_bridge_server["security"]
    code = sec.pairing_code

    # 1. Attempt pairing
    pair_url = f"{base}/api/pair"
    pair_body = json.dumps({"pairing_code": code}).encode("utf-8")
    req = urllib.request.Request(pair_url, data=pair_body, method="POST")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://studysloth-ai.vercel.app")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "success"
        token = res["session_token"]
        assert token is not None

    # 2. Extract without token should fail with 401
    extract_url = f"{base}/api/extract"
    extract_body = json.dumps({
        "filename": "notes.txt",
        "content_base64": base64.b64encode(b"Mitochondria is the powerhouse of the cell.").decode("utf-8")
    }).encode("utf-8")

    req_no_auth = urllib.request.Request(extract_url, data=extract_body, method="POST")
    req_no_auth.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_no_auth.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_no_auth.add_header("Content-Type", "application/json")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_no_auth)
    assert exc_info.value.code == 401

    # 3. Extract WITH token should succeed
    req_auth = urllib.request.Request(extract_url, data=extract_body, method="POST")
    req_auth.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_auth.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_auth.add_header("Content-Type", "application/json")
    req_auth.add_header("X-Bridge-Token", token)

    with urllib.request.urlopen(req_auth) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "success"
        assert "Mitochondria" in res["text"]
        assert res["metadata"]["word_count"] > 0


def test_bridge_dns_rebinding_rejected(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/api/health"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Host", "malicious-site.com")  # Forged Host header

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_bridge_unauthorized_origin_rejected(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/api/health"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://evil-phishing.com")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 403


def test_bridge_admin_endpoint_forbidden(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/api/delete"  # Raw Ollama admin path
    req = urllib.request.Request(url, method="POST", data=b"{}")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://studysloth-ai.vercel.app")
    req.add_header("Content-Type", "application/json")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code in (401, 404)


def test_bridge_static_frontend_serving(live_bridge_server):
    url = f"{live_bridge_server['base_url']}/"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "StudySloth" in content
        assert "<div id=\"root\">" in content


def test_bridge_generate_offline_ollama(live_bridge_server):
    sec = live_bridge_server["security"]
    code = sec.pairing_code
    _, _, token = sec.verify_pairing_attempt(code, "https://studysloth-ai.vercel.app")

    url = f"{live_bridge_server['base_url']}/api/generate"
    body = json.dumps({
        "notes": "Sample notes for testing offline ollama response in bridge.",
        "output_type": "summary",
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req.add_header("Origin", "https://studysloth-ai.vercel.app")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Bridge-Token", token)

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 503
    err_data = json.loads(exc_info.value.read().decode("utf-8"))
    assert "Ollama is not running" in err_data["error"]


def test_bridge_health_session_validation(live_bridge_server):
    sec = live_bridge_server["security"]
    code = sec.pairing_code
    _, _, token = sec.verify_pairing_attempt(code, "https://studysloth-ai.vercel.app")

    url = f"{live_bridge_server['base_url']}/api/health"

    # 1. Health check with valid token
    req_valid = urllib.request.Request(url, method="GET")
    req_valid.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_valid.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_valid.add_header("X-Bridge-Token", token)

    with urllib.request.urlopen(req_valid) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["bridge_online"] is True
        assert data["session_valid"] is True

    # 2. Health check with invalid/expired token
    req_invalid = urllib.request.Request(url, method="GET")
    req_invalid.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_invalid.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_invalid.add_header("X-Bridge-Token", "invalid-expired-token")

    with urllib.request.urlopen(req_invalid) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["bridge_online"] is True
        assert data["session_valid"] is False


def test_bridge_test_endpoint_auth_and_offline(live_bridge_server):
    sec = live_bridge_server["security"]
    code = sec.pairing_code
    _, _, token = sec.verify_pairing_attempt(code, "https://studysloth-ai.vercel.app")

    url = f"{live_bridge_server['base_url']}/api/test"
    body = json.dumps({"model": "llama3.2:1b"}).encode("utf-8")

    # 1. Without token -> 401 Unauthorized
    req_no_auth = urllib.request.Request(url, data=body, method="POST")
    req_no_auth.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_no_auth.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_no_auth.add_header("Content-Type", "application/json")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_no_auth)
    assert exc_info.value.code == 401

    # 2. With token -> 503 (since dummy Ollama port is offline)
    req_auth = urllib.request.Request(url, data=body, method="POST")
    req_auth.add_header("Host", f"127.0.0.1:{live_bridge_server['port']}")
    req_auth.add_header("Origin", "https://studysloth-ai.vercel.app")
    req_auth.add_header("Content-Type", "application/json")
    req_auth.add_header("X-Bridge-Token", token)

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_auth)
    assert exc_info.value.code == 503
    data = json.loads(exc_info.value.read().decode("utf-8"))
    assert "Ollama is not running" in data["error"]

