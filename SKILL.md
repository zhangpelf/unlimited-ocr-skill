---
name: unlimited-ocr
description: >
  This skill should be used when the user wants to OCR a document, image,
  or PDF using Baidu's Unlimited-OCR model (3B, MIT). Trigger phrases:
  "OCR这个文件", "提取PDF文字", "run OCR on this", "文字识别",
  "百度OCR", "Unlimited OCR", "解析这个文档",
  "recognize text from", "extract text from image/PDF".
  Supports local NVIDIA GPU inference and remote SGLang server.
triggers:
  ocr: OCR/文字识别/提取文字/document parsing/recognize text
---

# unlimited-ocr-skill — Baidu Unlimited-OCR for OpenCode

在本地 NVIDIA GPU 上使用百度 Unlimited-OCR（3B 参数，MIT 协议）对图片或 PDF 进行一次性文字识别。支持单页（gundam 模式）和多页文档（base 模式，最高 32K tokens）。

## 快速路由

| 你的情况 | 方案 |
|---------|------|
| 有 NVIDIA GPU（≥6GB VRAM） | 本地模式，直接推理 |
| 没有 GPU | 远程模式，指向 SGLang 服务器 |
| 仅体验 | [HF Spaces](https://huggingface.co/spaces/baidu/Unlimited-OCR) 在线试用 |

## 安装

```bash
# 方式一：作为 opencode skill 安装
git clone https://github.com/zhangpelf/unlimited-ocr-skill.git \
    ~/.config/opencode/skills/unlimited-ocr

# 方式二：独立使用
git clone https://github.com/zhangpelf/unlimited-ocr-skill.git
cd unlimited-ocr-skill

# 创建 venv + 安装依赖
bash scripts/setup.sh
```

## 用法

```bash
# 本地 GPU 模式
OCR=".venv/bin/python scripts/ocr.py"

# 单张图片
$OCR receipt.jpg -o output.md
$OCR page.png --prompt "<image>document parsing." -o page.md

# PDF 文档
$OCR document.pdf -o document.md
$OCR document.pdf -o document.md --dpi 200  # 降低 DPI 加快处理

# 远程 SGLang 模式
$OCR document.pdf --server http://192.168.1.100:10000 -o document.md
$OCR image.jpg --server https://your-server.com:10000 -o result.md

# 检查 GPU
$OCR --check
```

## 技术参数

| 参数 | 单图 gundam | 单图 base | 多页/PDF base |
|------|------------|-----------|--------------|
| `image_size` | 640 | 1024 | 1024 |
| `crop_mode` | true | false | false |
| `ngram_window` | 128 | 128 | 1024 |
| `no_repeat_ngram_size` | 35 | 35 | 35 |

- 模型：`baidu/Unlimited-OCR`（~3B 参数，bf16 ~6GB VRAM）
- 上下文窗口：32,768 tokens（约 30–50 页文字）
- 输入格式：JPG / PNG / PDF
- 输出格式：Markdown / 纯文本

## 项目结构

```
unlimited-ocr-skill/
├── SKILL.md                 ← opencode skill 定义
├── scripts/
│   ├── setup.sh             ← 一键 venv + 依赖安装
│   └── ocr.py               ← 主 CLI 入口
├── references/
│   └── deploy-guide.md      ← 远程 SGLang 服务器部署
├── README.md                ← 本文件
└── LICENSE                  ← MIT
```

## 注意事项

- **需要 NVIDIA GPU（≥6GB VRAM）**，Apple Silicon MPS 暂不支持（模型包含 CUDA 算子）
- 首次下载模型权重约 6GB（自动缓存到 `~/.cache/huggingface/`）
- PDF 超过 50 页建议分段，或加大 `--context-length`
- 远程模式需要预先部署 SGLang 服务（见 `references/deploy-guide.md`）
