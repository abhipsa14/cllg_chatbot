#!/bin/bash
# ═══════════════════════════════════════════════
#  Audio Test for Raspberry Pi 4
#  Tests microphone and speaker before running the assistant
# ═══════════════════════════════════════════════

echo "╔══════════════════════════════════════════╗"
echo "║     🔊 Audio Test — Raspberry Pi 4       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. List audio devices
echo "── Playback Devices ──"
aplay -l 2>/dev/null || echo "  (none found)"
echo ""

echo "── Recording Devices ──"
arecord -l 2>/dev/null || echo "  (none found — plug in a USB microphone)"
echo ""

# 2. Test speaker
echo "── Testing Speaker ──"
echo "  Playing a test tone on the headphone jack..."
speaker-test -t sine -f 440 -l 1 -D default -p 2   2>/dev/null &
SPEAKER_PID=$!
sleep 2
kill $SPEAKER_PID 2>/dev/null
echo "  Did you hear a tone? If not:"
echo "    1. Check your speaker/headphone is plugged into the 3.5mm jack"
echo "    2. Run: sudo raspi-config → System → Audio → Headphones"
echo "    3. Run: amixer set Master 80%"
echo ""

# 3. Test microphone
echo "── Testing Microphone ──"
echo "  Recording 3 seconds of audio..."
TEMP_WAV="/tmp/pitest_audio.wav"
arecord -d 3 -f cd -r 16000 -c 1 "${TEMP_WAV}" 2>/dev/null

if [ -f "${TEMP_WAV}" ]; then
    echo "  Playing back recording..."
    aplay "${TEMP_WAV}" 2>/dev/null
    rm -f "${TEMP_WAV}"
    echo "  If you heard your voice, the microphone is working!"
else
    echo "  ❌ Recording failed. Check:"
    echo "    1. USB microphone is plugged in"
    echo "    2. Run: arecord -l (to see available capture devices)"
    echo "    3. Update ~/.asoundrc with the correct card number"
fi

echo ""
echo "── Volume Controls ──"
echo "  Set speaker volume:  amixer set Master 80%"
echo "  Set mic volume:      amixer set Capture 80%"
echo "  GUI mixer:           alsamixer"
echo ""
echo "Done!"
