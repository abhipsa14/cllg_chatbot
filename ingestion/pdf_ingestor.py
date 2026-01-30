from pathlib import Path
from pypdf import PdfReader

def ingest_pdf(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)
