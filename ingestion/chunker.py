def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80
) -> list[str]:

    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        start = end - overlap

    return chunks
