"""TDD: Test app-password auth and cookie signing."""
import pytest
import os
from app.api.auth import sign_session, verify_session, check_app_password, COOKIE_NAME


def test_sign_and_verify_session(monkeypatch):
    """Test 1: sign_session creates token, verify_session validates it."""
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret")
    token = sign_session("dummy")
    assert token
    assert verify_session(token)


def test_verify_invalid_token():
    """Test 2: verify_session rejects invalid token."""
    assert not verify_session("invalid-token")


def test_check_app_password_correct(monkeypatch):
    """Test 3: check_app_password validates correct password."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "test-password")
    assert check_app_password("test-password")


def test_check_app_password_wrong(monkeypatch):
    """Test 4: check_app_password rejects wrong password."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "test-password")
    assert not check_app_password("wrong")


def test_check_app_password_no_password_set(monkeypatch):
    """Test 5: check_app_password returns False when no password set."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)
    assert not check_app_password("anything")
