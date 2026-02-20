"""
UIT Voice Assistant — Main application that ties everything together.

Runs as a system-tray application with wake-word activation.
Listens for "Hey Assistant" (or configured keywords), then:
  1. Captures voice query via microphone
  2. Routes through Hybrid RAG + Ollama pipeline
  3. Speaks the answer via TTS
  4. Returns to listening for the wake word

Can also run in console mode for debugging.
"""

import sys
import os
import time
import threading
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import WAKE_WORDS, TTS_RATE, TTS_VOLUME
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech
from voice.wake_word import WakeWordDetector
from rag.hybrid_pipeline import HybridPipeline

# ──────────────── LOGGING ──────────────── #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "assistant.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("voice_assistant")


class VoiceAssistant:
    """
    The core voice assistant that orchestrates:
    - Wake word detection
    - Speech-to-text
    - Query processing (RAG + Ollama)
    - Text-to-speech response
    """

    def __init__(self):
        logger.info("═" * 50)
        logger.info("  UIT Voice Assistant — Initializing...")
        logger.info("═" * 50)

        # Initialize components
        logger.info("Loading Speech-to-Text engine...")
        self.stt = SpeechToText()

        logger.info("Loading Text-to-Speech engine...")
        self.tts = TextToSpeech(rate=TTS_RATE, volume=TTS_VOLUME)

        logger.info("Loading AI Pipeline (RAG + Ollama)...")
        self.pipeline = HybridPipeline()

        logger.info("Setting up Wake Word Detector...")
        self.wake_detector = WakeWordDetector(
            wake_words=WAKE_WORDS,
            on_wake=self._on_wake_word,
            stt=self.stt,
        )

        self._running = False
        self._active_session = False
        logger.info("✅ All components initialized successfully!")

    def start(self):
        """Start the voice assistant (begins listening for wake word)."""
        if self._running:
            return

        self._running = True
        self.tts.speak("UIT Voice Assistant is ready. Say 'Hey Assistant' to begin.", block=True)
        self.wake_detector.start()

        logger.info("🟢 Assistant is live and listening for wake words.")
        print("\n" + "=" * 50)
        print("  🎙️  UIT Voice Assistant is ACTIVE")
        print(f"  Wake words: {', '.join(WAKE_WORDS)}")
        print("  Press Ctrl+C to stop")
        print("=" * 50 + "\n")

    def stop(self):
        """Stop the voice assistant."""
        self._running = False
        self.wake_detector.stop()
        self.tts.speak("Goodbye! Voice assistant shutting down.")
        logger.info("🔴 Assistant stopped.")

    def _on_wake_word(self):
        """Called when a wake word is detected."""
        if self._active_session:
            return

        self._active_session = True
        try:
            # Play acknowledgment
            self.tts.speak("Yes, I'm listening.", block=True)

            # Enter conversation loop
            self._conversation_loop()

        except Exception as e:
            logger.error(f"Session error: {e}")
            self.tts.speak("Sorry, something went wrong. Please try again.")
        finally:
            self._active_session = False

    def _conversation_loop(self):
        """
        Active conversation: keep listening for follow-up questions
        until user says goodbye or silence timeout.
        """
        consecutive_silence = 0
        max_silence = 2  # Exit after 2 consecutive silence timeouts

        while self._running and consecutive_silence < max_silence:
            # Listen for user's question
            print("🎤 Listening for your question...")
            user_text = self.stt.listen(timeout=8, phrase_time_limit=20)

            if user_text is None:
                consecutive_silence += 1
                if consecutive_silence < max_silence:
                    self.tts.speak("I didn't hear anything. I'm still listening.")
                continue

            consecutive_silence = 0  # Reset silence counter
            print(f"\n👤 You: {user_text}")

            # Process the question
            logger.info(f"Processing: {user_text}")
            print("🤔 Thinking...")

            response = self.pipeline.answer(user_text)

            # Check for exit command
            if response == "__EXIT__":
                self.tts.speak("Okay, going back to sleep. Say the wake word when you need me.")
                return

            print(f"🤖 Assistant: {response}\n")

            # Speak the response
            self.tts.speak(response, block=True)

        if consecutive_silence >= max_silence:
            self.tts.speak("I'll go back to listening for the wake word.")

    def run_console(self):
        """
        Run in console mode (type instead of speak) for testing.
        """
        print("\n" + "=" * 50)
        print("  🖥️  UIT Assistant — Console Mode")
        print("  Type your questions (type 'exit' to quit)")
        print("=" * 50 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "bye"):
                    print("Goodbye!")
                    break

                response = self.pipeline.answer(user_input)
                if response == "__EXIT__":
                    print("Goodbye!")
                    break

                print(f"\nAssistant: {response}\n")

                # Optionally speak
                self.tts.speak(response, block=True)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                break
