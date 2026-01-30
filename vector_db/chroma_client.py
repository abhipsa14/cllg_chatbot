import chromadb

def get_chroma_client(persist_dir="vector_db/chroma_db"):
    return chromadb.PersistentClient(path=persist_dir)
