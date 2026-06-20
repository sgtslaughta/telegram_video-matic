"""App-password authentication with signed HTTP-only cookies."""
import hmac
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime, timezone

COOKIE_NAME = "tvm_session"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def get_cookie_signer() -> URLSafeTimedSerializer:
    """Create signer with secret from env."""
    secret = os.getenv("TVM_SECRET_KEY", "default-dev-secret")
    return URLSafeTimedSerializer(secret)


def sign_session(password: str) -> str:
    """Sign a dummy session token."""
    signer = get_cookie_signer()
    return signer.dumps({"authenticated_at": datetime.now(timezone.utc).isoformat()})


def verify_session(token: str, max_age: int = COOKIE_MAX_AGE) -> bool:
    """Verify signed session token."""
    signer = get_cookie_signer()
    try:
        signer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


def get_app_password() -> str | None:
    """Return app password from env, or None if unset."""
    return os.getenv("TVM_APP_PASSWORD")


def check_app_password(password: str) -> bool:
    """Check if password matches."""
    stored = get_app_password()
    if stored is None:
        return False
    # constant-time comparison to avoid leaking password length/prefix via timing
    return hmac.compare_digest(password, stored)
