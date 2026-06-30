from __future__ import annotations

import argparse
import json
import plistlib
import shlex
import sys
from pathlib import Path
from typing import Any


DEFAULT_DIR = "./model-shelf"
SCHEMA_VERSION = "0.1"
SUPPORTED_PROVIDERS = ("ollama", "lmstudio", "mlx", "llama.cpp")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ms", description="Model Shelf resolver CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a Model Shelf")
    init_parser.add_argument("--dir", help="Shelf directory. If omitted, ms asks interactively.")

    add_parser = subparsers.add_parser("add", help="Register a Hugging Face repo")
    add_parser.add_argument("hf_repo")

    subparsers.add_parser("list", help="List registered models")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve candidate paths for a model/runtime")
    resolve_parser.add_argument("model_id")
    resolve_parser.add_argument("--runtime")

    commands_parser = subparsers.add_parser("commands", help="Print command templates for a model")
    commands_parser.add_argument("model_id")

    provider_parser = subparsers.add_parser("provider-path", help="Configure a provider to use a Model Shelf path")
    provider_parser.add_argument("provider", choices=SUPPORTED_PROVIDERS)
    provider_parser.add_argument("--models-path", help="Path to expose to the provider. Defaults to ./models.")
    provider_parser.add_argument("--config-path", help="Provider config file to edit. Defaults to a shelf-local generated config.")
    provider_parser.add_argument("--apply", action="store_true", help="Write the config. Without this, show the planned edit only.")

    args = parser.parse_args(argv)

    if args.command == "init":
        init(args.dir)
    elif args.command == "add":
        add(args.hf_repo)
    elif args.command == "list":
        list_models()
    elif args.command == "resolve":
        resolve(args.model_id, args.runtime)
    elif args.command == "commands":
        print_commands(args.model_id)
    elif args.command == "provider-path":
        provider_path(args.provider, args.models_path, args.config_path, args.apply)


def init(directory: str | None) -> None:
    if directory is None:
        directory = ask_directory()
    shelf_root = Path(directory).expanduser().resolve()
    init_paths: tuple[str, ...] = (
        "models/hf",
        "models/mlx",
        "models/gguf",
        "models/ollama",
        "models/cache",
        "models/logs",
        "provider-configs",
    )
    for path in init_paths:
        (shelf_root / path).mkdir(parents=True, exist_ok=True)

    config_path = shelf_root / "model-shelf.json"
    registry_path = shelf_root / "models" / "registry.json"
    if not config_path.exists():
        write_json(config_path, default_config())
    if not registry_path.exists():
        write_json(registry_path, {"schema_version": SCHEMA_VERSION, "models": []})

    print(f"Initialized Model Shelf at {shelf_root}")
    print(f"Next: cd {shlex.quote(str(shelf_root))}")


def add(repo: str) -> None:
    shelf_root = find_shelf_root()
    model_id = normalize_repo(repo)
    namespace, name = split_model_id(model_id)
    model_dir = shelf_root / "models" / "hf" / namespace / name
    for path in ("source", "mlx/q4", "mlx/q3", "gguf"):
        (model_dir / path).mkdir(parents=True, exist_ok=True)

    manifest = create_manifest(model_id)
    write_json(model_dir / "manifest.json", manifest)
    (model_dir / "commands.md").write_text(commands_markdown(manifest), encoding="utf-8")

    registry = read_registry(shelf_root)
    entry = {
        "model_id": model_id,
        "manifest_path": f"models/hf/{namespace}/{name}/manifest.json",
        "source_type": "huggingface",
        "source_url": f"https://huggingface.co/{model_id}",
        "available_formats": [
            "hf-repo",
            "hf-safetensors-source-planned",
            "mlx-q4-planned",
            "mlx-q3-planned",
            "gguf-planned",
        ],
        "notes": "Registered as metadata and command templates only. No model files have been downloaded.",
    }
    registry["models"] = [model for model in registry["models"] if model["model_id"] != model_id]
    registry["models"].append(entry)
    write_json(shelf_root / "models" / "registry.json", registry)
    print(f"Registered {model_id}")
    print(f"Manifest: {entry['manifest_path']}")


def list_models() -> None:
    shelf_root = find_shelf_root()
    for model in read_registry(shelf_root)["models"]:
        print(f"{model['model_id']}\t{model['manifest_path']}")


def resolve(model_id: str, runtime: str | None) -> None:
    shelf_root = find_shelf_root()
    manifest = read_manifest(shelf_root, model_id)
    candidates = []
    for key, runtimes in manifest.get("compatible_runtimes", {}).items():
        if runtime is None or runtime in runtimes:
            local_path = manifest.get("local_paths", {}).get(key)
            exists = bool(local_path and (shelf_root / local_path).exists())
            candidates.append({"key": key, "path": local_path, "exists": exists})
    print(json.dumps({"model_id": model_id, "runtime": runtime, "candidates": candidates}, indent=2))


def print_commands(model_id: str) -> None:
    shelf_root = find_shelf_root()
    manifest = read_manifest(shelf_root, model_id)
    for section in ("download_commands", "conversion_commands", "launch_commands"):
        print(f"\n{section}")
        for name, command in manifest.get(section, {}).items():
            print(f"  {name}: {shlex.join(command)}")


def provider_path(provider: str, models_path: str | None, config_path: str | None, apply: bool) -> None:
    shelf_root = find_shelf_root()
    target_path = Path(models_path).expanduser() if models_path else shelf_root / "models"
    target_path = target_path.resolve()
    plan = provider_config_plan(shelf_root, provider, target_path, config_path)

    print(json.dumps({"provider": provider, "models_path": str(target_path), "config_path": str(plan['path']), "format": plan["format"]}, indent=2))
    if not apply:
        print("Dry run only. Re-run with --apply to write this config.")
        return

    plan["path"].parent.mkdir(parents=True, exist_ok=True)
    if plan["format"] == "json":
        existing = read_json_if_exists(plan["path"])
        existing.update(plan["content"])
        write_json(plan["path"], existing)
    elif plan["format"] == "env":
        plan["path"].write_text(render_env(plan["content"]), encoding="utf-8")
    elif plan["format"] == "plist":
        existing = read_plist_if_exists(plan["path"])
        existing.update(plan["content"])
        with plan["path"].open("wb") as handle:
            plistlib.dump(existing, handle)
    else:
        raise SystemExit(f"Unsupported config format: {plan['format']}")
    print(f"Wrote provider config: {plan['path']}")


def provider_config_plan(shelf_root: Path, provider: str, models_path: Path, config_path: str | None) -> dict[str, Any]:
    generated = shelf_root / "provider-configs"
    if provider == "ollama":
        path = Path(config_path).expanduser() if config_path else generated / "ollama.env"
        return {"path": path, "format": "env", "content": {"OLLAMA_MODELS": str(models_path / "ollama")}}
    if provider == "lmstudio":
        path = Path(config_path).expanduser() if config_path else generated / "lmstudio.json"
        return {"path": path, "format": "json", "content": {"modelsPath": str(models_path)}}
    if provider == "mlx":
        path = Path(config_path).expanduser() if config_path else generated / "mlx.json"
        return {"path": path, "format": "json", "content": {"model_shelf_path": str(models_path), "mlx_models_path": str(models_path / "mlx")}}
    if provider == "llama.cpp":
        path = Path(config_path).expanduser() if config_path else generated / "llama-cpp.env"
        return {"path": path, "format": "env", "content": {"LLAMA_CPP_MODELS": str(models_path / "gguf")}}
    raise SystemExit(f"Unsupported provider: {provider}")


def ask_directory() -> str:
    if not sys.stdin.isatty():
        return DEFAULT_DIR
    answer = input(f"Where should Model Shelf live? [{DEFAULT_DIR}] ").strip()
    return answer or DEFAULT_DIR


def find_shelf_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / "model-shelf.json").exists() and (current / "models" / "registry.json").exists():
            return current
        if current.parent == current:
            raise SystemExit("No Model Shelf found. Run `ms init` and cd into the chosen shelf directory.")
        current = current.parent


def read_registry(shelf_root: Path) -> dict[str, Any]:
    registry_path = shelf_root / "models" / "registry.json"
    if not registry_path.exists():
        raise SystemExit("No models/registry.json found. Run `ms init` first.")
    return json.loads(registry_path.read_text(encoding="utf-8"))


def read_manifest(shelf_root: Path, model_id: str) -> dict[str, Any]:
    registry = read_registry(shelf_root)
    for model in registry["models"]:
        if model["model_id"] == model_id:
            return json.loads((shelf_root / model["manifest_path"]).read_text(encoding="utf-8"))
    raise SystemExit(f"Model not found: {model_id}")


def create_manifest(model_id: str) -> dict[str, Any]:
    namespace, name = split_model_id(model_id)
    base = f"models/hf/{namespace}/{name}"
    return {
        "schema_version": SCHEMA_VERSION,
        "model_id": model_id,
        "name": name,
        "source_url": f"https://huggingface.co/{model_id}",
        "source_type": "huggingface",
        "architecture": None,
        "parameter_count": infer_parameter_count(name),
        "available_formats": [
            {"format": "hf-repo", "status": "remote", "path": None},
            {"format": "hf-safetensors", "status": "planned", "path": f"{base}/source"},
            {"format": "mlx-safetensors", "quantization": "q4", "status": "planned", "path": f"{base}/mlx/q4"},
            {"format": "mlx-safetensors", "quantization": "q3", "status": "planned", "path": f"{base}/mlx/q3"},
            {"format": "gguf", "status": "planned", "path": f"{base}/gguf"},
        ],
        "local_paths": {"source": f"{base}/source", "mlx_q4": f"{base}/mlx/q4", "mlx_q3": f"{base}/mlx/q3", "gguf": f"{base}/gguf"},
        "compatible_runtimes": {"source": ["vllm", "sglang"], "mlx_q4": ["mlx"], "mlx_q3": ["mlx"], "gguf": ["llama.cpp", "lm-studio"], "ollama": ["ollama"]},
        "download_commands": {
            "hf_snapshot": ["huggingface-cli", "download", model_id, "--local-dir", f"{base}/source"],
            "git_lfs": ["git", "clone", f"https://huggingface.co/{model_id}", f"{base}/source"],
        },
        "conversion_commands": {
            "mlx_q4": ["python3", "-m", "mlx_lm.convert", "--hf-path", f"{base}/source", "-q", "--q-bits", "4", "--mlx-path", f"{base}/mlx/q4"],
            "mlx_q3": ["python3", "-m", "mlx_lm.convert", "--hf-path", f"{base}/source", "-q", "--q-bits", "3", "--mlx-path", f"{base}/mlx/q3"],
            "gguf": ["python3", "llama.cpp/convert_hf_to_gguf.py", f"{base}/source", "--outfile", f"{base}/gguf/{name}.gguf"],
        },
        "launch_commands": {
            "mlx_q4": ["mlx_lm.server", "--model", f"{base}/mlx/q4", "--host", "127.0.0.1", "--port", "8081"],
            "mlx_q3": ["mlx_lm.server", "--model", f"{base}/mlx/q3", "--host", "127.0.0.1", "--port", "8081"],
            "llama_cpp_gguf": ["llama-server", "-m", f"{base}/gguf/{name}.gguf", "--host", "127.0.0.1", "--port", "8082"],
            "vllm_source": ["vllm", "serve", f"{base}/source", "--host", "127.0.0.1", "--port", "8083"],
            "sglang_source": ["python3", "-m", "sglang.launch_server", "--model-path", f"{base}/source", "--host", "127.0.0.1", "--port", "8084"],
        },
        "notes": [
            "This manifest is a resolver record and command catalog, not proof that files exist.",
            "Do not run download_commands or conversion_commands unless the user explicitly asks.",
            "Preserve source files under source/ and write converted artifacts to separate format folders.",
        ],
    }


def commands_markdown(manifest: dict[str, Any]) -> str:
    return f"""# {manifest['name']} Commands

These commands are templates. Show the exact command before executing.

## Pull Hugging Face Repo

```bash
{shlex.join(manifest['download_commands']['hf_snapshot'])}
```

## Convert To MLX 4-bit

```bash
{shlex.join(manifest['conversion_commands']['mlx_q4'])}
```

## Convert To MLX 3-bit

```bash
{shlex.join(manifest['conversion_commands']['mlx_q3'])}
```

## Optionally Convert To GGUF

```bash
{shlex.join(manifest['conversion_commands']['gguf'])}
```
"""


def default_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "shelf_root": "./models",
        "registry_path": "./models/registry.json",
        "default_source_type": "huggingface",
        "policy": {
            "preserve_original_files": True,
            "commands_are_templates": True,
            "require_explicit_confirmation_before_download": True,
            "require_explicit_confirmation_before_conversion": True,
        },
    }


def normalize_repo(repo: str) -> str:
    return repo.removeprefix("https://huggingface.co/").strip("/")


def split_model_id(model_id: str) -> tuple[str, str]:
    parts = model_id.split("/")
    if len(parts) != 2:
        raise SystemExit(f"Expected Hugging Face repo as namespace/name, got: {model_id}")
    return parts[0], parts[1]


def infer_parameter_count(name: str) -> str | None:
    import re

    match = re.search(r"(\d+(?:\.\d+)?B)", name, re.IGNORECASE)
    return match.group(1) if match else None


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_plist_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return plistlib.load(handle)


def render_env(values: dict[str, str]) -> str:
    return "".join(f"{key}={shlex.quote(value)}\n" for key, value in values.items())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
