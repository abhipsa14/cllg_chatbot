from vector_db.retriever import Retriever
from rag.prompt_builder import build_prompt
from llm.ollama_client import call_ollama

retriever = Retriever()

def chat(question: str) -> str:
    contexts = retriever.retrieve(question, top_k=4)

    context_text = "\n\n".join(
        f"- {c['text']}" for c in contexts
    )

    prompt = build_prompt(context_text, question)
    return call_ollama(prompt)
