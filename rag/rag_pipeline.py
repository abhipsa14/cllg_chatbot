from vector_db.retriever import Retriever
import subprocess

retriever = Retriever()

PROMPT_TEMPLATE = """
You are a college regulation assistant.

Answer ONLY using the context below.
If the answer is not found, say:
"Not mentioned in official college sources."

Context:
{context}

Question:
{question}

Answer in plain text.
"""

def ask_llm(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "smollm2"],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout.strip()

def answer_question(question: str) -> str:
    contexts = retriever.retrieve(question)

    context_text = "\n\n".join(
        f"- {c['text']}" for c in contexts
    )

    prompt = PROMPT_TEMPLATE.format(
        context=context_text,
        question=question
    )

    return ask_llm(prompt)
