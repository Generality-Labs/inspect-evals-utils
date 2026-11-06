"""Tests for the free-text verdict parser in inspect_evals_utils.scorers."""

import math
import time

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT

from inspect_evals_utils.scorers import (
    GRADER_FAILED,
    GRADER_PARSE_FAILURE,
    VERDICT_LABEL,
    VerdictMatch,
    VerdictParseFailure,
    find_verdict,
    parse_verdict,
    verdict_instruction,
)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"tokens": [], "anchor": "label", "label": "answer"}, "at least one token"),
        ({"tokens": ["yes", ""], "anchor": "label", "label": "answer"}, "empty"),
        ({"tokens": ["yes", "not sure"], "anchor": "label", "label": "answer"}, "whitespace"),
        ({"tokens": ["Yes", "yes"], "anchor": "label", "label": "answer"}, "collide"),
        ({"tokens": ["yes", "no"], "anchor": "line", "label": "answer"}, "label"),
        ({"tokens": ["yes", "no"], "anchor": "label"}, "label"),
        ({"tokens": ["yes", "no"], "anchor": "label", "label": ""}, "label"),
    ],
)
def test_find_verdict_rejects_bad_arguments(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        find_verdict("ANSWER: yes", position="last", **kwargs)


@pytest.mark.parametrize("text", ["", "   ", "\n\n", "\r\n"])
@pytest.mark.parametrize("anchor", ["label", "line"])
def test_find_verdict_empty_text_is_failure(text: str, anchor: str) -> None:
    label = "answer" if anchor == "label" else None
    result = find_verdict(text, ["yes", "no"], anchor=anchor, position="last", label=label)
    assert isinstance(result, VerdictParseFailure)
    assert result.text == text


YES_NO = ["yes", "no"]

LABEL_CASES = [
    # id, text, label, tokens, position, ignore_quoted, expected
    (
        "reason-then-verdict",
        "The answer is wrong because...\nAnswer: no",
        "answer",
        YES_NO,
        "last",
        False,
        "no",
    ),
    (
        "both-tokens-in-reasoning",
        "Not yes, not no, hard to say.\nAnswer: yes",
        "answer",
        YES_NO,
        "last",
        False,
        "yes",
    ),
    ("quoted-line-ignored", "> Answer: yes\nAnswer: no", "answer", YES_NO, "last", True, "no"),
    ("quoted-line-counted", "> Answer: yes\nAnswer: no", "answer", YES_NO, "first", False, "yes"),
    ("incorrect-is-not-correct", "incorrect: yes", "correct", YES_NO, "last", False, None),
    ("numbered", "1. Answer: yes", "answer", YES_NO, "last", False, "yes"),
    ("bulleted", "- Answer: yes", "answer", YES_NO, "last", False, "yes"),
    ("block-quoted", "> Answer: yes", "answer", YES_NO, "last", False, "yes"),
    ("heading", "## Answer: yes", "answer", YES_NO, "last", False, "yes"),
    ("mixed-prefix", "> - **Answer:** yes", "answer", YES_NO, "last", False, "yes"),
    ("bold-label-and-colon", "**Answer:** yes", "answer", YES_NO, "last", False, "yes"),
    ("bold-label-only", "**Answer**: yes", "answer", YES_NO, "last", False, "yes"),
    ("bold-token", "Answer: **yes**", "answer", YES_NO, "last", False, "yes"),
    ("capitalised", "Correct: Yes", "correct", YES_NO, "last", False, "yes"),
    ("tag-form", "<answer>yes</answer>", "answer", YES_NO, "last", False, "yes"),
    ("bare-tag-separator", "answer>yes", "answer", YES_NO, "last", False, "yes"),
    ("equals-separator", "answer = no", "answer", YES_NO, "last", False, "no"),
    ("two-tokens-fail", "Answer: yes or no", "answer", YES_NO, "last", False, None),
    (
        "prose-after-verdict-fails",
        "ANSWER: INCORRECT, the claim is not correct.",
        "answer",
        ["CORRECT", "INCORRECT"],
        "last",
        False,
        None,
    ),
    ("same-token-twice-ok", "Answer: yes. Yes.", "answer", YES_NO, "last", False, "yes"),
    ("label-then-newline", "Answer:\nyes", "answer", YES_NO, "last", False, None),
    (
        "last-labelled-line-invalid",
        "ANSWER: yes\n...\nANSWER: maybe",
        "answer",
        YES_NO,
        "last",
        False,
        None,
    ),
    ("first-of-several", "ANSWER: yes\nANSWER: no", "answer", YES_NO, "first", False, "yes"),
    ("last-of-several", "ANSWER: yes\nANSWER: no", "answer", YES_NO, "last", False, "no"),
    (
        "all-fields-no-verdict",
        "extracted_final_answer: 42\nreasoning: matches\nconfidence: 90",
        "correct",
        YES_NO,
        "last",
        False,
        None,
    ),
    ("rating-off-scale", "Rating: 7", "rating", ["1", "2", "3", "4", "5"], "last", False, None),
    ("rating-on-scale", "Rating: 4", "rating", ["1", "2", "3", "4", "5"], "last", False, "4"),
    ("nbsp-after-separator", "ANSWER:\u00a0yes", "answer", YES_NO, "last", False, "yes"),
    ("tab-after-separator", "ANSWER:\tyes", "answer", YES_NO, "last", False, "yes"),
    ("underscore-token", "Answer: _yes_", "answer", YES_NO, "last", False, "yes"),
    ("double-underscore-token", "Answer: __no__", "answer", YES_NO, "last", False, "no"),
    (
        "label-is-a-token-word",
        "Correct: INCORRECT",
        "correct",
        ["CORRECT", "INCORRECT"],
        "last",
        False,
        "INCORRECT",
    ),
    (
        "numbered-numeric-token",
        "1. Rating: 3",
        "rating",
        ["1", "2", "3", "4", "5"],
        "last",
        False,
        "3",
    ),
    ("dotless-i-folds-to-i", "Answer: \u0131", "answer", ["i", "o"], "last", False, "i"),
    ("label-prefix-of-word", "answers: yes", "answer", YES_NO, "last", False, None),
    ("trailing-punctuation", "ANSWER: yes.", "answer", YES_NO, "last", False, "yes"),
    ("token-prefix-of-word", "Answer: yesterday", "answer", YES_NO, "last", False, None),
    ("crlf", "Reasoning.\r\nAnswer: no\r\n", "answer", YES_NO, "last", False, "no"),
]


@pytest.mark.parametrize(
    ("text", "label", "tokens", "position", "ignore_quoted", "expected"),
    [case[1:] for case in LABEL_CASES],
    ids=[case[0] for case in LABEL_CASES],
)
def test_find_verdict_label_mode(
    text: str,
    label: str,
    tokens: list[str],
    position: str,
    ignore_quoted: bool,
    expected: str | None,
) -> None:
    result = find_verdict(
        text, tokens, anchor="label", position=position, label=label, ignore_quoted=ignore_quoted
    )
    if expected is None:
        assert isinstance(result, VerdictParseFailure)
    else:
        assert isinstance(result, VerdictMatch)
        assert result.token == expected


def test_find_verdict_label_mode_offsets_index_original_text() -> None:
    text = "Reasoning.\r\nAnswer: **no**\r\n"
    result = find_verdict(text, YES_NO, anchor="label", position="last", label="answer")
    assert isinstance(result, VerdictMatch)
    assert text[result.start : result.end].lower() == "no"
    assert result.line == "Answer: **no**"


MCQ = ["(A)", "(B)", "(C)", "(D)", "(E)"]

LINE_CASES = [
    # id, text, tokens, position, ignore_quoted, expected
    ("bare-yes", "yes", YES_NO, "first", False, "yes"),
    ("bare-n", "n", ["y", "n"], "first", False, "n"),
    ("bare-zero", "0", ["0", "1"], "first", False, "0"),
    ("capitalised-first", "Yes, because the file exists.", YES_NO, "first", False, "yes"),
    ("bold-first", "**No**, the file is missing.", YES_NO, "first", False, "no"),
    ("underscore-first", "_No_, the file is missing.", YES_NO, "first", False, "no"),
    ("bulleted", "- yes", YES_NO, "first", False, "yes"),
    ("yesterday", "yesterday it worked", YES_NO, "first", False, None),
    ("knowledge", "knowledge is missing", ["y", "n"], "first", False, None),
    ("token-mid-line", "I think yes", YES_NO, "first", False, None),
    ("preface-then-verdict-first", "Based on the file...\nYes", YES_NO, "first", False, None),
    (
        "reasoning-starts-with-token",
        "No tests ran.\nSo overall it is fine.\nYes",
        YES_NO,
        "first",
        False,
        "no",
    ),
    ("last-line-verdict", "Reasoning here.\nyes", YES_NO, "last", False, "yes"),
    ("two-tokens-fail", "Yes, but no tests were run", YES_NO, "first", False, None),
    ("mcq-letter", "(C)", MCQ, "first", False, "(C)"),
    ("mcq-lowercase-in-reasoning", "(C)\n(a) was wrong because...", MCQ, "first", False, "(C)"),
    ("quoted-skipped", "> yes\nno", YES_NO, "first", True, "no"),
    ("only-quoted-line", "> yes", YES_NO, "first", True, None),
    ("overlapping-tokens", "Yes", ["y", "n", "yes", "no"], "first", False, "yes"),
    ("blank-lines-skipped", "\n\n  no  \n\n", YES_NO, "first", False, "no"),
    ("crlf", "Reasoning.\r\nno\r\n", YES_NO, "last", False, "no"),
]


@pytest.mark.parametrize(
    ("text", "tokens", "position", "ignore_quoted", "expected"),
    [case[1:] for case in LINE_CASES],
    ids=[case[0] for case in LINE_CASES],
)
def test_find_verdict_line_mode(
    text: str,
    tokens: list[str],
    position: str,
    ignore_quoted: bool,
    expected: str | None,
) -> None:
    result = find_verdict(
        text, tokens, anchor="line", position=position, ignore_quoted=ignore_quoted
    )
    if expected is None:
        assert isinstance(result, VerdictParseFailure)
    else:
        assert isinstance(result, VerdictMatch)
        assert result.token == expected


def test_parse_verdict_maps_token_to_value() -> None:
    result = parse_verdict(
        "Answer: no",
        {"yes": CORRECT, "no": INCORRECT},
        anchor="label",
        position="last",
        label="answer",
    )
    assert result == INCORRECT


def test_parse_verdict_uses_caller_spelling() -> None:
    result = parse_verdict(
        "ANSWER: yes",
        {"Yes": CORRECT, "No": INCORRECT},
        anchor="label",
        position="last",
        label="answer",
    )
    assert result == CORRECT
    match = find_verdict(
        "ANSWER: yes", ["Yes", "No"], anchor="label", position="last", label="answer"
    )
    assert isinstance(match, VerdictMatch)
    assert match.token == "Yes"


def test_parse_verdict_failure_unscored() -> None:
    failure = parse_verdict(
        "I cannot tell.", {"yes": True, "no": False}, anchor="line", position="first"
    )
    assert isinstance(failure, VerdictParseFailure)
    score = failure.unscored(answer="the model's answer", metadata={"checkpoint": 3})
    assert math.isnan(score.as_float())
    assert score.reason == GRADER_FAILED
    assert score.answer == "the model's answer"
    assert score.metadata is not None
    assert score.metadata["grader_failure_mode"] == GRADER_PARSE_FAILURE
    assert score.metadata["grader_payload"]["grader_response"] == "I cannot tell."
    assert score.metadata["checkpoint"] == 3
    assert score.explanation is not None
    assert "I cannot tell." in score.explanation


def test_verdict_instruction_two_tokens() -> None:
    assert verdict_instruction(["yes", "no"]) == (
        "End your reply with a line of the form `ANSWER: yes` or `ANSWER: no`, "
        "and nothing after it."
    )


def test_verdict_instruction_three_tokens_custom_label() -> None:
    assert verdict_instruction(["1", "2", "3"], label="Rating") == (
        "End your reply with a line of the form `Rating: 1`, `Rating: 2` or `Rating: 3`, "
        "and nothing after it."
    )


def test_verdict_instruction_round_trips_through_find_verdict() -> None:
    reply = "Some reasoning.\n" + f"{VERDICT_LABEL}: no"
    match = find_verdict(reply, YES_NO, anchor="label", position="last", label=VERDICT_LABEL)
    assert isinstance(match, VerdictMatch)
    assert match.token == "no"


def test_verdict_instruction_rejects_single_token() -> None:
    with pytest.raises(ValueError, match="two"):
        verdict_instruction(["yes"])


@pytest.mark.parametrize(
    "run",
    ["*" * 26 + " nothing here", "_" * 26 + " nothing here", "> " * 26 + "nothing here"],
    ids=["asterisks", "underscores", "quotes"],
)
def test_find_verdict_prefix_runs_do_not_backtrack(run: str) -> None:
    text = run + "\nAnswer: yes"
    started = time.perf_counter()
    result = find_verdict(text, YES_NO, anchor="label", position="last", label="answer")
    assert time.perf_counter() - started < 0.5
    assert isinstance(result, VerdictMatch)
    assert result.token == "yes"
