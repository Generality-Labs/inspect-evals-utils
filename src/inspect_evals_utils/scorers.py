"""Grader vocabulary and the free-text verdict parser for LLM-judged scorers.

The ``ScoreReason`` constants and ``GraderFailureMode`` were moved here from
``inspect_evals.utils.scorers`` so that a standalone eval can name a grader
failure the same way the registry does. ``schema_tool_graded_scorer`` stays in
inspect_evals: it uses private inspect_ai registry APIs.
"""

from collections.abc import Iterable
from dataclasses import dataclass
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


VerdictAnchor = Literal["label", "line"]
"""Where a verdict is read from: a labelled line, or the leading token of a line."""

VerdictPosition = Literal["first", "last"]
"""Which candidate line holds the verdict when the reply has more than one."""


@dataclass(frozen=True)
class VerdictMatch:
    """A verdict read from a judge's reply.

    Attributes:
        token: The matched token, spelled as the caller passed it in ``tokens``.
        start: Offset of the token in the original text.
        end: Offset just past the token in the original text.
        line: The line the verdict was read from, without its line ending.
    """

    token: str
    start: int
    end: int
    line: str


@dataclass(frozen=True)
class VerdictParseFailure:
    """A judge's reply that holds no usable verdict.

    Attributes:
        text: The reply as received.
        detail: Why no verdict was read, in a few words.
    """

    text: str
    detail: str


def _validate_tokens(tokens: Iterable[str]) -> list[str]:
    """Return the tokens in caller order, or raise ``ValueError`` for an unusable set."""
    token_list = list(tokens)
    if not token_list:
        raise ValueError("find_verdict needs at least one token")
    seen: dict[str, str] = {}
    for token in token_list:
        if not token:
            raise ValueError("a verdict token must not be empty")
        if any(char.isspace() for char in token):
            raise ValueError(f"a verdict token must not contain whitespace: {token!r}")
        key = token.casefold()
        if key in seen:
            raise ValueError(
                f"verdict tokens {seen[key]!r} and {token!r} collide case-insensitively"
            )
        seen[key] = token
    return token_list


def find_verdict(
    text: str,
    tokens: Iterable[str],
    *,
    anchor: VerdictAnchor,
    position: VerdictPosition,
    label: str | None = None,
    ignore_quoted: bool = False,
) -> VerdictMatch | VerdictParseFailure:
    """Read a single-value verdict from a judge's free-text reply.

    Args:
        text: The judge's reply.
        tokens: The verdicts the prompt offered, such as ``("yes", "no")``.
            Matched case-insensitively as whole words.
        anchor: ``"label"`` reads the token after ``label`` and a separator on
            the same line; ``"line"`` reads the token that leads a line.
        position: ``"first"`` or ``"last"`` candidate line. There is no default,
            because the position follows the prompt.
        label: The field name the prompt asks for, required with
            ``anchor="label"`` and not allowed otherwise.
        ignore_quoted: Skip lines that start with ``>``, for prompts that quote
            the model under test.

    Returns:
        A ``VerdictMatch``, or a ``VerdictParseFailure`` when the reply holds
        no usable verdict.

    Raises:
        ValueError: The token set or the label is unusable.
    """
    token_list = _validate_tokens(tokens)
    if anchor == "label":
        if not label:
            raise ValueError("anchor='label' needs a non-empty label")
    elif label is not None:
        raise ValueError("label is only used with anchor='label'")
    if not text.strip():
        return VerdictParseFailure(text, "empty reply")
    del token_list
    raise NotImplementedError
