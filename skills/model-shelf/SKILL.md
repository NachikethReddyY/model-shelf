# Model Shelf

Use this skill when an AI coding agent needs to find, reuse, download, or launch local model files through a filesystem-based Model Shelf.

## Rule

Model Shelf is a local-first storage standard and resolver. It is not a web app, database service, API gateway, or runtime-specific manager.

The shelf is format-first. Providers and runtimes pull from the same three visible format folders:

- `models/gguf/`
- `models/mlx/`
- `models/safetensors/`

Do not use `.models/` or any hidden directory.

## Shelf Layout

```text
models/
├── gguf/
│   └── Qwen/
│       └── Qwen3-14B-GGUF/
│           └── Qwen3-14B-Q4_K_M.gguf
├── mlx/
│   └── mlx-community/
│       └── Qwen3-14B-4bit/
└── safetensors/
    └── Qwen/
        └── Qwen3-14B/
```

Key files:

- `model-shelf.json`: root shelf config and policy.
- `models/registry.json`: searchable artifact registry.

Registry records include:

- publisher
- model name
- format: `gguf`, `mlx`, or `safetensors`
- quantization
- disk size estimate
- RAM estimate
- local path
- compatible runtimes
- download commands
- launch commands

## Agent Workflow

1. Read `model-shelf.json`.
2. Read `models/registry.json`.
3. Run or emulate `ms search <query>` before proposing a download. Can filter by param size with `--min-params`/`--max-params` and sort with `--sort params|params-desc|downloads`.
4. Prefer an already installed artifact when one matches the requested runtime.
5. If files are missing, show the matching command from `download_commands`.
6. Do not execute install commands unless the user explicitly confirms.
7. Keep files inside one of the three format folders.
8. Never assume GGUF, MLX, and safetensors artifacts are interchangeable.

## CLI

```bash
ms init
ms search qwen
ms search qwen --format gguf
ms search qwen --install
ms search qwen --min-params 9B --max-params 35B
ms search qwen --sort params
ms install qwen --format gguf --source
ms install qwen --format gguf --source --yes
ms install https://huggingface.co/Qwen/Qwen3-14B-GGUF
ms resolve qwen --runtime llama.cpp
ms commands qwen --format gguf
ms provider-path ollama
ms update --dry-run
ms update
```

`ms search --install` is interactive: shows match table, asks user to select number, shows install plan, then asks for one final confirmation.

`ms install <query> --source` shows match table when multiple results found, then interactive picker. Dry-run by default; executes only with `--yes` or interactive confirmation.

`ms install <URL>` (HF repo URL) installs directly, bypassing registry and search entirely.

`ms search --sort params` sorts ascending by param count; `--sort params-desc` descending; `--sort downloads` (default) uses HF sort.

`ms provider-path <provider>` is dry-run by default. Use `--apply` only after the user confirms the path and provider config target. Use `--config-path` when editing a real provider config file outside the shelf.

`ms update` updates the global CLI by running `uv tool install --force git+https://github.com/NachikethReddyY/model-shelf.git`. Downloads use `sys.executable -m huggingface_hub download` (no PATH dependency). Also includes `git-lfs` as alternative command key. Use `ms update --dry-run` to show the command without running it.

## Safety

Always show exact shell commands before running them. If an artifact is unsupported for a runtime, say so clearly and stop.
