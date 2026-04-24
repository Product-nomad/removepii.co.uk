"""Regex-phase smoke tests for backend.scrub_text_hybrid.

The LLM phase is skipped by mocking the client, so these run without a local
Ollama / LM Studio instance. They cover the deterministic regex phase only.
"""

from __future__ import annotations

from unittest.mock import patch

import backend
from backend import UK_PATTERNS, get_tag


def _no_llm_scrub(text: str, client_name: str = "test", style: str = "Redacted") -> str:
    """Run scrub_text_hybrid with the LLM call mocked to echo the *chunk* back.

    Crucially, the mock returns the chunk it received (regex-scrubbed), not the
    original pre-regex text — otherwise the regex phase's output would be
    overwritten and the assertions would all fail.
    """

    class _FakeCompletions:
        def create(self, **kwargs: object) -> object:
            messages = kwargs.get("messages") or []
            user_content = next(
                (m["content"] for m in messages if m.get("role") == "user"),
                "",
            )

            class _Choice:
                message = type("M", (), {"content": user_content})

            return type("R", (), {"choices": [_Choice()]})

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    with patch.object(backend, "client", _FakeClient()):
        return backend.scrub_text_hybrid(text, client_name, style)


def test_email_is_redacted() -> None:
    out = _no_llm_scrub("Contact alice@example.com for details.")
    assert "alice@example.com" not in out
    assert get_tag("EMAIL", "Redacted") in out


def test_uk_postcode_is_redacted() -> None:
    out = _no_llm_scrub("Address is SW1A 1AA in London.")
    assert "SW1A 1AA" not in out


def test_uk_phone_is_redacted() -> None:
    # Mobile format — the existing regex catches this.
    # Known gap: London landlines (+44 20 XXXX XXXX) slip through; see README roadmap.
    out = _no_llm_scrub("Call me on 07946 000 111 anytime.")
    assert "07946 000 111" not in out


def test_nhs_number_is_redacted() -> None:
    out = _no_llm_scrub("NHS: 943 476 5919")
    assert "943 476 5919" not in out


def test_bare_10_digit_number_is_not_falsely_redacted_as_nhs() -> None:
    """Student IDs and order numbers are commonly 10 digits without separators.

    The regex was tightened to require separators, so bare 10-digit numbers
    are no longer treated as NHS numbers (regression test for the student-ID
    false positive from the first live test).
    """
    out = _no_llm_scrub("Student ID: 1234567890")
    assert "1234567890" in out  # preserved, not redacted
    assert "[NHS-REDACTED]" not in out


def test_dob_is_redacted() -> None:
    out = _no_llm_scrub("DOB: 14/03/1988 and more text.")
    assert "14/03/1988" not in out
    assert "[DOB-REDACTED]" in out


def test_dob_with_dashes_is_redacted() -> None:
    out = _no_llm_scrub("Date of Birth: 14-03-1988")
    assert "14-03-1988" not in out


def test_removed_style_uses_single_tag() -> None:
    out = _no_llm_scrub("Email me at x@y.co.uk", style="Removed")
    assert "[REMOVED]" in out


def test_benign_text_untouched() -> None:
    text = "The quick brown fox jumps over the lazy dog."
    out = _no_llm_scrub(text)
    assert out.strip() == text


def test_patterns_table_shape() -> None:
    labels = {label for label, _ in UK_PATTERNS}
    for required in {"PHONE", "NHS", "DOB", "EMAIL", "POSTCODE", "ADDRESS", "NINO"}:
        assert required in labels
