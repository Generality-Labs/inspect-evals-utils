from pathlib import Path

import platformdirs
import pytest

from inspect_evals_utils.cache import cache_path


def test_default_is_platform_user_cache_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INSPECT_EVALS_CACHE_DIR", raising=False)
    assert cache_path() == Path(platformdirs.user_cache_dir("inspect_evals"))


def test_env_var_absolute_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSPECT_EVALS_CACHE_DIR", "/tmp/x")
    assert cache_path() == Path("/tmp/x")


def test_env_var_tilde_expands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSPECT_EVALS_CACHE_DIR", "~/x")
    assert cache_path() == Path.home() / "x"


def test_env_var_relative_path_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSPECT_EVALS_CACHE_DIR", "relative/x")
    with pytest.raises(ValueError, match="must be absolute or start with ~"):
        cache_path()


def test_error_names_the_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSPECT_EVALS_CACHE_DIR", "relative/x")
    with pytest.raises(ValueError, match="INSPECT_EVALS_CACHE_DIR"):
        cache_path()
