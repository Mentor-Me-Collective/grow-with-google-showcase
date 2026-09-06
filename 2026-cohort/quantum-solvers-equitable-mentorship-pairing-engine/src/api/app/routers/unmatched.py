import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.deps import CurrentAccount, DbSession, require_coordinator_of_program
from app.enums import (
    AuditAction,
    OriginMode,
    ParticipationStatus,
    Role,
    RunState,
    StrandState,
    UnmatchedReason,
)
from app.errors import Problem, not_found
from app.models import (
    Account,
    AuditEvent,
    Participation,
    Program,
    Run,
    RunUnmatched,
    Strand,
    StrandMember,
)
from app.schemas.matching import (
    AvailableMentorOut,
    StrandCreateIn,
    UnmatchedEntryOut,
    UnmatchedPageOut,
)
from app.schemas.reads import StrandOut
from app.services import strands as strand_svc

router = APIRouter(tags=["Unmatched"])


@router.get("/programs/{program_id}/unmatched")
def list_unmatched(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    reason: UnmatchedReason | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
) -> UnmatchedPageOut:
    """Everyone in the programme without a strand, and why.

    Built from the most recent published run plus anybody the roster shows as
    unmatched — somebody who joined in week three was never in a run at all, and
    a queue that only listed run failures would lose them silently.
    """
    require_coordinator_of_program(db, account, program_id)

    latest = db.scalar(
        select(Run)
        .where(Run.program_id == program_id, Run.state == RunState.PUBLISHED)
        .order_by(Run.created_at.desc())
        .limit(1)
    )
    from_run: dict[uuid.UUID, str] = {}
    if latest is not None:
        from_run = {
            row.participation_id: row.reason
            for row in db.scalars(
                select(RunUnmatched).where(RunUnmatched.run_id == latest.id)
            ).all()
        }

    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.status == ParticipationStatus.APPROVED,
            Participation.matched.is_(False),
        )
        .order_by(Account.name)
    ).all()

    entries: list[UnmatchedEntryOut] = []
    for participation, person in rows:
        if participation.role == Role.MENTOR and (participation.load or 0) > 0:
            continue
        entries.append(
            UnmatchedEntryOut(
                participation_id=participation.id,
                name=person.name,
                email=person.email,
                role=participation.role,
                reason=from_run.get(
                    participation.id,
                    # Not in the last run means they arrived after it.
                    UnmatchedReason.JOINED_AFTER_RUN
                    if latest is not None
                    else UnmatchedReason.NO_MENTOR_CAPACITY,
                ),
                profile_completeness=participation.profile_completeness,
                timezone=participation.timezone,
                skills=participation.skills or [],
                joined_at=participation.joined_at,
                last_run_id=latest.id if latest else None,
            )
        )

    filtered = [e for e in entries if reason is None or e.reason == reason]
    start = (page - 1) * page_size

    mentors = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.role == Role.MENTOR,
            Participation.status == ParticipationStatus.APPROVED,
        )
        .order_by(Account.name)
    ).all()

    return UnmatchedPageOut(
        items=filtered[start : start + page_size],
        page=page,
        page_size=page_size,
        total=len(filtered),
        available_mentors=[
            AvailableMentorOut(
                participation_id=participation.id,
                name=person.name,
                load=participation.load or 0,
                capacity=participation.capacity or 0,
                skills=participation.skills or [],
                timezone=participation.timezone,
            )
            for participation, person in mentors
            if participation.capacity is not None
            and (participation.load or 0) < participation.capacity
        ],
    )


@router.post("/programs/{program_id}/strands", status_code=201)
def create_strand(
    program_id: uuid.UUID,
    body: StrandCreateIn,
    db: DbSession,
    account: CurrentAccount,
) -> StrandOut:
    """Pair two people by hand.

    Recorded with origin mode `manual`, which is the whole reason origin mode
    exists: reports have to be able to answer whether the algorithm did better
    than the coordinator's hand-picks.
    """
    require_coordinator_of_program(db, account, program_id)

    mentee = db.get(Participation, body.mentee_participation_id)
    mentor = db.get(Participation, body.mentor_participation_id)
    if mentee is None or mentor is None:
        raise not_found("participant")
    if mentee.program_id != program_id or mentor.program_id != program_id:
        raise not_found("participant")
    if mentee.role != Role.MENTEE or mentor.role != Role.MENTOR:
        raise Problem(
            400,
            "invalid_pairing",
            "A strand pairs a mentee with a mentor.",
        )

    mentor_account = db.get(Account, mentor.account_id)
    mentee_account = db.get(Account, mentee.account_id)

    if mentor.capacity is not None and (mentor.load or 0) >= mentor.capacity:
        raise Problem(
            409,
            "mentor_full",
            f"{mentor_account.name if mentor_account else 'That mentor'} is "
            "already at the capacity they set.",
        )
    if mentee.matched:
        raise Problem(
            409,
            "already_matched",
            f"{mentee_account.name if mentee_account else 'That person'} "
            "already holds a strand.",
        )

    now = datetime.now(UTC)
    strand = Strand(
        program_id=program_id,
        state=StrandState.ACTIVE,
        origin_mode=OriginMode.MANUAL,
        # No score produced this pair, so it does not get a sentence that
        # sounds as though one did.
        match_rationale=f"Paired by {account.name} from the unmatched queue.",
        last_activity_at=None,
    )
    db.add(strand)
    db.flush()

    db.add(
        StrandMember(strand_id=strand.id, participation_id=mentee.id, role="mentee")
    )
    db.add(
        StrandMember(strand_id=strand.id, participation_id=mentor.id, role="mentor")
    )

    mentee.matched = True
    mentor.load = (mentor.load or 0) + 1
    mentor.matched = True

    program = db.get(Program, program_id)
    if program is not None:
        db.add(
            AuditEvent(
                organisation_id=program.organisation_id,
                at=now,
                actor_name=account.name,
                action=AuditAction.MANUAL_PAIRING,
                summary=(
                    f"Paired {mentee_account.name if mentee_account else 'a mentee'} "
                    f"with {mentor_account.name if mentor_account else 'a mentor'} "
                    "by hand, outside the run."
                ),
                subject_label=(
                    f"{mentee_account.name if mentee_account else 'Mentee'} and "
                    f"{mentor_account.name if mentor_account else 'mentor'}"
                ),
            )
        )

    db.commit()
    db.refresh(strand)
    return strand_svc.to_strand(db, strand)
