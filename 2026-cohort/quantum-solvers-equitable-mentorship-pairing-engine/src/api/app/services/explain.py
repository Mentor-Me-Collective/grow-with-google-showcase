"""Why a pair came out the way it did, assembled for the review screen.

The numbers already exist — fit contributions are stored on the pair, and the
priority rules are a pure function of the mentee's answers. What was missing is
the join back to the questions a person actually asked, which is the only form
in which any of it means anything to a coordinator.

Nothing here recomputes a score. The stored breakdown is the run's own record of
what it did; recomputing would risk showing a number the run never used.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching import normalise
from app.matching.engine import Recipe
from app.matching.scoring import priority_contributions
from app.models.core import Account, Participation
from app.models.forms import Application, FormVersion
from app.models.matching import DraftPair, MatchingRecipe, Run
from app.schemas.matching import PriorityContributionOut, ScoreContributionOut
from app.services import profiles


@dataclass
class PairExplanation:
    score_breakdown: list[ScoreContributionOut] = field(default_factory=list)
    unscored: list[str] = field(default_factory=list)
    priority_score: float | None = None
    priority_breakdown: list[PriorityContributionOut] = field(default_factory=list)


@dataclass
class _Person:
    """One side's form, as answered, so labels and answers come from the version
    that person actually saw rather than whatever is published today."""

    fields: dict[str, dict[str, Any]] = field(default_factory=dict)
    answers: dict[str, Any] = field(default_factory=dict)

    def label(self, field_id: str) -> str | None:
        definition = self.fields.get(field_id)
        return definition["label"] if definition else None

    def answer(self, field_id: str) -> str | None:
        definition = self.fields.get(field_id)
        record = self.answers.get(field_id)
        if not definition or not record:
            return None
        return profiles.readable(definition, record)


def _recipe_row(db: Session, run: Run) -> MatchingRecipe | None:
    """The recipe this run used, not the current one.

    A coordinator who edits the criteria after a run must still be able to read
    that run back, and explaining it with today's weights would be a fiction.
    """
    stmt = select(MatchingRecipe).where(MatchingRecipe.program_id == run.program_id)
    if run.recipe_version is not None:
        row = db.scalar(stmt.where(MatchingRecipe.version == run.recipe_version))
        if row is not None:
            return row
    return db.scalar(stmt.order_by(MatchingRecipe.version.desc()).limit(1))


def _people(
    db: Session, program_id: uuid.UUID, participation_ids: set[uuid.UUID]
) -> dict[uuid.UUID, _Person]:
    if not participation_ids:
        return {}

    rows = db.execute(
        select(Participation.id, Account.email)
        .join(Account, Participation.account_id == Account.id)
        .where(Participation.id.in_(participation_ids))
    ).all()
    by_email: dict[str, list[uuid.UUID]] = {}
    for participation_id, email in rows:
        by_email.setdefault(email, []).append(participation_id)

    if not by_email:
        return {}

    applications = db.execute(
        select(Application, FormVersion)
        .join(FormVersion, Application.form_version_id == FormVersion.id)
        .where(
            Application.program_id == program_id,
            Application.email.in_(by_email.keys()),
        )
        .order_by(Application.submitted_at.asc())
    ).all()

    people: dict[uuid.UUID, _Person] = {}
    for application, version in applications:
        definitions = {f["id"]: f for f in profiles.all_fields(version)}
        for participation_id in by_email.get(application.email, []):
            people[participation_id] = _Person(
                fields=definitions, answers=application.answers or {}
            )
    return people


def _fit(
    pair: DraftPair, recipe: Recipe, mentee: _Person, mentor: _Person
) -> tuple[list[ScoreContributionOut], list[str]]:
    if pair.score_breakdown is None:
        # A run from before the breakdown was kept. Saying nothing is right;
        # listing every question as unscored would read as "none of this
        # matched", which is a claim about the pair rather than about us.
        return [], []

    stored = pair.score_breakdown
    scored: list[ScoreContributionOut] = []
    unscored: list[str] = []

    for weight in recipe.weights:
        if weight.weight <= 0:
            continue
        label = mentee.label(weight.field_id) or mentor.label(weight.field_id)
        if label is None:
            continue

        if weight.field_id in stored:
            scored.append(
                ScoreContributionOut(
                    field_id=uuid.UUID(weight.field_id),
                    label=label,
                    weight=weight.weight,
                    direction=weight.direction,
                    contribution=float(stored[weight.field_id]),
                    mentee_answer=mentee.answer(weight.field_id),
                    mentor_answer=mentor.answer(weight.field_id),
                )
            )
        else:
            unscored.append(label)

    scored.sort(key=lambda c: c.weight, reverse=True)
    return scored, unscored


def explain(
    db: Session, run: Run, pairs: list[DraftPair]
) -> dict[uuid.UUID, PairExplanation]:
    """One explanation per pair, keyed by pair id.

    Returns empty explanations rather than raising when a run predates the
    stored breakdown — an older run is still readable, just less so.
    """
    if not pairs:
        return {}

    row = _recipe_row(db, run)
    if row is None:
        return {pair.id: PairExplanation() for pair in pairs}
    recipe = Recipe.from_row(row)

    ids = {p.mentee_participation_id for p in pairs} | {
        p.mentor_participation_id for p in pairs
    }
    people = _people(db, run.program_id, ids)
    attributes = normalise.load(db, run.program_id)

    out: dict[uuid.UUID, PairExplanation] = {}
    for pair in pairs:
        mentee = people.get(pair.mentee_participation_id, _Person())
        mentor = people.get(pair.mentor_participation_id, _Person())
        scored, unscored = _fit(pair, recipe, mentee, mentor)

        mentee_attributes = attributes.get(pair.mentee_participation_id, {})
        values = priority_contributions(recipe.equity_weights, mentee_attributes)
        priority = [
            PriorityContributionOut(
                field_id=uuid.UUID(field_id),
                label=mentee.label(field_id) or "A question on the mentee's form",
                weight=recipe.equity_weights[field_id],
                value=round(value, 3),
                answer=mentee.answer(field_id),
            )
            for field_id, value in values.items()
        ]
        priority.sort(key=lambda c: c.weight, reverse=True)

        total = sum(c.value * c.weight for c in priority)
        used = sum(c.weight for c in priority)

        out[pair.id] = PairExplanation(
            score_breakdown=scored,
            unscored=unscored,
            priority_score=round(total / used, 4) if used else None,
            priority_breakdown=priority,
        )
    return out
