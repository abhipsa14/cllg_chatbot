import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,      # Lower = more focused/deterministic
            "top_p": 0.9,            # Nucleus sampling
            "num_predict": 512,      # Max tokens to generate
            "stop": ["\n\nQUESTION:", "\n\nCONTEXT:"]  # Stop sequences
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    return response.json()["response"].strip()
