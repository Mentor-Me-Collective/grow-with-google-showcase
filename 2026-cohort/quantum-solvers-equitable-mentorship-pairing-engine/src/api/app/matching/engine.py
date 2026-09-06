"""Running a match: gather, score, assign, summarise.

The run is a stored object with a lifecycle, so this writes progress as it goes
rather than returning at the end — the review screen follows the row.
"""

import statistics
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import ParticipationStatus, PriorityBand, Role, RunState
from app.matching import normalise
from app.matching.assign import Result, solve
from app.matching.eligibility import Constraints
from app.matching.scoring import Person, Weight, band_for, priority_score
from app.models import (
    Account,
    DraftPair,
    MatchingRecipe,
    Participation,
    Run,
    RunUnmatched,
)


@dataclass
class Recipe:
    hard_constraints: list[dict[str, Any]]
    weights: list[Weight]
    equity_weights: dict[str, int]
    coverage_floor: float
    mentor_capacity_cap: int | None

    @classmethod
    def from_row(cls, row: Any) -> "Recipe":
        fairness = row.fairness or {}
        return cls(
            hard_constraints=row.hard_constraints or [],
            weights=[
                Weight(
                    field_id=w["fieldId"],
                    weight=int(w.get("weight", 0)),
                    direction=w.get("direction", "similar"),
                )
                for w in (row.weights or [])
            ],
            equity_weights={
                w["fieldId"]: int(w.get("weight", 0))
                for w in fairness.get("priorityWeights", [])
            },
            coverage_floor=float(fairness.get("coverageFloor", 0.0)),
            mentor_capacity_cap=fairness.get("mentorCapacityCap"),
        )


def load_people(
    db: Session, program_id: uuid.UUID, cap: int | None
) -> tuple[list[Person], list[Person]]:
    attributes = normalise.load(db, program_id)

    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.status == ParticipationStatus.APPROVED,
        )
    ).all()

    mentees: list[Person] = []
    mentors: list[Person] = []

    for participation, account in rows:
        capacity = participation.capacity
        if capacity is not None and cap is not None:
            # A ceiling over what mentors set for themselves, never a floor:
            # the cap can only reduce what somebody volunteered for.
            capacity = min(capacity, cap)

        person = Person(
            participation_id=participation.id,
            name=account.name,
            role=participation.role,
            timezone=participation.timezone,
            capacity=capacity,
            load=participation.load or 0,
            profile_completeness=participation.profile_completeness,
            attributes=attributes.get(participation.id, {}),
        )
        (mentors if participation.role == Role.MENTOR else mentees).append(person)

    return mentees, mentors


def run_matching(
    db: Session, program_id: uuid.UUID, recipe: Recipe
) -> tuple[Result, dict[uuid.UUID, float], list[Person], list[Person]]:
    mentees, mentors = load_people(db, program_id, recipe.mentor_capacity_cap)

    priorities = {
        m.participation_id: priority_score(recipe.equity_weights, m.attributes)
        for m in mentees
    }

    result = solve(
        mentees=mentees,
        mentors=mentors,
        weights=recipe.weights,
        constraints=Constraints.from_recipe(recipe.hard_constraints),
        coverage_floor=recipe.coverage_floor,
        equity_weights=recipe.equity_weights,
        priorities=priorities,
    )
    return result, priorities, mentees, mentors


def fairness_summary(
    result: Result,
    priorities: dict[uuid.UUID, float],
    mentees: list[Person],
    mentors: list[Person],
) -> dict[str, Any]:
    """What the coordinator sees before a single name.

    Reports against priority bands because the question that matters is whether
    high-priority mentees came out with match quality comparable to everyone
    else — a single average cannot answer it, and a list of pairs actively
    hides it.
    """
    by_band: dict[str, list[float]] = {b.value: [] for b in PriorityBand}
    for assignment in result.assignments:
        band = band_for(priorities.get(assignment.mentee.participation_id, 0.5))
        by_band[band.value].append(assignment.score)

    buckets = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
    scores = [a.score for a in result.assignments]

    loads: dict[uuid.UUID, int] = {}
    for assignment in result.assignments:
        loads[assignment.mentor.participation_id] = (
            loads.get(assignment.mentor.participation_id, 0) + 1
        )

    return {
        "coverageRate": round(len(result.assignments) / len(mentees), 4)
        if mentees
        else 0.0,
        "matchedCount": len(result.assignments),
        "unmatchedCount": len(result.unmatched),
        "totalMentees": len(mentees),
        "mentorLoad": [
            {
                "mentor": {
                    "participationId": str(mentor.participation_id),
                    "name": mentor.name,
                    "photoUrl": None,
                },
                "load": mentor.load + loads.get(mentor.participation_id, 0),
                "capacity": mentor.capacity if mentor.capacity is not None else 0,
            }
            for mentor in mentors
        ],
        "priorityBands": [
            {
                "band": band,
                "menteeCount": len(values),
                "meanScore": round(statistics.fmean(values), 3) if values else 0.0,
                "medianScore": round(statistics.median(values), 3) if values else 0.0,
            }
            for band, values in by_band.items()
        ],
        "scoreDistribution": [
            {
                "rangeStart": start,
                "rangeEnd": end,
                "count": sum(
                    1
                    for s in scores
                    if s >= start and (s <= end if end == 1.0 else s < end)
                ),
            }
            for start, end in buckets
        ],
    }


def execute(db: Session, run_id: uuid.UUID) -> None:
    """Take a queued run through to drafted.

    Progress is committed at each step so a poll can observe it. If anything
    fails the run is left discarded rather than stuck at `running`, because a
    run that never finishes is indistinguishable from one still working.
    """
    run = db.get(Run, run_id)
    if run is None:
        return

    try:
        run.state = RunState.RUNNING
        run.started_at = datetime.now(UTC)
        run.progress = 0.15
        db.commit()

        normalise.rebuild(db, run.program_id)
        run.progress = 0.45
        db.commit()

        recipe_row = db.scalar(
            select(MatchingRecipe)
            .where(MatchingRecipe.program_id == run.program_id)
            .order_by(MatchingRecipe.version.desc())
            .limit(1)
        )
        if recipe_row is None:
            run.state = RunState.DISCARDED
            db.commit()
            return

        recipe = Recipe.from_row(recipe_row)
        run.recipe_version = recipe_row.version
        run.progress = 0.7
        db.commit()

        result, priorities, mentees, mentors = run_matching(db, run.program_id, recipe)

        for assignment in result.assignments:
            db.add(
                DraftPair(
                    run_id=run.id,
                    mentee_participation_id=assignment.mentee.participation_id,
                    mentor_participation_id=assignment.mentor.participation_id,
                    score=assignment.score,
                    priority_band=band_for(assignment.priority).value,
                    score_breakdown=assignment.breakdown,
                )
            )

        for participation_id, reason in result.unmatched.items():
            db.add(
                RunUnmatched(
                    run_id=run.id,
                    participation_id=participation_id,
                    reason=reason.value,
                )
            )

        summary = fairness_summary(result, priorities, mentees, mentors)
        run.fairness_summary = summary
        run.coverage_rate = summary["coverageRate"]
        run.drafted_count = len(result.assignments)
        run.state = RunState.DRAFTED
        run.progress = 1.0
        db.commit()

    except Exception:
        db.rollback()
        stuck = db.get(Run, run_id)
        if stuck is not None:
            stuck.state = RunState.DISCARDED
            stuck.progress = 1.0
            db.commit()
        raise
