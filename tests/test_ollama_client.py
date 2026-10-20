"""Tests for Ollama client utility functions."""

from unittest.mock import patch, MagicMock
import pytest
import requests

from utils.ollama_client import (
    check_ollama_status,
    extract_json_block,
    generate_text_sync,
    generate_text_stream,
    RECOMMENDED_MODELS,
    OllamaClientError,
    DEFAULT_MODEL,
)


def test_recommended_models_structure():
    assert "llama3.2:1b" in RECOMMENDED_MODELS
    assert "llama3.2:3b" in RECOMMENDED_MODELS
    assert "phi3:mini" in RECOMMENDED_MODELS
    assert "qwen2.5:1.5b" in RECOMMENDED_MODELS

    for key, info in RECOMMENDED_MODELS.items():
        assert "name" in info
        assert "parameter_size" in info
        assert "download_size" in info
        assert "recommended_ram" in info
        assert "license" in info
        assert "command" in info


def test_check_ollama_status_offline():
    # Calling non-existent port should return is_online=False without crashing
    is_online, msg, models = check_ollama_status("http://127.0.0.1:54321", timeout=0.5)
    assert is_online is False
    assert "cannot connect" in msg.lower() or "error" in msg.lower() or "timed out" in msg.lower()
    assert models == []


def test_extract_json_block_fenced():
    markdown_text = """Here is the response:
```json
[
  {"id": 1, "question": "What is ATP?", "answer": "Energy currency of cell"}
]
```
Hope this helps!"""
    parsed = extract_json_block(markdown_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["question"] == "What is ATP?"


def test_extract_json_block_raw_array():
    raw_text = """Some text before:
[
  {"id": 1, "question": "What is Big-O?", "answer": "Asymptotic complexity"}
]
Some text after."""
    parsed = extract_json_block(raw_text)
    assert isinstance(parsed, list)
    assert parsed[0]["answer"] == "Asymptotic complexity"


def test_extract_json_block_raw_dict():
    raw_text = """Some text before:
{
  "flashcards": [
    {"id": 1, "question": "What is Mitochondria?", "answer": "Powerhouse of the cell"}
  ]
}
Some text after."""
    parsed = extract_json_block(raw_text)
    # The array regex matches the embedded list directly
    assert isinstance(parsed, list)
    assert parsed[0]["question"] == "What is Mitochondria?"
    assert parsed[0]["answer"] == "Powerhouse of the cell"




def test_extract_json_block_none_found():
    assert extract_json_block("Plain text with no json.") is None
    assert extract_json_block("") is None


@patch("requests.get")
def test_check_ollama_status_online(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3.2:1b"}, {"name": "phi3:mini"}]
    }
    mock_get.return_value = mock_resp

    is_online, msg, models = check_ollama_status("http://localhost:11434")
    assert is_online is True
    assert "llama3.2:1b" in models
    assert "phi3:mini" in models


@patch("requests.post")
def test_generate_text_stream_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'{"response": "Hello ", "done": false}',
        b'{"response": "Sloth!", "done": true}',
    ]
    mock_post.return_value = mock_resp

    output = list(generate_text_stream("Hi", "System", "llama3.2:1b"))
    assert "".join(output) == "Hello Sloth!"


@patch("requests.post")
def test_generate_text_model_not_found(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_post.return_value = mock_resp

    with pytest.raises(OllamaClientError) as exc_info:
        list(generate_text_stream("Hi", "System", "non-existent-model"))
    assert "was not found" in str(exc_info.value)
