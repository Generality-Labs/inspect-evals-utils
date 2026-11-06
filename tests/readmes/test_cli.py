import shutil
from pathlib import Path

from inspect_evals_utils.readmes.cli import main

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_eval"


def _copy_fixture(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    shutil.copytree(FIXTURE, src / "sample_eval")
    return src


def test_check_exits_zero_when_current(tmp_path: Path) -> None:
    src = _copy_fixture(tmp_path)
    assert main(["generate", "--src", str(src)]) == 0
    before = (src / "sample_eval" / "README.md").read_bytes()
    assert main(["generate", "--check", "--src", str(src)]) == 0
    assert (src / "sample_eval" / "README.md").read_bytes() == before


def test_check_exits_one_when_stale_and_writes_nothing(tmp_path: Path) -> None:
    src = _copy_fixture(tmp_path)
    assert main(["generate", "--src", str(src)]) == 0
    readme = src / "sample_eval" / "README.md"
    text = readme.read_text()
    marker = "<!-- Usage: Automatically Generated -->"
    assert marker in text
    stale = text.replace(marker, marker + "\nstale line", 1)
    readme.write_text(stale)
    assert main(["generate", "--check", "--src", str(src)]) == 1
    assert readme.read_text() == stale


def test_add_section_subcommand(tmp_path: Path) -> None:
    src = _copy_fixture(tmp_path)
    readme = src / "sample_eval" / "README.md"
    text = readme.read_text()
    text = text.replace("<!-- Parameters: Automatically Generated -->\n", "").replace(
        "<!-- /Parameters: Automatically Generated -->\n", ""
    )
    readme.write_text(text)
    assert "Parameters: Automatically Generated" not in readme.read_text()
    assert (
        main(["add-section", "--src", str(src), "--key", "Parameters", "--insert-after", "Options"])
        == 0
    )
    new = readme.read_text()
    assert "<!-- Parameters: Automatically Generated -->" in new
    assert new.index("<!-- /Options: Automatically Generated -->") < new.index(
        "<!-- Parameters: Automatically Generated -->"
    )
