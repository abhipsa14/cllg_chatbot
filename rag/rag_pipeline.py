from vector_db.retriever import Retriever
from llm.ollama_client import call_ollama

retriever = Retriever()

PROMPT_TEMPLATE = """You are a helpful college information assistant for UIT (University Institute of Technology).

INSTRUCTIONS:
1. Answer the question ONLY using the provided context below.
2. If the answer is not in the context, respond: "I couldn't find this information in the official college sources."
3. Be concise, accurate, and helpful.
4. Format your answer clearly with proper structure.

CONTEXT FROM OFFICIAL SOURCES:
---
{context}
---

QUESTION: {question}

ANSWER:"""

def answer_question(question: str) -> str:
    contexts = retriever.retrieve(question, top_k=5)

    context_text = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in contexts
    )

    prompt = PROMPT_TEMPLATE.format(
        context=context_text,
        question=question
    )

    return call_ollama(prompt)
