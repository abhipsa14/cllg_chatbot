"""
Central configuration for the UIT Voice Assistant.
All settings can be overridden via environment variables or .env file.
"""

import os
import platform
from pathlib import Path

# ──────────────── PLATFORM ──────────────── #
IS_LINUX = platform.system() == "Linux"
IS_PI = IS_LINUX and os.path.exists("/proc/device-tree/model")
if IS_PI:
    try:
        with open("/proc/device-tree/model", "r") as f:
            PI_MODEL = f.read().strip()
    except Exception:
        PI_MODEL = "Raspberry Pi"
else:
    PI_MODEL = None

# Load .env file if it exists
_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    with open(_env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# ──────────────── PATHS ──────────────── #
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
EXTRACTED_PDF_DIR = DATA_DIR / "extracted_text" / "pdf"
EXTRACTED_WEB_DIR = DATA_DIR / "extracted_text" / "web"
NORMALIZED_PDF_DIR = DATA_DIR / "normalized_text" / "pdf"
NORMALIZED_WEB_DIR = DATA_DIR / "normalized_text" / "web"
CHUNKS_FILE = DATA_DIR / "processed_chunks" / "unified_chunks.json"
CHROMA_DB_DIR = str(BASE_DIR / "vector_db" / "chroma_db")

# ──────────────── OLLAMA LLM ──────────────── #
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ──────────────── EMBEDDINGS ──────────────── #
EMBED_MODEL = "all-MiniLM-L6-v2"

# ──────────────── CHUNKING ──────────────── #
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# ──────────────── RETRIEVAL ──────────────── #
COLLECTION_NAME = "college_knowledge"
TOP_K = 5
RELEVANCE_THRESHOLD = 0.35  # below this similarity → use general LLM answer

# ──────────────── WAKE WORD ──────────────── #
WAKE_WORD = os.getenv("WAKE_WORD", "hey computer")
# Alternative wake words the system will listen for
WAKE_WORDS = ["hey assistant", "hey computer", "ok assistant"]

# ──────────────── TTS ──────────────── #
TTS_RATE = 150 if IS_PI else 175  # slower on Pi for clarity via espeak
TTS_VOLUME = 0.9
TTS_ENGINE = os.getenv("TTS_ENGINE", "espeak" if IS_LINUX else "sapi5")

# ──────────────── AUDIO (Pi) ──────────────── #
# Pi mic settings — lower threshold for USB mics
MIC_ENERGY_THRESHOLD = 200 if IS_PI else 300
MIC_PAUSE_THRESHOLD = 1.2 if IS_PI else 1.0

# ──────────────── WEBSITE SOURCES ──────────────── #
WEBSITE_URLS = {
    "about_uit": "https://www.united.ac.in/uit/",
    "principal_message": "https://www.united.ac.in/uit/Principal-Messages.php",
    "vision_mission": "https://www.united.ac.in/uit/Vision-Mission.php",
    "programs_offered": "https://www.united.ac.in/uit/engineering.php",
    "governing_bodies": "https://www.united.ac.in/uit/Governing-Body.php",
    "canteen": "https://www.united.ac.in/uit/Cafeteria.php",
    "library": "https://www.united.ac.in/uit/Library.php",
}
