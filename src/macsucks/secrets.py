"""Secure API key storage via Windows DPAPI (keyring)."""

from __future__ import annotations

SERVICE_NAME = "macsucks"
USER_NAME = "llama_cloud_api_key"


def get_api_key() -> str | None:
    try:
        import keyring
    except ImportError:
        return None
    return keyring.get_password(SERVICE_NAME, USER_NAME)


def set_api_key(key: str) -> None:
    import keyring

    keyring.set_password(SERVICE_NAME, USER_NAME, key)


def delete_api_key() -> None:
    import keyring

    try:
        keyring.delete_password(SERVICE_NAME, USER_NAME)
    except keyring.errors.PasswordDeleteError:
        pass


def has_api_key() -> bool:
    key = get_api_key()
    return bool(key and key.strip())
