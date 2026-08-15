import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import CurrentAccount, DbSession, require_coordinator_of_program
from app.enums import AuditAction, Role, TemplateKind
from app.errors import Problem, not_found
from app.matching import engine, normalise
from app.models import (
    Application,
    AuditEvent,
    FormVersion,
    MatchingRecipe,
    MessageTemplate,
    Program,
    ProgramMilestone,
)
from app.schemas.reads import FormVersionOut
from app.schemas.setup import (
    CriteriaEditorStateOut,
    CriteriaFieldOut,
    FormDraftSaveIn,
    FormEditorStateOut,
    FormVersionSummaryOut,
    MatchingRecipeOut,
    MatchingRecipeSaveIn,
    MergeCodeOut,
    MessageTemplateOut,
    MessageTemplateSaveIn,
    ProgramMilestoneOut,
    ProgramMilestonesSaveIn,
    TemplateSetOut,
)
from app.services.profiles import all_fields, published_version

router = APIRouter(tags=["Setup"])


def _audit(db: Session, program_id: uuid.UUID, actor: str, action, summary, subject):
    program = db.get(Program, program_id)
    if program is None:
        return
    db.add(
        AuditEvent(
            organisation_id=program.organisation_id,
            at=datetime.now(UTC),
            actor_name=actor,
            action=action,
            summary=summary,
            subject_label=subject,
        )
    )


# --- form builder -------------------------------------------------------


@router.get("/programs/{program_id}/forms")
def get_form_editor_state(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    role: Role = Query(...),
) -> FormEditorStateOut:
    """Everything the builder needs for one role.

    A programme may hold a draft and a published version at once — that is the
    normal state while somebody is editing a live form.
    """
    require_coordinator_of_program(db, account, program_id)

    versions = list(
        db.scalars(
            select(FormVersion)
            .where(FormVersion.program_id == program_id, FormVersion.role == role)
            .order_by(FormVersion.version.desc())
        ).all()
    )

    return FormEditorStateOut(
        role=role,
        draft=next(
            (
                FormVersionOut.model_validate(v)
                for v in versions
                if v.published_at is None
            ),
            None,
        ),
        published=(
            FormVersionOut.model_validate(published_version(db, program_id, role))
            if published_version(db, program_id, role)
            else None
        ),
        history=[
            FormVersionSummaryOut(
                id=v.id,
                version=v.version,
                published_at=v.published_at,
                question_count=len(all_fields(v)),
                application_count=db.scalar(
                    select(func.count())
                    .select_from(Application)
                    .where(Application.form_version_id == v.id)
                )
                or 0,
            )
            for v in versions
        ],
    )


@router.put("/programs/{program_id}/forms/{role}/draft")
def save_form_draft(
    program_id: uuid.UUID,
    role: Role,
    body: FormDraftSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> FormVersionOut:
    """Writes to the draft, never to anything published.

    If the role has no draft yet, one is started from the published version — so
    opening a live form and editing it cannot alter what applicants are
    answering right now.
    """
    require_coordinator_of_program(db, account, program_id)

    draft = db.scalar(
        select(FormVersion).where(
            FormVersion.program_id == program_id,
            FormVersion.role == role,
            FormVersion.published_at.is_(None),
        )
    )
    if draft is None:
        live = published_version(db, program_id, role)
        draft = FormVersion(
            program_id=program_id,
            role=role,
            version=(live.version if live else 0) + 1,
            published_at=None,
            sections=[],
        )
        db.add(draft)

    draft.sections = body.sections
    db.commit()
    db.refresh(draft)
    return FormVersionOut.model_validate(draft)


def _unpublishable(sections: list[dict]) -> str | None:
    """What would make a published form unusable to an applicant.

    Checked before publishing rather than after, because the version that goes
    live is the one strangers answer on a phone from a link.
    """
    fields = [f for s in sections for f in s.get("fields", [])]
    if not fields:
        return "This form has no questions in it yet."
    if any(not (f.get("label") or "").strip() for f in fields):
        return "Every question needs a label before this can go live."
    empty = next(
        (
            f
            for f in fields
            if f.get("type") in ("single_select", "multi_select")
            and not (f.get("options") or [])
        ),
        None,
    )
    if empty is not None:
        return f'"{empty["label"]}" is a choice question with nothing to choose from.'
    if any(not (s.get("title") or "").strip() for s in sections):
        return "Every section needs a title before this can go live."
    return None


@router.post("/programs/{program_id}/forms/{role}/publish")
def publish_form_draft(
    program_id: uuid.UUID, role: Role, db: DbSession, account: CurrentAccount
) -> FormVersionOut:
    """Mints the next version.

    Applications already submitted keep the version they were answered against
    for good: the form somebody saw is part of what they said, and re-reading an
    old application through new questions would put words in their mouth.
    """
    require_coordinator_of_program(db, account, program_id)

    draft = db.scalar(
        select(FormVersion).where(
            FormVersion.program_id == program_id,
            FormVersion.role == role,
            FormVersion.published_at.is_(None),
        )
    )
    if draft is None:
        raise Problem(409, "nothing_to_publish", "There is no draft to publish.")

    complaint = _unpublishable(draft.sections)
    if complaint:
        raise Problem(409, "draft_incomplete", complaint)

    draft.published_at = datetime.now(UTC)
    _audit(
        db,
        program_id,
        account.name,
        f"Published version {draft.version} of the {role} form.",
        AuditAction.FORM_PUBLISHED,
        f"{role.title()} form, version {draft.version}",
    )
    db.commit()
    db.refresh(draft)
    return FormVersionOut.model_validate(draft)


# --- milestones ---------------------------------------------------------


def _ordered(db: Session, program_id: uuid.UUID) -> list[ProgramMilestone]:
    """Week order, ties broken by position, so the arc always reads forwards."""
    return list(
        db.scalars(
            select(ProgramMilestone)
            .where(ProgramMilestone.program_id == program_id)
            .order_by(ProgramMilestone.week_offset, ProgramMilestone.position)
        ).all()
    )


@router.get("/programs/{program_id}/milestones")
def list_milestones(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> list[ProgramMilestoneOut]:
    require_coordinator_of_program(db, account, program_id)
    return [ProgramMilestoneOut.model_validate(m) for m in _ordered(db, program_id)]


@router.put("/programs/{program_id}/milestones")
def save_milestones(
    program_id: uuid.UUID,
    body: ProgramMilestonesSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> list[ProgramMilestoneOut]:
    """Written whole rather than per milestone.

    The arc is one thing a coordinator edits as a shape — adding a step changes
    what comes after it — and a sequence of row-level calls would let a
    half-saved arc exist between two of them.
    """
    require_coordinator_of_program(db, account, program_id)

    if any(not item.title.strip() for item in body.items):
        raise Problem(400, "missing_title", "Every milestone needs a title.")

    keep = {item.id for item in body.items if item.id is not None}
    for existing in _ordered(db, program_id):
        if existing.id not in keep:
            db.delete(existing)

    for index, item in enumerate(body.items, start=1):
        if item.id is not None:
            milestone = db.get(ProgramMilestone, item.id)
            if milestone is None:
                continue
        else:
            milestone = ProgramMilestone(program_id=program_id)
            db.add(milestone)

        milestone.title = item.title.strip()
        milestone.description = item.description
        milestone.week_offset = item.week_offset
        milestone.strand_prompt = item.strand_prompt
        milestone.reminder_days_before = item.reminder_days_before
        milestone.position = index

    db.commit()
    return [ProgramMilestoneOut.model_validate(m) for m in _ordered(db, program_id)]


# --- templates ----------------------------------------------------------

#: System-defined, not per programme: they are the values the sender knows how
#: to substitute, and a coordinator inventing one would produce a literal brace
#: in somebody's inbox.
MERGE_CODES = [
    MergeCodeOut(
        code="participant.firstName",
        description="The person being written to",
        sample="Blessing",
    ),
    MergeCodeOut(
        code="partner.firstName",
        description="The other side of their strand",
        sample="Amara",
    ),
    MergeCodeOut(code="programme.name", description="This programme", sample=""),
    MergeCodeOut(
        code="organisation.name", description="The host organisation", sample=""
    ),
    MergeCodeOut(
        code="programme.matchingDate",
        description="When matching runs",
        sample="14 September",
    ),
]

DEFAULT_TEMPLATES: dict[str, tuple[str, str]] = {
    TemplateKind.WELCOME: (
        "You are in, {participant.firstName}",
        "Hello {participant.firstName},\n\nYou are on the roster for "
        "{programme.name} at {organisation.name}. Matching runs on "
        "{programme.matchingDate}, and you will hear from us either way that "
        "day.\n\nThere is nothing you need to do until then.",
    ),
    TemplateKind.MATCH_NOTIFICATION: (
        "You have been matched with {partner.firstName}",
        "Hello {participant.firstName},\n\nYou have been matched with "
        "{partner.firstName} for {programme.name}.\n\nThe first conversation is "
        "the hardest one to arrange and the one that decides whether the rest "
        "happen.",
    ),
    TemplateKind.NUDGE: (
        "It has been quiet in your strand",
        "Hello {participant.firstName},\n\nYou and {partner.firstName} have not "
        "spoken in a couple of weeks. That is normal and it is not a failure.",
    ),
    TemplateKind.MID_POINT_CHECK_IN: (
        "Halfway through {programme.name}",
        "Hello {participant.firstName},\n\nYou are halfway through "
        "{programme.name}. What has been useful, and what would you change?",
    ),
    TemplateKind.CLOSING: (
        "{programme.name} has finished",
        "Hello {participant.firstName},\n\n{programme.name} has come to an end. "
        "Thank you for the time you gave it.",
    ),
}


def _merge_codes(program: Program | None) -> list[MergeCodeOut]:
    codes = [c.model_copy() for c in MERGE_CODES]
    for code in codes:
        if code.code == "programme.name" and program is not None:
            code.sample = program.name
        if code.code == "organisation.name" and program is not None:
            org = program.organisation
            code.sample = org.name if org else ""
    return codes


def _ensure_templates(db: Session, program_id: uuid.UUID) -> list[MessageTemplate]:
    """Ship with defaults, so a programme that never opens the screen still
    sends something that reads like a person wrote it."""
    existing = {
        t.kind: t
        for t in db.scalars(
            select(MessageTemplate).where(MessageTemplate.program_id == program_id)
        ).all()
    }
    for kind, (subject, body) in DEFAULT_TEMPLATES.items():
        if kind not in existing:
            template = MessageTemplate(
                program_id=program_id,
                kind=kind,
                subject=subject,
                body=body,
                is_default=True,
            )
            db.add(template)
            existing[kind] = template
    db.flush()
    return [existing[k] for k in DEFAULT_TEMPLATES if k in existing]


@router.get("/programs/{program_id}/templates")
def list_templates(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> TemplateSetOut:
    require_coordinator_of_program(db, account, program_id)
    templates = _ensure_templates(db, program_id)
    db.commit()
    return TemplateSetOut(
        items=[MessageTemplateOut.model_validate(t) for t in templates],
        merge_codes=_merge_codes(db.get(Program, program_id)),
    )


def _unknown_codes(text: str) -> list[str]:
    import re

    allowed = {c.code for c in MERGE_CODES}
    used = [m.strip() for m in re.findall(r"\{([^}]+)\}", text)]
    return sorted({c for c in used if c not in allowed})


@router.put("/programs/{program_id}/templates/{kind}")
def save_template(
    program_id: uuid.UUID,
    kind: TemplateKind,
    body: MessageTemplateSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> MessageTemplateOut:
    require_coordinator_of_program(db, account, program_id)
    _ensure_templates(db, program_id)

    template = db.scalar(
        select(MessageTemplate).where(
            MessageTemplate.program_id == program_id, MessageTemplate.kind == kind
        )
    )
    if template is None:
        raise not_found("template")

    if not body.subject.strip() or not body.body.strip():
        raise Problem(400, "invalid_body", "A template needs a subject and a body.")

    # Rejected here rather than at send time: an unknown code would otherwise
    # reach a participant as a literal brace in an email.
    unknown = _unknown_codes(f"{body.subject} {body.body}")
    if unknown:
        raise Problem(
            400,
            "unknown_merge_code",
            f"There is no such code as {{{unknown[0]}}}. Use one from the list.",
        )

    template.subject = body.subject
    template.body = body.body
    template.is_default = False
    template.updated_by = account.name
    _audit(
        db,
        program_id,
        account.name,
        f"Edited the {kind.replace('_', ' ')} template.",
        AuditAction.TEMPLATE_EDITED,
        kind.replace("_", " "),
    )
    db.commit()
    db.refresh(template)
    return MessageTemplateOut.model_validate(template)


@router.delete("/programs/{program_id}/templates/{kind}")
def reset_template(
    program_id: uuid.UUID, kind: TemplateKind, db: DbSession, account: CurrentAccount
) -> MessageTemplateOut:
    """Removes the programme's override. The default is Braid's, so this cannot
    fail with nothing to fall back on."""
    require_coordinator_of_program(db, account, program_id)
    _ensure_templates(db, program_id)

    template = db.scalar(
        select(MessageTemplate).where(
            MessageTemplate.program_id == program_id, MessageTemplate.kind == kind
        )
    )
    if template is None:
        raise not_found("template")

    subject, body = DEFAULT_TEMPLATES[kind]
    template.subject = subject
    template.body = body
    template.is_default = True
    template.updated_by = None
    db.commit()
    db.refresh(template)
    return MessageTemplateOut.model_validate(template)


# --- criteria -----------------------------------------------------------


def _recipe_out(recipe: MatchingRecipe) -> MatchingRecipeOut:
    return MatchingRecipeOut(
        name=recipe.name,
        version=recipe.version,
        hard_constraints=recipe.hard_constraints,
        weights=recipe.weights,
        fairness=recipe.fairness,
        updated_at=recipe.updated_at,
        updated_by=recipe.updated_by,
    )


def _flagged(db: Session, program_id: uuid.UUID, flag: str) -> list[CriteriaFieldOut]:
    """Published questions carrying a flag, for both roles.

    Read from the published form, so a weight can only exist for a question that
    is actually asked.
    """
    out: list[CriteriaFieldOut] = []
    for role in (Role.MENTEE, Role.MENTOR):
        version = published_version(db, program_id, role)
        if version is None:
            continue
        out.extend(
            CriteriaFieldOut(
                field_id=field["id"],
                label=field["label"],
                role=role,
                type=field["type"],
            )
            for field in all_fields(version)
            if field.get(flag)
        )
    return out


@router.get("/programs/{program_id}/criteria")
def get_criteria(
    program_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> CriteriaEditorStateOut:
    require_coordinator_of_program(db, account, program_id)

    recipe = db.scalar(
        select(MatchingRecipe)
        .where(MatchingRecipe.program_id == program_id)
        .order_by(MatchingRecipe.version.desc())
        .limit(1)
    )
    if recipe is None:
        raise not_found("recipe")

    return CriteriaEditorStateOut(
        recipe=_recipe_out(recipe),
        matching_fields=_flagged(db, program_id, "matching"),
        equity_fields=_flagged(db, program_id, "equity"),
    )


def _bad_recipe(body: MatchingRecipeSaveIn) -> str | None:
    if not body.name.strip():
        return "The recipe needs a name."
    floor = body.fairness.coverage_floor
    if floor < 0 or floor > 1:
        return "The coverage floor is a share between 0 and 100 percent."
    if any(w.weight < 0 or w.weight > 100 for w in body.weights):
        return "Weights run from 0 to 100."
    if body.weights and all(w.weight == 0 for w in body.weights):
        return (
            "Every weight is zero, so nothing would score. Give at least one "
            "question some weight."
        )
    return None


@router.put("/programs/{program_id}/criteria")
def save_criteria(
    program_id: uuid.UUID,
    body: MatchingRecipeSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> MatchingRecipeOut:
    require_coordinator_of_program(db, account, program_id)

    complaint = _bad_recipe(body)
    if complaint:
        raise Problem(400, "invalid_recipe", complaint)

    recipe = db.scalar(
        select(MatchingRecipe)
        .where(MatchingRecipe.program_id == program_id)
        .order_by(MatchingRecipe.version.desc())
        .limit(1)
    )
    if recipe is None:
        raise not_found("recipe")

    recipe.name = body.name.strip()
    recipe.version += 1
    recipe.hard_constraints = [
        c.model_dump(by_alias=True) for c in body.hard_constraints
    ]
    recipe.weights = [w.model_dump(by_alias=True) for w in body.weights]
    recipe.fairness = body.fairness.model_dump(by_alias=True)
    recipe.updated_by = account.name

    _audit(
        db,
        program_id,
        account.name,
        f"Changed the matching recipe to version {recipe.version}.",
        AuditAction.CRITERIA_SAVED,
        f"{recipe.name}, version {recipe.version}",
    )
    db.commit()
    db.refresh(recipe)
    return _recipe_out(recipe)


@router.post("/programs/{program_id}/criteria/test-run")
def test_run_criteria(
    program_id: uuid.UUID,
    body: MatchingRecipeSaveIn,
    db: DbSession,
    account: CurrentAccount,
) -> dict:
    """Scores the current roster and returns the fairness summary — and nothing
    else.

    No pairs leave this endpoint, deliberately. Architecture 5.5 requires that
    weight tuning is not driven by looking at individual matches, for the same
    reason the run review puts the summary above the names: somebody who tunes
    until one particular pair appears has optimised the cohort for one person.

    Nothing is stored. This is not a run.
    """
    require_coordinator_of_program(db, account, program_id)

    complaint = _bad_recipe(body)
    if complaint:
        raise Problem(400, "invalid_recipe", complaint)

    normalise.rebuild(db, program_id)

    recipe = engine.Recipe(
        hard_constraints=[c.model_dump(by_alias=True) for c in body.hard_constraints],
        weights=[
            engine.Weight(
                field_id=w.field_id, weight=w.weight, direction=w.direction
            )
            for w in body.weights
        ],
        equity_weights={
            w.field_id: w.weight for w in body.fairness.priority_weights
        },
        coverage_floor=body.fairness.coverage_floor,
        mentor_capacity_cap=body.fairness.mentor_capacity_cap,
    )

    result, priorities, mentees, mentors = engine.run_matching(db, program_id, recipe)
    summary = engine.fairness_summary(result, priorities, mentees, mentors)

    # Rolled back rather than committed: a test must not leave the projection
    # or anything else changed behind it.
    db.rollback()
    return summary
