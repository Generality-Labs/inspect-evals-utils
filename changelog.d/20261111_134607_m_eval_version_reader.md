### Added

- `inspect_evals_utils.metadata.load_eval_version` reads the `version` field of the `eval.yaml` beside a task module. Call it as `EVAL_VERSION = load_eval_version(__file__)`. It takes a file path, so it also works when Inspect loads the module by path, as in `inspect eval src/my_eval/my_eval.py`. It raises `TypeError` when `version` is missing or is not a quoted string.
