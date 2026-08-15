import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.deps import CurrentAccount, DbSession, require_coordinator_of_program
from app.enums import (
    AuditAction,
    OriginMode,
    RunState,
    StrandState,
)
from app.errors import Problem, not_found
from app.matching import engine
from app.models import (
    Account,
    AuditEvent,
    DraftPair,
    MatchingRecipe,
    Participation,
    Program,
    Run,
    Strand,
    StrandMember,
)
from app.schemas.matching import (
    DraftPairOut,
    PersonRefOut,
    RunDetailOut,
    RunOut,
    RunPageOut,
)

router = APIRouter(tags=["Matching"])


def _run_out(run: Run) -> RunOut:
    return RunOut(
        id=run.id,
        program_id=run.program_id,
        state=run.state,
        progress=run.progress,
        recipe_version=run.recipe_version,
        created_at=run.created_at,
        created_by=run.created_by,
        published_at=run.published_at,
        published_by=run.published_by,
        drafted_count=run.drafted_count,
        published_count=run.published_count,
        coverage_rate=run.coverage_rate,
    )


def _people(
    db: Session, ids: set[uuid.UUID]
) -> dict[uuid.UUID, tuple[str, str | None]]:
    rows = db.execute(
        select(Participation.id, Account.name, Account.photo_url)
        .join(Account, Participation.account_id == Account.id)
        .where(Participation.id.in_(ids))
    ).all()
    return {row[0]: (row[1], row[2]) for row in rows}


def _detail(db: Session, run: Run) -> RunDetailOut:
    pairs = list(db.scalars(select(DraftPair).where(DraftPair.run_id == run.id)).all())
    ids = {p.mentee_participation_id for p in pairs} | {
        p.mentor_participation_id for p in pairs
    }
    people = _people(db, ids)

    def ref(participation_id: uuid.UUID) -> PersonRefOut:
        name, photo = people.get(participation_id, ("Someone", None))
        return PersonRefOut(
            participation_id=participation_id, name=name, photo_url=photo
        )

    return RunDetailOut(
        **_run_out(run).model_dump(by_alias=False),
        fairness_summary=run.fairness_summary,
        pairs=[
            DraftPairOut(
                id=pair.id,
                mentee=ref(pair.mentee_participation_id),
                mentor=ref(pair.mentor_participation_id),
                score=pair.score,
                priority_band=pair.priority_band,
            )
            for pair in pairs
        ],
        unmatched_count=len(run.unmatched),
    )


def _execute_in_background(run_id: uuid.UUID) -> None:
    """A background task gets its own session.

    The request's session is closed the moment the 202 is returned, and the run
    outlives the request by design — that is what makes it a stored object with
    a lifecycle rather than a function call.
    """
    with SessionLocal() as db:
        engine.execute(db, run_id)


@router.get("/programs/{program_id}/runs")
def list_runs(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
) -> RunPageOut:
    require_coordinator_of_program(db, account, program_id)

    runs = list(
        db.scalars(
            select(Run)
            .where(Run.program_id == program_id)
            .order_by(Run.created_at.desc())
        ).all()
    )
    start = (page - 1) * page_size
    return RunPageOut(
        items=[_run_out(r) for r in runs[start : start + page_size]],
        page=page,
        page_size=page_size,
        total=len(runs),
    )


@router.post("/programs/{program_id}/runs", status_code=202)
def create_run(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    background: BackgroundTasks,
) -> RunDetailOut:
    """Returns immediately with state `queued`.

    A run is not a function call: the work happens after the response, and the
    review screen follows the row from queued to drafted. Nothing is visible to
    a participant until it is published.
    """
    require_coordinator_of_program(db, account, program_id)

    in_flight = db.scalar(
        select(Run).where(
            Run.program_id == program_id,
            Run.state.in_([RunState.QUEUED, RunState.RUNNING]),
        )
    )
    if in_flight is not None:
        raise Problem(
            409, "run_in_progress", "A matching run is already in progress."
        )

    recipe = db.scalar(
        select(MatchingRecipe).where(MatchingRecipe.program_id == program_id)
    )
    if recipe is None:
        raise Problem(
            409,
            "no_recipe",
            "This programme has no matching criteria yet, so there is nothing to "
            "run.",
        )

    run = Run(
        program_id=program_id,
        state=RunState.QUEUED,
        progress=0.0,
        created_at=datetime.now(UTC),
        created_by=account.name,
    )
    db.add(run)
    db.commit()

    background.add_task(_execute_in_background, run.id)
    return _detail(db, run)


@router.get("/runs/{run_id}")
def get_run(
    run_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> RunDetailOut:
    run = db.get(Run, run_id)
    if run is None:
        raise not_found("run")
    require_coordinator_of_program(db, account, run.program_id)
    # Read fresh: the background task writes progress from another session.
    db.refresh(run)
    return _detail(db, run)


@router.post("/runs/{run_id}/publish")
def publish_run(
    run_id: uuid.UUID, db: DbSession, account: CurrentAccount, response: Response
) -> RunDetailOut:
    """Irreversible. Turns every draft pair into an active strand.

    Publication is the only step that reaches a participant, which is why it is
    the only one that cannot be undone — and why the interface spells out the
    counts before it happens.
    """
    run = db.get(Run, run_id)
    if run is None:
        raise not_found("run")
    require_coordinator_of_program(db, account, run.program_id)

    if run.state != RunState.DRAFTED:
        raise Problem(
            409,
            "not_publishable",
            "Only a drafted run can be published.",
        )

    now = datetime.now(UTC)
    pairs = list(db.scalars(select(DraftPair).where(DraftPair.run_id == run.id)).all())

    for pair in pairs:
        strand = Strand(
            program_id=run.program_id,
            state=StrandState.ACTIVE,
            # Batch, so reports can later ask whether the algorithm did better
            # than the coordinator's hand-picks.
            origin_mode=OriginMode.BATCH,
            match_rationale=_rationale(pair),
            last_activity_at=None,
        )
        db.add(strand)
        db.flush()

        db.add(
            StrandMember(
                strand_id=strand.id,
                participation_id=pair.mentee_participation_id,
                role="mentee",
            )
        )
        db.add(
            StrandMember(
                strand_id=strand.id,
                participation_id=pair.mentor_participation_id,
                role="mentor",
            )
        )

        mentee = db.get(Participation, pair.mentee_participation_id)
        mentor = db.get(Participation, pair.mentor_participation_id)
        if mentee is not None:
            mentee.matched = True
        if mentor is not None:
            mentor.load = (mentor.load or 0) + 1
            mentor.matched = True

    run.state = RunState.PUBLISHED
    run.published_at = now
    run.published_by = account.name
    run.published_count = len(pairs)

    program = db.get(Program, run.program_id)
    if program is not None:
        db.add(
            AuditEvent(
                organisation_id=program.organisation_id,
                at=now,
                actor_name=account.name,
                action=AuditAction.RUN_PUBLISHED,
                summary=(
                    f"Published a run of {len(pairs)} pairs. "
                    f"{len(run.unmatched)} left unmatched."
                ),
                subject_label=f"Run of {run.created_at:%-d %B}",
            )
        )

    db.commit()
    db.refresh(run)
    return _detail(db, run)


def _rationale(pair: DraftPair) -> str:
    """A partial explanation, and labelled as one.

    In a global assignment the true reason a mentee received a particular mentor
    is frequently about a third person — she got her second choice because
    somebody else had no other option. That cannot be expressed per pair, so
    this says what contributed rather than claiming to be the whole reason.
    """
    contributions = pair.score_breakdown or {}
    strongest = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:2]
    if not strongest:
        return (
            "Matched by the programme's criteria. This names the strongest "
            "signals; in a whole-cohort assignment the outcome also depends on "
            "who else was available."
        )
    return (
        f"Matched on {len(strongest)} of the questions the programme scores, "
        f"at {pair.score:.2f} overall. This names the strongest signals; in a "
        "whole-cohort assignment the outcome also depends on who else was "
        "available."
    )
