import sys
from pathlib import Path
import json
import uuid
import os

# Allow running from project root or from ingestion/ directory
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_PROJECT_ROOT))

from pdf_ingestor import ingest_file
from web_ingestor import ingest_web
from normalizer import normalize_text
from chunker import chunk_text
from embedder import Embedder

# ---------------- CONFIG ---------------- #

# Resolve paths relative to project root
PDF_DIR = _PROJECT_ROOT / "data" / "raw_pdfs"
DOCX_FILES = [_PROJECT_ROOT / "UIT Data Set.docx"]  # Primary knowledge base

WEBSITE_URLS = {
    "about_uit": "https://www.united.ac.in/uit/",
    "principal_message": "https://www.united.ac.in/uit/Principal-Messages.php",
    "vision_mission": "https://www.united.ac.in/uit/Vision-Mission.php",
    "programs_offered": "https://www.united.ac.in/uit/engineering.php",
    "governing_bodies": "https://www.united.ac.in/uit/Governing-Body.php",
    "canteen": "https://www.united.ac.in/uit/Cafeteria.php",
    "library": "https://www.united.ac.in/uit/Library.php",
}

EXTRACTED_PDF_DIR = _PROJECT_ROOT / "data" / "extracted_text" / "pdf"
EXTRACTED_WEB_DIR = _PROJECT_ROOT / "data" / "extracted_text" / "web"
NORMALIZED_PDF_DIR = _PROJECT_ROOT / "data" / "normalized_text" / "pdf"
NORMALIZED_WEB_DIR = _PROJECT_ROOT / "data" / "normalized_text" / "web"

CHUNKS_FILE = _PROJECT_ROOT / "data" / "processed_chunks" / "unified_chunks.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# ---------------------------------------- #


def save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    """Run the full ingestion pipeline."""
    embedder = Embedder()

    all_chunks = []
    all_chunk_texts = []

    # ----------- DOCX KNOWLEDGE BASE ----------- #
    # Ingest the primary UIT Data Set.docx file
    for docx_path in DOCX_FILES:
        if docx_path.exists():
            print(f"📄 Ingesting knowledge base: {docx_path.name}")
            raw_text = ingest_file(docx_path)

            if not raw_text.strip():
                print(f"  ⚠️ Empty file: {docx_path.name}")
                continue

            save_text(EXTRACTED_PDF_DIR / f"{docx_path.stem}.txt", raw_text)

            normalized = normalize_text(raw_text)
            save_text(NORMALIZED_PDF_DIR / f"{docx_path.stem}.txt", normalized)

            chunks = chunk_text(normalized, CHUNK_SIZE, CHUNK_OVERLAP)
            print(f"  → {len(chunks)} chunks created from {docx_path.name}")

            for chunk in chunks:
                chunk_obj = {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk,
                    "source_type": "docx",
                    "source": docx_path.name,
                }
                all_chunks.append(chunk_obj)
                all_chunk_texts.append(chunk)
        else:
            print(f"  ⚠️ File not found: {docx_path}")

    # ----------- PDF / TXT INGESTION ----------- #
    for pattern in ["*.pdf", "*.txt", "*.docx", "*.doc"]:
        for file in PDF_DIR.glob(pattern):
            raw_text = ingest_file(file)

            if not raw_text.strip():
                print(f"Skipping empty file: {file.name}")
                continue

            save_text(EXTRACTED_PDF_DIR / f"{file.stem}.txt", raw_text)

            normalized = normalize_text(raw_text)
            save_text(NORMALIZED_PDF_DIR / f"{file.stem}.txt", normalized)

            chunks = chunk_text(normalized, CHUNK_SIZE, CHUNK_OVERLAP)

            for chunk in chunks:
                chunk_obj = {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk,
                    "source_type": file.suffix.lstrip("."),
                    "source": file.name,
                }
                all_chunks.append(chunk_obj)
                all_chunk_texts.append(chunk)

    # ----------- WEB INGESTION ----------- #
    for section, url in WEBSITE_URLS.items():
        try:
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
                    "url": url,
                }
                all_chunks.append(chunk_obj)
                all_chunk_texts.append(chunk)
        except Exception as e:
            print(f"  ⚠️ Failed to ingest {section}: {e}")

    # ----------- EMBEDDINGS ----------- #
    if not all_chunk_texts:
        print("❌ No chunks to embed. Check your data sources.")
        return

    embeddings = embedder.embed(all_chunk_texts)

    for chunk, embedding in zip(all_chunks, embeddings):
        chunk["embedding"] = embedding

    CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Ingestion complete")
    print(f"📄 Total chunks stored: {len(all_chunks)}")
    print(f"📁 Extracted text saved in: data/extracted_text/")
    print(f"📁 Normalized text saved in: data/normalized_text/")
    print(f"📦 Chunks + embeddings saved in: {CHUNKS_FILE}")


if __name__ == "__main__":
    main()
