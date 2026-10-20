"""Local Ollama client for StudySloth AI.
Handles health checks, installed models discovery, and text generation via Ollama's REST API.
100% on-device inference: No data is ever sent across the public internet.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional, Generator
import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"

# Recommended open-weight models with hardware footprints and licenses
RECOMMENDED_MODELS = {
    "llama3.2:1b": {
        "name": "Llama 3.2 (1B)",
        "parameter_size": "1.23 Billion",
        "download_size": "~1.3 GB",
        "recommended_ram": "4 GB RAM",
        "vram": "None required (runs fast on standard CPU)",
        "license": "Meta Llama 3.2 Community License",
        "command": "ollama run llama3.2:1b",
        "description": "Ultra-lightweight, extremely fast on standard laptops, ideal for quick summaries and flashcards.",
    },
    "llama3.2:3b": {
        "name": "Llama 3.2 (3B)",
        "parameter_size": "3.21 Billion",
        "download_size": "~2.0 GB",
        "recommended_ram": "8 GB RAM",
        "vram": "2 GB VRAM or modern CPU",
        "license": "Meta Llama 3.2 Community License",
        "command": "ollama run llama3.2:3b",
        "description": "Sweet spot between reasoning accuracy and speed. Best for complex quizzes and comprehensive study guides.",
    },
    "phi3:mini": {
        "name": "Phi-3 Mini (3.8B)",
        "parameter_size": "3.8 Billion",
        "download_size": "~2.2 GB",
        "recommended_ram": "8 GB RAM",
        "vram": "2-4 GB VRAM or modern CPU",
        "license": "MIT License",
        "command": "ollama run phi3:mini",
        "description": "Microsoft's math and logic heavyweight, great for STEM, formulas, and technical reasoning.",
    },
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 (1.5B)",
        "parameter_size": "1.54 Billion",
        "download_size": "~1.0 GB",
        "recommended_ram": "4 GB RAM",
        "vram": "None required",
        "license": "Apache 2.0",
        "command": "ollama run qwen2.5:1.5b",
        "description": "Permissively licensed (Apache 2.0) with strong multilingual and structured formatting capability.",
    },
}


class OllamaClientError(Exception):
    """Raised when an error occurs during communication with local Ollama service."""
    pass


def check_ollama_status(base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 2.5) -> Tuple[bool, str, List[str]]:
    """
    Checks if Ollama is running locally and retrieves the list of installed models.
    Returns:
        (is_online, status_message, list_of_installed_model_names)
    """
    clean_url = base_url.rstrip("/")
    try:
        response = requests.get(f"{clean_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            models_list = [m.get("name", "") for m in data.get("models", [])]
            return True, "Ollama local AI server is active and online.", models_list
        else:
            return (
                False,
                f"Ollama server responded with unexpected status code {response.status_code}.",
                [],
            )
    except requests.exceptions.ConnectionError:
        return (
            False,
            "Cannot connect to local Ollama server at localhost:11434. Please ensure Ollama is installed and running (`ollama serve`).",
            [],
        )
    except requests.exceptions.Timeout:
        return (
            False,
            f"Connection to Ollama at {clean_url} timed out after {timeout} seconds.",
            [],
        )
    except Exception as exc:
        return False, f"Unexpected error checking Ollama: {str(exc)}", []


def generate_text_stream(
    prompt: str,
    system_prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    temperature: float = 0.3,
    timeout: float = 120.0,
) -> Generator[str, None, None]:
    """
    Streams generated text tokens from the local Ollama API.
    Yields chunks of text as they are computed on-device.
    """
    clean_url = base_url.rstrip("/")
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": 2048,
        },
    }

    try:
        response = requests.post(
            f"{clean_url}/api/generate",
            json=payload,
            stream=True,
            timeout=timeout,
        )
        if response.status_code == 404:
            raise OllamaClientError(
                f"Model '{model}' was not found on your local Ollama instance. "
                f"Please open PowerShell and run: `ollama pull {model}`."
            )
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    except requests.exceptions.ConnectionError as exc:
        raise OllamaClientError(
            "Connection to Ollama was lost during generation. Make sure Ollama didn't crash or run out of memory."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise OllamaClientError(
            f"Generation timed out after {timeout}s. The model may be running too slowly on your CPU. Consider trying a smaller model like `llama3.2:1b`."
        ) from exc
    except OllamaClientError:
        raise
    except Exception as exc:
        raise OllamaClientError(f"Ollama generation failed: {str(exc)}") from exc


def generate_text_sync(
    prompt: str,
    system_prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    temperature: float = 0.3,
    timeout: float = 120.0,
) -> str:
    """Non-streaming text generation fallback."""
    full_text = []
    for chunk in generate_text_stream(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        base_url=base_url,
        temperature=temperature,
        timeout=timeout,
    ):
        full_text.append(chunk)
    return "".join(full_text)


def extract_json_block(text: str) -> Optional[Any]:
    """
    Safely extracts and parses a JSON code block from markdown text.
    Handles ```json ... ``` or loose JSON arrays/objects.
    """
    if not text:
        return None
    # Look for fenced json block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Look for raw array [ ... ]
    match_arr = re.search(r"(\[\s*\{[\s\S]*\}\s*\])", text)
    if match_arr:
        try:
            return json.loads(match_arr.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Look for raw object { ... }
    match_obj = re.search(r"(\{\s*\"[\s\S]*\}\s*)", text)
    if match_obj:
        try:
            return json.loads(match_obj.group(1).strip())
        except json.JSONDecodeError:
            pass

    return None

