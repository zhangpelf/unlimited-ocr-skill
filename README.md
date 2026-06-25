# unlimited-ocr-skill

> 百度 Unlimited-OCR（3B 参数）的 OpenCode skill — 本地 NVIDIA GPU 或远程 SGLang 部署，一键 OCR 图片和 PDF。

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Model](https://img.shields.io/badge/model-baidu/Unlimited--OCR-bf5700)](https://huggingface.co/baidu/Unlimited-OCR)
[![Paper](https://img.shields.io/badge/arXiv-2606.23050-b31b1b)](https://arxiv.org/abs/2606.23050)

---

## 快速开始

```bash
# 1. 安装
git clone https://github.com/<your-github-username>/unlimited-ocr-skill.git
cd unlimited-ocr-skill
bash scripts/setup.sh

# 2. 使用
./.venv/bin/python scripts/ocr.py receipt.jpg -o output.md
```

**需要 NVIDIA GPU（≥6GB VRAM）**。没有 GPU？使用远程模式 → 见下方。

---

## 两种模式

### 本地模式（CUDA GPU）

直接在本地 GPU 上推理，数据不出本机。

```bash
OCR="./.venv/bin/python scripts/ocr.py"

# 单张图片
$OCR scan.png -o text.md

# PDF 文档
$OCR document.pdf -o text.md
$OCR document.pdf -o text.md --dpi 200   # 低 DPI 加快速度

# 查看 GPU 状态
$OCR --check
# → GPU status: cuda  (NVIDIA A100, 79.4 GB)
```

### 远程模式（SGLang 服务器）

任何有 GPU 的机器上启动服务，本机通过网络调用。

```bash
# 设置远程服务（详见 references/deploy-guide.md）
sglang.launch_server --model baidu/Unlimited-OCR --port 10000

# 调用
$OCR document.pdf --server http://192.168.1.100:10000 -o text.md
$OCR image.png --server https://your-server.com:10000 -o result.md
```

---

## 作为 OpenCode Skill 安装

```bash
# 克隆到 opencode skills 目录
git clone https://github.com/<your-github-username>/unlimited-ocr-skill.git \
    ~/.config/opencode/skills/unlimited-ocr

# 初始化一次
bash ~/.config/opencode/skills/unlimited-ocr/scripts/setup.sh
```

然后在任何 OpenCode 对话中触发：

- "OCR 这个 PDF" → 本地模式
- "用远程服务器提取这张图片的文字" → 远程模式
- "帮我解析这个文档" → 自动判断

---

## Claude Code 集成

克隆到项目目录或 home 目录后，Claude Code 会自动发现子代理：

```bash
# 作为项目级子代理（推荐）
cd your-project
git clone https://github.com/<your-github-username>/unlimited-ocr-skill.git .claude/unlimited-ocr

# 或放到 Claude Code 的全局 skills 目录（如果使用了 oh-my-claudecode）
git clone https://github.com/<your-github-username>/unlimited-ocr-skill.git \
    ~/.claude/skills/unlimited-ocr

# 初始化环境
bash .claude/unlimited-ocr/scripts/setup.sh
```

### 触发方式

仓库中的 `.claude/agents/ocr-unlimited.md` 定义了 Claude Code 子代理。克隆后，在 Claude Code 对话中：

- "OCR this file" → 自动调起子代理
- "帮我识别这张图片的文字" → 自动识别并执行
- "把 PDF 的文字提取出来" → 自动处理

子代理会自动找到 skill 目录、检查环境、运行 OCR 并返回结果。

---

## 技术细节

| 属性 | 值 |
|------|------|
| 模型 | [`baidu/Unlimited-OCR`](https://huggingface.co/baidu/Unlimited-OCR)（~3B） |
| 协议 | MIT License |
| 精度 | bfloat16 |
| 显存 | ~6 GB |
| 上下文 | 32,768 tokens（约 30–50 页文字） |
| 输入 | JPG / PNG / PDF |
| 输出 | Markdown / 纯文本 |

---

## 项目结构

```
unlimited-ocr-skill/
├── .claude/
│   └── agents/
│       └── ocr-unlimited.md   # Claude Code 子代理定义
├── SKILL.md                   # OpenCode skill 触发与文档
├── scripts/
│   ├── setup.sh               # 环境初始化
│   └── ocr.py                 # 主程序
├── references/
│   └── deploy-guide.md        # 远程服务器部署
├── README.md                  # 本文件
└── LICENSE                    # MIT
```

## 许可

本项目采用 MIT License。模型权重本身同样使用 MIT License（[baidu/Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR)）。
