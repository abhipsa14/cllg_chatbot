"""
Speech-to-Text module — captures microphone audio and transcribes to text.
Uses Google Speech Recognition (online) with Vosk as offline fallback.
Compatible with Raspberry Pi 4 (USB/I2S microphone via ALSA).
"""

import speech_recognition as sr
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import IS_PI, MIC_ENERGY_THRESHOLD, MIC_PAUSE_THRESHOLD

logger = logging.getLogger("voice_assistant.stt")


class SpeechToText:
    """Microphone-based speech-to-text engine."""

    def __init__(self, energy_threshold: int = None, pause_threshold: float = None):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold or MIC_ENERGY_THRESHOLD
        self.recognizer.pause_threshold = pause_threshold or MIC_PAUSE_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True

        # On Pi, select the correct ALSA device index if needed
        device_index = self._find_microphone()
        self.mic = sr.Microphone(device_index=device_index)

        # Calibrate for ambient noise once at start
        logger.info("Calibrating microphone for ambient noise...")
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0 if IS_PI else 1.5)
            logger.info(f"Energy threshold set to {self.recognizer.energy_threshold}")
        except Exception as e:
            logger.warning(f"Mic calibration failed: {e}. Using defaults.")

    def _find_microphone(self) -> int | None:
        """Auto-detect the best microphone, especially on Pi."""
        if not IS_PI:
            return None  # Use system default

        try:
            mic_names = sr.Microphone.list_microphone_names()
            logger.info(f"Available microphones: {mic_names}")

            # Prefer USB mic on Pi (common names)
            preferred = ["usb", "seeed", "respeaker", "plugable", "blue", "samson"]
            for i, name in enumerate(mic_names):
                for pref in preferred:
                    if pref in name.lower():
                        logger.info(f"Selected microphone [{i}]: {name}")
                        return i

            # Fallback: pick first non-default device
            for i, name in enumerate(mic_names):
                if "default" not in name.lower() and "hdmi" not in name.lower():
                    logger.info(f"Selected microphone [{i}]: {name}")
                    return i

        except Exception as e:
            logger.warning(f"Mic detection failed: {e}")

        return None  # Use system default

    def listen(self, timeout: float = 8.0, phrase_time_limit: float = 15.0) -> str | None:
        """
        Listen to microphone and return transcribed text.
        
        Args:
            timeout: Max seconds to wait for speech to begin.
            phrase_time_limit: Max seconds of speech to capture.
        
        Returns:
            Transcribed text string, or None if nothing was understood.
        """
        try:
            with self.mic as source:
                logger.info("🎤 Listening...")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            logger.info("Processing speech...")
            # Primary: Google Speech Recognition (free, online)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text.strip()

        except sr.WaitTimeoutError:
            logger.debug("No speech detected within timeout.")
            return None
        except sr.UnknownValueError:
            logger.debug("Speech was unintelligible.")
            return None
        except sr.RequestError as e:
            logger.warning(f"Google STT unavailable: {e}. Trying offline...")
            return self._offline_recognize(audio)
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None

    def _offline_recognize(self, audio) -> str | None:
        """Fallback to Vosk offline recognition if available."""
        try:
            text = self.recognizer.recognize_vosk(audio)
            import json
            result = json.loads(text)
            return result.get("text", "").strip() or None
        except Exception:
            logger.warning("Offline STT also failed.")
            return None

    def listen_for_wake_word(self, wake_words: list[str], timeout: float = None) -> bool:
        """
        Continuously listen for a wake word.
        
        Args:
            wake_words: List of phrases that trigger activation.
            timeout: Max seconds to listen (None = indefinitely via loop).
        
        Returns:
            True if a wake word was detected.
        """
        try:
            with self.mic as source:
                audio = self.recognizer.listen(
                    source, timeout=timeout or 3, phrase_time_limit=4
                )

            text = self.recognizer.recognize_google(audio).lower().strip()
            logger.debug(f"Heard: '{text}'")

            for word in wake_words:
                if word.lower() in text:
                    logger.info(f"🔔 Wake word detected: '{word}' in '{text}'")
                    return True

            return False

        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return False
        except sr.RequestError:
            # If online recognition fails, skip this cycle
            return False
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            return False
