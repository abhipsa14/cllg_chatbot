"""
Main entry point for the UIT Voice Assistant.

Usage:
    python main.py              → System tray mode (Windows) / Voice mode (Pi)
    python main.py --console    → Console/text mode (for testing)
    python main.py --voice      → Voice-only mode (no tray, direct mic)
    python main.py --daemon     → Daemon mode (for systemd service on Pi)
    python main.py --ingest     → Re-ingest data into knowledge base
"""

import sys
import signal
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import IS_PI, PI_MODEL


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(PROJECT_ROOT / "assistant.log", encoding="utf-8"),
        ],
    )


def run_ingest():
    """Run the data ingestion pipeline to process UIT Data Set.docx and other sources."""
    print("📥 Starting data ingestion pipeline...")
    print("=" * 50)

    from ingestion.run_ingestion import main as ingest_main
    ingest_main()

    # Also run the indexer to load into ChromaDB
    print("\n📊 Indexing chunks into ChromaDB...")
    from vector_db.indexer import index_chunks
    index_chunks()

    print("\n✅ Ingestion and indexing complete!")


def run_console():
    """Run in console/text mode."""
    from assistant import VoiceAssistant
    va = VoiceAssistant()
    va.run_console()


def run_voice():
    """Run in voice-only mode (no system tray)."""
    from assistant import VoiceAssistant
    va = VoiceAssistant()

    def signal_handler(sig, frame):
        va.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        va.start()
        # Keep the main thread alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        va.stop()
        print("\nAssistant stopped.")


def run_daemon():
    """Run as a headless daemon (for systemd on Pi). No console I/O."""
    import logging
    logger = logging.getLogger("voice_assistant")
    logger.info("Starting in daemon mode (headless, no console)...")

    from assistant import VoiceAssistant
    va = VoiceAssistant()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        va.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        va.start()
        import time
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        va.stop()
        sys.exit(1)


def run_tray():
    """Run as a system tray application."""
    from tray_app import run_tray_app
    run_tray_app()


def main():
    parser = argparse.ArgumentParser(
        description="UIT Voice Assistant — AI-powered voice assistant with custom knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Start as system tray app (Windows) or voice mode (Pi)
  python main.py --voice      Start in voice-only mode
  python main.py --daemon     Start as headless daemon (for systemd on Pi)
  python main.py --console    Start in text/console mode
  python main.py --ingest     Re-process and index data
  python main.py --ingest --console  Ingest data, then start console
        """,
    )

    parser.add_argument(
        "--console", action="store_true",
        help="Run in console/text mode (type instead of speak)"
    )
    parser.add_argument(
        "--voice", action="store_true",
        help="Run in voice-only mode (no system tray)"
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run as headless daemon (for systemd service on Pi)"
    )
    parser.add_argument(
        "--ingest", action="store_true",
        help="Run data ingestion pipeline before starting"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose/debug logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    print(r"""
    ╔══════════════════════════════════════════════╗
    ║        🎓 UIT Voice Assistant v1.0           ║
    ║    AI-Powered College Information System     ║
    ║        Powered by Ollama + RAG                ║
    ╚══════════════════════════════════════════════╝
    """)

    if IS_PI:
        print(f"    🍓 Running on: {PI_MODEL}")
        print()

    # Run ingestion if requested
    if args.ingest:
        run_ingest()
        print()

    # Start the assistant in the chosen mode
    if args.console:
        run_console()
    elif args.daemon:
        run_daemon()
    elif args.voice or IS_PI:
        # Default to voice mode on Pi (no GUI/tray available)
        run_voice()
    else:
        run_tray()


if __name__ == "__main__":
    main()
