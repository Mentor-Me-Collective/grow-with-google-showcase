import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.deps import CurrentAccount, DbSession, require_coordinator_of_program
from app.enums import ParticipationStatus, Role
from app.models import Account, Participation
from app.schemas.auth import AccountOut
from app.schemas.reads import RosterEntryOut, RosterPageOut

router = APIRouter(tags=["Roster"])


@router.get("/programs/{program_id}/roster")
def list_roster(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    role: Role | None = Query(None),
    status: ParticipationStatus | None = Query(None),
    matched: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200, alias="pageSize"),
) -> RosterPageOut:
    """Everyone approved into a programme. Coordinators only.

    The roster carries email addresses and completeness figures for every
    participant, which is the coordinator's working data and nobody else's.
    """
    require_coordinator_of_program(db, account, program_id)

    query = (
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(Participation.program_id == program_id)
    )
    if role is not None:
        query = query.where(Participation.role == role)
    if status is not None:
        query = query.where(Participation.status == status)
    if matched is not None:
        query = query.where(Participation.matched.is_(matched))

    rows = db.execute(query.order_by(Account.name)).all()
    start = (page - 1) * page_size

    return RosterPageOut(
        items=[
            RosterEntryOut(
                id=participation.id,
                account=AccountOut.model_validate(person),
                role=participation.role,
                status=participation.status,
                matched=participation.matched,
                capacity=participation.capacity,
                load=participation.load,
                profile_completeness=participation.profile_completeness,
                timezone=participation.timezone,
                joined_at=participation.joined_at,
            )
            for participation, person in rows[start : start + page_size]
        ],
        page=page,
        page_size=page_size,
        total=len(rows),
    )
