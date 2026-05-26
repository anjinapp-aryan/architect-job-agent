import pytest

from architect_job_agent.core.exceptions import AIProviderError
from architect_job_agent.infrastructure.ai.base import extract_json


def test_extract_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_fenced_json():
    txt = "```json\n{\"a\": 2}\n```"
    assert extract_json(txt) == {"a": 2}


def test_extract_json_with_prose():
    txt = "Sure! Here is the result: {\"score\": 88, \"notes\": \"good\"} done."
    assert extract_json(txt)["score"] == 88


def test_extract_invalid_raises():
    with pytest.raises(AIProviderError):
        extract_json("totally not json")
