@echo off
title UIT Assistant - Setup
echo.
echo ╔══════════════════════════════════════════════╗
echo ║           Setup - UIT Voice Assistant        ║
echo ╚══════════════════════════════════════════════╝
echo.

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
echo.

echo [2/4] Installing PyAudio (Windows)...
pip install PyAudio
if errorlevel 1 (
    echo     PyAudio pip install failed. Trying pipwin...
    pip install pipwin
    pipwin install pyaudio
)
echo.

echo [3/4] Checking Ollama is installed...
where ollama >nul 2>&1
if errorlevel 1 (
    echo     Ollama not found. Please install from https://ollama.com
) else (
    echo     Ollama found. Pulling llama3.2 model...
    ollama pull llama3.2
)
echo.

echo [4/4] Ingesting knowledge base...
python main.py --ingest
echo.

echo ══════════════════════════════════════════════
echo  Setup complete! Run 'start_assistant.bat' to launch.
echo ══════════════════════════════════════════════
pause
