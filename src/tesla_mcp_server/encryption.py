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

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypts the given encrypted data using the provided Fernet key.

    Args:
        encrypted_data (bytes): The data to decrypt.
        key (bytes): The Fernet key to use for decryption.

    Returns:
        bytes: The decrypted plaintext data.

    Raises:
        cryptography.fernet.InvalidToken: If the key is incorrect or the
                                          token is otherwise invalid.
    """
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data
