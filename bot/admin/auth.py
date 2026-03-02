import hmac
import secrets

from fastapi import Request

from bot.config import settings

_sessions: set[str] = set()


def verify_password(password: str) -> bool:
    if not settings.admin_password:
        return False
    return hmac.compare_digest(password, settings.admin_password)


def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions.add(token)
    return token


def delete_session(token: str) -> None:
    _sessions.discard(token)


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get("admin_session")
    return token is not None and token in _sessions
