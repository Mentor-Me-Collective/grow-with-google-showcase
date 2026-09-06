import uuid
from typing import Literal

from pydantic import EmailStr, Field

from app.enums import ParticipationStatus, Role
from app.schemas.common import Wire


class AccountOut(Wire):
    id: uuid.UUID
    name: str
    email: EmailStr
    email_verified: bool
    photo_url: str | None = None


class ParticipationSummaryOut(Wire):
    """One membership, flattened with the programme and organisation it belongs
    to — the frontend's guards and switcher read all of it together."""

    id: uuid.UUID
    program_id: uuid.UUID
    program_name: str
    organisation_name: str | None = None
    org_slug: str
    program_slug: str
    role: Role
    status: ParticipationStatus
    is_coordinator: bool = False


class SessionOut(Wire):
    account: AccountOut
    participations: list[ParticipationSummaryOut]


class MagicLinkRequest(Wire):
    email: EmailStr
    # Where to return the person after verifying, when they arrived from a
    # particular programme rather than the bare sign-in screen.
    org_slug: str | None = None
    program_slug: str | None = None


class VerifyRequest(Wire):
    token: str


class DemoSignInRequest(Wire):
    """`as` is a Python keyword, so the field is named around it and mapped back
    to the contract's spelling explicitly."""

    as_: Literal["coordinator", "participant"] = Field(alias="as")
