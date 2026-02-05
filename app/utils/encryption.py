from cryptography.fernet import Fernet
from flask import current_app
import base64
import hashlib


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    @staticmethod
    def _get_cipher():
        """Get Fernet cipher from app config"""
        key = current_app.config['ENCRYPTION_KEY'].encode()
        # Ensure key is 32 bytes
        key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(key)
    
    @staticmethod
    def encrypt(data: str) -> str:
        """Encrypt string data"""
        if not data:
            return data
        
        cipher = EncryptionService._get_cipher()
        encrypted = cipher.encrypt(data.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return encrypted_data
        
        cipher = EncryptionService._get_cipher()
        decrypted = cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
