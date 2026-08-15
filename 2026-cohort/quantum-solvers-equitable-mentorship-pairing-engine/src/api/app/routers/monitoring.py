import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import CurrentAccount, DbSession, require_coordinator_of_program
from app.enums import (
    ApplicationStatus,
    AuditAction,
    BroadcastSegment,
    BroadcastState,
    ParticipationStatus,
    Role,
    StrandState,
)
from app.errors import Problem, not_found
from app.models import (
    Application,
    AuditEvent,
    Broadcast,
    Participation,
    Program,
    ProgramMilestone,
    Strand,
    StrandMember,
)
from app.routers.setup import _merge_codes, _unknown_codes
from app.schemas.monitoring import (
    AttentionItemOut,
    BroadcastCreateIn,
    BroadcastListingOut,
    BroadcastOut,
    DashboardSummaryOut,
    NudgeResultOut,
    SegmentCountOut,
    StrandHealthCountsOut,
    StrandMonitorEntryOut,
    StrandMonitorPageOut,
    StrandStateChangeIn,
)
from app.schemas.reads import MilestoneOut
from app.services import health as health_svc
from app.services import strands as strand_svc

router = APIRouter(tags=["Monitoring"])


def _entries(db: Session, program_id: uuid.UUID) -> list[StrandMonitorEntryOut]:
    total_milestones = health_svc.milestone_total(db, program_id)
    out: list[StrandMonitorEntryOut] = []

    for strand in db.scalars(
        select(Strand)
        .where(Strand.program_id == program_id)
        .order_by(Strand.last_activity_at.desc().nullsfirst())
    ).all():
        days = health_svc.days_since(strand.last_activity_at)
        out.append(
            StrandMonitorEntryOut(
                id=strand.id,
                state=strand.state,
                origin_mode=strand.origin_mode,
                # The full membership, not "everybody except me": a coordinator
                # is not a party to most of these and needs both names to know
                # which pairing a row is.
                members=[
                    strand_svc.to_member(p, a)
                    for p, a in strand_svc.member_rows(db, strand)
                ],
                days_since_activity=days,
                sessions_logged=strand.sessions_logged,
                milestones_completed=strand.milestones_completed,
                milestones_total=total_milestones,
                health=health_svc.health_of(
                    strand,
                    days,
                    health_svc.has_messages(db, strand.id),
                    strand.milestones_completed,
                    total_milestones,
                ),
            )
        )
    return out


@router.get("/programs/{program_id}/dashboard")
def get_dashboard(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> DashboardSummaryOut:
    """Programme health in one response.

    The attention list is the point of it: counts say how things are, and the
    list says what to do about them.
    """
    require_coordinator_of_program(db, account, program_id)
    program = db.get(Program, program_id)

    def people(role: Role) -> int:
        return (
            db.scalar(
                select(func.count())
                .select_from(Participation)
                .where(
                    Participation.program_id == program_id,
                    Participation.role == role,
                    Participation.status == ParticipationStatus.APPROVED,
                )
            )
            or 0
        )

    entries = _entries(db, program_id)
    active = [e for e in entries if e.state == StrandState.ACTIVE]
    quiet = [e for e in active if e.health == "quiet"]
    never_started = [e for e in active if e.health == "not_started"]

    matched = (
        db.scalar(
            select(func.count())
            .select_from(Participation)
            .where(
                Participation.program_id == program_id,
                Participation.role == Role.MENTEE,
                Participation.matched.is_(True),
            )
        )
        or 0
    )
    unmatched = (
        db.scalar(
            select(func.count())
            .select_from(Participation)
            .where(
                Participation.program_id == program_id,
                Participation.status == ParticipationStatus.APPROVED,
                Participation.matched.is_(False),
            )
        )
        or 0
    )
    waiting = (
        db.scalar(
            select(func.count())
            .select_from(Application)
            .where(
                Application.program_id == program_id,
                Application.status == ApplicationStatus.SUBMITTED,
            )
        )
        or 0
    )
    over_capacity = len(
        [
            p
            for p in db.scalars(
                select(Participation).where(
                    Participation.program_id == program_id,
                    Participation.role == Role.MENTOR,
                )
            ).all()
            if p.capacity is not None and (p.load or 0) > p.capacity
        ]
    )
    incomplete = (
        db.scalar(
            select(func.count())
            .select_from(Participation)
            .where(
                Participation.program_id == program_id,
                Participation.status == ParticipationStatus.APPROVED,
                Participation.profile_completeness < 0.6,
            )
        )
        or 0
    )

    # Ordered by what it costs to leave alone, not by count. An unread
    # application stops somebody joining at all; a thin profile only makes a
    # match worse.
    attention: list[AttentionItemOut] = []
    if waiting:
        attention.append(
            AttentionItemOut(
                kind="applications_waiting",
                count=waiting,
                title=(
                    f"{waiting} "
                    f"{'application is' if waiting == 1 else 'applications are'} "
                    "waiting to be read"
                ),
                body="Nobody joins the roster until these are decided.",
                action_label="Read them",
                href="/applications",
            )
        )
    if unmatched:
        attention.append(
            AttentionItemOut(
                kind="unmatched_people",
                count=unmatched,
                title=(
                    f"{unmatched} "
                    f"{'person has' if unmatched == 1 else 'people have'} "
                    "no strand"
                ),
                body="Each one has a reason, and the reasons need different things.",
                action_label="Open the queue",
                href="/unmatched",
            )
        )
    if never_started:
        n = len(never_started)
        attention.append(
            AttentionItemOut(
                kind="strands_never_started",
                count=n,
                title=f"{n} {'strand has' if n == 1 else 'strands have'} never started",
                body=(
                    "Matched, but nobody has written anything yet. The first "
                    "message is the one that decides whether the rest happen."
                ),
                action_label="See which",
                href="/strands?health=not_started",
            )
        )
    if quiet:
        n = len(quiet)
        attention.append(
            AttentionItemOut(
                kind="quiet_strands",
                count=n,
                title=f"{n} {'strand has' if n == 1 else 'strands have'} gone quiet",
                body="A fortnight without a message. A nudge is usually enough.",
                action_label="See which",
                href="/strands?health=quiet",
            )
        )
    if over_capacity:
        attention.append(
            AttentionItemOut(
                kind="mentors_over_capacity",
                count=over_capacity,
                title=(
                    f"{over_capacity} "
                    f"{'mentor is' if over_capacity == 1 else 'mentors are'} "
                    "over the capacity they set"
                ),
                body="They agreed to fewer mentees than they now hold.",
                action_label="Open the roster",
                href="/roster",
            )
        )
    if incomplete:
        attention.append(
            AttentionItemOut(
                kind="incomplete_profiles",
                count=incomplete,
                title=(
                    f"{incomplete} "
                    f"{'profile is' if incomplete == 1 else 'profiles are'} "
                    "too thin to match well"
                ),
                body=(
                    "Matching works on what people tell us. These need a nudge, "
                    "not a decision."
                ),
                action_label="Open the roster",
                href="/roster",
            )
        )

    return DashboardSummaryOut(
        mentor_count=people(Role.MENTOR),
        mentee_count=people(Role.MENTEE),
        recruitment_goal=program.recruitment_goal if program else None,
        matched_count=matched,
        unmatched_count=unmatched,
        active_strands=len(active),
        quiet_strands=len(quiet),
        # Logged, not scheduled: logging is the engagement signal the health
        # view and the report both read.
        sessions_logged_this_week=sum(e.sessions_logged for e in active),
        upcoming_milestone=_next_milestone(db, program),
        attention=attention,
    )


def _next_milestone(db: Session, program: Program | None) -> MilestoneOut | None:
    if program is None or program.cohort_start is None:
        return None
    now = datetime.now(UTC)
    for milestone in db.scalars(
        select(ProgramMilestone)
        .where(ProgramMilestone.program_id == program.id)
        .order_by(ProgramMilestone.week_offset, ProgramMilestone.position)
    ).all():
        due = datetime.combine(
            program.cohort_start, datetime.min.time(), tzinfo=UTC
        ) + timedelta(weeks=milestone.week_offset)
        if due >= now:
            return MilestoneOut(
                id=milestone.id, title=milestone.title, due_at=due, completed=False
            )
    return None


@router.get("/programs/{program_id}/strand-monitor")
def monitor_strands(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    health: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200, alias="pageSize"),
) -> StrandMonitorPageOut:
    require_coordinator_of_program(db, account, program_id)

    entries = _entries(db, program_id)
    counts = StrandHealthCountsOut()
    for entry in entries:
        setattr(counts, entry.health, getattr(counts, entry.health, 0) + 1)

    filtered = [e for e in entries if health is None or e.health == health]
    start = (page - 1) * page_size

    return StrandMonitorPageOut(
        items=filtered[start : start + page_size],
        page=page,
        page_size=page_size,
        total=len(filtered),
        health_counts=counts,
    )


@router.post("/strands/{strand_id}/nudge", status_code=202)
def nudge_strand(
    strand_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> NudgeResultOut:
    """Sends the programme's nudge template rather than free text, so the
    wording is the one already reviewed and every quiet strand gets the same
    message."""
    strand = db.get(Strand, strand_id)
    if strand is None:
        raise not_found("strand")
    require_coordinator_of_program(db, account, strand.program_id)

    if strand.state == StrandState.ENDED:
        raise Problem(
            409, "strand_ended", "This strand has ended. There is nobody to nudge."
        )

    members = (
        db.scalar(
            select(func.count())
            .select_from(StrandMember)
            .where(StrandMember.strand_id == strand.id)
        )
        or 0
    )
    return NudgeResultOut(sent_to=members)


@router.put("/strands/{strand_id}/state")
def set_strand_state(
    strand_id: uuid.UUID,
    body: StrandStateChangeIn,
    db: DbSession,
    account: CurrentAccount,
):
    """Ending is one way.

    A strand that ended keeps its conversation and stays readable to both sides;
    it is not deleted, because the record of what was said is the thing
    participants come back for.
    """
    strand = db.get(Strand, strand_id)
    if strand is None:
        raise not_found("strand")
    require_coordinator_of_program(db, account, strand.program_id)

    if body.state not in ("active", "paused", "ended"):
        raise Problem(400, "invalid_state", "Choose active, paused or ended.")
    if strand.state == StrandState.ENDED:
        raise Problem(409, "already_ended", "This strand has already ended.")

    strand.state = body.state
    strand.ended_at = datetime.now(UTC) if body.state == "ended" else None

    if body.state == "ended":
        for member in strand.members:
            participation = db.get(Participation, member.participation_id)
            if participation is None:
                continue
            if participation.role == Role.MENTOR:
                participation.load = max((participation.load or 1) - 1, 0)
            else:
                participation.matched = False

        program = db.get(Program, strand.program_id)
        if program is not None:
            db.add(
                AuditEvent(
                    organisation_id=program.organisation_id,
                    at=datetime.now(UTC),
                    actor_name=account.name,
                    action=AuditAction.STRAND_ENDED,
                    summary=(
                        "Ended a strand. The conversation is kept and stays "
                        "readable to both sides."
                    ),
                    subject_label=body.reason or "No reason given",
                )
            )

    db.commit()
    db.refresh(strand)
    return strand_svc.to_strand(db, strand)


# --- broadcast ----------------------------------------------------------

comms = APIRouter(tags=["Comms"])

SEGMENTS = list(BroadcastSegment)


def _segment_size(db: Session, program_id: uuid.UUID, segment: str) -> int:
    """Counted now, from the same data the monitor reads."""
    base = select(func.count()).select_from(Participation).where(
        Participation.program_id == program_id,
        Participation.status == ParticipationStatus.APPROVED,
    )
    if segment == BroadcastSegment.EVERYONE:
        return db.scalar(base) or 0
    if segment == BroadcastSegment.MENTORS:
        return db.scalar(base.where(Participation.role == Role.MENTOR)) or 0
    if segment == BroadcastSegment.MENTEES:
        return db.scalar(base.where(Participation.role == Role.MENTEE)) or 0
    if segment == BroadcastSegment.UNMATCHED:
        return db.scalar(base.where(Participation.matched.is_(False))) or 0
    if segment == BroadcastSegment.INCOMPLETE_PROFILES:
        return db.scalar(base.where(Participation.profile_completeness < 0.6)) or 0
    if segment == BroadcastSegment.QUIET_STRANDS:
        # People, not strands: both sides of a quiet strand hear about it.
        return sum(
            len(e.members)
            for e in _entries(db, program_id)
            if e.state == StrandState.ACTIVE and e.health in ("quiet", "not_started")
        )
    return 0


@comms.get("/programs/{program_id}/broadcasts")
def list_broadcasts(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> BroadcastListingOut:
    require_coordinator_of_program(db, account, program_id)

    return BroadcastListingOut(
        items=[
            BroadcastOut.model_validate(b)
            for b in db.scalars(
                select(Broadcast)
                .where(Broadcast.program_id == program_id)
                .order_by(Broadcast.created_at.desc())
            ).all()
        ],
        segments=[
            SegmentCountOut(segment=s, count=_segment_size(db, program_id, s))
            for s in SEGMENTS
        ],
        merge_codes=_merge_codes(db.get(Program, program_id)),
    )


@comms.post("/programs/{program_id}/broadcasts", status_code=202)
def send_broadcast(
    program_id: uuid.UUID,
    body: BroadcastCreateIn,
    db: DbSession,
    account: CurrentAccount,
) -> BroadcastOut:
    require_coordinator_of_program(db, account, program_id)

    if not body.subject.strip() or not body.body.strip():
        raise Problem(400, "invalid_body", "A message needs a subject and a body.")

    unknown = _unknown_codes(f"{body.subject} {body.body}")
    if unknown:
        raise Problem(
            400,
            "unknown_merge_code",
            f"There is no such code as {{{unknown[0]}}}. Use one from the list.",
        )

    count = _segment_size(db, program_id, body.segment)
    if count == 0:
        # Refused rather than sent to nobody: a send that reached zero people
        # still appears in the history as a send, and the coordinator would
        # believe the message went out.
        raise Problem(
            400,
            "empty_segment",
            "Nobody is in that group right now, so there is nobody to write to.",
        )

    now = datetime.now(UTC)
    broadcast = Broadcast(
        program_id=program_id,
        segment=body.segment,
        subject=body.subject,
        body=body.body,
        recipient_count=count,
        delivered_count=0 if body.scheduled_for else count,
        failed_count=0,
        state=BroadcastState.SCHEDULED if body.scheduled_for else BroadcastState.SENT,
        created_at=now,
        created_by=account.name,
        scheduled_for=body.scheduled_for,
    )
    db.add(broadcast)

    program = db.get(Program, program_id)
    if program is not None:
        db.add(
            AuditEvent(
                organisation_id=program.organisation_id,
                at=now,
                actor_name=account.name,
                action=AuditAction.BROADCAST_SENT,
                summary=f'Sent "{body.subject}" to {count} people.',
                subject_label=body.segment,
            )
        )

    db.commit()
    db.refresh(broadcast)
    return BroadcastOut.model_validate(broadcast)
