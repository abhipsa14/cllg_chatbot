from vector_db.chroma_client import get_chroma_client
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "college_knowledge"

class Retriever:
    def __init__(self, embed_model="all-MiniLM-L6-v2"):
        self.client = get_chroma_client()
        self.collection = self.client.get_collection(COLLECTION_NAME)
        self.embedder = SentenceTransformer(embed_model)

    def retrieve(self, query: str, top_k: int = 4) -> list[dict]:
        query_embedding = self.embedder.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        contexts = []
        for doc, meta in zip(
            results["documents"][0],
            results["metadatas"][0]
        ):
            contexts.append({
                "text": doc,
                "source_type": meta["source_type"],
                "source": meta["source"]
            })

        return contexts
