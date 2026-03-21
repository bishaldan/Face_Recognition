import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt_b64, digest_b64 = password_hash.split("$", maxsplit=1)
    salt = base64.b64decode(salt_b64.encode())
    expected = base64.b64decode(digest_b64.encode())
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return hmac.compare_digest(actual, expected)


def new_request_id() -> str:
    return secrets.token_hex(12)


def expires_at(minutes: int) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)

