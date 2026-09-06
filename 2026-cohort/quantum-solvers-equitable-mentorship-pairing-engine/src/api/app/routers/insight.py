"""What the programme did, and who changed it.

Two read-only endpoints that exist for the same reason: a fairness claim nobody
can inspect is a marketing claim. The report says what happened to the cohort;
the audit log says where a human overruled the algorithm on the way.
"""

import uuid
from datetime import UTC, date, datetime, time

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.deps import (
    CurrentAccount,
    DbSession,
    coordinator_of_org,
    load_program,
    require_coordinator_of_program,
)
from app.enums import AuditAction
from app.models import AuditEvent
from app.schemas.insight import AuditEventOut, AuditPageOut, ProgramReportOut
from app.services import report as report_service

router = APIRouter(tags=["Insight"])


@router.get("/programs/{program_id}/report", response_model=ProgramReportOut)
def get_report(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
) -> ProgramReportOut:
    program = load_program(db, program_id)
    require_coordinator_of_program(db, account, program_id)

    fallback_start, fallback_end = report_service.default_range(
        db, program, datetime.now(UTC).date()
    )
    start = from_ or fallback_start
    end = to or fallback_end
    # A backwards range is a mistyped URL rather than a request to invert the
    # report, so it is straightened instead of refused.
    if start > end:
        start, end = end, start

    return report_service.build(db, program, start, end)


def _range_filter(query, column, start: date | None, end: date | None):
    """Inclusive of both ends, in whole days.

    `to=2026-08-14` means the whole of the fourteenth. A naive `<= date` would
    compare against midnight and silently drop everything that happened that
    day, which is the day the coordinator is most likely to be looking for.
    """
    if start is not None:
        query = query.where(column >= datetime.combine(start, time.min, tzinfo=UTC))
    if end is not None:
        query = query.where(column <= datetime.combine(end, time.max, tzinfo=UTC))
    return query


@router.get("/orgs/{org_slug}/audit", response_model=AuditPageOut)
def list_audit_events(
    org_slug: str,
    db: DbSession,
    account: CurrentAccount,
    actor: str | None = Query(None),
    action: AuditAction | None = Query(None),
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200, alias="pageSize"),
) -> AuditPageOut:
    org, _ = coordinator_of_org(db, account, org_slug)

    def scoped(query):
        query = query.where(AuditEvent.organisation_id == org.id)
        return _range_filter(query, AuditEvent.at, from_, to)

    filtered = scoped(select(AuditEvent))
    if actor:
        filtered = filtered.where(AuditEvent.actor_name == actor)
    if action:
        filtered = filtered.where(AuditEvent.action == action)

    total = (
        db.scalar(
            select(func.count()).select_from(filtered.subquery())
        )
        or 0
    )

    rows = db.scalars(
        filtered.order_by(AuditEvent.at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Actors come from the whole log for the organisation, not from the filtered
    # page: a filter that removed its own option would be a one-way door out of
    # the view the coordinator just chose.
    actors = sorted(
        name
        for name in db.scalars(
            select(AuditEvent.actor_name)
            .where(AuditEvent.organisation_id == org.id)
            .distinct()
        ).all()
    )

    return AuditPageOut(
        items=[
            AuditEventOut(
                id=event.id,
                at=event.at,
                actor_name=event.actor_name,
                action=event.action,
                summary=event.summary,
                subject_label=event.subject_label,
            )
            for event in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
        actors=actors,
    )
