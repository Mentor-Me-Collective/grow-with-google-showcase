import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.deps import CurrentAccount, DbSession, participation_in
from app.enums import ParticipationStatus, Role, StrandState
from app.errors import not_found
from app.models import (
    Account,
    Application,
    Participation,
    Program,
    ProgramMilestone,
    Resource,
    Strand,
    StrandMember,
)
from app.schemas.reads import (
    DirectoryEntryOut,
    DirectoryPageOut,
    FormVersionOut,
    HomeSummaryOut,
    MilestoneOut,
    NextActionOut,
    ProfileSaveIn,
    ProfileViewOut,
    PublicProfileOut,
    ResourceOut,
)
from app.services import profiles

router = APIRouter(tags=["Participant"])


@router.get("/programs/{program_id}/home")
def get_home(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> HomeSummaryOut:
    """Everything the home screen puts on the page.

    One next action, never a list: design direction 9 gives home a single
    next-action card and says that if there is no next action, to say so plainly
    rather than invent one. A list of three would be a list of none.
    """
    me = participation_in(db, account, program_id)
    program = db.get(Program, program_id)

    strand_count = (
        db.scalar(
            select(func.count())
            .select_from(Strand)
            .join(StrandMember, StrandMember.strand_id == Strand.id)
            .where(
                StrandMember.participation_id == me.id,
                Strand.state == StrandState.ACTIVE,
            )
        )
        or 0
    )
    mentor_count = (
        db.scalar(
            select(func.count())
            .select_from(Participation)
            .where(
                Participation.program_id == program_id,
                Participation.role == Role.MENTOR,
                Participation.status == ParticipationStatus.APPROVED,
            )
        )
        or 0
    )

    version = profiles.published_version(db, program_id, me.role)
    answers = _my_answers(db, me, account)
    complete = (
        profiles.completeness(version, answers)
        if version
        else me.profile_completeness
    )

    return HomeSummaryOut(
        matching_opens_at=program.matching_opens_at if program else None,
        mentor_count=mentor_count,
        strand_count=strand_count,
        profile_completeness=complete,
        next_action=_next_action(complete, strand_count),
        announcement=None,
        upcoming_milestone=_upcoming_milestone(db, program),
    )


def _next_action(complete: float, strand_count: int) -> NextActionOut | None:
    if complete < 1.0:
        return NextActionOut(
            kind="complete_profile",
            title="Finish your profile",
            body=(
                "Matching works on what you tell us, so the answers you have not "
                "given are the ones costing you a better match."
            ),
            action_label="Finish it",
            href="/me/edit",
        )
    if strand_count > 0:
        return NextActionOut(
            kind="reply_to_message",
            title="Open your strand",
            body=(
                "The first conversation is the one that decides whether the "
                "rest happen."
            ),
            action_label="Open it",
            href="/strands",
        )
    return None


def _upcoming_milestone(db, program: Program | None) -> MilestoneOut | None:
    """The next point in the arc, resolved to a real date against the cohort
    start. The arc is stored in weeks so it survives a cohort being re-run."""
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


def _my_answers(db, me: Participation, account: Account) -> dict:
    """A profile is the application answers read back.

    There is no second store for it — inventing one would mean a coordinator's
    question could be asked and then never seen again.
    """
    application = db.scalar(
        select(Application)
        .where(
            Application.program_id == me.program_id,
            Application.email == account.email,
        )
        .order_by(Application.submitted_at.desc())
        .limit(1)
    )
    return dict(application.answers) if application else {}


@router.get("/programs/{program_id}/me")
def get_my_profile(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> ProfileViewOut:
    me = participation_in(db, account, program_id)
    version = profiles.published_version(db, program_id, me.role)
    if version is None:
        raise not_found("form")

    answers = _my_answers(db, me, account)
    return ProfileViewOut(
        participation_id=me.id,
        name=account.name,
        role=me.role,
        photo_url=account.photo_url,
        headline=me.headline,
        timezone=me.timezone,
        completeness=profiles.completeness(version, answers),
        form_version=FormVersionOut.model_validate(version),
        answers=answers,
        thin_field_ids=profiles.thin_field_ids(version, answers),
    )


@router.put("/programs/{program_id}/me")
def save_my_profile(
    program_id: uuid.UUID,
    body: ProfileSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> ProfileViewOut:
    """Partial by design: only the answers sent are written, so a per-section
    save cannot blank the sections that were never on screen."""
    me = participation_in(db, account, program_id)
    version = profiles.published_version(db, program_id, me.role)
    if version is None:
        raise not_found("form")

    application = db.scalar(
        select(Application)
        .where(
            Application.program_id == program_id,
            Application.email == account.email,
        )
        .order_by(Application.submitted_at.desc())
        .limit(1)
    )
    if application is None:
        raise not_found("application")

    now = datetime.now(UTC).isoformat()
    merged = dict(application.answers)
    for field_id, answer in body.answers.items():
        # The server owns the clock. A client-supplied timestamp is not
        # evidence of anything.
        merged[field_id] = {**answer, "answeredAt": now}
    application.answers = merged

    me.profile_completeness = profiles.completeness(version, merged)
    db.commit()

    return ProfileViewOut(
        participation_id=me.id,
        name=account.name,
        role=me.role,
        photo_url=account.photo_url,
        headline=me.headline,
        timezone=me.timezone,
        completeness=me.profile_completeness,
        form_version=FormVersionOut.model_validate(version),
        answers=merged,
        thin_field_ids=profiles.thin_field_ids(version, merged),
    )


@router.get("/programs/{program_id}/directory")
def list_directory(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    q: str | None = Query(None),
    skill: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
) -> DirectoryPageOut:
    me = participation_in(db, account, program_id)
    program = db.get(Program, program_id)

    wanted = Role.MENTEE if me.role == Role.MENTOR else Role.MENTOR
    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.role == wanted,
            Participation.status == ParticipationStatus.APPROVED,
        )
        .order_by(Account.name)
    ).all()

    entries = [
        DirectoryEntryOut(
            participation_id=participation.id,
            name=person.name,
            role=participation.role,
            photo_url=person.photo_url,
            headline=participation.headline,
            timezone=participation.timezone,
            skills=participation.skills or [],
            # Shown rather than hidden when full, per architecture 4.9: the
            # scarcity is the information.
            available=profiles.is_available(participation),
            unavailable_reason=(
                None
                if profiles.is_available(participation)
                else "Already mentoring as many people as they agreed to"
            ),
        )
        for participation, person in rows
    ]

    needle = (q or "").strip().lower()
    filtered = [
        e
        for e in entries
        if (not skill or skill in e.skills)
        and (
            not needle
            or needle in e.name.lower()
            or needle in (e.headline or "").lower()
            or any(needle in s.lower() for s in e.skills)
        )
    ]

    start = (page - 1) * page_size
    return DirectoryPageOut(
        items=filtered[start : start + page_size],
        page=page,
        page_size=page_size,
        total=len(filtered),
        self_matching_enabled=bool(program and program.self_matching_enabled),
        skills=sorted({s for e in entries for s in e.skills}),
    )


@router.get("/participations/{participation_id}/profile")
def get_public_profile(
    participation_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> PublicProfileOut:
    row = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(Participation.id == participation_id)
    ).first()
    if row is None:
        raise not_found("participant")
    participation, person = row

    # Only somebody in the same programme may read it.
    participation_in(db, account, participation.program_id)

    version = profiles.published_version(
        db, participation.program_id, participation.role
    )
    application = db.scalar(
        select(Application)
        .where(
            Application.program_id == participation.program_id,
            Application.email == person.email,
        )
        .order_by(Application.submitted_at.desc())
        .limit(1)
    )
    sections = (
        profiles.shareable_sections(version, application.answers)
        if version and application
        else []
    )

    return PublicProfileOut(
        participation_id=participation.id,
        name=person.name,
        role=participation.role,
        photo_url=person.photo_url,
        headline=participation.headline,
        timezone=participation.timezone,
        skills=participation.skills or [],
        available=profiles.is_available(participation),
        capacity=participation.capacity,
        load=participation.load,
        sections=sections,
    )


@router.get("/programs/{program_id}/resources")
def list_resources(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> list[ResourceOut]:
    participation_in(db, account, program_id)
    return [
        ResourceOut.model_validate(r)
        for r in db.scalars(
            select(Resource)
            .where(Resource.program_id == program_id)
            .order_by(Resource.title)
        ).all()
    ]
