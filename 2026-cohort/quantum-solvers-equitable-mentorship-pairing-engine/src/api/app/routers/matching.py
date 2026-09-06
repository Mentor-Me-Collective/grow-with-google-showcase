import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import limits
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
from app.services import explain

logger = logging.getLogger("braid.matching")

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
    explanations = explain.explain(db, run, pairs)

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
                score_breakdown=reasons.score_breakdown,
                unscored=reasons.unscored,
                priority_score=reasons.priority_score,
                priority_breakdown=reasons.priority_breakdown,
            )
            for pair in pairs
            for reasons in [explanations.get(pair.id, explain.PairExplanation())]
        ],
        unmatched_count=len(run.unmatched),
    )


#: How long a run may sit in queued or running before it is presumed dead.
#: Generous against the work itself — a cohort of a few hundred drafts in under
#: a second — because the cost of reaping a live run is a coordinator's wasted
#: afternoon and the cost of waiting is a few more minutes.
STALE_AFTER = timedelta(minutes=10)


def _reap_stale(db: Session, program_id: uuid.UUID) -> None:
    """Discard runs whose process died before they could finish.

    The engine already handles its own failure: an exception rolls back and
    lands the run in `discarded`. What it cannot handle is not being there —
    a deploy, an out-of-memory kill, or any restart takes the background task
    with it, and the `except` never runs. The row is then indistinguishable
    from one still working, for ever.

    Swept on read rather than on a schedule because the service has no
    scheduler, and the only person who cares is the one looking at the screen.
    """
    cutoff = datetime.now(UTC) - STALE_AFTER
    stale = list(
        db.scalars(
            select(Run).where(
                Run.program_id == program_id,
                Run.state.in_([RunState.QUEUED, RunState.RUNNING]),
                Run.created_at < cutoff,
            )
        ).all()
    )
    if not stale:
        return

    for run in stale:
        logger.warning(
            "discarding run %s: %s for %s",
            run.id,
            "started but never finished" if run.started_at else "never started",
            datetime.now(UTC) - run.created_at,
        )
        run.state = RunState.DISCARDED
        run.progress = 1.0
    db.commit()


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
    _reap_stale(db, program_id)

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

    # Keyed on the programme, not the coordinator: the cost being bounded is the
    # matching work, and a programme with three coordinators does not get three
    # times the budget for it.
    limits.enforce("run_create", str(program_id), limits.RUN_CREATE)

    # Before the check below, or a run whose process died holds the programme
    # shut for ever and the only remedy is the database.
    _reap_stale(db, program_id)

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
    try:
        db.commit()
    except IntegrityError:
        # The check above is a courtesy, not the guarantee. Two coordinators
        # clicking together both read no active run and both arrive here, and
        # only a partial unique index on the active states can refuse the second
        # — a lock would have to be taken on a row that does not exist yet.
        db.rollback()
        raise Problem(
            409, "run_in_progress", "A matching run is already in progress."
        ) from None

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
    # The screen that polls a run is the one place a stuck run is actually being
    # watched, so it is where noticing costs least.
    _reap_stale(db, run.program_id)
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

    The row is locked for the whole transaction rather than merely read. Two
    clicks on an irreversible button is the ordinary case, not the exotic one,
    and unlocked this would run the loop below twice: every pair published as
    two strands, and every mentor's load incremented twice. The second caller
    now waits for the first to commit and then finds the run already published.
    """
    run = db.scalar(select(Run).where(Run.id == run_id).with_for_update())
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
