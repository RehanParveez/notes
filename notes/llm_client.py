from __future__ import annotations
from pathlib import Path
import json
import os
import urllib.request
import urllib.error
import time

def _load_env_file(path: str | Path = ".env") -> dict:
  env: dict[str, str] = {}
  p = Path(path)
  
  if p.exists():
    for line in p.read_text(encoding="utf-8").splitlines():
      line = line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue
      key, _, value = line.partition("=")
      env[key.strip()] = value.strip()
  return env

_env = _load_env_file()

OLLAMA_URL = os.environ.get("OLLAMA_URL") or _env.get("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL") or _env.get("OLLAMA_MODEL", "qwen2.5-coder:7b")

def generate(
  prompt: str,
  model: str = DEFAULT_MODEL,
  url: str = OLLAMA_URL,
  timeout: int = 600,
  retries: int = 3,
  backoff_seconds: float = 2.0,
) -> str:
  payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")

  last_error: Exception | None = None
  for attempt in range(1, retries + 1):
    try:
      req = urllib.request.Request(
       url, data=payload, headers={"Content-Type": "application/json"}
      )
      with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
      return data.get("response", "").strip()
  
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
      last_error = e
      if attempt < retries:
        time.sleep(backoff_seconds * attempt)

  raise RuntimeError(
    f"Ollama call failed after {retries} attempts. "
    f"Is Ollama running ('ollama serve') and is the model pulled? "
    f"Last error: {last_error}"
  )