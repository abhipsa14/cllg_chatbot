"""
Wake Word Detector — Continuously listens for a trigger phrase to activate 
the voice assistant, similar to "Hey Google" or "Alexa".

Uses speech_recognition for phrase-based wake word detection.
Falls back to a simple always-listening loop.
"""

import threading
import time
import logging

from voice.speech_to_text import SpeechToText

logger = logging.getLogger("voice_assistant.wake_word")


class WakeWordDetector:
    """
    Continuously listens for a wake word/phrase via microphone.
    When detected, triggers a callback function.
    """

    def __init__(
        self,
        wake_words: list[str],
        on_wake: callable,
        stt: SpeechToText = None,
    ):
        """
        Args:
            wake_words: List of trigger phrases (e.g. ["hey assistant", "ok computer"]).
            on_wake: Callback function to invoke when a wake word is detected.
            stt: Optional shared SpeechToText instance.
        """
        self.wake_words = [w.lower().strip() for w in wake_words]
        self.on_wake = on_wake
        self.stt = stt or SpeechToText()
        self._running = False
        self._thread = None
        self._paused = False

    def start(self):
        """Start listening for wake words in a background thread."""
        if self._running:
            logger.warning("Wake word detector is already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"🟢 Wake word detector started. Listening for: {self.wake_words}")

    def stop(self):
        """Stop the wake word detector."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🔴 Wake word detector stopped.")

    def pause(self):
        """Pause detection (e.g., while processing a command)."""
        self._paused = True

    def resume(self):
        """Resume detection after pause."""
        self._paused = False

    def _listen_loop(self):
        """Main loop that continuously checks for wake words."""
        while self._running:
            if self._paused:
                time.sleep(0.3)
                continue

            try:
                detected = self.stt.listen_for_wake_word(self.wake_words, timeout=3)
                if detected and self._running and not self._paused:
                    logger.info("🔔 Wake word detected! Activating assistant...")
                    self._paused = True  # Pause during command processing
                    try:
                        self.on_wake()
                    except Exception as e:
                        logger.error(f"Error in wake callback: {e}")
                    finally:
                        self._paused = False  # Resume listening
            except Exception as e:
                logger.error(f"Wake word loop error: {e}")
                time.sleep(1)  # Brief pause before retrying

    @property
    def is_running(self) -> bool:
        return self._running
