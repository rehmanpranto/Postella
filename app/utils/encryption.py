"""
Encryption utility for OAuth tokens.

Uses cryptography.fernet when available (preferred).
Falls back to a stdlib-only HMAC+XOR approach if the
cryptography package cannot be installed (e.g. build
environments without Rust).
"""

from flask import current_app
import base64
import hashlib
import hmac
import os

try:
    from cryptography.fernet import Fernet
    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    # ── Fernet (preferred) ──────────────────────────────
    @staticmethod
    def _get_cipher():
        """Get Fernet cipher from app config"""
        key = current_app.config['ENCRYPTION_KEY'].encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(key)

    # ── stdlib fallback helpers ─────────────────────────
    @staticmethod
    def _derive_key(salt: bytes) -> bytes:
        key = current_app.config['ENCRYPTION_KEY'].encode()
        return hashlib.pbkdf2_hmac('sha256', key, salt, 100_000)

    @staticmethod
    def _xor_bytes(data: bytes, key: bytes) -> bytes:
        return bytes(a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[:len(data)]))

    # ── public API ──────────────────────────────────────
    @staticmethod
    def encrypt(data: str) -> str:
        """Encrypt string data"""
        if not data:
            return data

        if _HAS_FERNET:
            cipher = EncryptionService._get_cipher()
            return cipher.encrypt(data.encode()).decode()

        # stdlib fallback: salt + xor(data, derived-key) + hmac
        salt = os.urandom(16)
        dk = EncryptionService._derive_key(salt)
        ct = EncryptionService._xor_bytes(data.encode(), dk)
        mac = hmac.new(dk, ct, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(b'STDFB' + salt + mac + ct).decode()

    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return encrypted_data

        # Detect which scheme was used
        raw = base64.urlsafe_b64decode(encrypted_data.encode()) if encrypted_data.startswith('U1RERk') else None

        if raw and raw[:5] == b'STDFB':
            # stdlib fallback path
            salt = raw[5:21]
            mac_stored = raw[21:53]
            ct = raw[53:]
            dk = EncryptionService._derive_key(salt)
            mac_check = hmac.new(dk, ct, hashlib.sha256).digest()
            if not hmac.compare_digest(mac_stored, mac_check):
                raise ValueError('Decryption failed: invalid HMAC')
            return EncryptionService._xor_bytes(ct, dk).decode()

        if _HAS_FERNET:
            cipher = EncryptionService._get_cipher()
            return cipher.decrypt(encrypted_data.encode()).decode()

        raise RuntimeError(
            'Cannot decrypt Fernet token: the cryptography package is not installed. '
            'Run: pip install cryptography'
        )
