"""Stage 4: global assignment.

The stage that makes the rest worth doing.

Greedy matching walks the list and gives each mentee her best available mentor.
It looks reasonable and it is not, because early decisions consume options that
later mentees needed more. If the second mentee is the only person who could
have worked with a particular mentor, and the first took him because he was
marginally her best option too, the algorithm has produced a worse cohort while
making a locally sensible choice every time.

So the whole cohort is solved at once: a cost matrix over every eligible pair,
minimised across all of it, subject to capacity, a coverage floor, and priority
weighting. This is a well-understood class of problem and the engineering is
not novel. The objective function is where the argument lives.
"""

import uuid
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from app.enums import UnmatchedReason
from app.matching.eligibility import Constraints, eligible
from app.matching.scoring import (
    FitResult,
    Person,
    Weight,
    fit,
    priority_multiplier,
)

#: Large enough that the solver will never choose an ineligible pair when any
#: eligible one exists, small enough to stay finite — scipy cannot solve a
#: matrix containing infinities.
FORBIDDEN = 1e6


@dataclass
class Assignment:
    mentee: Person
    mentor: Person
    score: float
    breakdown: dict[str, float]
    priority: float


@dataclass
class Result:
    assignments: list[Assignment]
    unmatched: dict[uuid.UUID, UnmatchedReason]


def _slots(mentors: list[Person]) -> list[Person]:
    """One column per place a mentor has left.

    Capacity expansion is what stops three mentees converging on the one
    obviously excellent mentor: the solver can only use a column once, so a
    mentor with two places can appear in at most two pairs, however good a fit
    she looks to everybody.
    """
    columns: list[Person] = []
    for mentor in mentors:
        remaining = (
            mentor.capacity - mentor.load if mentor.capacity is not None else 1
        )
        columns.extend([mentor] * max(remaining, 0))
    return columns


def solve(
    mentees: list[Person],
    mentors: list[Person],
    weights: list[Weight],
    constraints: Constraints,
    coverage_floor: float,
    equity_weights: dict[str, int],
    priorities: dict[uuid.UUID, float],
) -> Result:
    columns = _slots(mentors)
    unmatched: dict[uuid.UUID, UnmatchedReason] = {}

    if not mentees:
        return Result(assignments=[], unmatched=unmatched)

    if not columns:
        return Result(
            assignments=[],
            unmatched={
                m.participation_id: UnmatchedReason.NO_MENTOR_CAPACITY
                for m in mentees
            },
        )

    # A per-assignment reward large enough that leaving somebody out always
    # costs more than any drop in quality. Without it an optimiser maximising
    # total fit will happily abandon the hardest-to-place mentees to protect its
    # average — and the tail is exactly who the programme is for. The coverage
    # floor scales it: a programme that cares more about reaching everybody
    # makes leaving somebody out more expensive still.
    coverage_reward = 1.0 + coverage_floor * 2.0

    cost = np.full((len(mentees), len(columns)), FORBIDDEN, dtype=float)
    fits: dict[tuple[int, int], FitResult] = {}
    reasons: dict[uuid.UUID, set[UnmatchedReason]] = {
        m.participation_id: set() for m in mentees
    }

    for row, mentee in enumerate(mentees):
        for column, mentor in enumerate(columns):
            failure = eligible(mentee, mentor, constraints)
            if failure is not None:
                reasons[mentee.participation_id].add(failure)
                continue

            result = fit(weights, mentee.attributes, mentor.attributes)
            fits[(row, column)] = result

            weighted = result.score * priority_multiplier(
                priorities.get(mentee.participation_id, 0.5),
                weight_strength=_strength(equity_weights),
            )
            # Minimised, so value is negated.
            cost[row, column] = -(weighted + coverage_reward)

    rows, cols = linear_sum_assignment(cost)

    assignments: list[Assignment] = []
    taken: set[int] = set()
    for row, column in zip(rows, cols, strict=False):
        # scipy fills the rectangle, so a pair it could only satisfy with a
        # forbidden cell is not a match — it is somebody it could not place.
        if cost[row, column] >= FORBIDDEN:
            continue
        result = fits[(row, column)]
        assignments.append(
            Assignment(
                mentee=mentees[row],
                mentor=columns[column],
                score=result.score,
                breakdown=result.breakdown,
                priority=priorities.get(mentees[row].participation_id, 0.5),
            )
        )
        taken.add(row)

    for row, mentee in enumerate(mentees):
        if row in taken:
            continue
        unmatched[mentee.participation_id] = _reason(reasons[mentee.participation_id])

    return Result(assignments=assignments, unmatched=unmatched)


def _strength(equity_weights: dict[str, int]) -> float:
    """How hard priority tilts the objective, from how much weight the
    coordinator gave the equity questions. Capped: priority should resolve close
    calls, not override suitability, because a mentee matched to somebody
    unsuitable has not been helped by being matched first."""
    if not equity_weights:
        return 0.0
    average = sum(equity_weights.values()) / (len(equity_weights) * 100)
    return min(average, 1.0) * 0.6


def _reason(found: set[UnmatchedReason]) -> UnmatchedReason:
    """The most actionable reason when several apply.

    Ordered by what a coordinator can do about it: an incomplete profile needs
    the participant, no capacity needs a mentor, no overlap needs a different
    pool or a group.
    """
    for reason in (
        UnmatchedReason.INCOMPLETE_PROFILE,
        UnmatchedReason.NO_MENTOR_CAPACITY,
        UnmatchedReason.NO_SKILL_OVERLAP,
    ):
        if reason in found:
            return reason
    # Everybody was eligible and the solver still ran out of places.
    return UnmatchedReason.NO_MENTOR_CAPACITY
