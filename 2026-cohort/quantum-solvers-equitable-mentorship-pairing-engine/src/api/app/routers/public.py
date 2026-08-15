from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.deps import DbSession
from app.enums import ParticipationStatus, Role
from app.errors import Problem, not_found
from app.models import Organisation, Participation, Program
from app.schemas.reads import FormVersionOut, OrganisationOut, ProgramPublicOut
from app.services.profiles import published_version

router = APIRouter(tags=["Public"])


def _program(db, org_slug: str, program_slug: str) -> tuple[Program, Organisation]:
    row = db.execute(
        select(Program, Organisation)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(Organisation.slug == org_slug, Program.slug == program_slug)
    ).first()
    if row is None:
        raise not_found("program")
    return row[0], row[1]


@router.get("/orgs/{org_slug}/programs/{program_slug}")
def get_program(org_slug: str, program_slug: str, db: DbSession) -> ProgramPublicOut:
    """The recruitment page's whole payload. No session required — this is the
    only page a cold link from WhatsApp ever hits."""
    program, org = _program(db, org_slug, program_slug)

    def count(role: Role) -> int:
        return (
            db.scalar(
                select(func.count())
                .select_from(Participation)
                .where(
                    Participation.program_id == program.id,
                    Participation.role == role,
                    Participation.status == ParticipationStatus.APPROVED,
                )
            )
            or 0
        )

    mentors = count(Role.MENTOR)
    mentees = count(Role.MENTEE)

    # Capacity is the sum of what mentors said they could take, so "places
    # remaining" is a real number rather than a marketing one.
    capacity = (
        db.scalar(
            select(func.coalesce(func.sum(Participation.capacity), 0)).where(
                Participation.program_id == program.id,
                Participation.role == Role.MENTOR,
                Participation.status == ParticipationStatus.APPROVED,
            )
        )
        or 0
    )

    return ProgramPublicOut(
        id=program.id,
        slug=program.slug,
        name=program.name,
        organisation=OrganisationOut.model_validate(org),
        description=program.description,
        state=program.state,
        cohort_start=program.cohort_start,
        cohort_end=program.cohort_end,
        applications_close_at=program.applications_close_at,
        matching_opens_at=program.matching_opens_at,
        time_commitment=program.time_commitment,
        eligibility=program.eligibility,
        open_roles=program.open_roles or [],
        mentor_count=mentors,
        mentee_count=mentees,
        capacity=capacity or None,
        places_remaining=max(capacity - mentees, 0) if capacity else None,
    )


@router.get("/orgs/{org_slug}/programs/{program_slug}/form-schema")
def get_form_schema(
    org_slug: str,
    program_slug: str,
    db: DbSession,
    role: Role = Query(...),
) -> FormVersionOut:
    """The live form for a role.

    404 with its own code when a programme has never published one: that is a
    programme not yet ready to take applications, which is different from a
    programme that does not exist, and the screen says so.
    """
    program, _ = _program(db, org_slug, program_slug)
    version = published_version(db, program.id, role)
    if version is None:
        raise Problem(
            404,
            "no_published_form",
            "This programme has no published form for that role yet.",
        )
    return FormVersionOut.model_validate(version)
