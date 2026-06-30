from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterator

import pytest

from model_shelf.cli import init, default_config, write_json, SCHEMA_VERSION


@pytest.fixture
def tmp_shelf() -> Iterator[Path]:
    """Create a fresh Model Shelf in a temp dir and cd into it."""
    tmp = Path(tempfile.mkdtemp())
    shelf = tmp / "model-shelf"
    init(str(tmp))
    old_cwd = Path.cwd()
    import os
    os.chdir(str(shelf))
    yield shelf
    os.chdir(str(old_cwd))
    shutil.rmtree(tmp)


@pytest.fixture
def shelf_with_registry(tmp_shelf: Path) -> Path:
    """Like tmp_shelf but with a pre-populated registry."""
    models = [
        {
            "id": "gguf:Qwen/Qwen3-14B-GGUF",
            "name": "Qwen3-14B-GGUF",
            "publisher": "Qwen",
            "source_repo": "Qwen/Qwen3-14B-GGUF",
            "source_url": "https://huggingface.co/Qwen/Qwen3-14B-GGUF",
            "format": "gguf",
            "quantization": "Q4_K_M",
            "disk_size": "~9 GB",
            "approx_ram": "~10 GB",
            "path": "gguf/Qwen/Qwen3-14B-GGUF",
            "expected_files": [],
            "compatible_runtimes": ["llama.cpp", "lm-studio", "ollama"],
            "download_commands": {"hf_snapshot": ["huggingface-cli", "download", "Qwen/Qwen3-14B-GGUF", "--local-dir", "gguf/Qwen/Qwen3-14B-GGUF"]},
            "launch_commands": {"llama_cpp": ["llama-server", "-m", "gguf/Qwen/Qwen3-14B-GGUF"]},
            "notes": "",
        }
    ]
    write_json(tmp_shelf / "registry.json", {"schema_version": SCHEMA_VERSION, "models": models})
    return tmp_shelf
