from pathlib import Path
from pypdf import PdfReader

def ingest_pdf(pdf_path: Path) -> str:
    """Ingest PDF files only"""
    reader = PdfReader(pdf_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)

def ingest_text(file_path: Path) -> str:
    """Ingest plain text files"""
    return file_path.read_text(encoding="utf-8")

def ingest_file(file_path: Path) -> str:
    """Ingest file based on extension"""
    ext = file_path.suffix.lower()
    
    if ext == ".pdf":
        return ingest_pdf(file_path)
    elif ext == ".txt":
        return ingest_text(file_path)
    elif ext in [".docx", ".doc"]:
        # For docx, you'd need python-docx package
        # For now, skip or handle as needed
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            print(f"Skipping {file_path.name}: python-docx not installed")
            return ""
    else:
        return ""
