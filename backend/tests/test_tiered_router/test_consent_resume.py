# backend/tests/test_tiered_router/test_consent_resume.py
"""Tests for consent detection and resume flow."""
import pytest
from app.api.v1.chat import is_consent_confirmation


class MockRequest:
    """Mock request object for testing consent detection."""
    def __init__(self, message=None, action=None):
        self.message = message
        self.action = action


def test_consent_confirmation_button_click():
    """Button click action should be detected"""
    request = MockRequest(action="consent_confirm")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_yes():
    """'yes' should be detected as consent"""
    request = MockRequest(message="yes")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_search_deeper():
    """'search deeper' should be detected as consent"""
    request = MockRequest(message="search deeper")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_case_insensitive():
    """Consent detection should be case insensitive"""
    request = MockRequest(message="YES")
    assert is_consent_confirmation(request) is True

    request = MockRequest(message="Search Deeper")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_continue():
    """'continue' should be detected as consent"""
    request = MockRequest(message="continue")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_ok():
    """'ok' should be detected as consent"""
    request = MockRequest(message="ok")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_proceed():
    """'proceed' should be detected as consent"""
    request = MockRequest(message="proceed")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_go_ahead():
    """'go ahead' should be detected as consent"""
    request = MockRequest(message="go ahead")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_yes_prefix():
    """Messages starting with 'yes' should be detected as consent"""
    request = MockRequest(message="yes please")
    assert is_consent_confirmation(request) is True

    request = MockRequest(message="yes, search deeper")
    assert is_consent_confirmation(request) is True


def test_non_consent_message():
    """Regular messages should not be detected as consent"""
    request = MockRequest(message="find me a vacuum")
    assert is_consent_confirmation(request) is False


def test_non_consent_message_with_yes_substring():
    """Messages containing 'yes' but not starting with it should not be consent"""
    request = MockRequest(message="say yes to the dress")
    assert is_consent_confirmation(request) is False


def test_consent_confirmation_empty():
    """Empty request should not be consent"""
    request = MockRequest()
    assert is_consent_confirmation(request) is False


def test_consent_confirmation_empty_message():
    """Empty message should not be consent"""
    request = MockRequest(message="")
    assert is_consent_confirmation(request) is False


def test_consent_confirmation_whitespace():
    """Whitespace-only message should not be consent"""
    request = MockRequest(message="   ")
    assert is_consent_confirmation(request) is False


def test_consent_confirmation_whitespace_trimmed():
    """Consent words with whitespace should be detected"""
    request = MockRequest(message="  yes  ")
    assert is_consent_confirmation(request) is True

    request = MockRequest(message="\tok\n")
    assert is_consent_confirmation(request) is True
