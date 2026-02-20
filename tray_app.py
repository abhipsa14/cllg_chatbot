"""
System Tray Application — Runs the UIT Voice Assistant as a background
system service with a tray icon (like Google Assistant / Cortana).

Features:
  - Sits in the system tray with a microphone icon
  - Right-click menu: Start/Stop listening, Console mode, Quit
  - Left-click: Toggle listening on/off
  - Runs wake word detection in the background
"""

import sys
import os
import threading
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("voice_assistant.tray")


def create_icon_image():
    """Create a simple microphone icon for the system tray."""
    try:
        from PIL import Image, ImageDraw
        # Create a 64x64 icon with a microphone shape
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        draw.ellipse([4, 4, 60, 60], fill=(33, 150, 243, 255))

        # Microphone body
        draw.rounded_rectangle([24, 12, 40, 36], radius=8, fill="white")

        # Microphone stand
        draw.arc([20, 24, 44, 48], start=0, end=180, fill="white", width=3)
        draw.line([32, 48, 32, 54], fill="white", width=3)
        draw.line([24, 54, 40, 54], fill="white", width=3)

        return img
    except ImportError:
        # Fallback: create a minimal valid icon
        from PIL import Image
        img = Image.new("RGB", (64, 64), (33, 150, 243))
        return img


def run_tray_app():
    """Launch the system tray application."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        print("❌ System tray requires 'pystray' and 'Pillow'. Install them:")
        print("   pip install pystray Pillow")
        print("\nFalling back to console mode...")
        _run_console_fallback()
        return

    from assistant import VoiceAssistant

    assistant = VoiceAssistant()
    is_listening = False

    def on_start_listening(icon, item):
        nonlocal is_listening
        if not is_listening:
            is_listening = True
            assistant.start()
            icon.title = "UIT Assistant — Listening 🎤"
            icon.notify("Voice Assistant is now listening!", "UIT Assistant")

    def on_stop_listening(icon, item):
        nonlocal is_listening
        if is_listening:
            is_listening = False
            assistant.stop()
            icon.title = "UIT Assistant — Paused"
            icon.notify("Voice Assistant paused.", "UIT Assistant")

    def on_console_mode(icon, item):
        """Open console mode in a separate thread."""
        thread = threading.Thread(target=assistant.run_console, daemon=True)
        thread.start()

    def on_quit(icon, item):
        nonlocal is_listening
        if is_listening:
            assistant.stop()
        icon.stop()

    def on_activate(icon, item):
        """Default action (left click) — toggle listening."""
        nonlocal is_listening
        if is_listening:
            on_stop_listening(icon, item)
        else:
            on_start_listening(icon, item)

    # Build menu
    menu = pystray.Menu(
        pystray.MenuItem("Start Listening", on_start_listening, default=True),
        pystray.MenuItem("Stop Listening", on_stop_listening),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Console Mode", on_console_mode),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon(
        name="UIT Assistant",
        icon=create_icon_image(),
        title="UIT Voice Assistant — Click to start",
        menu=menu,
    )

    print("✅ UIT Voice Assistant is running in the system tray.")
    print("   Right-click the tray icon for options.")
    print("   Left-click to toggle listening on/off.")

    # Auto-start listening
    def auto_start():
        import time
        time.sleep(2)
        on_start_listening(icon, None)

    threading.Thread(target=auto_start, daemon=True).start()

    icon.run()


def _run_console_fallback():
    """Fallback when tray dependencies aren't available."""
    from assistant import VoiceAssistant
    va = VoiceAssistant()
    va.run_console()


if __name__ == "__main__":
    run_tray_app()
