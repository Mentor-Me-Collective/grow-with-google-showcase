import uuid
from datetime import date, datetime
from typing import Any

from app.enums import (
    OriginMode,
    ParticipationStatus,
    ProgramState,
    ResourceKind,
    Role,
    StrandState,
)
from app.schemas.auth import AccountOut
from app.schemas.common import Wire


class OrganisationOut(Wire):
    id: uuid.UUID
    slug: str
    name: str
    logo_url: str | None = None


class ProgramPublicOut(Wire):
    """The landing page's whole payload.

    Counts are included because the page has to be able to say "eight mentors
    have joined" — a recruitment page that cannot show it is already populated
    asks someone to be first, which is a much harder thing to ask.
    """

    id: uuid.UUID
    slug: str
    name: str
    organisation: OrganisationOut
    description: str | None = None
    state: ProgramState
    cohort_start: date | None = None
    cohort_end: date | None = None
    applications_close_at: datetime | None = None
    matching_opens_at: datetime | None = None
    time_commitment: str | None = None
    eligibility: str | None = None
    open_roles: list[Role] = []
    mentor_count: int
    mentee_count: int
    capacity: int | None = None
    places_remaining: int | None = None


class RosterEntryOut(Wire):
    id: uuid.UUID
    account: AccountOut
    role: Role
    status: ParticipationStatus
    matched: bool
    capacity: int | None = None
    load: int | None = None
    profile_completeness: float
    timezone: str | None = None
    joined_at: datetime | None = None


class RosterPageOut(Wire):
    items: list[RosterEntryOut]
    page: int
    page_size: int
    total: int


class StrandMemberOut(Wire):
    participation_id: uuid.UUID
    name: str
    role: Role
    headline: str | None = None
    photo_url: str | None = None
    timezone: str | None = None
    skills: list[str] = []


class MessagePreviewOut(Wire):
    author_name: str
    body: str
    sent_at: datetime


class StrandSummaryOut(Wire):
    """A strand as one row in a list.

    `members` is everyone *except* the reader — the participant's own screens
    are about the other person. The admin monitor deliberately reads the full
    strand instead, because a coordinator is not a party to most of them.
    """

    id: uuid.UUID
    program_id: uuid.UUID
    state: StrandState
    origin_mode: OriginMode
    members: list[StrandMemberOut]
    last_message: MessagePreviewOut | None = None
    last_activity_at: datetime | None = None
    unread_count: int = 0
    next_session_at: datetime | None = None
    ended_at: datetime | None = None


class StrandOut(Wire):
    id: uuid.UUID
    program_id: uuid.UUID
    state: StrandState
    origin_mode: OriginMode
    #: Every member, including the reader.
    members: list[StrandMemberOut]
    match_rationale: str | None = None
    created_at: datetime
    ended_at: datetime | None = None


class MessageAuthorOut(Wire):
    participation_id: uuid.UUID
    name: str
    photo_url: str | None = None


class MessageOut(Wire):
    id: uuid.UUID
    strand_id: uuid.UUID
    author: MessageAuthorOut
    body: str
    sent_at: datetime
    delivery_state: str = "sent"
    client_token: str | None = None


class MessagePageOut(Wire):
    items: list[MessageOut]
    next_cursor: str | None = None


class MessageCreateIn(Wire):
    body: str
    client_token: str | None = None


class AnnouncementOut(Wire):
    id: uuid.UUID
    body: str
    author_name: str
    posted_at: datetime


class MilestoneOut(Wire):
    id: uuid.UUID
    title: str
    due_at: datetime
    completed: bool


class NextActionOut(Wire):
    kind: str
    title: str
    body: str | None = None
    action_label: str
    href: str


class HomeSummaryOut(Wire):
    matching_opens_at: datetime | None = None
    mentor_count: int
    strand_count: int
    profile_completeness: float
    next_action: NextActionOut | None = None
    announcement: AnnouncementOut | None = None
    upcoming_milestone: MilestoneOut | None = None


class ResourceOut(Wire):
    id: uuid.UUID
    title: str
    description: str | None = None
    kind: ResourceKind
    url: str
    size_bytes: int | None = None
    updated_at: datetime | None = None


class DirectoryEntryOut(Wire):
    participation_id: uuid.UUID
    name: str
    role: Role
    photo_url: str | None = None
    headline: str | None = None
    timezone: str | None = None
    skills: list[str] = []
    #: False for a mentor already at the capacity they set. Listed rather than
    #: hidden, so the scarcity is visible instead of looking like an empty
    #: directory.
    available: bool
    unavailable_reason: str | None = None


class DirectoryPageOut(Wire):
    items: list[DirectoryEntryOut]
    page: int
    page_size: int
    total: int
    self_matching_enabled: bool
    skills: list[str] = []


class PublicProfileEntryOut(Wire):
    label: str
    value: str


class PublicProfileSectionOut(Wire):
    title: str
    entries: list[PublicProfileEntryOut]


class PublicProfileOut(Wire):
    participation_id: uuid.UUID
    name: str
    role: Role
    photo_url: str | None = None
    headline: str | None = None
    timezone: str | None = None
    skills: list[str] = []
    available: bool
    capacity: int | None = None
    load: int | None = None
    #: Shareable answers only. Anything flagged `admin` never appears here.
    sections: list[PublicProfileSectionOut] = []


class FormVersionOut(Wire):
    id: uuid.UUID
    program_id: uuid.UUID
    role: Role
    version: int
    published_at: datetime | None = None
    sections: list[dict[str, Any]]


class AnswerRecordOut(Wire):
    value: Any
    provenance: str
    answered_at: datetime | None = None


class ProfileViewOut(Wire):
    participation_id: uuid.UUID
    name: str
    role: Role
    photo_url: str | None = None
    headline: str | None = None
    timezone: str | None = None
    completeness: float
    form_version: FormVersionOut
    answers: dict[str, dict[str, Any]]
    #: Unanswered, or answered so briefly there is nothing to match on.
    thin_field_ids: list[uuid.UUID | str] = []


class ProfileSaveIn(Wire):
    #: Only the fields being saved. Absent fields are left alone, so a
    #: per-section save cannot blank the sections that were not on screen.
    answers: dict[str, dict[str, Any]]
