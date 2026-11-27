"""The documentation site: every public module gets a page, and the build publishes the generated pages and their Markdown.

Runs where the docs group is installed: docs.yml, or `uv run --group docs pytest tests/test_docs.py`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytest.importorskip("griffe")
pytest.importorskip("mkdocs")

REPO = Path(__file__).resolve().parents[1]


def _load_hooks() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mkdocs_hooks", REPO / "mkdocs_hooks.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hooks = _load_hooks()


def test_every_public_module_has_a_reference_page() -> None:
    pages = set(hooks.site_files(REPO))
    for path in (REPO / "src" / "inspect_evals_utils").rglob("*.py"):
        if path.name.startswith("_"):
            continue
        relative = path.relative_to(REPO / "src" / "inspect_evals_utils").with_suffix(".md")
        assert f"reference/{relative.as_posix()}" in pages


def test_every_reference_module_has_a_summary() -> None:
    """The reference index and llms.txt describe each module by its docstring's first line."""
    for module in hooks.reference_modules(hooks.load_package(REPO)):
        assert hooks.summary(module), f"{module.path} has no module docstring"


def test_generated_pages_are_not_committed() -> None:
    for path in hooks.site_files(REPO):
        assert not (REPO / "docs" / path).exists(), f"docs/{path} is built with the site"


def test_site_index_links_modules_and_rewrites_repository_links(tmp_path: Path) -> None:
    package = hooks.load_package(REPO)
    modules = hooks.reference_modules(package)
    readme = (
        "# x\n\n- `inspect_evals_utils.ids`: ids.\n- `inspect_evals_utils.nope`: missing.\n\n"
        "See [release](RELEASING.md), [ext](https://example.test/a) and [same](#anchor).\n"
    )
    index = hooks.site_index(readme, tmp_path, modules)
    assert index.startswith("# x\n")
    assert hooks.GENERATED_NOTE in index
    assert "- [`inspect_evals_utils.ids`](reference/ids.md)" in index
    assert "- `inspect_evals_utils.nope`" in index
    assert f"[release]({hooks.REPO_BLOB}RELEASING.md)" in index
    assert "[ext](https://example.test/a)" in index
    assert "[same](#anchor)" in index


def test_module_markdown_renders_signatures_and_docstrings() -> None:
    package = hooks.load_package(REPO)
    datasets = hooks.module_markdown(package["datasets"])
    # The stub's signature, not the decorated assignment that replaces it at runtime.
    assert "def load_json_dataset(file_path: str, eval_name: str," in datasets
    assert "**reader_kwargs: Any) -> Dataset" in datasets
    assert "Load a JSON or JSONL dataset with caching support for remote URLs." in datasets
    scorers = hooks.module_markdown(package["scorers"])
    assert "## `GRADER_FAILED`" in scorers  # documented by a comment, still public
    assert "### `unscored`" in scorers
    assert "_validate_tokens" not in scorers
    assert "## `T`" not in scorers


def test_llms_txt_lists_every_module_as_raw_markdown() -> None:
    text = hooks.site_files(REPO)["llms.txt"]
    assert text.startswith("# inspect-evals-utils\n\n> ")
    for module in hooks.reference_modules(hooks.load_package(REPO)):
        assert f"[{module.path}]({hooks.SITE_URL}{hooks.page_path(module)})" in text
    assert "llms-full.txt" in text


def test_site_url_matches_mkdocs() -> None:
    import yaml

    config = yaml.safe_load((REPO / "mkdocs.yml").read_text(encoding="utf-8"))
    assert config["site_url"] == hooks.SITE_URL


def test_build_publishes_markdown_beside_each_page(tmp_path: Path) -> None:
    from mkdocs.commands.build import build
    from mkdocs.config import load_config  # pyright: ignore[reportUnknownVariableType]

    build(load_config(config_file=str(REPO / "mkdocs.yml"), site_dir=str(tmp_path)))
    files = hooks.site_files(REPO)
    assert (tmp_path / "llms.txt").read_text(encoding="utf-8") == files["llms.txt"]
    assert (tmp_path / "llms-full.txt").read_text(encoding="utf-8") == files["llms-full.txt"]
    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert index.startswith("# inspect-evals-utils\n")  # front matter stripped
    assert hooks.GENERATED_NOTE not in index
    ids = (tmp_path / "reference" / "ids.md").read_text(encoding="utf-8")
    assert ids == (tmp_path / "reference" / "ids" / "index.md").read_text(encoding="utf-8")
    assert ids.startswith("# `inspect_evals_utils.ids`")
    assert ":::" not in ids
    assert "def create_stable_id(" in ids
    assert (tmp_path / "reference" / "ids" / "index.html").exists()
    assert (tmp_path / "robots.txt").exists()
