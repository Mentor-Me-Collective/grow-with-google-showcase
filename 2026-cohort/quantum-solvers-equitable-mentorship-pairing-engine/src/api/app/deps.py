"""Request dependencies: who is asking, and what they are allowed to see.

These mirror `web/lib/auth/guard.ts`. Role lives on Participation, never on
Account, so "is this person a coordinator" is only ever a question about a
particular organisation or programme — never about the account on its own.
"""

import uuid
from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import forbidden, not_found, unauthorized
from app.models import Account, Organisation, Participation, Program
from app.security import resolve_session

settings = get_settings()

DbSession = Annotated[Session, Depends(get_db)]


def session_cookie(braid_session: Annotated[str | None, Cookie()] = None) -> str | None:
    """The raw session token, if the browser sent one.

    Named to match the cookie the contract declares; FastAPI maps the parameter
    name to the cookie name directly.
    """
    return braid_session


RawSession = Annotated[str | None, Depends(session_cookie)]


def current_account_optional(db: DbSession, raw: RawSession) -> Account | None:
    return resolve_session(db, raw)


CurrentAccountOptional = Annotated[Account | None, Depends(current_account_optional)]


def current_account(account: CurrentAccountOptional) -> Account:
    if account is None:
        raise unauthorized()
    return account


CurrentAccount = Annotated[Account, Depends(current_account)]


def load_program(db: Session, program_id: uuid.UUID) -> Program:
    program = db.get(Program, program_id)
    if program is None:
        raise not_found("programme")
    return program


def participation_in(
    db: Session, account: Account, program_id: uuid.UUID
) -> Participation:
    """The account's membership of one programme, or 403.

    403 rather than 404: the programme exists, and saying so is not a leak —
    programmes are advertised on public landing pages. What is withheld is
    what is inside.
    """
    participation = db.scalar(
        select(Participation).where(
            Participation.account_id == account.id,
            Participation.program_id == program_id,
        )
    )
    if participation is None:
        raise forbidden("You are not a member of this programme.")
    return participation


def coordinator_of_org(
    db: Session, account: Account, org_slug: str
) -> tuple[Organisation, list[Participation]]:
    """Every programme in this organisation the account coordinates.

    A coordinator of one programme is not a coordinator of the organisation, so
    this returns the list rather than a boolean — the admin shell needs to know
    which programmes it may show.
    """
    org = db.scalar(select(Organisation).where(Organisation.slug == org_slug))
    if org is None:
        raise not_found("organisation")

    coordinated = list(
        db.scalars(
            select(Participation)
            .join(Program, Participation.program_id == Program.id)
            .where(
                Participation.account_id == account.id,
                Participation.is_coordinator.is_(True),
                Program.organisation_id == org.id,
            )
        ).all()
    )
    if not coordinated:
        raise forbidden("You do not coordinate any programme in this organisation.")
    return org, coordinated


def require_coordinator_of_program(
    db: Session, account: Account, program_id: uuid.UUID
) -> Participation:
    participation = db.scalar(
        select(Participation).where(
            Participation.account_id == account.id,
            Participation.program_id == program_id,
            Participation.is_coordinator.is_(True),
        )
    )
    if participation is None:
        raise forbidden("You do not coordinate this programme.")
    return participation
