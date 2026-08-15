import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Account, MagicLinkToken, SessionToken

settings = get_settings()


def new_token() -> str:
    """32 bytes of entropy, URL-safe.

    `secrets`, not `random`: these are credentials, and the difference between
    the two modules is exactly that one is predictable.
    """
    return secrets.token_urlsafe(32)


def issue_magic_link(db: Session, email: str) -> MagicLinkToken:
    now = datetime.now(UTC)
    token = MagicLinkToken(
        token=new_token(),
        email=email.lower().strip(),
        created_at=now,
        expires_at=now + timedelta(minutes=settings.magic_link_ttl_minutes),
    )
    db.add(token)
    db.flush()
    return token


def consume_magic_link(db: Session, raw: str) -> MagicLinkToken | None:
    """Returns the token only if it is real, unused and unexpired.

    Marked used rather than deleted, so a second click can be told the link has
    already been used instead of that it never existed — which is what the
    person actually needs to hear.
    """
    token = db.scalar(select(MagicLinkToken).where(MagicLinkToken.token == raw))
    if token is None:
        return None
    if token.used_at is not None:
        return None
    if token.expires_at <= datetime.now(UTC):
        return None

    token.used_at = datetime.now(UTC)
    db.flush()
    return token


def open_session(db: Session, account: Account) -> SessionToken:
    now = datetime.now(UTC)
    session = SessionToken(
        token=new_token(),
        account_id=account.id,
        created_at=now,
        expires_at=now + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    db.flush()
    return session


def resolve_session(db: Session, raw: str | None) -> Account | None:
    if not raw:
        return None
    session = db.scalar(select(SessionToken).where(SessionToken.token == raw))
    if session is None or session.revoked_at is not None:
        return None
    if session.expires_at <= datetime.now(UTC):
        return None
    return db.get(Account, session.account_id)


def revoke_session(db: Session, raw: str | None) -> None:
    if not raw:
        return
    session = db.scalar(select(SessionToken).where(SessionToken.token == raw))
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.flush()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        # Never Strict: somebody arriving from a link in their email is a
        # cross-site navigation, and Strict would drop the cookie on exactly the
        # journey this product is built around. Lax locally, "none" when the
        # frontend and API are deployed to different hosts.
        samesite=settings.session_cookie_samesite,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        samesite=settings.session_cookie_samesite,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
        path="/",
    )
