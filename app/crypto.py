import os
from hashlib import sha256
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet

_cipher = None


def init_crypto() -> None:
    """Initialize the Fernet cipher from TVM_SECRET_KEY env var."""
    global _cipher

    key_str = os.getenv("TVM_SECRET_KEY", "").strip()
    if not key_str:
        raise ValueError(
            "TVM_SECRET_KEY environment variable must be set and non-empty. "
            "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    # Derive a 32-byte key from the secret via SHA256, then urlsafe_b64encode
    key_bytes = sha256(key_str.encode()).digest()
    key_b64 = urlsafe_b64encode(key_bytes)
    _cipher = Fernet(key_b64)


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext string to urlsafe ciphertext."""
    if _cipher is None:
        raise RuntimeError("crypto not initialized; call init_crypto() first")

    ciphertext_bytes = _cipher.encrypt(plaintext.encode())
    return ciphertext_bytes.decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt ciphertext string to plaintext."""
    if _cipher is None:
        raise RuntimeError("crypto not initialized; call init_crypto() first")

    plaintext_bytes = _cipher.decrypt(ciphertext.encode())
    return plaintext_bytes.decode()
