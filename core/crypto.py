import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

# We use an AES-256 GCM authenticated encryption paradigm as mandated by the spec
AES_KEY_SIZE = 32 # 256 bits

class CryptoEngine:
    """Manages AES-256-GCM operations for clipboard data and sensitive logs in an ephemeral process state."""
    
    def __init__(self, key: bytes):
        """
        Initializes the cryptographic engine instance using the derived user key.
        The Key length must be precisely 32 bytes (256-bit).
        """
        if len(key) != AES_KEY_SIZE:
            raise ValueError(f"AES Key must be strictly {AES_KEY_SIZE} bytes.")
        self.key = key
        self.aead = AESGCM(self.key)
        
    def encrypt(self, plaintext: bytes, associated_data: bytes = None) -> bytes:
        """
        Secures plaintext directly using robust GCM-authenticated AES encryption.
        Appends the 12-byte initialization nonce to the start of the returned cipher.
        """
        # Nonces in AES-GCM must ALWAYS strictly be unique. A 12-byte nonce secures us mathematically 
        # but means we have roughly a randomized 96-bit collision window. Never reuse a nonce.
        nonce = os.urandom(12)
        
        # Cipher contains Authentication TAG mapped tightly to the string payload automatically
        ciphertext = self.aead.encrypt(nonce, plaintext, associated_data)
        
        # Store as: (NONCE 12-Bytes) + (CIPHERTEXT | TAG)
        return nonce + ciphertext

    def decrypt(self, encrypted_bundle: bytes, associated_data: bytes = None) -> bytes:
        """
        Decrypts an encrypted AEAD bundle ensuring authenticity natively.
        Extracts the initial nonce bytes before verifying the decryption.
        """
        if len(encrypted_bundle) < 12:
            raise ValueError("Invalid encrypted data bundle size.")

        nonce = encrypted_bundle[:12]
        ciphertext = encrypted_bundle[12:]
        
        # Standard exceptions get raised natively on tag failures
        try:
            return self.aead.decrypt(nonce, ciphertext, associated_data)
        except InvalidTag:
            raise ValueError("Authentication TAG mismatched. Encrypted payload could be malformed or tampered.")
