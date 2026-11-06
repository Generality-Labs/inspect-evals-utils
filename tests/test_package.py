import importlib.metadata

import inspect_evals_utils


def test_version_comes_from_metadata() -> None:
    assert inspect_evals_utils.__version__ == importlib.metadata.version("inspect-evals-utils")
