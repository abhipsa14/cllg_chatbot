import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import OLLAMA_URL, OLLAMA_MODEL

MODEL = OLLAMA_MODEL


def call_ollama(prompt: str, temperature: float = 0.3) -> str:
    """Call local Ollama LLM with a raw prompt."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": 512,
            "stop": ["\n\nQUESTION:", "\n\nCONTEXT:"]
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        return "Sorry, I couldn't connect to Ollama. Make sure it's running (ollama serve)."
    except requests.exceptions.Timeout:
        return "Sorry, the request timed out. Please try again."
    except Exception as e:
        return f"Sorry, an error occurred: {e}"


def call_ollama_with_context(question: str, context: str) -> str:
    """Answer a question using RAG context via Ollama."""
    prompt = f"""You are a helpful college information assistant for UIT (University Institute of Technology).

INSTRUCTIONS:
1. Answer the question ONLY using the provided context below.
2. If the answer is not in the context, respond: "I couldn't find this information in the official college sources."
3. Be concise, accurate, and helpful. Your response will be spoken aloud.
4. Format your answer clearly. Avoid markdown formatting.
5. Do NOT make up information or use external knowledge.

CONTEXT FROM OFFICIAL SOURCES:
---
{context}
---

QUESTION: {question}

ANSWER:"""
    return call_ollama(prompt, temperature=0.3)


def call_ollama_general(question: str) -> str:
    """Answer a general question (no RAG context) via Ollama."""
    prompt = f"""You are UIT Assistant, a helpful and friendly voice assistant for students and staff at UIT (University Institute of Technology).
You can answer general knowledge questions, help with academics, and have natural conversations.
Be concise since your responses will be spoken aloud via text-to-speech.

Question: {question}

Answer:"""
    return call_ollama(prompt, temperature=0.7)
