from __future__ import annotations

from model_shelf.cli import search_registry, search_huggingface, _is_hf_url, _infer_format_from_repo, normalize_repo


class TestLocalSearch:
    def test_search_by_name(self, shelf_with_registry) -> None:
        matches = search_registry(shelf_with_registry, "Qwen3-14B-GGUF", None)
        assert len(matches) == 1
        assert matches[0]["id"] == "gguf:Qwen/Qwen3-14B-GGUF"

    def test_search_by_format(self, shelf_with_registry) -> None:
        matches = search_registry(shelf_with_registry, "", "gguf")
        assert len(matches) == 1

    def test_search_nonexistent(self, shelf_with_registry) -> None:
        matches = search_registry(shelf_with_registry, "gemma", None)
        assert len(matches) == 0


class TestHFSearch:
    def test_search_hf_returns_results(self) -> None:
        results = search_huggingface("gemma", None)
        assert len(results) > 0
        # First result should have valid fields
        r = results[0]
        assert "/" in r["id"]  # format:publisher/name
        assert r["format"] in ("gguf", "mlx", "safetensors")

    def test_search_hf_filter_format(self) -> None:
        results = search_huggingface("llama", "gguf")
        assert len(results) > 0
        for r in results:
            assert r["format"] == "gguf"


class TestHelpers:
    def test_is_hf_url(self) -> None:
        assert _is_hf_url("https://huggingface.co/Qwen/Qwen3-14B")
        assert _is_hf_url("hf.co/Qwen/Qwen3")
        assert not _is_hf_url("qwen")
        assert not _is_hf_url("")

    def test_infer_format(self) -> None:
        assert _infer_format_from_repo("Qwen/Qwen3-14B-GGUF") == "gguf"
        assert _infer_format_from_repo("mlx-community/Qwen3-14B-4bit") == "mlx"
        assert _infer_format_from_repo("Qwen/Qwen3-14B") == "safetensors"

    def test_normalize_repo(self) -> None:
        assert normalize_repo("https://huggingface.co/Qwen/Qwen3-14B") == "Qwen/Qwen3-14B"
        assert normalize_repo("Qwen/Qwen3-14B") == "Qwen/Qwen3-14B"
