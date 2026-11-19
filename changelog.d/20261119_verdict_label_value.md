### Fixed

- `find_verdict` and `parse_verdict` under `anchor="label"` now read the token only where it leads the value, after markdown emphasis or an opening quote mark. Before this, a token later in the value was read, so `ANSWER: not correct` gave `CORRECT` and `correct: I cannot say yes with confidence` gave `yes`. Both are now parse failures. Reported by av-writes-code on UKGovernmentBEIS/inspect_evals#2598.
- Under `anchor="label"`, the closing tag of the `<label>...</label>` form no longer counts as a second verdict, so `<correct>incorrect</correct>` with tokens `CORRECT` and `INCORRECT` reads `INCORRECT` instead of failing.
- A token that starts or ends with a digit is no longer read out of a longer number. `Rating: 3.7`, `Rating: -1`, `Score: 0.5`, `Rating: 4/5`, `Rating: 5/5` and `Rating: 3-4` are parse failures for single-digit tokens. Before this, the first three read `3`, `1` and `0`, and `Rating: 5/5` read `5`.
- A token joined to a word by an underscore (`not_correct`, `no_answer`) is no longer read as a whole word. Underscore emphasis around a token (`_yes_`, `__no__`) still reads.
