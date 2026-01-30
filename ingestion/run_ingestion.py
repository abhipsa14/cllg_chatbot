from pathlib import Path
import json
import uuid

from pdf_ingestor import ingest_pdf
from web_ingestor import ingest_web
from normalizer import normalize_text
from chunker import chunk_text
from embedder import Embedder

# ---------------- CONFIG ---------------- #

PDF_DIR = Path("data/raw_pdfs")


WEBSITE_URLS = {
    "about_uit": "https://www.united.ac.in/uit/",
    "principal_message":"https://www.united.ac.in/uit/Principal-Messages.php",
    "vision_mission":"https://www.united.ac.in/uit/Vision-Mission.php",
    "programs_offered": "https://www.united.ac.in/uit/engineering.php",
    "governing_bodies":"https://www.united.ac.in/uit/Governing-Body.php",
    "canteen":"https://www.united.ac.in/uit/Cafeteria.php",
    "library":"https://www.united.ac.in/uit/Library.php"
}


EXTRACTED_PDF_DIR = Path("data/extracted_text/pdf")
EXTRACTED_WEB_DIR = Path("data/extracted_text/web")
NORMALIZED_PDF_DIR = Path("data/normalized_text/pdf")
NORMALIZED_WEB_DIR = Path("data/normalized_text/web")

CHUNKS_FILE = Path("data/processed_chunks/unified_chunks.json")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# ---------------------------------------- #

def save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

embedder = Embedder()

all_chunks = []
all_chunk_texts = []

# ----------- PDF INGESTION ----------- #

for pdf in PDF_DIR.glob("*.pdf"):
    raw_text = ingest_pdf(pdf)

    save_text(EXTRACTED_PDF_DIR / f"{pdf.stem}.txt", raw_text)

    normalized = normalize_text(raw_text)
    save_text(NORMALIZED_PDF_DIR / f"{pdf.stem}.txt", normalized)

    chunks = chunk_text(normalized, CHUNK_SIZE, CHUNK_OVERLAP)

    for chunk in chunks:
        chunk_obj = {
            "chunk_id": str(uuid.uuid4()),
            "text": chunk,
            "source_type": "pdf",
            "source": pdf.name
        }
        all_chunks.append(chunk_obj)
        all_chunk_texts.append(chunk)

# ----------- WEB INGESTION ----------- #

for section, url in WEBSITE_URLS.items():
    raw_text = ingest_web(url)

    save_text(EXTRACTED_WEB_DIR / f"{section}.txt", raw_text)

    normalized = normalize_text(raw_text)
    save_text(NORMALIZED_WEB_DIR / f"{section}.txt", normalized)

    chunks = chunk_text(normalized, CHUNK_SIZE, CHUNK_OVERLAP)

    for chunk in chunks:
        chunk_obj = {
            "chunk_id": str(uuid.uuid4()),
            "text": chunk,
            "source_type": "website",
            "source": section,
            "url": url
        }
        all_chunks.append(chunk_obj)
        all_chunk_texts.append(chunk)

# ----------- EMBEDDINGS ----------- #

embeddings = embedder.embed(all_chunk_texts)

for chunk, embedding in zip(all_chunks, embeddings):
    chunk["embedding"] = embedding

CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

print(f"✅ Ingestion complete")
print(f"📄 Total chunks stored: {len(all_chunks)}")
print(f"📁 Extracted text saved in: data/extracted_text/")
print(f"📁 Normalized text saved in: data/normalized_text/")
print(f"📦 Chunks + embeddings saved in: {CHUNKS_FILE}")
