from __future__ import annotations

import json
from pathlib import Path

from model_shelf.cli import (
    install,
    model_from_repo,
    format_path,
    download_commands,
    launch_commands,
    compatible_runtimes,
)


class TestInstallHelpers:
    def test_model_from_repo_no_models_prefix(self) -> None:
        m = model_from_repo("Qwen/Qwen3-14B-GGUF", "gguf", None, None, None, None, None, None)
        assert m["path"] == "gguf/Qwen/Qwen3-14B-GGUF"  # no models/ prefix
        assert m["id"] == "gguf:Qwen/Qwen3-14B-GGUF"

    def test_download_commands_no_models_prefix(self) -> None:
        cmds = download_commands("Qwen/Qwen3-14B-GGUF", "gguf/Qwen/Qwen3-14B-GGUF", [])
        hf = cmds["hf_snapshot"]
        assert hf[0] == "huggingface-cli"
        # --local-dir should NOT have models/ prefix
        local_dir_idx = hf.index("--local-dir") + 1
        assert hf[local_dir_idx] == "gguf/Qwen/Qwen3-14B-GGUF"

    def test_git_lfs_no_models_prefix(self) -> None:
        cmds = download_commands("Qwen/Qwen3-14B-GGUF", "gguf/Qwen/Qwen3-14B-GGUF", [])
        git = cmds["git_lfs"]
        assert git[0] == "git"
        assert git[-1] == "gguf/Qwen/Qwen3-14B-GGUF"

    def test_launch_commands_no_models_prefix(self) -> None:
        cmds = launch_commands("gguf", "gguf/Qwen/Qwen3-14B-GGUF", ["Qwen3-14B-Q4_K_M.gguf"])
        llama = cmds["llama_cpp"]
        model_path = llama[llama.index("-m") + 1]
        assert model_path == "gguf/Qwen/Qwen3-14B-GGUF/Qwen3-14B-Q4_K_M.gguf"

    def test_compatible_runtimes(self) -> None:
        assert "llama.cpp" in compatible_runtimes("gguf")
        assert "mlx" in compatible_runtimes("mlx")
        assert "vllm" in compatible_runtimes("safetensors")


class TestFormatPath:
    def test_flat_path(self) -> None:
        assert format_path("gguf", "Qwen", "Qwen3-14B-GGUF") == "gguf/Qwen/Qwen3-14B-GGUF"
        assert format_path("mlx", "mlx-community", "Qwen3-14B-4bit") == "mlx/mlx-community/Qwen3-14B-4bit"
        assert format_path("safetensors", "Qwen", "Qwen3-14B") == "safetensors/Qwen/Qwen3-14B"
