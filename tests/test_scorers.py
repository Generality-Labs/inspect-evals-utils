"""Tests for the grader vocabulary in inspect_evals_utils.scorers."""

from typing import get_args

from inspect_ai.scorer import ScoreReason

from inspect_evals_utils import scorers


def test_score_reasons_are_inspect_values() -> None:
    allowed = set(get_args(ScoreReason))
    for name in (
        "INVALID_RESPONSE_FORMAT",
        "REFUSAL",
        "NO_RESPONSE",
        "GRADER_FAILED",
        "SCORING_FAILED",
    ):
        assert getattr(scorers, name) in allowed


def test_grader_failure_modes_match_literal() -> None:
    modes = set(get_args(scorers.GraderFailureMode))
    constants = {
        scorers.GRADER_PARSE_FAILURE,
        scorers.GRADER_REFUSAL,
        scorers.GRADER_NO_TOOL_CALL,
        scorers.GRADER_SCHEMA_MISMATCH,
        scorers.GRADER_INVALID_GRADE,
    }
    assert constants == modes
