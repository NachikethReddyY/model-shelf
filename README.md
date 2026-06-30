# Model Shelf

Model Shelf is a local-first model storage standard and resolver.

It gives agents and local runtimes a shared, inspectable place to answer:

- Is this model already on disk?
- Is it GGUF, MLX, or safetensors?
- Who published it?
- What quantization is it?
- How much disk and RAM should I expect?
- What exact command installs or launches it?

Model Shelf is intentionally file-based. There is no web app, database, background service, or API server.

The canonical shelf folder is visible: `models/`. Do not use `.models/` or any hidden directory.

## Install

macOS / Linux:

```bash
uv tool install --force git+https://github.com/NachikethReddyY/model-shelf.git
export PATH="$HOME/.local/bin:$PATH"
ms --help
```

Windows PowerShell:

```powershell
uv tool install --force git+https://github.com/NachikethReddyY/model-shelf.git
$env:Path = "$HOME\.local\bin;$env:Path"
ms --help
```

From a cloned repo:

```bash
git clone https://github.com/NachikethReddyY/model-shelf.git
cd model-shelf
bash scripts/install-global.sh
```

For local development without global install:

```bash
uv run ms --help
```

## Create A Shelf

```bash
ms init
```

`ms init` asks where the shelf should live:

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

Model Shelf has exactly three model storage formats:

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

Providers and runtimes do not get top-level folders. Ollama, LM Studio, MLX, llama.cpp, vLLM, and SGLang should resolve compatible files from these three format folders.

Important files:

- `model-shelf.json`: shelf config and safety policy
- `models/registry.json`: searchable index of registered artifacts

## Search

Search the local registry:

```bash
ms search qwen
```

Example output:

```text
#  format       publisher      model             quant   disk    ram     installed
-  -----------  -------------  ----------------  ------  ------  ------  ---------
1  gguf         Qwen           Qwen3-14B-GGUF    Q4_K_M  ~9 GB   ~10 GB  no
2  mlx          mlx-community  Qwen3-14B-4bit    4bit    ~8 GB   ~10 GB  no
3  safetensors  Qwen           Qwen3-14B         -       ~28 GB  ~31 GB  no
```

Filter by format:

```bash
ms search qwen --format gguf
ms search qwen --format mlx
ms search qwen --format safetensors
```

## Interactive Install

Search and choose a model interactively:

```bash
ms search qwen --install
```

Model Shelf will:

1. Show matching artifacts.
2. Ask which one to install.
3. Show the exact install command.
4. Ask for one final confirmation before running it.

No download happens unless you confirm.

## Direct Install

Dry run:

```bash
ms install qwen --format gguf --source
```

Actually run the install:

```bash
ms install qwen --format gguf --source --yes
```

Use a different manifest command:

```bash
ms install qwen --format gguf --source --command git_lfs --yes
```

## List

```bash
ms list
```

## Resolve A Runtime Path

Ask which local paths are compatible with a runtime:

```bash
ms resolve qwen --runtime mlx
ms resolve qwen --runtime llama.cpp
```

## Show Commands

Print download and launch command templates:

```bash
ms commands qwen --format gguf
ms commands qwen --format mlx
ms commands qwen --format safetensors
```

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

To write a specific provider config file, pass the path explicitly:

```bash
ms provider-path ollama --config-path ~/some/provider/config.env --apply
```

## Add A Model Artifact

Register a Hugging Face artifact without downloading it:

```bash
ms add Qwen/Qwen3-14B-GGUF --format gguf --quant Q4_K_M --disk "~9 GB" --ram "~10 GB" --file Qwen3-14B-Q4_K_M.gguf
ms add mlx-community/Qwen3-14B-4bit --format mlx --quant 4bit --disk "~8 GB" --ram "~10 GB"
ms add Qwen/Qwen3-14B --format safetensors --disk "~28 GB" --ram "~31 GB"
```

## Safety Rules

- `ms add` registers metadata only.
- `ms search` searches the local registry only.
- `ms install` is dry-run unless `--yes` is passed or you confirm interactively.
- No downloads happen automatically.
- No conversions happen automatically.
- Models live only under `models/gguf`, `models/mlx`, and `models/safetensors`.
- Do not assume GGUF, MLX, and safetensors files are interchangeable.
