"""
Unit tests for security utilities
"""

import pytest
from datetime import timedelta
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    encrypt_field,
    decrypt_field
)


class TestTokenGeneration:
    """Test JWT token generation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        token_data = {"sub": "test@example.com"}
        token = create_access_token(token_data, timedelta(minutes=30))
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token_data = {"sub": "test@example.com"}
        token = create_refresh_token(token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        token_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(token_data, timedelta(minutes=30))
        
        claims = verify_token(token)
        assert claims["sub"] == "test@example.com"
        assert claims["user_id"] == 1
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):
            verify_token(invalid_token)
    
    def test_token_with_jti(self):
        """Test token includes JTI claim for revocation"""
        token_data = {"sub": "test@example.com"}
        token = create_access_token(token_data, timedelta(minutes=30))
        
        claims = verify_token(token)
        assert "jti" in claims  # Should have JTI for revocation


class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > len(password)
    
    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_wrong_password(self):
        """Test verifying wrong password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert not verify_password("WrongPassword", hashed)
    
    def test_different_passwords_produce_different_hashes(self):
        """Test that same password produces different hashes (salting)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes due to salt
        assert hash1 != hash2
        # But both verify against the password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestEncryption:
    """Test field encryption/decryption"""
    
    def test_encrypt_field(self):
        """Test field encryption"""
        data = "sensitive_data"
        encrypted = encrypt_field(data)
        
        assert encrypted != data
        assert isinstance(encrypted, str)
        assert len(encrypted) > len(data)
    
    def test_decrypt_field(self):
        """Test field decryption"""
        original_data = "sensitive_data"
        encrypted = encrypt_field(original_data)
        decrypted = decrypt_field(encrypted)
        
        assert decrypted == original_data
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypt/decrypt roundtrip"""
        test_data = [
            "simple_string",
            "email@example.com",
            "1234567890",
            "special!@#$%chars"
        ]
        
        for original in test_data:
            encrypted = encrypt_field(original)
            decrypted = decrypt_field(encrypted)
            assert decrypted == original
    
    def test_encryption_fails_on_invalid_data(self):
        """Test encryption handles edge cases"""
        # None should raise error (fail-fast)
        with pytest.raises(Exception):
            encrypt_field(None)
    
    def test_decryption_fails_on_invalid_encrypted_data(self):
        """Test decryption fails on corrupted data"""
        invalid_encrypted = "invalid_encrypted_data"
        
        with pytest.raises(Exception):
            decrypt_field(invalid_encrypted)
