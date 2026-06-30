from __future__ import annotations

import argparse
import json
import plistlib
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_DIR = "./model-shelf"
SCHEMA_VERSION = "0.2"
FORMATS = ("gguf", "mlx", "safetensors")
SUPPORTED_PROVIDERS = ("ollama", "lmstudio", "mlx", "llama.cpp")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ms", description="Model Shelf resolver CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a Model Shelf")
    init_parser.add_argument("--dir", help="Shelf directory. If omitted, ms asks interactively.")

    add_parser = subparsers.add_parser("add", help="Register a model artifact")
    add_parser.add_argument("repo")
    add_parser.add_argument("--format", choices=FORMATS, default="safetensors")
    add_parser.add_argument("--name")
    add_parser.add_argument("--publisher")
    add_parser.add_argument("--quant")
    add_parser.add_argument("--disk")
    add_parser.add_argument("--ram")
    add_parser.add_argument("--file", help="Expected filename for single-file formats like GGUF.")

    subparsers.add_parser("list", help="List registered model artifacts")

    search_parser = subparsers.add_parser("search", help="Search registered model artifacts")
    search_parser.add_argument("query", nargs="?", default="")
    search_parser.add_argument("--format", choices=FORMATS)
    search_parser.add_argument("--install", action="store_true", help="Interactively select and install a result.")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve candidate paths for a runtime")
    resolve_parser.add_argument("query")
    resolve_parser.add_argument("--runtime")
    resolve_parser.add_argument("--format", choices=FORMATS)

    commands_parser = subparsers.add_parser("commands", help="Print command templates for a model artifact")
    commands_parser.add_argument("query")
    commands_parser.add_argument("--format", choices=FORMATS)

    install_parser = subparsers.add_parser("install", help="Install model files using registry command templates")
    install_parser.add_argument("query")
    install_parser.add_argument("--source", action="store_true", help="Install from the artifact source repository.")
    install_parser.add_argument("--format", choices=FORMATS)
    install_parser.add_argument("--command", dest="download_command", default="hf_snapshot")
    install_parser.add_argument("--yes", action="store_true", help="Run the command. Without this, show a dry run and ask in interactive terminals.")

    provider_parser = subparsers.add_parser("provider-path", help="Configure a provider to use a Model Shelf path")
    provider_parser.add_argument("provider", choices=SUPPORTED_PROVIDERS)
    provider_parser.add_argument("--models-path", help="Path to expose to the provider. Defaults to ./models.")
    provider_parser.add_argument("--config-path", help="Provider config file to edit. Defaults to a shelf-local generated config.")
    provider_parser.add_argument("--apply", action="store_true", help="Write the config. Without this, show the planned edit only.")

    args = parser.parse_args(argv)

    if args.command == "init":
        init(args.dir)
    elif args.command == "add":
        add(args.repo, args.format, args.name, args.publisher, args.quant, args.disk, args.ram, args.file)
    elif args.command == "list":
        list_models()
    elif args.command == "search":
        search(args.query, args.format, args.install)
    elif args.command == "resolve":
        resolve(args.query, args.runtime, args.format)
    elif args.command == "commands":
        print_commands(args.query, args.format)
    elif args.command == "install":
        install(args.query, args.format, args.download_command, args.yes)
    elif args.command == "provider-path":
        provider_path(args.provider, args.models_path, args.config_path, args.apply)


def init(directory: str | None) -> None:
    if directory is None:
        directory = ask_directory()
    shelf_root = Path(directory).expanduser().resolve()
    for path in ("models/gguf", "models/mlx", "models/safetensors", "provider-configs"):
        (shelf_root / path).mkdir(parents=True, exist_ok=True)

    config_path = shelf_root / "model-shelf.json"
    registry_path = shelf_root / "models" / "registry.json"
    if not config_path.exists():
        write_json(config_path, default_config())
    if not registry_path.exists():
        write_json(registry_path, {"schema_version": SCHEMA_VERSION, "models": []})

    print(f"Initialized Model Shelf at {shelf_root}")
    print(f"Next: cd {shlex.quote(str(shelf_root))}")


def add(repo: str, fmt: str, name: str | None, publisher: str | None, quant: str | None, disk: str | None, ram: str | None, file: str | None) -> None:
    shelf_root = find_shelf_root()
    model = model_from_repo(repo, fmt, name, publisher, quant, disk, ram, file)
    ensure_storage_path(shelf_root, model)

    registry = read_registry(shelf_root)
    registry["models"] = [entry for entry in registry["models"] if entry["id"] != model["id"]]
    registry["models"].append(model)
    write_json(shelf_root / "models" / "registry.json", registry)
    print(f"Registered {model['id']}")
    print(f"Path: {model['path']}")


def list_models() -> None:
    shelf_root = find_shelf_root()
    print_models(read_registry(shelf_root)["models"], shelf_root)


def search(query: str, fmt: str | None, install_selected: bool) -> None:
    shelf_root = find_shelf_root()
    matches = search_registry(shelf_root, query, fmt)
    print_models(matches, shelf_root)
    if install_selected:
        selected = choose_model(matches)
        if selected:
            install_model(shelf_root, selected, "hf_snapshot", yes=False, ask=True)


def resolve(query: str, runtime: str | None, fmt: str | None) -> None:
    shelf_root = find_shelf_root()
    matches = search_registry(shelf_root, query, fmt)
    candidates = []
    for model in matches:
        if runtime and runtime not in model.get("compatible_runtimes", []):
            continue
        candidates.append(
            {
                "id": model["id"],
                "format": model["format"],
                "publisher": model["publisher"],
                "path": model["path"],
                "installed": is_installed(shelf_root, model),
                "compatible_runtimes": model.get("compatible_runtimes", []),
            }
        )
    print(json.dumps({"query": query, "runtime": runtime, "format": fmt, "candidates": candidates}, indent=2))


def print_commands(query: str, fmt: str | None) -> None:
    shelf_root = find_shelf_root()
    model = require_one(search_registry(shelf_root, query, fmt), query)
    print(f"{model['id']} ({model['format']})")
    for section in ("download_commands", "launch_commands"):
        print(f"\n{section}")
        for name, command in model.get(section, {}).items():
            print(f"  {name}: {shlex.join(command)}")


def install(query: str, fmt: str | None, command_key: str, yes: bool) -> None:
    shelf_root = find_shelf_root()
    matches = search_registry(shelf_root, query, fmt)
    model = matches[0] if len(matches) == 1 else choose_model(matches)
    if not model:
        raise SystemExit("No model selected.")
    install_model(shelf_root, model, command_key, yes=yes, ask=not yes)


def install_model(shelf_root: Path, model: dict[str, Any], command_key: str, yes: bool, ask: bool) -> None:
    command = model.get("download_commands", {}).get(command_key)
    if not command:
        available = ", ".join(sorted(model.get("download_commands", {}).keys())) or "none"
        raise SystemExit(f"Download command not found: {command_key}. Available: {available}")

    print("Install plan:")
    print(f"  id: {model['id']}")
    print(f"  publisher: {model['publisher']}")
    print(f"  format: {model['format']}")
    print(f"  quant: {model.get('quantization') or 'none'}")
    print(f"  disk: {model.get('disk_size') or 'unknown'}")
    print(f"  approx ram: {model.get('approx_ram') or 'unknown'}")
    print(f"  target: {shelf_root / model['path']}")
    print(f"  command: {shlex.join(command)}")

    if not yes and ask and sys.stdin.isatty():
        answer = input("\nRun this install command now? [y/N] ").strip().lower()
        yes = answer in {"y", "yes"}

    if not yes:
        print("\nDry run only. Re-run with --yes or confirm interactively to install.")
        return

    subprocess.run(command, cwd=shelf_root, check=True)


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
        return {"path": path, "format": "env", "content": {"OLLAMA_MODELS": str(models_path / "gguf")}}
    if provider == "lmstudio":
        path = Path(config_path).expanduser() if config_path else generated / "lmstudio.json"
        return {"path": path, "format": "json", "content": {"modelsPath": str(models_path / "gguf")}}
    if provider == "mlx":
        path = Path(config_path).expanduser() if config_path else generated / "mlx.json"
        return {"path": path, "format": "json", "content": {"model_shelf_path": str(models_path), "mlx_models_path": str(models_path / "mlx")}}
    if provider == "llama.cpp":
        path = Path(config_path).expanduser() if config_path else generated / "llama-cpp.env"
        return {"path": path, "format": "env", "content": {"LLAMA_CPP_MODELS": str(models_path / "gguf")}}
    raise SystemExit(f"Unsupported provider: {provider}")


def model_from_repo(repo: str, fmt: str, name: str | None, publisher: str | None, quant: str | None, disk: str | None, ram: str | None, file: str | None) -> dict[str, Any]:
    repo_id = normalize_repo(repo)
    default_publisher, repo_name = split_model_id(repo_id)
    publisher = publisher or default_publisher
    name = name or repo_name
    path = format_path(fmt, publisher, name)
    expected_files = [file] if file else []
    return {
        "id": f"{fmt}:{publisher}/{name}",
        "name": name,
        "publisher": publisher,
        "source_repo": repo_id,
        "source_url": f"https://huggingface.co/{repo_id}",
        "format": fmt,
        "quantization": quant or infer_quantization(name),
        "disk_size": disk,
        "approx_ram": ram or infer_ram(name, quant or infer_quantization(name), fmt),
        "path": path,
        "expected_files": expected_files,
        "compatible_runtimes": compatible_runtimes(fmt),
        "download_commands": download_commands(repo_id, path, expected_files),
        "launch_commands": launch_commands(fmt, path, expected_files),
        "notes": "Registered as an installable artifact. Install commands are explicit and confirmed before execution.",
    }


def search_registry(shelf_root: Path, query: str, fmt: str | None) -> list[dict[str, Any]]:
    terms = [term.lower() for term in query.split() if term]
    models = read_registry(shelf_root)["models"]
    matches = []
    for model in models:
        if fmt and model.get("format") != fmt:
            continue
        haystack = " ".join(str(model.get(key, "")) for key in ("id", "name", "publisher", "source_repo", "format", "quantization")).lower()
        if all(term in haystack for term in terms):
            matches.append(model)
    return matches


def print_models(models: list[dict[str, Any]], shelf_root: Path) -> None:
    if not models:
        print("No models found.")
        return
    rows = []
    for idx, model in enumerate(models, start=1):
        rows.append(
            [
                str(idx),
                model["format"],
                model["publisher"],
                model["name"],
                model.get("quantization") or "-",
                model.get("disk_size") or "?",
                model.get("approx_ram") or "?",
                "yes" if is_installed(shelf_root, model) else "no",
            ]
        )
    print_table(["#", "format", "publisher", "model", "quant", "disk", "ram", "installed"], rows)


def choose_model(models: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not models:
        print("No models found.")
        return None
    if not sys.stdin.isatty():
        return models[0] if len(models) == 1 else None
    answer = input("\nSelect a model number to install, or press Enter to cancel: ").strip()
    if not answer:
        return None
    try:
        index = int(answer)
    except ValueError:
        raise SystemExit("Selection must be a number.")
    if index < 1 or index > len(models):
        raise SystemExit("Selection out of range.")
    return models[index - 1]


def require_one(models: list[dict[str, Any]], query: str) -> dict[str, Any]:
    if not models:
        raise SystemExit(f"No model found for: {query}")
    if len(models) > 1:
        print_models(models, find_shelf_root())
        raise SystemExit("More than one model matched. Narrow the query or pass --format.")
    return models[0]


def is_installed(shelf_root: Path, model: dict[str, Any]) -> bool:
    path = shelf_root / model["path"]
    expected_files = model.get("expected_files", [])
    if expected_files:
        return all((path / file).exists() for file in expected_files)
    return path.exists() and any(child.name != ".gitkeep" for child in path.iterdir())


def ensure_storage_path(shelf_root: Path, model: dict[str, Any]) -> None:
    path = shelf_root / model["path"]
    path.mkdir(parents=True, exist_ok=True)
    keep = path / ".gitkeep"
    if not keep.exists():
        keep.touch()


def format_path(fmt: str, publisher: str, name: str) -> str:
    return f"models/{fmt}/{publisher}/{name}"


def download_commands(repo_id: str, path: str, expected_files: list[str]) -> dict[str, list[str]]:
    command = ["huggingface-cli", "download", repo_id, "--local-dir", path]
    if expected_files:
        command = ["huggingface-cli", "download", repo_id, *expected_files, "--local-dir", path]
    return {
        "hf_snapshot": command,
        "git_lfs": ["git", "clone", f"https://huggingface.co/{repo_id}", path],
    }


def launch_commands(fmt: str, path: str, expected_files: list[str]) -> dict[str, list[str]]:
    if fmt == "gguf":
        model_path = f"{path}/{expected_files[0]}" if expected_files else path
        return {"llama_cpp": ["llama-server", "-m", model_path], "lmstudio": ["lms", "server", "start", "--model", model_path]}
    if fmt == "mlx":
        return {"mlx": ["mlx_lm.server", "--model", path]}
    return {"vllm": ["vllm", "serve", path], "sglang": ["python3", "-m", "sglang.launch_server", "--model-path", path]}


def compatible_runtimes(fmt: str) -> list[str]:
    if fmt == "gguf":
        return ["llama.cpp", "lm-studio", "ollama"]
    if fmt == "mlx":
        return ["mlx"]
    return ["vllm", "sglang"]


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


def default_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "shelf_root": "./models",
        "registry_path": "./models/registry.json",
        "formats": {"gguf": "models/gguf", "mlx": "models/mlx", "safetensors": "models/safetensors"},
        "policy": {"visible_models_folder": True, "require_confirmation_before_install": True},
    }


def normalize_repo(repo: str) -> str:
    return repo.removeprefix("https://huggingface.co/").strip("/")


def split_model_id(model_id: str) -> tuple[str, str]:
    parts = model_id.split("/")
    if len(parts) != 2:
        raise SystemExit(f"Expected Hugging Face repo as namespace/name, got: {model_id}")
    return parts[0], parts[1]


def infer_quantization(name: str) -> str | None:
    import re

    match = re.search(r"(Q\d(?:_[A-Z]+)*|\d+bit|FP\d+|BF16|FP16)", name, re.IGNORECASE)
    return match.group(1) if match else None


def infer_ram(name: str, quant: str | None, fmt: str) -> str | None:
    import re

    params = re.search(r"(\d+(?:\.\d+)?)B", name, re.IGNORECASE)
    if not params:
        return None
    billions = float(params.group(1))
    if quant and ("q4" in quant.lower() or "4bit" in quant.lower()):
        return f"~{max(1, round(billions * 0.7))} GB"
    if quant and "q3" in quant.lower():
        return f"~{max(1, round(billions * 0.55))} GB"
    if fmt == "safetensors":
        return f"~{round(billions * 2.2)} GB"
    return f"~{round(billions)} GB"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


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
