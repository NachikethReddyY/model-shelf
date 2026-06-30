from __future__ import annotations

from pathlib import Path

from model_shelf.cli import (
    default_config,
    find_shelf_root,
    format_path,
    init,
    read_registry,
)


class TestInit:
    def test_init_creates_flat_layout(self, tmp_shelf: Path) -> None:
        """Verify init creates dirs directly in shelf root (no models/ wrapper)."""
        assert (tmp_shelf / "model-shelf.json").exists()
        assert (tmp_shelf / "registry.json").exists()
        assert (tmp_shelf / "gguf").is_dir()
        assert (tmp_shelf / "mlx").is_dir()
        assert (tmp_shelf / "safetensors").is_dir()
        assert (tmp_shelf / "provider-configs").is_dir()
        # No models/ wrapper
        assert not (tmp_shelf / "models").exists()

    def test_init_auto_subfolder(self) -> None:
        """Given a parent path, init creates model-shelf subfolder."""
        import tempfile, os, shutil
        tmp = Path(tempfile.mkdtemp())
        parent = tmp / "somewhere"
        parent.mkdir()
        init(str(parent))
        # Should create somewhere/model-shelf/
        assert (parent / "model-shelf" / "model-shelf.json").exists()
        shutil.rmtree(tmp)

    def test_init_no_double_nesting(self) -> None:
        """Give a path that already ends in model-shelf, do not nest again."""
        import tempfile, os, shutil
        tmp = Path(tempfile.mkdtemp())
        shelf = tmp / "model-shelf"
        init(str(shelf))
        # model-shelf.json should be at shelf/, not shelf/model-shelf/
        assert (shelf / "model-shelf.json").exists()
        assert not (shelf / "model-shelf" / "model-shelf.json").exists()
        shutil.rmtree(tmp)

    def test_init_creates_config(self, tmp_shelf: Path) -> None:
        """model-shelf.json has correct flat paths."""
        cfg = default_config()
        assert cfg["shelf_root"] == "."
        assert cfg["registry_path"] == "./registry.json"
        assert cfg["formats"]["gguf"] == "gguf"
        assert cfg["formats"]["mlx"] == "mlx"
        assert cfg["formats"]["safetensors"] == "safetensors"

    def test_init_creates_empty_registry(self, tmp_shelf: Path) -> None:
        reg = read_registry(tmp_shelf)
        assert reg["schema_version"] == "0.2"
        assert reg["models"] == []


class TestFindShelfRoot:
    def test_find_from_inside(self, tmp_shelf: Path) -> None:
        root = find_shelf_root()
        assert root == tmp_shelf.resolve()

    def test_find_from_subdir(self, tmp_shelf: Path) -> None:
        """Walking up from gguf/ still finds shelf."""
        (tmp_shelf / "gguf" / "some-model").mkdir(parents=True, exist_ok=True)
        import os
        old = Path.cwd()
        os.chdir(str(tmp_shelf / "gguf" / "some-model"))
        try:
            root = find_shelf_root()
            assert root == tmp_shelf.resolve()
        finally:
            os.chdir(str(old))


class TestFormatPath:
    def test_no_models_prefix(self) -> None:
        assert format_path("gguf", "Qwen", "Qwen3-14B-GGUF") == "gguf/Qwen/Qwen3-14B-GGUF"
        assert format_path("mlx", "mlx-community", "Qwen3-14B-4bit") == "mlx/mlx-community/Qwen3-14B-4bit"
        assert format_path("safetensors", "Qwen", "Qwen3-14B") == "safetensors/Qwen/Qwen3-14B"
