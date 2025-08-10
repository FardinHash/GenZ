import base64
from typing import Tuple

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

from app.core.config import get_settings


def _derive_key(secret: str, salt: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode("utf-8"),
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))


def get_fernet() -> Fernet:
    settings = get_settings()
    key = _derive_key(settings.encryption_secret, settings.encryption_salt)
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    f = get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(token: str) -> str:
    f = get_fernet()
    plaintext = f.decrypt(token.encode("utf-8"))
    return plaintext.decode("utf-8") 