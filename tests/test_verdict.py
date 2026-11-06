"""Tests for the free-text verdict parser in inspect_evals_utils.scorers."""

import pytest

from inspect_evals_utils.scorers import VerdictParseFailure, find_verdict


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
