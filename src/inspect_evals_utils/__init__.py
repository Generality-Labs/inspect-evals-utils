"""Runtime helpers for Inspect AI evaluations: dataset loading with retries, sample ids, prompts and README generation"""

from importlib.metadata import PackageNotFoundError, version

# The version is set once, in pyproject.toml; this reads it back from the
# installed package metadata.
try:
    __version__ = version("inspect-evals-utils")
except PackageNotFoundError:  # a source tree that was never installed
    __version__ = "unknown"
