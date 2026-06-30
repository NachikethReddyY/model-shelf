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
3. Run or emulate `ms search <query>` before proposing a download.
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
ms install qwen --format gguf --source
ms install qwen --format gguf --source --yes
ms resolve qwen --runtime llama.cpp
ms commands qwen --format gguf
ms provider-path ollama
```

`ms search --install` is interactive: it shows matches, asks the user to select a model, shows the exact install command, then asks for one final confirmation.

`ms install <query> --source` is dry-run by default. It may execute a download only when the user passes `--yes` or confirms interactively.

`ms provider-path <provider>` is dry-run by default. Use `--apply` only after the user confirms the path and provider config target. Use `--config-path` when editing a real provider config file outside the shelf.

## Safety

Always show exact shell commands before running them. If an artifact is unsupported for a runtime, say so clearly and stop.
