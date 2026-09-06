"""Rate limiting.

A fixed window counted in Postgres rather than in process memory. In-memory is
faster and silently wrong the moment a second instance exists: each process
keeps its own count, the effective limit multiplies by the instance count, and
nothing anywhere reports it. A counter in the database is the same number
however many instances read it.

Counted on its own connection and committed immediately, so an attempt still
counts when the request that made it goes on to fail. A limiter that only counts
successful requests does not limit the thing worth limiting — repeated failure
is the shape of every attack it exists to bound. The cost is that a limited
request briefly holds two pooled connections rather than one.

Fixed rather than sliding. A caller can spend the whole allowance at the end of
one window and again at the start of the next, so the true short-term ceiling is
twice the stated number. That is deliberate: a sliding window costs a row per
request, and every limit below is set so the doubled figure is still harmless.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import text

from app.db import engine
from app.errors import Problem

#: Old windows are litter, not history. Swept opportunistically rather than on a
#: schedule, because the service has no scheduler and this needs no accuracy.
_SWEEP_CHANCE = 0.01
_KEEP = timedelta(days=1)


@dataclass(frozen=True)
class Limit:
    allowed: int
    per_seconds: int


#: Two layers on the sign-in link, because they stop different things. The
#: per-address limit is what keeps somebody's inbox from being used as a weapon,
#: and it holds even when the source address is forged. The per-source limit is
#: what stops one caller walking a list of addresses.
MAGIC_LINK_PER_ADDRESS = Limit(5, 3600)
MAGIC_LINK_PER_SOURCE = Limit(20, 3600)

DEMO_SIGN_IN = Limit(20, 3600)

#: An application is a person filling in a long form, not a thing anybody does
#: repeatedly. Low enough to bound a script, high enough to survive a resubmit
#: after a validation failure.
APPLICATION_SUBMIT = Limit(5, 3600)
WAITLIST_JOIN = Limit(5, 3600)
INVITE_RESPONSE = Limit(20, 3600)

#: Generous on purpose: a real conversation never approaches it, and the point
#: is to bound a script rather than to pace a person mid-thought.
MESSAGE_SEND = Limit(60, 60)

#: The most expensive thing the service does, and the one operation where a
#: repeat is both costly and pointless.
RUN_CREATE = Limit(10, 3600)


def source(request: Request) -> str:
    """The caller's address, trusting the platform's forwarding header.

    Every managed host terminates TLS in front of the process and forwards the
    original address here, so `request.client` is the proxy and useless on its
    own. The leftmost entry is supplied by the caller and therefore forgeable —
    which is exactly why nothing important is keyed on this alone.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return request.client.host if request.client else "unknown"


def enforce(scope: str, subject: str, limit: Limit) -> None:
    """Count one attempt against `scope:subject`, or raise 429.

    Call before doing the work, not after. The count is the attempt, and an
    attempt that was refused for some other reason still consumed one.
    """
    now = datetime.now(UTC)
    window_start = datetime.fromtimestamp(
        int(now.timestamp()) // limit.per_seconds * limit.per_seconds, UTC
    )
    key = f"{scope}:{subject}"[:200]

    with engine.begin() as conn:
        used = conn.execute(
            text(
                "INSERT INTO rate_limit_counter (key, window_start, count) "
                "VALUES (:key, :window_start, 1) "
                "ON CONFLICT (key, window_start) "
                "DO UPDATE SET count = rate_limit_counter.count + 1 "
                "RETURNING count"
            ),
            {"key": key, "window_start": window_start},
        ).scalar_one()

        if random.random() < _SWEEP_CHANCE:
            conn.execute(
                text("DELETE FROM rate_limit_counter WHERE window_start < :cutoff"),
                {"cutoff": now - _KEEP},
            )

    if used > limit.allowed:
        wait = window_start + timedelta(seconds=limit.per_seconds) - now
        seconds = max(int(wait.total_seconds()), 1)
        raise Problem(
            429,
            "too_many_requests",
            f"Too many attempts. Try again {_in_words(seconds)}.",
            headers={"Retry-After": str(seconds)},
        )


def _in_words(seconds: int) -> str:
    """Sentence-case, no numerals below a minute. "Try again in 43 seconds" reads
    as a countdown the person is expected to run."""
    if seconds < 60:
        return "in a moment"
    minutes = round(seconds / 60)
    if minutes == 1:
        return "in a minute"
    if minutes < 60:
        return f"in {minutes} minutes"
    hours = round(minutes / 60)
    return "in an hour" if hours == 1 else f"in {hours} hours"
