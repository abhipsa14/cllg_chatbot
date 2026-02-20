#!/bin/bash
# ═══════════════════════════════════════════════════
#  UIT Voice Assistant — Raspberry Pi 4 Full Setup
#  Run as: chmod +x pi/install_pi.sh && sudo ./pi/install_pi.sh
# ═══════════════════════════════════════════════════

set -e

INSTALL_DIR="/home/pi/cllg_chatbot"
VENV_DIR="${INSTALL_DIR}/venv"
SERVICE_USER="pi"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    🎓 UIT Voice Assistant — Pi4 Setup        ║"
echo "║    Installing all dependencies & services    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─────────── 1. SYSTEM PACKAGES ─────────── #
echo "[1/8] Installing system packages..."
apt-get update -qq
apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    python3-pyaudio \
    portaudio19-dev \
    espeak espeak-data libespeak-dev \
    ffmpeg \
    libasound2-dev \
    alsa-utils pulseaudio \
    curl wget git \
    build-essential libffi-dev libssl-dev

echo "  ✅ System packages installed."

# ─────────── 2. ALSA AUDIO CONFIG ─────────── #
echo ""
echo "[2/8] Configuring audio (ALSA)..."

# Set up ALSA config for USB mic + headphone jack
if [ ! -f /home/pi/.asoundrc ]; then
    cp "${INSTALL_DIR}/pi/asoundrc" /home/pi/.asoundrc
    chown ${SERVICE_USER}:${SERVICE_USER} /home/pi/.asoundrc
    echo "  ✅ ALSA config created at ~/.asoundrc"
else
    echo "  ⏭️  ~/.asoundrc already exists, skipping."
fi

# Add user to audio group
usermod -aG audio ${SERVICE_USER} 2>/dev/null || true

echo "  ✅ Audio configured."

# ─────────── 3. INSTALL OLLAMA ─────────── #
echo ""
echo "[3/8] Installing Ollama..."

if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "  ✅ Ollama installed."
else
    echo "  ⏭️  Ollama already installed."
fi

# ─────────── 4. PULL LLM MODEL ─────────── #
echo ""
echo "[4/8] Pulling llama3.2 model (this may take a while)..."
sudo -u ${SERVICE_USER} ollama pull llama3.2
echo "  ✅ Model ready."

# ─────────── 5. PYTHON VENV & DEPS ─────────── #
echo ""
echo "[5/8] Setting up Python virtual environment..."

if [ ! -d "${VENV_DIR}" ]; then
    sudo -u ${SERVICE_USER} python3 -m venv "${VENV_DIR}"
fi

# Install Pi-compatible requirements
sudo -u ${SERVICE_USER} "${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel
sudo -u ${SERVICE_USER} "${VENV_DIR}/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu
sudo -u ${SERVICE_USER} "${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements_pi.txt"

echo "  ✅ Python dependencies installed."

# ─────────── 6. INGEST KNOWLEDGE BASE ─────────── #
echo ""
echo "[6/8] Ingesting UIT Data Set into knowledge base..."
cd "${INSTALL_DIR}"
sudo -u ${SERVICE_USER} "${VENV_DIR}/bin/python" main.py --ingest
echo "  ✅ Knowledge base ready."

# ─────────── 7. INSTALL SYSTEMD SERVICES ─────────── #
echo ""
echo "[7/8] Installing systemd services..."

# Ollama service
cp "${INSTALL_DIR}/pi/ollama.service" /etc/systemd/system/ollama.service
systemctl daemon-reload
systemctl enable ollama.service
systemctl start ollama.service
echo "  ✅ Ollama service enabled (auto-start on boot)."

# Wait a moment for Ollama to start
sleep 3

# UIT Assistant service
cp "${INSTALL_DIR}/pi/uit-assistant.service" /etc/systemd/system/uit-assistant.service
systemctl daemon-reload
systemctl enable uit-assistant.service
systemctl start uit-assistant.service
echo "  ✅ UIT Assistant service enabled (auto-start on boot)."

# ─────────── 8. VERIFY ─────────── #
echo ""
echo "[8/8] Verifying installation..."
echo ""

echo "  Ollama status:"
systemctl is-active ollama.service && echo "    ✅ Running" || echo "    ❌ Not running"

echo "  UIT Assistant status:"
systemctl is-active uit-assistant.service && echo "    ✅ Running" || echo "    ❌ Not running"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🎉 Installation complete!"
echo ""
echo "  The voice assistant is now running as a service."
echo "  It will auto-start on every boot."
echo "  Say 'Hey Assistant' to activate it!"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status uit-assistant  # check status"
echo "    sudo systemctl restart uit-assistant # restart"
echo "    sudo systemctl stop uit-assistant    # stop"
echo "    journalctl -u uit-assistant -f       # view logs"
echo "═══════════════════════════════════════════════════"
