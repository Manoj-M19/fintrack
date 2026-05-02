import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_subject_from_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        assert hash_password("mysecret") != "mysecret"

    def test_correct_password_verifies(self):
        hashed = hash_password("mysecret")
        assert verify_password("mysecret", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("mysecret")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        # bcrypt uses a random salt — same input ≠ same hash
        assert hash_password("mysecret") != hash_password("mysecret")


class TestJWTTokens:
    def test_access_token_round_trip(self):
        token = create_access_token(subject=42)
        assert get_subject_from_token(token, "access") == "42"

    def test_refresh_token_round_trip(self):
        token = create_refresh_token(subject=99)
        assert get_subject_from_token(token, "refresh") == "99"

    def test_wrong_token_type_raises(self):
        access = create_access_token(subject=1)
        with pytest.raises(JWTError):
            get_subject_from_token(access, token_type="refresh")

    def test_tampered_token_raises(self):
        token = create_access_token(subject=1)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            get_subject_from_token(tampered)