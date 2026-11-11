# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- scriv-insert-here -->

## [0.3.0] - 2026-11-11

### Added

- `inspect_evals_utils.metadata.load_eval_version` reads the `version` field of the `eval.yaml` beside a task module. Call it as `EVAL_VERSION = load_eval_version(__file__)`. It takes a file path, so it also works when Inspect loads the module by path, as in `inspect eval src/my_eval/my_eval.py`. It raises `TypeError` when `version` is missing or is not a quoted string.

## [0.2.0] - 2026-11-06

### Added

- `inspect_evals_utils.scorers`, with the grader vocabulary moved from `inspect_evals.utils.scorers`: the `ScoreReason` constants and `GraderFailureMode`. `schema_tool_graded_scorer` stays in inspect_evals.
- `find_verdict` and `parse_verdict`, a parser for single-value free-text judge verdicts following the decisions on UKGovernmentBEIS/inspect_evals#2600: a labelled line or a leading token, a required `position`, no fallback verdict, and `VerdictParseFailure.unscored()` for the failure score. `verdict_instruction` and `VERDICT_LABEL` give the closing sentence for prompts an eval words itself.

## [0.1.0] - 2026-11-06

### Added

- First release: the runtime helpers from inspect_evals.utils (sample ids, Hugging Face wrappers with retries, cached dataset loaders, code-block extraction, message and prompt helpers, seeded shuffle), the shared cache path, and the inspect-evals-readmes README generator.
