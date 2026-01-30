import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "smollm2"

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()["response"].strip()
