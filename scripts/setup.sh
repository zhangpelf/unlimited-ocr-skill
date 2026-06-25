#!/usr/bin/env bash
# ------------------------------------------------------------------
# unlimited-ocr-skill — one-shot environment setup (CUDA)
# Creates a dedicated venv and installs dependencies.
# Run ONCE before first use.
# ------------------------------------------------------------------
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
PYTHON="${PYTHON:-python3}"

echo "==> Creating venv at $VENV_DIR"
"$PYTHON" -m venv "$VENV_DIR"

echo "==> Installing dependencies (torch + transformers + pymupdf …)"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install \
    torch>=2.10.0 \
    torchvision>=0.25.0 \
    transformers>=4.57.0 \
    Pillow>=12.0.0 \
    einops>=0.8.0 \
    pymupdf>=1.27.0 \
    requests>=2.32.0

echo "==> Done."
echo ""
echo "Usage:  $VENV_DIR/bin/python \"$SKILL_DIR/scripts/ocr.py\" --help"
