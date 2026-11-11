import runpy
from pathlib import Path

import pytest

from inspect_evals_utils.metadata import load_eval_version

TASK_MODULE = """
from inspect_evals_utils.metadata import load_eval_version

EVAL_VERSION = load_eval_version(__file__)
"""


@pytest.fixture
def eval_dir(tmp_path: Path) -> Path:
    path = tmp_path / "my_eval"
    path.mkdir()
    (path / "eval.yaml").write_text('title: "My eval"\nversion: "2-B"\n', encoding="utf-8")
    (path / "my_eval.py").write_text(TASK_MODULE, encoding="utf-8")
    return path


def test_reads_the_version_next_to_the_given_file(eval_dir: Path) -> None:
    assert load_eval_version(eval_dir / "my_eval.py") == "2-B"


def test_accepts_a_string_path(eval_dir: Path) -> None:
    assert load_eval_version(str(eval_dir / "my_eval.py")) == "2-B"


def test_works_in_a_module_loaded_by_file_path(eval_dir: Path) -> None:
    # `inspect eval path/to/task.py` loads the module this way, with no package.
    namespace = runpy.run_path(str(eval_dir / "my_eval.py"))
    assert namespace["__package__"] in (None, "")
    assert namespace["EVAL_VERSION"] == "2-B"


@pytest.mark.parametrize(
    ("yaml_text", "found"),
    [("version: 1.10\n", "1.1"), ("version: 2\n", "2"), ("title: no version\n", "None")],
)
def test_rejects_a_version_that_is_not_a_string(eval_dir: Path, yaml_text: str, found: str) -> None:
    eval_yaml = eval_dir / "eval.yaml"
    eval_yaml.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(TypeError) as excinfo:
        load_eval_version(eval_dir / "my_eval.py")
    assert str(eval_yaml) in str(excinfo.value)
    assert f"found {found}" in str(excinfo.value)
