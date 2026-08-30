from datetime import timedelta
import jwt
import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_password = "SecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_token_hashing():
    raw_token = "some_random_refresh_token_string"
    hashed1 = hash_token(raw_token)
    hashed2 = hash_token(raw_token)

    assert hashed1 == hashed2
    assert len(hashed1) == 64  # SHA-256 hex string


def test_jwt_token_generation_and_decoding():
    subject = "user-id-12345"
    token = create_access_token(subject=subject, expires_delta=timedelta(minutes=15))

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == subject
    assert payload["type"] == "access"


def test_jwt_token_expired():
    subject = "user-id-12345"
    # Create expired token
    token = create_access_token(subject=subject, expires_delta=timedelta(seconds=-10))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_refresh_token_jti_uniqueness():
    subject = "user-id-12345"
    token1_str, _ = create_refresh_token(subject=subject)
    token2_str, _ = create_refresh_token(subject=subject)

    assert token1_str != token2_str
    payload1 = decode_token(token1_str)
    payload2 = decode_token(token2_str)
    assert payload1["jti"] != payload2["jti"]
