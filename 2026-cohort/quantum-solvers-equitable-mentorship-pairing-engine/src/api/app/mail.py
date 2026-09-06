"""Outbound email.

Deliberately one seam rather than provider calls scattered through the routers,
so changing provider is a change in this file and nowhere else.

With no API key configured the message is logged instead of sent, and that is a
supported mode rather than a broken one: the sign-in link appears in the server
output and can be pasted into the browser, which is what makes a local run need
no provider account. `send` returning cleanly must never be read as "the person
received it" — `delivered` says which it was, and it is false for a missing key
and a refusing provider alike.
"""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger("braid.mail")
settings = get_settings()

RESEND_ENDPOINT = "https://api.resend.com/emails"

#: Bounded because this runs inside a request. FastAPI serves sync handlers from
#: a threadpool, so a hung provider costs a thread rather than the event loop —
#: but a pool is still finite, and an unbounded wait exhausts it.
TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class Sent:
    to: str
    subject: str
    delivered: bool


def send(to: str, subject: str, body: str) -> Sent:
    if not settings.mail_configured:
        _log_instead(to, subject, body)
        return Sent(to=to, subject=subject, delivered=False)

    try:
        response = httpx.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.mail_from,
                "to": [to],
                "subject": subject,
                "text": body,
            },
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        # Logged rather than raised. The only caller answers 202 whether or not
        # the address has an account, and a provider outage that turned it into
        # a 500 would both fail the sign-in and answer the enumeration question
        # the 202 exists to refuse.
        logger.exception("mail provider unreachable, nothing sent to %s", to)
        return Sent(to=to, subject=subject, delivered=False)

    if response.is_error:
        # Truncated: a provider error body is unbounded and this is the log a
        # deployment reads most often.
        logger.error(
            "mail provider refused the message\n  to:     %s\n"
            "  status: %s\n  body:   %s",
            to,
            response.status_code,
            response.text[:500],
        )
        return Sent(to=to, subject=subject, delivered=False)

    logger.info("sent %r to %s", subject, to)
    return Sent(to=to, subject=subject, delivered=True)


def _log_instead(to: str, subject: str, body: str) -> None:
    logger.info(
        "email not delivered (no provider configured)\n"
        "  to:      %s\n"
        "  subject: %s\n"
        "%s",
        to,
        subject,
        "\n".join(f"  | {line}" for line in body.splitlines()),
    )


def send_magic_link(to: str, link: str) -> Sent:
    return send(
        to,
        "Your Braid sign-in link",
        (
            "Hello,\n\n"
            "Here is your link into Braid. It works once and expires in "
            f"{settings.magic_link_ttl_minutes} minutes.\n\n"
            f"{link}\n\n"
            "If you did not ask for this, nothing has happened and you can "
            "ignore it."
        ),
    )
