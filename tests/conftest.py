"""Shared test setup: make the suite hermetic w.r.t. secrets.

Sets a throwaway TVM_SECRET_KEY before app.crypto is imported anywhere, then
initializes the global Fernet cipher once per session. This means tests don't
depend on the ambient environment (CI-safe).
"""
import os

# ponytail: setdefault so a real env var (if a dev sets one) still wins.
os.environ.setdefault("TVM_SECRET_KEY", "test-secret-key")

import pytest
from app.crypto import init_crypto


@pytest.fixture(scope="session", autouse=True)
def _init_crypto():
    init_crypto()
