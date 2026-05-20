#!/bin/bash
# One-shot install for Chatterbox TTS on a fresh RunPod pod.
# Run this once after the pod boots; after that just run generate.py.
set -e

echo "[1/5] System packages..."
apt-get update -qq || true   # tolerate transient mirror failures
apt-get install -y -qq ffmpeg

echo "[2/5] Python deps..."
pip install --quiet --upgrade pip
pip install --quiet chatterbox-tts

echo "[3/5] Pinning torch/torchvision/torchaudio to a matching cu124 trio..."
# chatterbox-tts pulls torch but leaves torchvision out of sync, which breaks
# transformers' Llama import. Force the matched cu124 trio explicitly.
pip install --quiet --force-reinstall --no-deps \
  torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 \
  --index-url https://download.pytorch.org/whl/cu124

echo "[4/5] Pre-download model weights (one-time, ~2 GB)..."
python - <<'PY'
from chatterbox.tts import ChatterboxTTS
print("Loading model to warm cache...")
ChatterboxTTS.from_pretrained(device="cuda")
print("Model cached.")
PY

echo "[5/5] Done. Try:"
echo "  python generate.py sample.txt --reference paul-heygen-31s.wav --output sample.mp3"
