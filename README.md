# Model Shelf

Model Shelf is a local-first model storage standard and resolver.

It gives agents and local runtimes a shared, inspectable place to answer:

- Where should model files live?
- Is this model already on disk?
- Which local path should MLX, Ollama, LM Studio, or llama.cpp use?
- What command would download, convert, or launch this model?

Model Shelf is intentionally file-based. There is no web app, database, background service, or API server.

## Install

From this project directory:

```bash
uv tool install --force .
uv tool update-shell
```

Restart your terminal, then check:

```bash
ms --help
```

You can also use the included installer:

```bash
bash scripts/install-global.sh
```

If you do not want a global command, run from this project directory with:

```bash
uv run ms --help
```

## Create A Shelf

Run:

```bash
ms init
```

`ms init` asks where the shelf directory should live:

```text
Where should Model Shelf live? [./model-shelf]
```

For non-interactive setup:

```bash
ms init --dir ~/Models/model-shelf
```

Then move into the shelf:

```bash
cd ~/Models/model-shelf
```

## Shelf Layout

```text
model-shelf/
  model-shelf.json
  models/
    registry.json
    hf/
      <namespace>/
        <model>/
          source/
          mlx/
            q4/
            q3/
          gguf/
          manifest.json
          commands.md
    mlx/
    gguf/
    ollama/
    cache/
    logs/
  provider-configs/
```

Important files:

- `model-shelf.json`: shelf config and safety policy
- `models/registry.json`: index of registered models
- `manifest.json`: machine-readable model metadata and command templates
- `commands.md`: human-readable command templates

## Add A Model

Register a Hugging Face repo:

```bash
ms add deepreinforce-ai/Ornith-1.0-35B-FP8
```

This creates folders, a manifest, and command templates.

It does **not** download the model.

## List Models

```bash
ms list
```

Example:

```text
deepreinforce-ai/Ornith-1.0-35B-FP8  models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/manifest.json
```

## Resolve A Runtime Path

Ask which local paths are compatible with a runtime:

```bash
ms resolve deepreinforce-ai/Ornith-1.0-35B-FP8 --runtime mlx
```

Example output:

```json
{
  "model_id": "deepreinforce-ai/Ornith-1.0-35B-FP8",
  "runtime": "mlx",
  "candidates": [
    {
      "key": "mlx_q4",
      "path": "models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/mlx/q4",
      "exists": true
    }
  ]
}
```

`exists` means the folder exists. It does not prove that converted model files are complete.

## Show Commands

Print download, conversion, and launch command templates:

```bash
ms commands deepreinforce-ai/Ornith-1.0-35B-FP8
```

This shows commands such as:

```bash
huggingface-cli download deepreinforce-ai/Ornith-1.0-35B-FP8 --local-dir models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source
python3 -m mlx_lm.convert --hf-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/source -q --q-bits 4 --mlx-path models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/mlx/q4
```

Model Shelf only prints these commands. It does **not** run them unless you explicitly run them yourself.

## Configure Provider Paths

Use `provider-path` to point a provider at the shelf model directory.

Dry run:

```bash
ms provider-path ollama
ms provider-path lmstudio
ms provider-path mlx
ms provider-path llama.cpp
```

Write a generated config inside the shelf:

```bash
ms provider-path ollama --apply
```

That writes:

```text
provider-configs/ollama.env
```

To write a specific provider config file, pass the path explicitly:

```bash
ms provider-path ollama --config-path ~/some/provider/config.env --apply
```

Model Shelf will not edit real provider config files unless you provide `--config-path` and `--apply`.

## Safety Rules

- `ms add` registers metadata only.
- `ms commands` prints commands only.
- No downloads happen automatically.
- No conversions happen automatically.
- Original model files belong under `source/`.
- Converted outputs belong under format folders such as `mlx/q4`, `mlx/q3`, or `gguf`.
- Do not assume HF safetensors, MLX safetensors, GGUF, Ollama, and LM Studio files are interchangeable.

## First Seeded Model

This scaffold includes:

```text
deepreinforce-ai/Ornith-1.0-35B-FP8
```

Manifest:

```text
models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/manifest.json
```

Commands:

```text
models/hf/deepreinforce-ai/Ornith-1.0-35B-FP8/commands.md
```
