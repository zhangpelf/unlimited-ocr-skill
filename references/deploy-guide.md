# 远程 GPU 部署指南

在有一张 NVIDIA GPU 的机器上启动 SGLang 推理服务，供本地 Mac 调用。

## 前置要求

- Linux 或 macOS（NVIDIA GPU，≥8GB VRAM）
- CUDA 12.x + 驱动 ≥ 530
- Python 3.12 + uv

## 步骤

### 1. 克隆仓库 + 创建环境

```bash
git clone https://github.com/baidu/Unlimited-OCR.git
cd Unlimited-OCR

uv venv --python 3.12
source .venv/bin/activate

# 安装 SGLang wheel（仓库已打包）
uv pip install wheel/sglang-0.0.0.dev11416+g92e8bb79e-py3-none-any.whl
uv pip install kernels==0.11.7
uv pip install pymupdf==1.27.2.2
```

### 2. 启动服务

```bash
CUDA_VISIBLE_DEVICES=0 python -m sglang.launch_server \
    --model baidu/Unlimited-OCR \
    --served-model-name Unlimited-OCR \
    --attention-backend fa3 \
    --page-size 1 \
    --mem-fraction-static 0.8 \
    --context-length 32768 \
    --enable-custom-logit-processor \
    --disable-overlap-schedule \
    --skip-server-warmup \
    --host 0.0.0.0 \
    --port 10000
```

参数说明：
- `--attention-backend fa3` — 使用 FlashAttention 3，对 R-SWA 优化
- `--page-size 1` — 配合 R-SWA 的 KV cache 管理
- `--mem-fraction-static 0.8` — 分配 80% 显存给 KV cache（剩余给模型权重）
- `--context-length 32768` — 最大上下文长度（可根据文档长度调大）

### 3. 验证服务

```bash
curl http://127.0.0.1:10000/v1/models | python -m json.tool
```

返回中有 `Unlimited-OCR` 即成功。

### 4. 开放远程访问

如果需要从其他机器访问，注意防火墙和安全组：

```bash
# 确保 --host 0.0.0.0 已经设置
# 建议加一层 Nginx 反代 + HTTPS 或使用 SSH 隧道
```

**SSH 隧道方式（推荐）：**

```bash
# 在本地 Mac 上
ssh -L 10000:127.0.0.1:10000 user@your-gpu-server
# 然后使用 --server http://127.0.0.1:10000
```

### 5. 批量处理（服务启动后）

```bash
# 仓库自带的 infer.py
python infer.py \
    --image_dir ./images \
    --output_dir ./outputs \
    --concurrency 8 \
    --image_mode gundam

# 或
python infer.py \
    --pdf ./document.pdf \
    --output_dir ./outputs \
    --concurrency 8
```

## 硬件参考

| GPU | VRAM | 最大 pages | 推荐 |
|-----|------|-----------|------|
| RTX 4090 | 24 GB | ~30 页 | ✅ |
| A100 80G | 80 GB | ~150 页 | ✅ 推荐 |
| RTX 3090 | 24 GB | ~30 页 | ✅ |
| RTX 4080 | 16 GB | ~15 页 | ⚠️ |
| RTX 3060 | 12 GB | ~8 页 | ⚠️ 小文档可用 |

## Docker 方式

```dockerfile
FROM nvidia/cuda:12.4.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y python3.12 python3.12-venv git
RUN python3.12 -m ensurepip && pip install uv

WORKDIR /app
RUN git clone https://github.com/baidu/Unlimited-OCR.git .
RUN uv venv && . .venv/bin/activate && \
    uv pip install wheel/sglang-*.whl kernels==0.11.7 pymupdf

EXPOSE 10000
CMD ["python3", "-m", "sglang.launch_server", \
     "--model", "baidu/Unlimited-OCR", \
     "--host", "0.0.0.0", "--port", "10000"]
```

## 常见问题

**Q: 显存不足怎么办？**
- 降低 `--mem-fraction-static`（如 0.6）
- 减少 `--context-length`（如 16384）
- 使用更小的 batch（`--concurrency 1`）

**Q: 服务启动很慢？**
- 首次需要下载模型权重（~6GB），后续自动缓存
- 添加 `--skip-server-warmup` 跳过预热（已默认包含）

**Q: 请求超时？**
- 长文档可能超过 60 秒，CLI 已设置 600 秒超时
- 可用 `--timeout 900` 进一步加大
