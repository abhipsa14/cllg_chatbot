"""
Hybrid RAG + Ollama Pipeline — routes queries intelligently:
  1. First searches the UIT knowledge base (ChromaDB) for relevant context.
  2. If the context is highly relevant → answer using Ollama with RAG context.
  3. If context is weak or irrelevant → answer using Ollama's general knowledge.
  
This gives the best of both worlds: accurate college-specific answers AND
versatile general-purpose AI capabilities via a local LLM.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vector_db.retriever import Retriever
from llm.ollama_client import call_ollama, call_ollama_with_context, call_ollama_general
from config import TOP_K, RELEVANCE_THRESHOLD

logger = logging.getLogger("voice_assistant.pipeline")


class HybridPipeline:
    """
    Intelligent query router that combines RAG with local Ollama LLM.
    """

    def __init__(self):
        try:
            self.retriever = Retriever()
            self._rag_available = True
            logger.info("RAG retriever initialized successfully.")
        except Exception as e:
            logger.warning(f"RAG retriever unavailable: {e}. Using Ollama-only mode.")
            self.retriever = None
            self._rag_available = False

    def answer(self, question: str) -> str:
        """
        Process a question through the hybrid pipeline.
        
        Flow:
        1. Check if it's a system command (time, date, etc.)
        2. Search RAG knowledge base
        3. If relevant context found → use Ollama + context
        4. If no relevant context → use Ollama general knowledge
        """
        question = question.strip()
        if not question:
            return "I didn't catch that. Could you repeat?"

        # Handle system commands
        system_response = self._handle_system_commands(question)
        if system_response:
            return system_response

        # Try RAG first
        if self._rag_available:
            try:
                contexts = self.retriever.retrieve(question, top_k=TOP_K)

                if contexts and self._is_relevant(contexts):
                    context_text = "\n\n".join(
                        f"[Source: {c['source']}]\n{c['text']}" for c in contexts
                    )
                    logger.info(f"📚 Using RAG context ({len(contexts)} chunks)")
                    return call_ollama_with_context(question, context_text)
                else:
                    logger.info("🌐 No relevant RAG context — using Ollama general knowledge")
                    return call_ollama_general(question)

            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")
                return call_ollama_general(question)
        else:
            return call_ollama_general(question)

    def _is_relevant(self, contexts: list[dict]) -> bool:
        """
        Heuristic check: determine if retrieved contexts are actually relevant.
        Uses keyword overlap and distance scoring.
        """
        if not contexts:
            return False

        # If we have at least one context with substantial text, consider it relevant
        for ctx in contexts:
            text = ctx.get("text", "")
            if len(text.split()) > 20:  # At least 20 words
                return True

        return False

    def _handle_system_commands(self, question: str) -> str | None:
        """Handle simple system/utility questions directly."""
        q = question.lower()

        if any(w in q for w in ["what time", "current time", "tell me the time"]):
            from datetime import datetime
            now = datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}."

        if any(w in q for w in ["what date", "today's date", "what day"]):
            from datetime import datetime
            now = datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {now}."

        if any(w in q for w in ["stop listening", "go to sleep", "goodbye", "bye"]):
            return "__EXIT__"

        return None


# Singleton instance
_pipeline = None


def get_pipeline() -> HybridPipeline:
    """Get or create the singleton pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = HybridPipeline()
    return _pipeline


def answer_question(question: str) -> str:
    """Convenience function for answering a question."""
    return get_pipeline().answer(question)


if __name__ == "__main__":
    # Quick interactive test
    pipeline = HybridPipeline()
    print("🤖 Hybrid Pipeline Test (type 'exit' to quit)\n")
    while True:
        q = input("You: ").strip()
        if q.lower() == "exit":
            break
        answer = pipeline.answer(q)
        print(f"\nAssistant: {answer}\n")
