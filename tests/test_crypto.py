import pytest
import os
from app.crypto import encrypt, decrypt, init_crypto


def test_encrypt_decrypt_roundtrip(monkeypatch):
    """encrypt(plaintext) then decrypt() returns original plaintext."""
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret-key")
    init_crypto()

    plaintext = "my_api_hash_xyz"
    ciphertext = encrypt(plaintext)
    decrypted = decrypt(ciphertext)

    assert decrypted == plaintext
    assert ciphertext != plaintext  # ensure it's actually encrypted


def test_encrypt_different_each_time(monkeypatch):
    """Fernet's IV ensures same plaintext encrypts differently each call."""
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret-key")
    init_crypto()

    plaintext = "api_hash"
    c1 = encrypt(plaintext)
    c2 = encrypt(plaintext)

    assert c1 != c2  # different ciphertexts
    assert decrypt(c1) == decrypt(c2) == plaintext


def test_crypto_fails_without_key(monkeypatch):
    """encrypt/decrypt fail fast if TVM_SECRET_KEY not set."""
    monkeypatch.delenv("TVM_SECRET_KEY", raising=False)

    with pytest.raises(ValueError, match="TVM_SECRET_KEY"):
        init_crypto()


def test_decrypt_invalid_ciphertext_fails(monkeypatch):
    """decrypt(corrupted_ciphertext) raises cryptography.fernet.InvalidToken."""
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret-key")
    init_crypto()

    with pytest.raises(Exception):  # InvalidToken
        decrypt("not-a-valid-fernet-token")
