import uuid
from datetime import datetime
from typing import Any

from pydantic import EmailStr, Field

from app.enums import DigestFrequency, InviteState, ParticipationStatus, Role
from app.schemas.auth import AccountOut, SessionOut
from app.schemas.common import Wire


class NotificationPreferencesOut(Wire):
    """One switch per kind, not one switch.

    Somebody who wants to know when their mentor writes but not when the
    programme sends a newsletter should not have to choose between both and
    neither.
    """

    new_message: bool = True
    match_published: bool = True
    milestone_reminders: bool = True
    broadcasts: bool = True
    digest: DigestFrequency = DigestFrequency.WEEKLY


class AccountProgramOut(Wire):
    participation_id: uuid.UUID
    program_id: uuid.UUID
    program_name: str
    organisation_name: str
    org_slug: str
    program_slug: str
    role: Role
    status: ParticipationStatus
    is_coordinator: bool = False
    muted: bool = False
    unread_count: int = 0
    #: True once a cohort has finished. The programme stays open to read rather
    #: than disappearing — architecture 4.17 asks for exactly that.
    read_only: bool = False


class AccountSettingsOut(Wire):
    account: AccountOut
    notifications: NotificationPreferencesOut
    programs: list[AccountProgramOut] = []


class AccountSettingsSaveIn(Wire):
    """Both fields optional: the screen saves each section on its own, so a
    request that carries only notifications must not blank the name."""

    name: str | None = Field(None, min_length=1, max_length=200)
    notifications: NotificationPreferencesOut | None = None


class MuteChangeIn(Wire):
    muted: bool


class InviteOut(Wire):
    token: str
    state: InviteState
    email: str
    organisation_name: str
    program_name: str
    org_slug: str
    program_slug: str
    role: Role
    invited_by_name: str
    message: str | None = None
    expires_at: datetime | None = None
    #: Whether the invited address already belongs to an account. The screen
    #: says which, so nobody accepting fears they are creating a duplicate.
    has_account: bool = False


class InviteResponseIn(Wire):
    accept: bool
    #: Required when accepting without an existing account.
    name: str | None = None


class InviteAcceptedOut(Wire):
    session: SessionOut
    org_slug: str
    program_slug: str


class ApplicationDraftOut(Wire):
    draft_id: uuid.UUID
    role: Role
    form_version_id: uuid.UUID
    answers: dict[str, Any] = {}
    #: What the autosave indicator shows. Design direction 9: a timestamp, never
    #: a spinner — a spinner says "wait", and the applicant has nothing to wait
    #: for.
    saved_at: datetime


class ApplicationDraftSaveIn(Wire):
    #: Omitted on the first save. The server mints one and returns it.
    draft_id: uuid.UUID | None = None
    role: Role
    form_version_id: uuid.UUID
    answers: dict[str, Any] = {}


class WaitlistJoinIn(Wire):
    email: EmailStr
    role: Role | None = None
