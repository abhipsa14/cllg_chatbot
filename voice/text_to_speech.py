"""
Text-to-Speech module — converts text responses to spoken audio.
Uses pyttsx3 for fully offline, cross-platform TTS.
On Raspberry Pi, uses the espeak backend.
"""

import pyttsx3
import threading
import logging
import queue
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import IS_PI, IS_LINUX, TTS_ENGINE

logger = logging.getLogger("voice_assistant.tts")


class TextToSpeech:
    """Offline text-to-speech engine using pyttsx3 (espeak on Pi)."""

    def __init__(self, rate: int = 175, volume: float = 0.9, voice_index: int = None):
        """
        Initialize the TTS engine.
        
        Args:
            rate: Words per minute.
            volume: Volume level 0.0 to 1.0.
            voice_index: Index of the voice to use (None = default).
        """
        # On Linux/Pi, use espeak driver explicitly
        if IS_LINUX:
            self.engine = pyttsx3.init(driverName="espeak")
        else:
            self.engine = pyttsx3.init()

        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)

        # Select a voice
        voices = self.engine.getProperty("voices")
        if voice_index is not None and voice_index < len(voices):
            self.engine.setProperty("voice", voices[voice_index].id)
        elif IS_PI:
            # On Pi, pick the default English voice (espeak)
            for v in voices:
                if "english" in v.name.lower() or "en" in v.id.lower():
                    self.engine.setProperty("voice", v.id)
                    break
        elif len(voices) > 1:
            # Try to pick a female/clearer voice (usually index 1 on Windows)
            self.engine.setProperty("voice", voices[1].id)

        self._speech_queue = queue.Queue()
        self._is_speaking = False
        self._stop_flag = False

        logger.info(f"TTS initialized — rate={rate}, volume={volume}")
        for i, v in enumerate(voices):
            logger.debug(f"  Voice {i}: {v.name} ({v.id})")

    def speak(self, text: str, block: bool = True):
        """
        Speak the given text.
        
        Args:
            text: The text to speak.
            block: If True, wait until speech is done. If False, run in background.
        """
        if not text or not text.strip():
            return

        # Clean text for speech
        clean_text = self._clean_for_speech(text)
        logger.info(f"🔊 Speaking: {clean_text[:80]}...")

        if block:
            self._speak_sync(clean_text)
        else:
            thread = threading.Thread(target=self._speak_sync, args=(clean_text,), daemon=True)
            thread.start()

    def _speak_sync(self, text: str):
        """Synchronously speak text."""
        self._is_speaking = True
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self._is_speaking = False

    def stop(self):
        """Stop any ongoing speech."""
        self._stop_flag = True
        try:
            self.engine.stop()
        except Exception:
            pass
        self._is_speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Clean text to be more natural when spoken."""
        import re
        # Remove markdown-style formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)       # italic
        text = re.sub(r'`(.*?)`', r'\1', text)          # code
        text = re.sub(r'#{1,6}\s*', '', text)            # headers
        # Remove bullet points
        text = re.sub(r'^[\-\*•]\s*', '', text, flags=re.MULTILINE)
        # Remove numbered list markers
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove emojis (basic)
        text = re.sub(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
            r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
            r'\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
            r'\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F]+',
            '', text
        )
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
