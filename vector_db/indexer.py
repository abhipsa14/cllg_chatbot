import json
from pathlib import Path

from vector_db.chroma_client import get_chroma_client

CHUNKS_FILE = Path("data/processed_chunks/unified_chunks.json")
COLLECTION_NAME = "college_knowledge"

def index_chunks():
    client = get_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        documents.append(chunk["text"])
        embeddings.append(chunk["embedding"])
        metadatas.append({
            "source_type": chunk["source_type"],
            "source": chunk["source"]
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"✅ Indexed {len(ids)} chunks into ChromaDB")

if __name__ == "__main__":
    index_chunks()
