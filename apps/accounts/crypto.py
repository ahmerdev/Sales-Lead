"""
Small helper to store secrets (SMTP password, API keys) encrypted in the database.

The key is derived from Django's SECRET_KEY. If you ever change SECRET_KEY in .env,
saved passwords/API keys can no longer be decrypted and must be entered again in Settings.
Requires:  pip install cryptography
"""
import base64
import hashlib

from django.conf import settings


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'cryptography' package is required to store passwords/API keys securely. "
            "Run:  pip install cryptography"
        ) from exc
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def encrypt(value):
    if not value:
        return ""
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(token):
    if not token:
        return ""
    try:
        from cryptography.fernet import InvalidToken
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""
