import importlib
import sys

import pytest

EXPORTS = {
    "create_stable_id": "ids",
    "filter_duplicate_ids": "ids",
    "drop_known_broken": "ids",
    "require_optional_dependency": "ids",
    "DuplicateIdError": "ids",
    "KnownBrokenSampleError": "ids",
    "load_json_dataset": "datasets",
    "load_csv_dataset": "datasets",
    "message_content_text": "messages",
    "reasoning_to_text": "messages",
    "Prompt": "prompts",
    "shuffle_and_seed": "shuffle",
    "INSPECT_EVALS_CACHE_PATH": "cache",
}


@pytest.mark.parametrize(("name", "module"), EXPORTS.items())
def test_top_level_exports(name: str, module: str) -> None:
    import inspect_evals_utils

    assert name in inspect_evals_utils.__all__
    target = importlib.import_module(f"inspect_evals_utils.{module}")
    assert getattr(inspect_evals_utils, name) is getattr(target, name)


def test_top_level_import_does_not_need_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [m for m in sys.modules if m == "datasets" or m.startswith("datasets.")]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "datasets", None)
    for name in [m for m in sys.modules if m.startswith("inspect_evals_utils")]:
        monkeypatch.delitem(sys.modules, name)
    module = importlib.import_module("inspect_evals_utils")
    assert "create_stable_id" in module.__all__
