"""Runtime helpers for Inspect AI evaluations: dataset loading with retries, sample ids, prompts and README generation."""

from importlib.metadata import PackageNotFoundError, version

from inspect_evals_utils.cache import INSPECT_EVALS_CACHE_PATH
from inspect_evals_utils.datasets import load_csv_dataset, load_json_dataset
from inspect_evals_utils.ids import (
    DuplicateIdError,
    KnownBrokenSampleError,
    create_stable_id,
    drop_known_broken,
    filter_duplicate_ids,
    require_optional_dependency,
)
from inspect_evals_utils.messages import message_content_text, reasoning_to_text
from inspect_evals_utils.prompts import Prompt
from inspect_evals_utils.scorers import (
    GRADER_FAILED,
    GRADER_PARSE_FAILURE,
    GraderFailureMode,
)
from inspect_evals_utils.shuffle import shuffle_and_seed

# The version is set once, in pyproject.toml; this reads it back from the
# installed package metadata.
try:
    __version__ = version("inspect-evals-utils")
except PackageNotFoundError:  # a source tree that was never installed
    __version__ = "unknown"

# inspect_evals_utils.huggingface is not imported here: it needs the
# huggingface extra, and the base package must import without it.
__all__ = [
    "GRADER_FAILED",
    "GRADER_PARSE_FAILURE",
    "INSPECT_EVALS_CACHE_PATH",
    "DuplicateIdError",
    "GraderFailureMode",
    "KnownBrokenSampleError",
    "Prompt",
    "__version__",
    "create_stable_id",
    "drop_known_broken",
    "filter_duplicate_ids",
    "load_csv_dataset",
    "load_json_dataset",
    "message_content_text",
    "reasoning_to_text",
    "require_optional_dependency",
    "shuffle_and_seed",
]
