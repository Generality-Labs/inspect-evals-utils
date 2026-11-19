### Fixed

- `find_verdict` and `parse_verdict` under `anchor="label"` now read the token only where it leads the value, after markdown emphasis or an opening quote mark. Before this, a token later in the value was read, so `ANSWER: not correct` gave `CORRECT` and `correct: I cannot say yes with confidence` gave `yes`. Both are now parse failures. Reported by av-writes-code on UKGovernmentBEIS/inspect_evals#2598.
