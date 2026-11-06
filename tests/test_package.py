import importlib.metadata

import inspect_evals_utils


def test_version_comes_from_metadata() -> None:
    assert inspect_evals_utils.__version__ == importlib.metadata.version("inspect-evals-utils")


def test_package_is_marked_typed() -> None:
    from importlib.resources import files

    assert files("inspect_evals_utils").joinpath("py.typed").is_file()
