from cryptography.fernet import Fernet, InvalidToken

def generate_key() -> bytes:
    """
    Generates a new Fernet key for encryption and decryption.

    Returns:
        bytes: A new Fernet key.
    """
    return Fernet.generate_key()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """
    Encrypts the given data using the provided Fernet key.

    Args:
        data (bytes): The plaintext data to encrypt.
        key (bytes): The Fernet key to use for encryption.

    Returns:
        bytes: The encrypted data.
    """
    f = Fernet(key)
    encrypted_data = f.encrypt(data)
    return encrypted_data

def decrypt_data(encrypted_data: bytes, encryption_key: bytes) -> bytes:
    """Decrypt data using the provided encryption key."""
    f = Fernet(encryption_key)
    return f.decrypt(encrypted_data)
