"""Grader vocabulary and the free-text verdict parser for LLM-judged scorers.

The ``ScoreReason`` constants and ``GraderFailureMode`` were moved here from
``inspect_evals.utils.scorers`` so that a standalone eval can name a grader
failure the same way the registry does. ``schema_tool_graded_scorer`` stays in
inspect_evals: it uses private inspect_ai registry APIs.
"""

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Final, Literal, TypeVar

from inspect_ai.scorer import Score, ScoreReason

T = TypeVar("T")

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

    def unscored(self, **kwargs: Any) -> Score:
        """Build the unscored ``Score`` for this failure.

        The score has ``reason`` ``grader_failed``,
        ``metadata["grader_failure_mode"]`` ``grader_parse_failure`` and the
        reply under ``metadata["grader_payload"]["grader_response"]``, the keys
        inspect_evals' ``schema_tool_graded_scorer`` records. Keyword arguments
        pass through to ``Score.unscored``; a ``metadata`` argument is merged
        over those defaults.
        """
        metadata: dict[str, Any] = {
            "grader_failure_mode": GRADER_PARSE_FAILURE,
            "grader_payload": {"grader_response": self.text},
        }
        metadata.update(kwargs.pop("metadata", None) or {})
        kwargs.setdefault("explanation", f"{self.detail}: {self.text}")
        return Score.unscored(reason=GRADER_FAILED, metadata=metadata, **kwargs)


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


# Horizontal whitespace, including the non-breaking and zero-width characters a judge
# can emit around a separator.
_HSPACE = "[ \t\u00a0\u200b\u200c\u200d\ufeff]"
_EMPHASIS = r"[*_`]"
# What may stand before a label or a leading token: list markers, a block quote, a
# heading and markdown emphasis, in any mix. A bullet needs a space after it so that
# the ``**`` of bold text is read as emphasis rather than as a bullet.
_PREFIX = (
    rf"(?:{_HSPACE}*(?:[-*+]{_HSPACE}+|\d+[.)]{_HSPACE}+|>{_HSPACE}*|#+{_HSPACE}+"
    rf"|{_EMPHASIS}+))*{_HSPACE}*"
)
# Between a label and its token: optional emphasis either side of the separator.
_SEPARATOR = rf"{_EMPHASIS}*{_HSPACE}*[:=>]{_HSPACE}*{_EMPHASIS}*{_HSPACE}*"
_PREFIX_REGEX = re.compile(rf"^{_PREFIX}")
_LINE_ENDING = re.compile(r"\r\n|\r|\n")
_QUOTED = re.compile(rf"^{_HSPACE}*>")


def _iter_lines(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield ``(start, end, line)`` for each line, with offsets into ``text``.

    The line ending is not part of ``line``, so CRLF text needs no rewriting
    and offsets index the caller's string.
    """
    start = 0
    for ending in _LINE_ENDING.finditer(text):
        yield start, ending.start(), text[start : ending.start()]
        start = ending.end()
    if start < len(text):
        yield start, len(text), text[start:]


def _token_regex(tokens: list[str]) -> re.Pattern[str]:
    """Match any token as a whole word, case-insensitively, longest token first."""
    alternatives = "|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)


def _label_regex(label: str) -> re.Pattern[str]:
    """Match a line's prefix, the label and its separator, up to where the token starts."""
    return re.compile(
        rf"^{_PREFIX}<?{_HSPACE}*{re.escape(label)}{_HSPACE}*{_SEPARATOR}", re.IGNORECASE
    )


def _read_token(
    tokens: list[str],
    token_regex: re.Pattern[str],
    line_start: int,
    line: str,
    from_offset: int,
    detail_when_missing: str,
) -> VerdictMatch | VerdictParseFailure:
    """Read the one verdict on a candidate line, scanning from ``from_offset``.

    A line that names two different tokens is a failure: ``Answer: yes or no``
    carries no verdict, and reading its first token would hide that.
    """
    spelled = {t.casefold(): t for t in tokens}
    matches = list(token_regex.finditer(line, from_offset))
    distinct = {m.group(0).casefold() for m in matches}
    if not distinct:
        return VerdictParseFailure(line, detail_when_missing)
    if len(distinct) > 1:
        return VerdictParseFailure(line, "two verdicts on one line")
    first = matches[0]
    return VerdictMatch(
        token=spelled[first.group(0).casefold()],
        start=line_start + first.start(),
        end=line_start + first.end(),
        line=line,
    )


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

    lines = [
        (start, end, line)
        for start, end, line in _iter_lines(text)
        if not (ignore_quoted and _QUOTED.match(line))
    ]
    token_regex = _token_regex(token_list)

    if anchor == "label":
        assert label is not None
        label_regex = _label_regex(label)
        labelled = [
            (start, line, found.end())
            for start, _end, line in lines
            if (found := label_regex.match(line)) is not None
        ]
        if not labelled:
            return VerdictParseFailure(text, "no labelled line")
        start, line, token_from = labelled[0] if position == "first" else labelled[-1]
        result = _read_token(
            token_list, token_regex, start, line, token_from, "no verdict on the labelled line"
        )
    else:
        candidates = [(start, line) for start, _end, line in lines if line.strip()]
        if not candidates:
            return VerdictParseFailure(text, "no verdict line")
        start, line = candidates[0] if position == "first" else candidates[-1]
        prefix_end = _PREFIX_REGEX.match(line).end()  # type: ignore[union-attr]
        if token_regex.match(line, prefix_end) is None:
            return VerdictParseFailure(text, "no leading verdict")
        result = _read_token(token_list, token_regex, start, line, 0, "no leading verdict")
    if isinstance(result, VerdictParseFailure):
        return VerdictParseFailure(text, result.detail)
    return result


def parse_verdict(
    text: str,
    tokens: Mapping[str, T],
    *,
    anchor: VerdictAnchor,
    position: VerdictPosition,
    label: str | None = None,
    ignore_quoted: bool = False,
) -> T | VerdictParseFailure:
    """Read a single-value verdict from a judge's reply and map it to a value.

    This is for a verdict that is one value: yes or no, a letter, one number.
    A judge that returns several fields (a rubric, a verdict plus a
    confidence) should use a structured grader, such as a tool call with a
    schema, rather than this parser.

    On a ``VerdictParseFailure``, a scorer that returns one value returns
    ``failure.unscored()``. A scorer whose ``Score.value`` is a dict fed by
    several judges sets this judge's key to ``nan`` and keeps the other keys.
    Bounded, grader-only retries for a format failure are acceptable before
    unscoring, and a retry must not be served from the cache.

    Args:
        text: The judge's reply.
        tokens: Each verdict the prompt offered, mapped to the value to return.
        anchor: As for ``find_verdict``.
        position: As for ``find_verdict``.
        label: As for ``find_verdict``.
        ignore_quoted: As for ``find_verdict``.

    Returns:
        The value mapped from the matched token, or a ``VerdictParseFailure``.
    """
    match = find_verdict(
        text,
        tokens.keys(),
        anchor=anchor,
        position=position,
        label=label,
        ignore_quoted=ignore_quoted,
    )
    if isinstance(match, VerdictParseFailure):
        return match
    return tokens[match.token]
