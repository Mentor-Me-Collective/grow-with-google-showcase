"""Stages 2 and 3: how good a pairing would be, and who most needs one.

Kept apart on purpose. Fit measures the quality of a pairing and says nothing
about who deserves one; priority measures how much difference the structured
route makes to a person and says nothing about whether a particular mentor
suits them. Mixing them into a single number is what makes a system impossible
to explain afterwards.
"""

import uuid
from dataclasses import dataclass
from dataclasses import field as dataclass_field

from app.enums import PriorityBand
from app.models.matching import ParticipantAttribute

Attributes = dict[str, ParticipantAttribute]


@dataclass
class Weight:
    field_id: str
    weight: int
    direction: str  # "similar" | "complementary"


@dataclass
class FitResult:
    score: float
    #: Per-field contributions, kept for the per-pair view. Always presented as
    #: a partial explanation: in a global assignment the real reason a pairing
    #: happened often involves a third person.
    breakdown: dict[str, float] = dataclass_field(default_factory=dict)


def _options(attribute: ParticipantAttribute | None) -> set[str]:
    return set(attribute.option_values) if attribute else set()


def _overlap(a: set[str], b: set[str]) -> float:
    """Jaccard: shared over combined.

    Not raw count — a mentor who lists ten skills should not out-score one who
    lists three and shares two of them.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _numeric_closeness(a: float, b: float, span: float = 5.0) -> float:
    return max(0.0, 1.0 - abs(a - b) / span)


def option_bag(attributes: Attributes) -> set[str]:
    """Every option this person chose on any question that feeds matching.

    Comparison has to cross two different forms. Mentees are asked "what would
    you like to work on?" and mentors "what can you help someone with?" — two
    field ids that never meet, but drawn from the same list of options. Since an
    option id is unique to its option, ids from unrelated questions cannot
    collide, so intersecting the two bags compares like with like without
    needing to know which question each came from.

    This is the thin version of the taxonomy the architecture calls for. It
    works because both sides answered a fixed list; free text still compares to
    nothing, and that is the gap a real taxonomy would close.
    """
    return {
        option
        for attribute in attributes.values()
        if attribute.matching
        for option in attribute.option_values
    }


def field_score(
    weight: Weight,
    mine: ParticipantAttribute | None,
    other_options: set[str],
    other_numbers: list[float],
) -> float | None:
    """One weighted question's contribution, 0..1, or None when it cannot be
    compared at all.

    None rather than zero: an unanswered question is not evidence of a bad
    match, and scoring it zero would quietly punish the people whose profiles
    are thin — the exact bias the project exists to correct.
    """
    if mine is None:
        return None

    chosen = _options(mine)
    if chosen:
        covered = chosen & other_options
        if not other_options:
            return None
        if weight.direction == "complementary":
            # How much of what this person wants the other side actually has. A
            # mentor who knows only what the mentee already knows teaches her
            # nothing, so coverage is the measure rather than similarity.
            return len(covered) / len(chosen)
        return _overlap(chosen, other_options)

    if mine.number_value is not None and other_numbers:
        # Compared against the closest number the other side gave, since the
        # two forms rarely ask the same numeric question.
        closeness = max(
            _numeric_closeness(mine.number_value, value) for value in other_numbers
        )
        return 1.0 - closeness if weight.direction == "complementary" else closeness

    # Free text. Without a taxonomy there is nothing honest to compare, so it
    # contributes nothing rather than a similarity invented from string overlap,
    # which would reward writing style rather than suitability.
    return None


def _numbers(attributes: Attributes) -> list[float]:
    return [
        a.number_value
        for a in attributes.values()
        if a.matching and a.number_value is not None
    ]


def fit(
    weights: list[Weight],
    mentee: Attributes,
    mentor: Attributes,
) -> FitResult:
    total = 0.0
    used = 0.0
    breakdown: dict[str, float] = {}

    mentee_bag, mentor_bag = option_bag(mentee), option_bag(mentor)
    mentee_numbers, mentor_numbers = _numbers(mentee), _numbers(mentor)

    for weight in weights:
        if weight.weight <= 0:
            continue

        # A weight names one question, and that question lives on one of the two
        # forms. Whichever side holds it is scored against the other's answers.
        if weight.field_id in mentee:
            score = field_score(
                weight, mentee[weight.field_id], mentor_bag, mentor_numbers
            )
        elif weight.field_id in mentor:
            score = field_score(
                weight, mentor[weight.field_id], mentee_bag, mentee_numbers
            )
        else:
            continue

        if score is None:
            continue
        total += score * weight.weight
        used += weight.weight
        breakdown[weight.field_id] = round(score, 3)

    # Divided by the weight actually used, not the weight configured, so a pair
    # is not penalised for questions neither of them was asked.
    return FitResult(
        score=round(total / used, 4) if used else 0.0, breakdown=breakdown
    )


def priority_score(
    equity_weights: dict[str, int], attributes: Attributes
) -> float:
    """How much difference the structured route makes for this person.

    Not merit, and not need in a charitable sense. A woman with two existing
    mentors and a strong network loses less by waiting a round than one who has
    neither, so the same mentor hour produces more for the second.

    Each equity answer is read as "less existing access scores higher": a low
    number on a scale, or an option indicating no prior mentorship, raises it.
    """
    contributions = priority_contributions(equity_weights, attributes)
    total = sum(value * equity_weights[f] for f, value in contributions.items())
    used = sum(equity_weights[f] for f in contributions)

    return round(total / used, 4) if used else 0.5


def priority_contributions(
    equity_weights: dict[str, int], attributes: Attributes
) -> dict[str, float]:
    """Each equity question's value on its own, before weighting.

    Split out of `priority_score` so the review screen can show what produced a
    band without a second copy of the inversion rules — two copies would drift,
    and a band nobody can reproduce is worse than no band at all.
    """
    values: dict[str, float] = {}

    for field_id, weight in equity_weights.items():
        if weight <= 0:
            continue
        attribute = attributes.get(field_id)
        if attribute is None:
            continue

        if attribute.number_value is not None:
            # Scales run low-to-high as confidence or experience, so invert.
            span = 5.0 if attribute.field_type == "scale" else 10.0
            value = 1.0 - min(attribute.number_value / span, 1.0)
        elif attribute.option_values:
            # Without a taxonomy of which option means "less access", presence
            # of an answer is all that can be read honestly, so it sits in the
            # middle rather than inventing a direction.
            value = 0.5
        else:
            continue

        values[field_id] = value

    return values


def band_for(score: float) -> PriorityBand:
    """Bands, not a continuous rank.

    The fairness summary reports against bands because a coordinator has to be
    able to answer "did high-priority mentees do as well as everyone else",
    and that question needs groups to compare.
    """
    if score >= 0.66:
        return PriorityBand.HIGH
    if score >= 0.33:
        return PriorityBand.MEDIUM
    return PriorityBand.LOW


def priority_multiplier(score: float, weight_strength: float) -> float:
    """How much a high-priority mentee's fit counts for extra.

    Bounded deliberately. Priority resolves ties and tilts close calls; it does
    not let a poor pairing beat a good one, because a mentee matched to somebody
    unsuitable has not been helped by being matched first.
    """
    return 1.0 + (score - 0.5) * weight_strength


@dataclass
class Person:
    participation_id: uuid.UUID
    name: str
    role: str
    timezone: str | None
    capacity: int | None
    load: int
    profile_completeness: float
    attributes: Attributes
