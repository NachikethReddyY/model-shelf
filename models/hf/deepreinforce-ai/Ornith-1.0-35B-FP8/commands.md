# Ornith-1.0-35B-FP8 Commands

These commands are templates. Show the exact command to the user before executing. Do not download, convert, overwrite, or delete model files unless explicitly requested.

## Pull Hugging Face Repo

```bash
huggingface-cli download deepreinforce-ai/Ornith-1.0-35B-FP8 --local-dir models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source
```

Alternative with Git LFS:

```bash
git clone https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B-FP8 models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source
```

## Convert To MLX 4-bit

```bash
python3 -m mlx_lm.convert --hf-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source -q --q-bits 4 --mlx-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/mlx/q4
```

## Convert To MLX 3-bit

```bash
python3 -m mlx_lm.convert --hf-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source -q --q-bits 3 --mlx-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/mlx/q3
```

## Optionally Convert To GGUF

```bash
python3 llama.cpp/convert_hf_to_gguf.py models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source --outfile models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/gguf/Ornith-1.0-35B-FP8.gguf
```

## Launch Examples

MLX q4:

```bash
mlx_lm.server --model models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/mlx/q4 --host 127.0.0.1 --port 8081
```

llama.cpp GGUF:

```bash
llama-server -m models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/gguf/Ornith-1.0-35B-FP8.gguf --host 127.0.0.1 --port 8082
```
