"""Grader vocabulary and the free-text verdict parser for LLM-judged scorers.

The ``ScoreReason`` constants and ``GraderFailureMode`` were moved here from
``inspect_evals.utils.scorers`` so that a standalone eval can name a grader
failure the same way the registry does. ``schema_tool_graded_scorer`` stays in
inspect_evals: it uses private inspect_ai registry APIs.
"""

from typing import Final, Literal

from inspect_ai.scorer import ScoreReason

GraderFailureMode = Literal[
    "grader_parse_failure",
    "grader_refusal",
    "grader_no_tool_call",
    "grader_schema_mismatch",
    "grader_invalid_grade",
]
"""How the grader failed, one level finer than ``ScoreReason``.

All of these are ``grader_failed`` upstream. We keep the distinction under our
own ``metadata["grader_failure_mode"]`` key so that a run can be partitioned by
failure mode without parsing prose out of ``explanation``, without claiming a
vocabulary inspect_ai has not adopted.
"""

# Named values of inspect_ai's ScoreReason, which ships the type but no constants.
# Logs written before Score.reason existed (inspect_ai < 0.3.261) carry these under
# metadata["unscored_reason"]; inspect_ai's read shim lifts that key into reason.
INVALID_RESPONSE_FORMAT: Final[ScoreReason] = "invalid_response_format"
REFUSAL: Final[ScoreReason] = "refusal"
NO_RESPONSE: Final[ScoreReason] = "no_response"
GRADER_FAILED: Final[ScoreReason] = "grader_failed"
SCORING_FAILED: Final[ScoreReason] = "scoring_failed"

GRADER_PARSE_FAILURE: Final[GraderFailureMode] = "grader_parse_failure"
GRADER_REFUSAL: Final[GraderFailureMode] = "grader_refusal"
GRADER_NO_TOOL_CALL: Final[GraderFailureMode] = "grader_no_tool_call"
GRADER_SCHEMA_MISMATCH: Final[GraderFailureMode] = "grader_schema_mismatch"
GRADER_INVALID_GRADE: Final[GraderFailureMode] = "grader_invalid_grade"
