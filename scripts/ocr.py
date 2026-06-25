#!/usr/bin/env python3
"""
Unlimited-OCR — one-shot document parsing CLI (CUDA-only)

Two modes:
  1) Local  — NVIDIA GPU + CUDA (bf16, ~6GB VRAM)
  2) Remote — SGLang server (any machine with a GPU)

Usage:
  # Local GPU inference
  python ocr.py image.jpg -o output.md
  python ocr.py doc.pdf -o output.md --dpi 200

  # Remote SGLang server
  python ocr.py doc.pdf --server http://192.168.1.100:10000 -o output.md

  # Check GPU
  python ocr.py --check
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list[str]:
    """Convert PDF pages to PNG images via PyMuPDF."""
    import fitz

    doc = fitz.open(pdf_path)
    tmp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    paths: list[str] = []
    for i, page in enumerate(doc):
        out = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


def check_gpu() -> str:
    """Return 'cuda' or 'cpu'."""
    import torch

    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        return f"cuda  ({name}, {vram:.1f} GB)"
    return "cpu   (no CUDA GPU found)"


# ── remote mode ──────────────────────────────────────────────────────────


def remote_ocr(
    server_url: str,
    image_paths: list[str],
    prompt: str = "<image>document parsing.",
    image_mode: str = "gundam",
    ngram_window: int = 128,
) -> str:
    """OCR via remote SGLang server (OpenAI-compatible API)."""
    import requests
    from sglang.srt.sampling.custom_logit_processor import (
        DeepseekOCRNoRepeatNGramLogitProcessor,
    )

    session = requests.Session()
    session.trust_env = False

    def _encode(path: str) -> dict:
        ext = os.path.splitext(path)[1].lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext.lstrip('.')}"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}

    content: list[dict] = [{"type": "text", "text": prompt}]
    for p in image_paths:
        content.append(_encode(p))

    payload = {
        "model": "Unlimited-OCR",
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "skip_special_tokens": False,
        "images_config": {"image_mode": image_mode},
        "custom_logit_processor": DeepseekOCRNoRepeatNGramLogitProcessor.to_str(),
        "custom_params": {"ngram_size": 35, "window_size": ngram_window},
        "stream": False,
    }

    resp = session.post(
        f"{server_url}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=600,
    )
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]


# ── local mode ───────────────────────────────────────────────────────────


def local_ocr(
    image_path: str,
    prompt: str = "<image>document parsing.",
    image_size: int = 640,
    base_size: int = 1024,
    crop_mode: bool = True,
    max_length: int = 32768,
    no_repeat_ngram_size: int = 35,
    ngram_window: int = 128,
) -> str:
    """OCR via local HF Transformers inference (CUDA GPU required)."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    model_name = "baidu/Unlimited-OCR"

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16,
    )
    model = model.eval().cuda()

    result = model.infer(
        tokenizer=tokenizer,
        prompt=prompt,
        image_file=image_path,
        output_path=None,
        base_size=base_size,
        image_size=image_size,
        crop_mode=crop_mode,
        max_length=max_length,
        no_repeat_ngram_size=no_repeat_ngram_size,
        ngram_window=ngram_window,
        save_results=False,
    )
    return str(result)


def local_ocr_multi(
    image_paths: list[str],
    prompt: str = "<image>Multi page parsing.",
    image_size: int = 1024,
    max_length: int = 32768,
    no_repeat_ngram_size: int = 35,
    ngram_window: int = 1024,
) -> str:
    """Multi-page OCR via local HF Transformers (CUDA GPU required)."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    model_name = "baidu/Unlimited-OCR"

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16,
    )
    model = model.eval().cuda()

    result = model.infer_multi(
        tokenizer=tokenizer,
        prompt=prompt,
        image_files=image_paths,
        output_path=None,
        image_size=image_size,
        max_length=max_length,
        no_repeat_ngram_size=no_repeat_ngram_size,
        ngram_window=ngram_window,
        save_results=False,
    )
    return str(result)


# ── main ─────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baidu Unlimited-OCR — one-shot document parsing (CUDA)"
    )
    parser.add_argument("input", nargs="?", help="Image file or PDF path")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--server", help="Remote SGLang server URL (omit for local)")
    parser.add_argument("--prompt", default="<image>document parsing.")
    parser.add_argument("--dpi", type=int, default=300, help="PDF render DPI")
    parser.add_argument("--check", action="store_true", help="Check GPU availability and exit")
    args = parser.parse_args()

    # ── check ──
    if args.check:
        print("GPU status:", check_gpu())
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: file not found — {input_path}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(input_path)[1].lower()
    is_pdf = ext == ".pdf"

    # ── remote mode ──
    if args.server:
        server = args.server.rstrip("/")
        if is_pdf:
            pages = pdf_to_images(input_path, dpi=args.dpi)
            result = remote_ocr(server, pages, image_mode="base", ngram_window=1024)
        else:
            pages = [input_path]
            result = remote_ocr(server, pages)
        print(f"→ Sending to {server}  |  {len(pages)} page(s)")
    # ── local mode ──
    else:
        import torch

        if not torch.cuda.is_available():
            print(
                "Error: No CUDA GPU found. Use --server <URL> for remote inference.",
                file=sys.stderr,
            )
            sys.exit(1)

        if is_pdf:
            pages = pdf_to_images(input_path, dpi=args.dpi)
            print(f"→ Local inference  |  {len(pages)} page(s)  |  mode=base")
            result = local_ocr_multi(pages)
        else:
            print(f"→ Local inference  |  single image  |  mode=gundam")
            result = local_ocr(input_path)

    # ── output ──
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"✓ Written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
