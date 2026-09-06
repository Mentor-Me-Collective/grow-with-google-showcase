import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import limits
from app.deps import (
    CurrentAccount,
    DbSession,
    require_coordinator_of_program,
)
from app.enums import (
    ApplicationStatus,
    AuditAction,
    DecisionKind,
    ParticipationStatus,
    Role,
)
from app.errors import Problem, not_found
from app.models import (
    Account,
    Application,
    AuditEvent,
    FormVersion,
    Organisation,
    Participation,
    Program,
)
from app.schemas.reads import FormVersionOut
from app.schemas.setup import (
    ApplicationCountsOut,
    ApplicationCreateIn,
    ApplicationDecisionIn,
    ApplicationOut,
    ApplicationPageOut,
    ApplicationSummaryOut,
    BulkDecisionIn,
    BulkDecisionResultOut,
    SkippedDecisionOut,
)
from app.services.profiles import all_fields, completeness, published_version

router = APIRouter(tags=["Applications"])

#: One way in this slice. Nothing un-decides an application, because undoing it
#: would have to decide what happens to a strand the person may already hold.
DECIDED = {
    ApplicationStatus.APPROVED,
    ApplicationStatus.WAITLISTED,
    ApplicationStatus.REJECTED,
}

_OUTCOME = {
    DecisionKind.APPROVE: ApplicationStatus.APPROVED,
    DecisionKind.WAITLIST: ApplicationStatus.WAITLISTED,
    DecisionKind.REJECT: ApplicationStatus.REJECTED,
}


def _flags(db: Session, application: Application, complete: float) -> list[str]:
    """Things worth a second look, named rather than scored."""
    flags: list[str] = []
    if complete < 0.6:
        flags.append("incomplete")
    duplicate = db.scalar(
        select(Application.id).where(
            Application.program_id == application.program_id,
            Application.email == application.email,
            Application.id != application.id,
        )
    )
    if duplicate is not None:
        flags.append("duplicate_email")
    already = db.scalar(
        select(Participation.id)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == application.program_id,
            Account.email == application.email,
        )
    )
    if already is not None:
        flags.append("reapplied")
    return flags


def _summary(db: Session, application: Application) -> ApplicationSummaryOut:
    version = db.get(FormVersion, application.form_version_id)
    complete = completeness(version, application.answers) if version else 0.0
    return ApplicationSummaryOut(
        id=application.id,
        program_id=application.program_id,
        role=application.role,
        name=application.name,
        email=application.email,
        status=application.status,
        submitted_at=application.submitted_at,
        decided_at=application.decided_at,
        decided_by=application.decided_by,
        completeness=complete,
        flags=_flags(db, application, complete),
    )


def _decide(
    db: Session,
    application: Application,
    outcome: ApplicationStatus,
    actor: str,
) -> None:
    """Approving is the only decision that changes anything beyond the
    application: it creates the participation that puts somebody on the roster,
    which is the whole point of the queue."""
    application.status = outcome
    application.decided_at = datetime.now(UTC)
    application.decided_by = actor

    if outcome != ApplicationStatus.APPROVED:
        return

    account = db.scalar(select(Account).where(Account.email == application.email))
    if account is None:
        account = Account(
            name=application.name, email=application.email, email_verified=False
        )
        db.add(account)
        db.flush()

    existing = db.scalar(
        select(Participation).where(
            Participation.account_id == account.id,
            Participation.program_id == application.program_id,
        )
    )
    if existing is not None:
        existing.status = ParticipationStatus.APPROVED
        return

    version = db.get(FormVersion, application.form_version_id)
    db.add(
        Participation(
            account_id=account.id,
            program_id=application.program_id,
            role=application.role,
            status=ParticipationStatus.APPROVED,
            capacity=2 if application.role == Role.MENTOR else None,
            load=0 if application.role == Role.MENTOR else None,
            profile_completeness=(
                completeness(version, application.answers) if version else 0.0
            ),
            joined_at=datetime.now(UTC),
        )
    )


def _audit(db: Session, program_id: uuid.UUID, actor: str, summary: str, subject: str):
    program = db.get(Program, program_id)
    if program is None:
        return
    db.add(
        AuditEvent(
            organisation_id=program.organisation_id,
            at=datetime.now(UTC),
            actor_name=actor,
            action=AuditAction.APPLICATION_DECIDED,
            summary=summary,
            subject_label=subject,
        )
    )


@router.get("/programs/{program_id}/applications")
def list_applications(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    status: ApplicationStatus | None = Query(None),
    role: Role | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200, alias="pageSize"),
) -> ApplicationPageOut:
    require_coordinator_of_program(db, account, program_id)

    everything = list(
        db.scalars(
            select(Application).where(Application.program_id == program_id)
        ).all()
    )
    filtered = [
        a
        for a in everything
        if (status is None or a.status == status) and (role is None or a.role == role)
    ]
    # Newest first: the queue is read top down and today's intake is the work.
    filtered.sort(key=lambda a: a.submitted_at, reverse=True)
    start = (page - 1) * page_size

    counts = ApplicationCountsOut()
    for a in everything:
        setattr(counts, a.status, getattr(counts, a.status, 0) + 1)

    return ApplicationPageOut(
        items=[_summary(db, a) for a in filtered[start : start + page_size]],
        page=page,
        page_size=page_size,
        total=len(filtered),
        counts=counts,
    )


@router.post("/applications/{application_id}/decision")
def decide_application(
    application_id: uuid.UUID,
    body: ApplicationDecisionIn,
    db: DbSession,
    account: CurrentAccount,
) -> ApplicationOut:
    application = db.get(Application, application_id)
    if application is None:
        raise not_found("application")
    require_coordinator_of_program(db, account, application.program_id)

    if application.status in DECIDED:
        raise Problem(
            409,
            "already_decided",
            f"This application was already {application.status}.",
        )

    _decide(db, application, _OUTCOME[body.decision], account.name)
    _audit(
        db,
        application.program_id,
        account.name,
        f"{body.decision.value.title()}d {application.name} "
        f"as a {application.role}.",
        application.name,
    )
    db.commit()
    db.refresh(application)
    return ApplicationOut.model_validate(application)


@router.post("/programs/{program_id}/applications/decisions")
def decide_applications(
    program_id: uuid.UUID,
    body: BulkDecisionIn,
    db: DbSession,
    account: CurrentAccount,
) -> BulkDecisionResultOut:
    require_coordinator_of_program(db, account, program_id)

    decided = 0
    skipped: list[SkippedDecisionOut] = []

    for application_id in body.application_ids:
        application = db.get(Application, application_id)
        if application is None or application.program_id != program_id:
            skipped.append(
                SkippedDecisionOut(
                    application_id=application_id, reason="No such application."
                )
            )
            continue
        if application.status in DECIDED:
            skipped.append(
                SkippedDecisionOut(
                    application_id=application_id,
                    reason=f"Already {application.status}.",
                )
            )
            continue
        _decide(db, application, _OUTCOME[body.decision], account.name)
        decided += 1

    if decided:
        _audit(
            db,
            program_id,
            account.name,
            f"{body.decision.value.title()}d {decided} applications at once.",
            f"{decided} applications",
        )
    db.commit()
    return BulkDecisionResultOut(decided=decided, skipped=skipped)


@router.get("/form-versions/{form_version_id}")
def get_form_version(
    form_version_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> FormVersionOut:
    """An application stores the version it was answered against, and answers
    are keyed by field id. Reading one back therefore needs that exact version —
    not the current published one, which may have moved on — or the answers are
    a map of uuids to values."""
    version = db.get(FormVersion, form_version_id)
    if version is None:
        raise not_found("form version")
    return FormVersionOut.model_validate(version)


# --- public intake ------------------------------------------------------


@router.post(
    "/orgs/{org_slug}/programs/{program_slug}/applications",
    status_code=201,
    tags=["Public"],
)
def submit_application(
    org_slug: str,
    program_slug: str,
    body: ApplicationCreateIn,
    db: DbSession,
    request: Request,
) -> ApplicationOut:
    """No session required. Somebody applying does not have an account yet.

    Which is also why it is limited by source: this writes an account and a
    participation for anybody who asks, and nothing else stands in front of it.
    """
    limits.enforce("application", limits.source(request), limits.APPLICATION_SUBMIT)
    row = db.execute(
        select(Program, Organisation)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(Organisation.slug == org_slug, Program.slug == program_slug)
    ).first()
    if row is None:
        raise not_found("program")
    program, _ = row

    if program.state == "closed":
        raise Problem(
            409, "applications_closed", "Applications have closed for this programme."
        )

    email = body.email.lower().strip()
    if db.scalar(
        select(Application.id).where(
            Application.program_id == program.id, Application.email == email
        )
    ):
        raise Problem(
            409,
            "already_applied",
            "An application already exists for this email address.",
        )

    version = db.get(FormVersion, body.form_version_id)
    if version is None or version.role != body.role or version.program_id != program.id:
        raise Problem(
            409,
            "stale_form_version",
            "The form has changed since you started. Reload to see the current "
            "questions.",
        )

    # The client asserts provenance; the server owns the clock.
    now = datetime.now(UTC)
    stamped = {
        field_id: {**answer, "answeredAt": now.isoformat()}
        for field_id, answer in (body.answers or {}).items()
    }

    application = Application(
        program_id=program.id,
        form_version_id=version.id,
        role=body.role,
        name=body.name.strip(),
        email=email,
        status=ApplicationStatus.SUBMITTED,
        submitted_at=now,
        editable_until=program.applications_close_at,
        matching_opens_at=program.matching_opens_at,
        answers=stamped,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    out = ApplicationOut.model_validate(application)
    out.program_name = program.name
    return out


@router.get("/applications/{application_id}", tags=["Public"])
def get_application(application_id: uuid.UUID, db: DbSession) -> ApplicationOut:
    """Backs the "what happens next" screen after submitting.

    Keyed by a raw UUID and requiring no session, which is acceptable for this
    slice and is a real access-control hole: in production the emailed link
    carries a signed, expiring token scoped to this one application, and the raw
    UUID stops being a valid credential.
    """
    application = db.get(Application, application_id)
    if application is None:
        raise not_found("application")
    program = db.get(Program, application.program_id)

    out = ApplicationOut.model_validate(application)
    out.program_name = program.name if program else None
    return out


def _askable(version: FormVersion) -> int:
    return len(all_fields(version))


def _published(db: Session, program_id: uuid.UUID, role: Role) -> FormVersion | None:
    return published_version(db, program_id, role)
