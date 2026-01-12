import hashlib
import re
from datetime import datetime, timedelta, UTC

import pytest
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWKError, JWTError

from bioscopeai_core.app.auth import auth
from bioscopeai_core.app.models import RefreshToken
from bioscopeai_core.tests.conftest import TEST_PUBLIC_KEY


@pytest.mark.unit
class TestGenerateRefreshToken:
    """Tests for refresh token generation."""

    def test_generates_non_empty_string(self):
        """Refresh token should be a non-empty string."""
        token = auth.generate_refresh_token()

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generates_sufficiently_long_token(self):
        """Token should be at least 64 characters for security."""
        token = auth.generate_refresh_token()

        assert len(token) >= 64, "Token too short for security requirements"

    def test_generates_unique_tokens(self):
        """Each invocation must produce a unique token."""
        tokens = {auth.generate_refresh_token() for _ in range(100)}

        assert len(tokens) == 100, "Duplicate tokens generated"

    def test_token_is_url_safe(self):
        """Token should only contain URL-safe characters."""
        token = auth.generate_refresh_token()

        url_safe_pattern = re.compile(r"^[A-Za-z0-9_-]+$")
        assert url_safe_pattern.match(token), (
            f"Token contains non-URL-safe chars: {token}"
        )

    def test_consistent_length_distribution(self):
        """Token length should be consistent across generations."""
        lengths = {len(auth.generate_refresh_token()) for _ in range(50)}

        assert max(lengths) - min(lengths) <= 2, "Inconsistent token lengths"


@pytest.mark.unit
class TestHashRefreshToken:
    """Tests for refresh token hashing."""

    def test_produces_hex_string(self):
        """Hash should be a hexadecimal string."""
        hashed = auth.hash_refresh_token("test_token")

        assert isinstance(hashed, str)
        assert all(c in "0123456789abcdef" for c in hashed), (
            "Non-hex characters in hash"
        )

    def test_produces_sha256_length(self):
        """SHA-256 hash should be exactly 64 hex characters."""
        hashed = auth.hash_refresh_token("test_token")

        assert len(hashed) == 64, f"Expected 64 chars, got {len(hashed)}"

    @pytest.mark.parametrize(
        "input_token",
        [
            "simple",
            "with spaces",
            "with-special!@#$%^&*()",
            "unicode_éèê",
            "very_long_token_" * 100,
            "",
        ],
    )
    def test_deterministic_hashing(self, input_token):
        """Same input must always produce same hash."""
        hash1 = auth.hash_refresh_token(input_token)
        hash2 = auth.hash_refresh_token(input_token)

        assert hash1 == hash2, f"Inconsistent hashing for: {input_token}"

    @pytest.mark.parametrize(
        "token1,token2",
        [
            ("token_a", "token_b"),
            ("TOKEN", "token"),
            ("test123", "test124"),
            ("abc", "abcd"),
        ],
    )
    def test_collision_resistance(self, token1, token2):
        """Different inputs must produce different hashes."""
        hash1 = auth.hash_refresh_token(token1)
        hash2 = auth.hash_refresh_token(token2)

        assert hash1 != hash2, f"Hash collision: {token1} == {token2}"

    def test_matches_standard_sha256(self):
        """Implementation should match Python's hashlib.sha256."""
        test_token = "standard_test_token"
        expected = hashlib.sha256(test_token.encode()).hexdigest()
        actual = auth.hash_refresh_token(test_token)

        assert actual == expected, "Hash doesn't match standard SHA-256"


@pytest.mark.unit
class TestCreateAccessToken:
    """Tests for JWT access token creation."""

    def test_produces_valid_jwt_structure(self, mock_auth_settings):
        """Token must have standard JWT structure."""
        token = auth.create_access_token("user-id-123", "admin")

        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3, "JWT must have 3 parts (header.payload.signature)"

    @pytest.mark.parametrize(
        "user_id,role",
        [
            ("123e4567-e89b-12d3-a456-426614174000", "admin"),
            ("987e6543-e89b-12d3-a456-426614174999", "researcher"),
            ("simple-id", "viewer"),
            ("123", "analyst"),
        ],
    )
    def test_token_contains_required_claims(self, mock_auth_settings, user_id, role):
        """Token payload must contain all required claims."""
        token = auth.create_access_token(user_id, role)

        payload = jwt.decode(
            token,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        assert payload["sub"] == user_id, "Subject (user ID) mismatch"
        assert payload["roles"] == role, "Role mismatch"
        assert "exp" in payload, "Missing expiration claim"
        assert "iat" in payload, "Missing issued-at claim"

    def test_token_expiry_matches_settings(self, mock_auth_settings):
        """Token expiry should match configured TTL."""
        user_id = "test-user-id"
        role = "researcher"

        token = auth.create_access_token(user_id, role)

        payload = jwt.decode(
            token,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], UTC)

        actual_ttl = (exp_time - iat_time).total_seconds() / 60
        expected_ttl = mock_auth_settings.ACCESS_TOKEN_TTL_MINUTES

        assert abs(actual_ttl - expected_ttl) < 1, (
            f"TTL {actual_ttl} min doesn't match expected {expected_ttl} min"
        )

    def test_token_iat_is_current_time(self, mock_auth_settings):
        """Issued-at time should be approximately current time."""
        before_creation = datetime.now(UTC)
        token = auth.create_access_token("user-id", "role")

        payload = jwt.decode(
            token,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        iat_time = datetime.fromtimestamp(payload["iat"], UTC)
        time_diff = abs((iat_time - before_creation).total_seconds())

        assert time_diff < 2, f"iat time difference too large: {time_diff}s"

    def test_token_is_verifiable_with_public_key(self, mock_auth_settings):
        """Token signature must be verifiable with public key."""
        token = auth.create_access_token("user-id", "admin")

        # Should not raise JWTError
        payload = jwt.decode(
            token,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        assert payload is not None

    def test_token_fails_verification_with_wrong_key(self, mock_auth_settings):
        """Token should fail verification with incorrect public key."""
        token = auth.create_access_token("user-id", "admin")

        wrong_key = TEST_PUBLIC_KEY.replace("vZDeVz", "XXXXXX")

        with pytest.raises((JWTError, JWKError)):
            jwt.decode(token, wrong_key, algorithms=["RS256"])


@pytest.mark.integration
class TestObtainTokenPair:
    """Integration tests for token pair generation."""

    async def test_returns_tuple_of_two_strings(self, test_user, mock_auth_settings):
        """Should return (access_token, refresh_token) as strings."""
        access, refresh = await auth.obtain_token_pair(test_user)

        assert isinstance(access, str)
        assert isinstance(refresh, str)
        assert len(access) > 0
        assert len(refresh) > 0

    async def test_access_token_contains_user_data(self, test_user, mock_auth_settings):
        """Access token should contain correct user claims."""
        access, _ = await auth.obtain_token_pair(test_user)

        payload = jwt.decode(
            access,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        assert payload["sub"] == str(test_user.id)
        assert payload["roles"] == test_user.role.value

    async def test_creates_refresh_token_record(self, test_user, mock_auth_settings):
        """Should create RefreshToken record in database."""
        initial_count = await RefreshToken.filter(user=test_user).count()

        _, refresh = await auth.obtain_token_pair(test_user)

        final_count = await RefreshToken.filter(user=test_user).count()
        assert final_count == initial_count + 1

    async def test_stored_token_is_properly_hashed(self, test_user, mock_auth_settings):
        """Raw refresh token should be hashed before storage."""
        _, raw_refresh = await auth.obtain_token_pair(test_user)

        expected_hash = auth.hash_refresh_token(raw_refresh)
        stored = await RefreshToken.get_or_none(token_hash=expected_hash)

        assert stored is not None, "Token not found in database"
        assert stored.token_hash == expected_hash
        assert stored.user_id == test_user.id

    async def test_refresh_token_not_revoked(self, test_user, mock_auth_settings):
        """New refresh tokens should not be revoked."""
        _, raw_refresh = await auth.obtain_token_pair(test_user)

        token_hash = auth.hash_refresh_token(raw_refresh)
        stored = await RefreshToken.get(token_hash=token_hash)

        assert stored.revoked is False

    async def test_refresh_token_expiry_set_correctly(
        self, test_user, mock_auth_settings
    ):
        """Refresh token expiry should match configured TTL."""
        before = datetime.now(UTC)
        _, raw_refresh = await auth.obtain_token_pair(test_user)
        after = datetime.now(UTC)

        token_hash = auth.hash_refresh_token(raw_refresh)
        stored = await RefreshToken.get(token_hash=token_hash)

        expected_min = before + timedelta(
            minutes=mock_auth_settings.REFRESH_TOKEN_TTL_MINUTES
        )
        expected_max = after + timedelta(
            minutes=mock_auth_settings.REFRESH_TOKEN_TTL_MINUTES
        )

        assert expected_min <= stored.exp <= expected_max

    async def test_multiple_tokens_for_same_user(self, test_user, mock_auth_settings):
        """User can have multiple valid refresh tokens."""
        _, token1 = await auth.obtain_token_pair(test_user)
        _, token2 = await auth.obtain_token_pair(test_user)

        assert token1 != token2

        count = await RefreshToken.filter(user=test_user, revoked=False).count()
        assert count >= 2


@pytest.mark.integration
class TestRotateRefreshToken:
    """Integration tests for refresh token rotation."""

    async def test_successful_rotation(self, valid_refresh_token, mock_auth_settings):
        """Valid token should rotate successfully."""
        stored_token, raw_token = valid_refresh_token

        new_access, new_refresh = await auth.rotate_refresh_token(raw_token)

        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)
        assert new_refresh != raw_token, "New token should differ from old"

    async def test_old_token_marked_revoked(
        self, valid_refresh_token, mock_auth_settings
    ):
        """Old token must be marked as revoked after rotation."""
        stored_token, raw_token = valid_refresh_token
        old_hash = auth.hash_refresh_token(raw_token)

        await auth.rotate_refresh_token(raw_token)

        # Refresh from database
        await stored_token.refresh_from_db()
        assert stored_token.revoked is True

    async def test_new_token_created_in_database(
        self, valid_refresh_token, mock_auth_settings
    ):
        """New refresh token should be persisted to database."""
        stored_token, raw_token = valid_refresh_token
        user = await stored_token.user
        initial_count = await RefreshToken.filter(user=user).count()

        _, new_refresh = await auth.rotate_refresh_token(raw_token)

        final_count = await RefreshToken.filter(user=user).count()
        assert final_count == initial_count + 1

        new_hash = auth.hash_refresh_token(new_refresh)
        new_stored = await RefreshToken.get(token_hash=new_hash)
        assert new_stored.revoked is False

    async def test_new_access_token_contains_user_data(
        self, valid_refresh_token, mock_auth_settings
    ):
        """New access token should have correct user claims."""
        stored_token, raw_token = valid_refresh_token
        user = await stored_token.user

        new_access, _ = await auth.rotate_refresh_token(raw_token)

        payload = jwt.decode(
            new_access,
            mock_auth_settings.PUBLIC_KEY,
            algorithms=["RS256"],
        )

        assert payload["sub"] == str(user.id)
        assert payload["roles"] == user.role.value

    async def test_expired_token_raises_unauthorized(
        self, expired_refresh_token, mock_auth_settings
    ):
        """Expired token should raise 401 Unauthorized."""
        _, raw_token = expired_refresh_token

        with pytest.raises(HTTPException) as exc_info:
            await auth.rotate_refresh_token(raw_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    async def test_revoked_token_raises_unauthorized(
        self, revoked_refresh_token, mock_auth_settings
    ):
        """Revoked token should raise 401 Unauthorized."""
        _, raw_token = revoked_refresh_token

        with pytest.raises(HTTPException) as exc_info:
            await auth.rotate_refresh_token(raw_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_nonexistent_token_raises_unauthorized(self, db, mock_auth_settings):
        """Non-existent token should raise 401 Unauthorized."""
        fake_token = "nonexistent_token_12345"

        with pytest.raises(HTTPException) as exc_info:
            await auth.rotate_refresh_token(fake_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cannot_reuse_rotated_token(
        self, valid_refresh_token, mock_auth_settings
    ):
        """Once rotated, old token cannot be used again."""
        _, old_token = valid_refresh_token

        await auth.rotate_refresh_token(old_token)

        with pytest.raises(HTTPException) as exc_info:
            await auth.rotate_refresh_token(old_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestRevokeRefresh:
    """Integration tests for refresh token revocation."""

    async def test_revokes_valid_token(self, valid_refresh_token, mock_auth_settings):
        """Valid token should be successfully revoked."""
        stored_token, raw_token = valid_refresh_token

        await auth.revoke_refresh(raw_token)

        await stored_token.refresh_from_db()
        assert stored_token.revoked is True

    async def test_revocation_is_idempotent(
        self, valid_refresh_token, mock_auth_settings
    ):
        """Revoking same token multiple times should work."""
        stored_token, raw_token = valid_refresh_token

        await auth.revoke_refresh(raw_token)
        await auth.revoke_refresh(raw_token)
        await auth.revoke_refresh(raw_token)

        await stored_token.refresh_from_db()
        assert stored_token.revoked is True

    async def test_nonexistent_token_does_not_error(self, db, mock_auth_settings):
        """Revoking non-existent token should not raise error."""
        fake_token = "this_token_does_not_exist"

        await auth.revoke_refresh(fake_token)

    async def test_revoked_token_cannot_be_rotated(
        self, valid_refresh_token, mock_auth_settings
    ):
        """Revoked token should not be rotatable."""
        _, raw_token = valid_refresh_token

        await auth.revoke_refresh(raw_token)

        with pytest.raises(HTTPException) as exc_info:
            await auth.rotate_refresh_token(raw_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_only_affects_specified_token(self, test_user, mock_auth_settings):
        """Revoking one token should not affect others."""
        # Create two tokens
        _, token1 = await auth.obtain_token_pair(test_user)
        _, token2 = await auth.obtain_token_pair(test_user)

        await auth.revoke_refresh(token1)

        hash2 = auth.hash_refresh_token(token2)
        stored2 = await RefreshToken.get(token_hash=hash2)
        assert stored2.revoked is False
