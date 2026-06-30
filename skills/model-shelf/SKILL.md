# Model Shelf

Use this skill when an AI coding agent needs to find, reuse, download, convert, or launch local model files through a filesystem-based Model Shelf.

## Rule

Model Shelf is a local-first storage standard and resolver. It is not a web app, database service, API gateway, or runtime-specific manager.

## Shelf Layout

The canonical shelf root is the visible folder `models/`. Do not use `.models/` or any other hidden directory.

Key files:

- `model-shelf.json`: root shelf config and policy.
- `models/registry.json`: index of known models and manifest paths.
- `models/hf/{namespace}/{model}/manifest.json`: source of truth for a model.
- `models/hf/{namespace}/{model}/commands.md`: human-readable command templates.

Format folders:

- `source/`: original Hugging Face files.
- `mlx/q4/`: MLX 4-bit conversion output.
- `mlx/q3/`: MLX 3-bit conversion output.
- `gguf/`: GGUF conversion output.

Runtime indexes:

- `models/mlx/`
- `models/gguf/`
- `models/ollama/`

Cache and logs:

- `models/cache/`
- `models/logs/`

## Agent Workflow

1. Read `model-shelf.json`.
2. Read `models/registry.json`.
3. Before downloading anything, search the registry for the requested `model_id`.
4. Open the model `manifest.json`.
5. Resolve by runtime using `compatible_runtimes` and `local_paths`.
6. Check whether the resolved path exists and contains expected files.
7. If files are missing, show the matching command from `download_commands` or `conversion_commands`.
8. Do not execute download or conversion commands unless the user explicitly asks.
9. Preserve original files under `source/`.
10. Write converted files only into format-specific folders such as `mlx/q4`, `mlx/q3`, or `gguf`.

## CLI

Install the global `ms` command from the Model Shelf project root:

```bash
uv tool install --force .
uv tool update-shell
```

After restarting the shell, use `ms` directly. Before that, `uv run ms` works from the project root.

Use the local CLI from the shelf root:

```bash
uv run ms init
uv run ms init --dir ./my-model-shelf
uv run ms add deepreinforce-ai/Ornith-1.0-35B-FP8
uv run ms list
uv run ms resolve deepreinforce-ai/Ornith-1.0-35B-FP8 --runtime mlx
uv run ms commands deepreinforce-ai/Ornith-1.0-35B-FP8
uv run ms provider-path ollama
uv run ms provider-path mlx
```

`ms init` should ask the user where they want the shelf directory to live. Use `--dir` only when the user has already specified the location or an automated setup needs non-interactive behavior.

`ms provider-path <provider>` is dry-run by default. Use `--apply` only after the user confirms the path and provider config target. Use `--config-path` when editing a real provider config file outside the shelf.

## Safety

Always show exact shell commands before running them. Never assume HF safetensors, MLX safetensors, GGUF, Ollama, and LM Studio files are interchangeable. If a conversion is unsupported or its toolchain is missing, say so clearly and stop.
