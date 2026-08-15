"""Outbound email.

Nothing is actually delivered yet. In development the message is logged, which
is enough to sign in: the link appears in the server output and can be pasted
into the browser.

Deliberately one seam rather than provider calls scattered through the routers,
so adding Resend or SES later is a change in this file and nowhere else. Until
then `send` returning cleanly must not be read as "the person received it" —
`delivered` says which it was.
"""

import logging
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger("braid.mail")
settings = get_settings()


@dataclass(frozen=True)
class Sent:
    to: str
    subject: str
    #: False while no provider is configured. The caller can then be honest
    #: about what it tells the person.
    delivered: bool


def send(to: str, subject: str, body: str) -> Sent:
    """Log it. Replace the body of this function with a provider call."""
    logger.info(
        "email not delivered (no provider configured)\n"
        "  to:      %s\n"
        "  subject: %s\n"
        "%s",
        to,
        subject,
        "\n".join(f"  | {line}" for line in body.splitlines()),
    )
    return Sent(to=to, subject=subject, delivered=False)


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
