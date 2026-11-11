"""Read an eval's eval.yaml file."""

from os import PathLike
from pathlib import Path

import yaml


def load_eval_version(module_file: str | PathLike[str]) -> str:
    """Return the `version` field of the eval.yaml beside a module.

    Call it from the module that defines the eval's tasks:

        EVAL_VERSION = load_eval_version(__file__)

    The argument is a file path and not a package name because Inspect also loads
    a task module by file path (`inspect eval src/my_eval/my_eval.py`), and
    `__package__` does not name the package there.

    Args:
        module_file: Path of a file in the directory that holds eval.yaml.

    Returns:
        The version string, for example "1-A".

    Raises:
        TypeError: eval.yaml has no `version`, or YAML read it as a number.
    """
    eval_yaml = Path(module_file).parent / "eval.yaml"
    version = yaml.safe_load(eval_yaml.read_text(encoding="utf-8")).get("version")
    if not isinstance(version, str):
        raise TypeError(
            f'{eval_yaml}: `version` must be a quoted string such as "1-A", found {version!r}'
        )
    return version
