# inspect-evals-utils

Runtime helpers for [Inspect AI](https://inspect.aisi.org.uk/) evaluations, moved out of [inspect_evals](https://github.com/UKGovernmentBEIS/inspect_evals) so that a standalone eval repo can use them without depending on the whole registry. inspect_evals will depend on this package and re-export everything under its old `inspect_evals.utils` paths, so existing imports keep working.

## Install

```bash
uv add inspect-evals-utils
# or, for the Hugging Face wrappers:
uv add "inspect-evals-utils[huggingface]"
```

## Modules

- `inspect_evals_utils.ids`: `create_stable_id`, `filter_duplicate_ids`, `drop_known_broken`, `require_optional_dependency`, `DuplicateIdError`, `KnownBrokenSampleError`.
- `inspect_evals_utils.datasets`: `load_json_dataset` and `load_csv_dataset`, which cache remote files and retry transient errors, plus `cache_dataset_loader`, `is_remote_url`, `get_cached_fname`, `is_transient_error`.
- `inspect_evals_utils.huggingface` (needs the `huggingface` extra): `hf_dataset`, `load_dataset`, `get_dataset_split_names`, `snapshot_download`, `hf_hub_download`, `sentence_transformer`, `transformers_pipeline`, `auto_model_for_sequence_classification`, `auto_tokenizer`. Each retries on rate limits and transient errors and requires a `revision=` keyword, so datasets are pinned. `set_hf_call_recorder` and `set_backoff_recorder` register callbacks that test sessions use to count calls and retries; both default to doing nothing.
- `inspect_evals_utils.code`: `extract_code_blocks`, `extract_code_block`, `strip_json_fence`, `defines`.
- `inspect_evals_utils.messages`: `message_content_text`, `reasoning_to_text`.
- `inspect_evals_utils.prompts`: `Prompt`, a dataclass recording a prompt with its provenance.
- `inspect_evals_utils.shuffle`: `shuffle_and_seed`.
- `inspect_evals_utils.cache`: `cache_path()` and `INSPECT_EVALS_CACHE_PATH`.

The most-used names are also importable from the top level, for example `from inspect_evals_utils import create_stable_id`. The Hugging Face module is not, so the base package imports without the extra.

## Cache directory

Downloads land in `INSPECT_EVALS_CACHE_PATH`, which defaults to the platform user cache directory for `inspect_evals`. Set `INSPECT_EVALS_CACHE_DIR` to move it or point it at a pre-populated directory. It must be absolute or start with `~`, and it is read once when the package is imported. inspect_evals reads the same variable and default, so one machine has one cache.

## README generation

The `inspect-evals-readmes` command rewrites the generated sections of each eval's README (Contributors, Usage, Options and Parameters) from its `eval.yaml` and `@task` signatures. It finds evals as `<src>/<eval>/eval.yaml` (default `src`), imports each package to read the task parameters, and writes between the `<!-- Usage: Automatically Generated -->` style tag pairs.

```bash
uv run inspect-evals-readmes generate                      # rewrite the sections
uv run inspect-evals-readmes generate --check              # exit 1 if any README is out of date; writes nothing
uv run inspect-evals-readmes generate --eval my_eval --create-missing
uv run inspect-evals-readmes add-section --key Parameters --insert-after Options
```

`add-section` inserts a missing tag pair after the first listed section it finds, or at the end of the file.

## Private inspect_ai APIs

`inspect_evals_utils.datasets` uses `inspect_ai._util.file.file` to open local and remote files through one interface. There is no public equivalent yet, so a future inspect_ai release could break it.

## Development

```bash
uv sync
uv run pre-commit install   # optional: run the lint stack on every commit
uv run pytest
uv run basedpyright src
```

Each pull request adds a changelog fragment rather than editing `CHANGELOG.md`, so concurrent PRs don't conflict. Run `uv run scriv create`, uncomment the sections that apply in the new file under `changelog.d/`, and commit it with the change, or delete it if the change needs no entry. To release, run the **Prepare release** workflow from the Actions tab. It bumps `version` in `pyproject.toml`, collects the fragments into `CHANGELOG.md`, and opens a release pull request, whose CI starts once you click **Approve workflows to run** on it; merging it tags the release. It needs _Settings → Actions → General_ → **Allow GitHub Actions to create and approve pull requests**. By hand, the same is `uv version --bump minor` and `uv run scriv collect`.

Linting (ruff, [zizmor](https://docs.zizmor.sh/), mdformat) runs via [pre-commit](https://pre-commit.com); CI runs the same stack plus basedpyright and pytest via the shared [`python-ci`](https://github.com/Generality-Labs/python-project-template) reusable workflow.

## Releasing

See [RELEASING.md](RELEASING.md).
