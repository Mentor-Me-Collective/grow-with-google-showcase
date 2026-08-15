"""The report a coordinator sends a funder, derived rather than stored.

Nothing here is a counter that somebody has to remember to increment. Every
figure is computed from the roster, the strands and the projection at read time,
so a report cannot drift from the programme it describes — and a run published
this morning shows up in it this morning.

Two rules in here are ethical rather than technical and are not tuning knobs:

*   Demographics are gated on the reporting consent the applicant actually
    ticked, not on the fact that the answer exists. An answer given so a match
    could be made was not given so it could appear in a funder's PDF.
*   Buckets at or below `SUPPRESSION_THRESHOLD` are withheld and counted, never
    rounded or merged into an "other". In a cohort of twenty, a column of one
    plus any second column is an identification.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums import (
    ApplicationStatus,
    ParticipationStatus,
    PriorityBand,
    Role,
    RunState,
    StrandState,
)
from app.models import (
    Account,
    Application,
    FormVersion,
    Message,
    Participation,
    Program,
    ProgramMilestone,
    Run,
    Strand,
    StrandMember,
)
from app.models.matching import ParticipantAttribute
from app.schemas.insight import (
    CountPointOut,
    DemographicBreakdownOut,
    DropOffStageOut,
    MentorLoadOut,
    MilestoneCompletionOut,
    ProgramReportOut,
    TimePointOut,
)
from app.schemas.matching import PersonRefOut
from app.services.profiles import all_fields, published_version

#: Design direction: a bucket this size or smaller is withheld. Three is the
#: smallest number at which a reader cannot walk a column back to a person by
#: crossing it with anything else they already know about the cohort.
SUPPRESSION_THRESHOLD = 3

#: How far back the report looks when the coordinator has not chosen a range.
DEFAULT_RANGE_DAYS = 90


def default_range(db: Session, program: Program, today: date) -> tuple[date, date]:
    """The window the report opens on when nobody has chosen one.

    Not the cohort's advertised dates. A cohort that starts in September has
    been taking applications since June, and anchoring on `cohort_start` would
    open the report on an empty range in exactly the weeks a coordinator is
    reporting on recruitment. So it starts at the earliest thing there is to
    say something about, and only falls back to a fixed quarter when there is
    nothing at all.
    """
    end = min(program.cohort_end, today) if program.cohort_end else today

    earliest = db.scalar(
        select(func.min(Application.submitted_at)).where(
            Application.program_id == program.id
        )
    )
    candidates = [
        candidate
        for candidate in (program.cohort_start, earliest.date() if earliest else None)
        if candidate is not None and candidate <= end
    ]
    start = min(candidates) if candidates else end - timedelta(days=DEFAULT_RANGE_DAYS)
    return start, end


def _end_of(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=UTC)


def _weeks(start: date, end: date, limit: int = 26) -> list[date]:
    """Week endings across the range, newest last.

    Capped so a two-year cohort does not produce a chart with a hundred and four
    unreadable points; the range is widened per step rather than truncated, so
    the last point is always `end`.
    """
    span = max((end - start).days, 0)
    step = max(7, -(-span // limit) if limit else 7)
    days = list(range(0, span + 1, step))
    if not days or days[-1] != span:
        days.append(span)
    return [start + timedelta(days=d) for d in days]


def coverage_over_time(
    db: Session, program_id: uuid.UUID, start: date, end: date
) -> list[TimePointOut]:
    """Share of mentees holding a strand, at each week end.

    Both halves move: a mentee approved in week six changes the denominator for
    week six onwards but not for week five. Computing it against a fixed final
    roster would flatter the early weeks, which is exactly the part a funder is
    reading for.
    """
    mentees = db.execute(
        select(Participation.id, Participation.joined_at).where(
            Participation.program_id == program_id,
            Participation.role == Role.MENTEE,
            Participation.status == ParticipationStatus.APPROVED,
        )
    ).all()

    # When a mentee joined a strand, taken as when the strand was created.
    matched_at = dict(
        db.execute(
            select(StrandMember.participation_id, func.min(Strand.created_at))
            .join(Strand, StrandMember.strand_id == Strand.id)
            .where(Strand.program_id == program_id)
            .group_by(StrandMember.participation_id)
        ).all()
    )

    points: list[TimePointOut] = []
    for week in _weeks(start, end):
        cutoff = _end_of(week)
        pool = [m for m in mentees if m.joined_at is None or m.joined_at <= cutoff]
        if not pool:
            points.append(TimePointOut(date=week, value=0.0))
            continue
        held = sum(
            1
            for m in pool
            if (at := matched_at.get(m.id)) is not None and at <= cutoff
        )
        points.append(TimePointOut(date=week, value=round(held / len(pool), 4)))
    return points


def mentor_load(db: Session, program_id: uuid.UUID) -> list[MentorLoadOut]:
    """Live load against stated capacity, counted from strands.

    Not `Participation.load`, which is a cached number: a report that repeated a
    stale counter would be wrong in precisely the direction nobody checks.
    """
    counts = dict(
        db.execute(
            select(StrandMember.participation_id, func.count())
            .join(Strand, StrandMember.strand_id == Strand.id)
            .where(
                Strand.program_id == program_id,
                Strand.state != StrandState.ENDED,
            )
            .group_by(StrandMember.participation_id)
        ).all()
    )

    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.role == Role.MENTOR,
            Participation.status == ParticipationStatus.APPROVED,
        )
        .order_by(Account.name)
    ).all()

    return [
        MentorLoadOut(
            mentor=PersonRefOut(
                participation_id=participation.id,
                name=account.name,
                photo_url=account.photo_url,
            ),
            load=counts.get(participation.id, 0),
            capacity=participation.capacity or 0,
        )
        for participation, account in rows
    ]


def quality_by_band(db: Session, program_id: uuid.UUID) -> list[dict[str, Any]]:
    """The published run's own fairness figures, not recomputed here.

    The report has to agree with what the coordinator approved on the run review
    screen. Recomputing would let the two disagree after a recipe edit, and the
    number that was signed off is the one that has to be defensible.
    """
    run = db.scalar(
        select(Run)
        .where(
            Run.program_id == program_id,
            Run.state == RunState.PUBLISHED,
            Run.fairness_summary.is_not(None),
        )
        .order_by(Run.published_at.desc())
        .limit(1)
    )
    if run is None:
        return []
    bands = (run.fairness_summary or {}).get("priorityBands") or []
    order = {b.value: i for i, b in enumerate(PriorityBand)}
    return sorted(bands, key=lambda b: order.get(b.get("band", ""), 99))


def milestone_completion(
    db: Session, program_id: uuid.UUID
) -> list[MilestoneCompletionOut]:
    """How far each milestone got, from the per-strand count.

    A strand records how many milestones it has reached rather than which ones,
    and the milestones are an ordered arc, so a strand at three has passed one,
    two and three. That is an assumption about the model, not about the people:
    if milestones ever become individually tickable, this reads the join table
    instead and nothing above it changes.
    """
    milestones = db.scalars(
        select(ProgramMilestone)
        .where(ProgramMilestone.program_id == program_id)
        .order_by(ProgramMilestone.position, ProgramMilestone.week_offset)
    ).all()
    if not milestones:
        return []

    reached = db.scalars(
        select(Strand.milestones_completed).where(Strand.program_id == program_id)
    ).all()
    total = len(reached)

    return [
        MilestoneCompletionOut(
            title=milestone.title,
            completed=sum(1 for r in reached if r >= index),
            total=total,
        )
        for index, milestone in enumerate(milestones, start=1)
    ]


def drop_off(db: Session, program_id: uuid.UUID, end: date) -> list[DropOffStageOut]:
    """Counts at each stage of the funnel, as they stood at the end of the range.

    Cumulative to `to` rather than confined to the window, and every stage on the
    same footing. The mixed reading — applications inside the window against a
    roster that ignores it — is the one that produces a funnel widening as it
    goes down, which reads as a bug even when every figure in it is right.

    Every stage counts people, not events, and each is a subset of the one
    above, so the differences are readable as losses without further arithmetic.
    """
    until = _end_of(end)

    applied = (
        db.scalar(
            select(func.count())
            .select_from(Application)
            .where(
                Application.program_id == program_id,
                Application.submitted_at <= until,
            )
        )
        or 0
    )

    approved_ids = set(
        db.scalars(
            select(Participation.id).where(
                Participation.program_id == program_id,
                Participation.status == ParticipationStatus.APPROVED,
                # A participation with no joining date predates the record
                # rather than postdating the range, so it counts.
                (Participation.joined_at.is_(None))
                | (Participation.joined_at <= until),
            )
        ).all()
    )

    members = db.execute(
        select(
            StrandMember.participation_id,
            Strand.state,
            Strand.sessions_logged,
        )
        .join(Strand, StrandMember.strand_id == Strand.id)
        .where(Strand.program_id == program_id, Strand.created_at <= until)
    ).all()

    matched = {m.participation_id for m in members} & approved_ids
    with_sessions = {
        m.participation_id for m in members if m.sessions_logged > 0
    } & approved_ids
    still_active = {
        m.participation_id for m in members if m.state == StrandState.ACTIVE
    } & approved_ids

    # Intersected with `matched` rather than with the roster: somebody can only
    # have written in a strand they were in, so anything else would let a stage
    # come out larger than the one above it and the funnel would read backwards.
    spoke = (
        set(
            db.scalars(
                select(Message.author_participation_id)
                .join(Strand, Message.strand_id == Strand.id)
                .where(Strand.program_id == program_id, Message.sent_at <= until)
            ).all()
        )
        & matched
    )

    # An applicant may never have become a participation, so `applied` is
    # allowed to exceed everything below it — that gap is the first loss and the
    # one a recruitment drive is judged on.
    return [
        DropOffStageOut(stage="applied", count=max(applied, len(approved_ids))),
        DropOffStageOut(stage="approved", count=len(approved_ids)),
        DropOffStageOut(stage="matched", count=len(matched)),
        DropOffStageOut(stage="first_message", count=len(spoke)),
        DropOffStageOut(stage="first_session", count=len(with_sessions)),
        DropOffStageOut(stage="still_active", count=len(still_active)),
    ]


def _reporting_consent_fields(version: FormVersion) -> list[str]:
    """Which questions on this form ask permission to be reported on.

    Recognised by being an optional consent whose statement is about reporting.
    A required consent is a condition of applying and so carries no choice; an
    optional one is the only place in the form where somebody actually says yes
    or no to this.

    The honest fix is a `purpose` on the consent field in the contract, so the
    form builder states it rather than the reader inferring it. Until then this
    is deliberately narrow: a form that asks nothing yields nobody, and the
    demographics section stays empty rather than reporting people who were never
    asked.
    """
    return [
        field["id"]
        for field in all_fields(version)
        if field["type"] == "consent"
        and not field.get("required")
        and "report" in ((field.get("consent") or {}).get("statement") or "").lower()
    ]


def consenting_participations(db: Session, program_id: uuid.UUID) -> set[uuid.UUID]:
    """Participations whose applicant ticked every reporting consent asked."""
    versions = {
        role: published_version(db, program_id, role)
        for role in (Role.MENTEE, Role.MENTOR)
    }
    wanted = {
        version.id: _reporting_consent_fields(version)
        for version in versions.values()
        if version is not None
    }
    if not any(wanted.values()):
        return set()

    by_email = {
        email: participation_id
        for participation_id, email in db.execute(
            select(Participation.id, Account.email)
            .join(Account, Participation.account_id == Account.id)
            .where(
                Participation.program_id == program_id,
                Participation.status == ParticipationStatus.APPROVED,
            )
        ).all()
    }

    consenting: set[uuid.UUID] = set()
    for application in db.scalars(
        select(Application).where(
            Application.program_id == program_id,
            Application.status == ApplicationStatus.APPROVED,
        )
    ).all():
        fields = wanted.get(application.form_version_id)
        if not fields:
            continue
        answers = application.answers or {}
        if all(bool((answers.get(f) or {}).get("value")) for f in fields):
            participation_id = by_email.get(application.email)
            if participation_id is not None:
                consenting.add(participation_id)
    return consenting


def _field_catalogue(db: Session, program_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    """Every equity question on either live form, by id, with its option labels."""
    catalogue: dict[str, dict[str, Any]] = {}
    for role in (Role.MENTEE, Role.MENTOR):
        version = published_version(db, program_id, role)
        if version is None:
            continue
        for field in all_fields(version):
            # `admin` fields are the coordinator's own working notes and never
            # leave the roster, whatever else is flagged on them.
            if field.get("equity") and not field.get("admin"):
                catalogue.setdefault(field["id"], field)
    return catalogue


def _bucket_label(field: dict[str, Any], value: Any) -> str | None:
    """One answer as the word a reader would use for it.

    Free text is not bucketed at all: it has no vocabulary to count, and
    grouping it by hand would be the report inventing categories nobody chose.
    """
    kind = field["type"]
    if kind in ("single_select", "multi_select"):
        labels = {o["id"]: o["label"] for o in (field.get("options") or [])}
        return labels.get(str(value))
    if kind == "scale":
        scale = field.get("scale") or {}
        low, high = scale.get("min", 1), scale.get("max", 5)
        if int(value) == low and scale.get("minLabel"):
            return f"{int(value)} — {scale['minLabel']}"
        if int(value) == high and scale.get("maxLabel"):
            return f"{int(value)} — {scale['maxLabel']}"
        return str(int(value))
    if kind == "number":
        # Bands rather than raw years: "7" is one person, "5 to 9" is a group.
        years = float(value)
        for lower, upper in ((0, 1), (2, 4), (5, 9)):
            if lower <= years <= upper:
                return f"{lower} to {upper}" if lower != upper else str(lower)
        return "10 or more"
    return None


def demographics(
    db: Session, program_id: uuid.UUID
) -> list[DemographicBreakdownOut]:
    catalogue = _field_catalogue(db, program_id)
    if not catalogue:
        return []

    consenting = consenting_participations(db, program_id)
    if not consenting:
        return []

    attributes = db.scalars(
        select(ParticipantAttribute).where(
            ParticipantAttribute.program_id == program_id,
            ParticipantAttribute.equity.is_(True),
            ParticipantAttribute.participation_id.in_(consenting),
        )
    ).all()

    tallies: dict[str, Counter[str]] = {}
    for attribute in attributes:
        field = catalogue.get(str(attribute.field_id))
        if field is None:
            continue
        values: list[Any] = (
            list(attribute.option_values)
            if attribute.option_values
            else [attribute.number_value]
            if attribute.number_value is not None
            else []
        )
        for value in values:
            label = _bucket_label(field, value)
            if label is not None:
                tallies.setdefault(str(attribute.field_id), Counter())[label] += 1

    out: list[DemographicBreakdownOut] = []
    for field_id, counter in tallies.items():
        kept = [
            CountPointOut(label=label, count=count)
            for label, count in sorted(counter.items())
            if count > SUPPRESSION_THRESHOLD
        ]
        withheld = len(counter) - len(kept)
        # A breakdown where everything was suppressed is still reported, as a
        # label with nothing under it. Silently dropping it would read as a
        # question nobody answered.
        out.append(
            DemographicBreakdownOut(
                field_id=uuid.UUID(field_id),
                label=catalogue[field_id]["label"],
                buckets=kept,
                suppressed_buckets=withheld,
            )
        )
    return out


def sessions_by_week(db: Session, program_id: uuid.UUID) -> list[CountPointOut]:
    """Empty, on purpose.

    A strand carries how many sessions it has logged but not when any of them
    happened, so there is no honest way to put them on a week axis. Attributing
    a strand's whole total to the week it last spoke would draw a plausible
    chart out of a number that does not contain that information, and a report
    whose weakest figure is invented is not worth its strongest.

    This fills in when sessions become dated rows rather than a counter.
    """
    return []


def check_in_sentiment(db: Session, program_id: uuid.UUID) -> list[CountPointOut]:
    """Empty until check-ins exist. The mid-point check-in is a message template
    today, not a question with recorded answers, so there is nothing to count."""
    return []


def build(db: Session, program: Program, start: date, end: date) -> ProgramReportOut:
    bands = quality_by_band(db, program.id)
    return ProgramReportOut(
        program_name=program.name,
        from_=start,
        to=end,
        coverage_over_time=coverage_over_time(db, program.id, start, end),
        mentor_load=mentor_load(db, program.id),
        quality_by_band=bands,
        sessions_by_week=sessions_by_week(db, program.id),
        check_in_sentiment=check_in_sentiment(db, program.id),
        check_in_response_rate=None,
        milestone_completion=milestone_completion(db, program.id),
        drop_off=drop_off(db, program.id, end),
        demographics=demographics(db, program.id),
        suppression_threshold=SUPPRESSION_THRESHOLD,
    )
