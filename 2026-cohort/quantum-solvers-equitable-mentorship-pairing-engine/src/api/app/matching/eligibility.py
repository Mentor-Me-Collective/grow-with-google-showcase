"""Stage 1: rules that must hold, not preferences.

A pair failing any enabled constraint is removed from consideration entirely
rather than given a low score. The distinction matters: a heavily weighted
preference can still be overridden by a strong score elsewhere, and a hard
constraint cannot.

Every constraint switched on shrinks the pool, and a shrunken pool is what
produces unmatched people — which is why the interface states the cost of each
one and why there are deliberately few of them.
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.enums import UnmatchedReason
from app.matching.scoring import Person

#: Hours apart beyond which a fortnightly call stops being arrangeable.
TIMEZONE_BAND_HOURS = 3

#: Below this a profile has too little in it to match on, and pairing anyway
#: produces a match neither side can see the reason for.
MIN_PROFILE_COMPLETENESS = 0.25


@dataclass(frozen=True)
class Constraints:
    role_compatible: bool = True
    shared_skill: bool = False
    same_timezone_band: bool = False
    different_team: bool = False

    @classmethod
    def from_recipe(cls, hard_constraints: list[dict]) -> "Constraints":
        enabled = {
            c["kind"] for c in hard_constraints if c.get("enabled")
        }
        return cls(
            role_compatible="role_compatible" in enabled,
            shared_skill="shared_skill" in enabled,
            same_timezone_band="same_timezone_band" in enabled,
            different_team="different_team" in enabled,
        )


def _offset_hours(zone: str | None) -> float | None:
    if not zone:
        return None
    try:
        now = datetime.now(ZoneInfo(zone))
    except (ZoneInfoNotFoundError, ValueError):
        return None
    offset = now.utcoffset()
    return offset.total_seconds() / 3600 if offset else 0.0


def timezones_workable(a: str | None, b: str | None) -> bool:
    """Unknown zones pass.

    Excluding somebody because they did not fill in a field would turn a missing
    answer into a hard rejection, which is the opposite of what the equity work
    at the input layer is for.
    """
    left, right = _offset_hours(a), _offset_hours(b)
    if left is None or right is None:
        return True
    return abs(left - right) <= TIMEZONE_BAND_HOURS


def shares_a_skill(mentee: Person, mentor: Person) -> bool:
    mentee_options = {
        option
        for attribute in mentee.attributes.values()
        if attribute.matching
        for option in attribute.option_values
    }
    mentor_options = {
        option
        for attribute in mentor.attributes.values()
        if attribute.matching
        for option in attribute.option_values
    }
    if not mentee_options or not mentor_options:
        # Nothing to compare is not evidence of no overlap.
        return True
    return bool(mentee_options & mentor_options)


def eligible(
    mentee: Person, mentor: Person, constraints: Constraints
) -> UnmatchedReason | None:
    """None when the pair may be considered, otherwise why it may not.

    Returning the reason rather than a boolean is what lets the unmatched queue
    say something a coordinator can act on, instead of a silent absence.
    """
    if constraints.role_compatible and not (
        mentee.role == "mentee" and mentor.role == "mentor"
    ):
        return UnmatchedReason.NO_SKILL_OVERLAP

    if mentor.capacity is not None and mentor.load >= mentor.capacity:
        return UnmatchedReason.NO_MENTOR_CAPACITY

    if mentee.profile_completeness < MIN_PROFILE_COMPLETENESS:
        return UnmatchedReason.INCOMPLETE_PROFILE

    if constraints.shared_skill and not shares_a_skill(mentee, mentor):
        return UnmatchedReason.NO_SKILL_OVERLAP

    if constraints.same_timezone_band and not timezones_workable(
        mentee.timezone, mentor.timezone
    ):
        return UnmatchedReason.NO_SKILL_OVERLAP

    # different_team is honoured in the contract but there is no team or
    # reporting-line data to check it against yet, so switching it on currently
    # excludes nobody. Stated here rather than silently treated as satisfied.
    return None
