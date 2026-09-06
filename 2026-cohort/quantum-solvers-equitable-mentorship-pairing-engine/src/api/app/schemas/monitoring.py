import uuid
from datetime import datetime

from pydantic import ConfigDict

from app.enums import BroadcastSegment, BroadcastState, OriginMode, StrandState
from app.schemas.common import Wire
from app.schemas.reads import MilestoneOut, StrandMemberOut
from app.schemas.setup import MergeCodeOut


class AttentionItemOut(Wire):
    """A thing a human has to decide, not a metric.

    Anything that resolves itself with time does not belong here, and every item
    carries the address of the page that resolves it — an item with nowhere to
    go is a worry rather than a task.
    """

    kind: str
    count: int
    title: str
    body: str | None = None
    action_label: str
    #: Relative to the programme's admin base, so the server does not need to
    #: know which org slug the coordinator arrived by.
    href: str


class DashboardSummaryOut(Wire):
    mentor_count: int
    mentee_count: int
    recruitment_goal: int | None = None
    matched_count: int
    unmatched_count: int
    active_strands: int
    #: Active strands with no message for a fortnight.
    quiet_strands: int
    sessions_logged_this_week: int
    upcoming_milestone: MilestoneOut | None = None
    #: Ordered by what it costs to leave alone, not by size. An empty list is a
    #: real and good answer.
    attention: list[AttentionItemOut] = []


class StrandMonitorEntryOut(Wire):
    id: uuid.UUID
    state: StrandState
    origin_mode: OriginMode
    #: Everybody, including the coordinator if she is in it — unlike a
    #: participant's own list, which is about the other person.
    members: list[StrandMemberOut]
    days_since_activity: int | None = None
    sessions_logged: int = 0
    milestones_completed: int = 0
    milestones_total: int = 0
    health: str


class StrandHealthCountsOut(Wire):
    """Keys stay snake_case: they are StrandHealth values, not field names. As
    camelCase the frontend reads `not_started` as undefined and the filter tab
    shows no number at all."""

    model_config = ConfigDict(
        alias_generator=None,
        serialize_by_alias=False,
        populate_by_name=True,
        from_attributes=True,
    )

    on_track: int = 0
    slow: int = 0
    quiet: int = 0
    not_started: int = 0
    ended: int = 0


class StrandMonitorPageOut(Wire):
    items: list[StrandMonitorEntryOut]
    page: int
    page_size: int
    total: int
    health_counts: StrandHealthCountsOut


class NudgeResultOut(Wire):
    sent_to: int


class StrandStateChangeIn(Wire):
    state: str
    reason: str | None = None


class SegmentCountOut(Wire):
    segment: BroadcastSegment
    count: int


class BroadcastOut(Wire):
    id: uuid.UUID
    segment: BroadcastSegment
    subject: str
    body: str
    #: Counted when it was sent, not recomputed. A segment's size changes, and a
    #: history that recalculated it would rewrite what happened.
    recipient_count: int
    state: BroadcastState
    created_at: datetime
    created_by: str
    scheduled_for: datetime | None = None
    delivered_count: int = 0
    failed_count: int = 0


class BroadcastCreateIn(Wire):
    segment: BroadcastSegment
    subject: str
    body: str
    #: Null sends now.
    scheduled_for: datetime | None = None


class BroadcastListingOut(Wire):
    items: list[BroadcastOut]
    segments: list[SegmentCountOut]
    merge_codes: list[MergeCodeOut]
