import importlib
import sys

import pytest


def test_import_without_datasets_names_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [m for m in sys.modules if m == "datasets" or m.startswith("datasets.")]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "datasets", None)
    monkeypatch.delitem(sys.modules, "inspect_evals_utils.huggingface", raising=False)
    with pytest.raises(ImportError, match=r"inspect-evals-utils\[huggingface\]"):
        importlib.import_module("inspect_evals_utils.huggingface")
