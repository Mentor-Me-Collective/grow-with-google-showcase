"""The person, rather than any one programme they are in.

Everything here is scoped to the signed-in account and to nothing else — there
is no org slug and no programme id in any of these paths, which is exactly why
`(account)` is its own route group on the frontend and cannot inherit the
participant layout.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import CurrentAccount, DbSession
from app.enums import ParticipationStatus, StrandState
from app.errors import Problem, not_found
from app.models import (
    Account,
    Message,
    MessageRead,
    Organisation,
    Participation,
    Program,
    Strand,
    StrandMember,
)
from app.schemas.account import (
    AccountProgramOut,
    AccountSettingsOut,
    AccountSettingsSaveIn,
    MuteChangeIn,
    NotificationPreferencesOut,
)
from app.schemas.auth import AccountOut

router = APIRouter(tags=["Account"])


def _preferences(account: Account) -> NotificationPreferencesOut:
    return NotificationPreferencesOut(
        new_message=account.notify_new_message,
        match_published=account.notify_match_published,
        milestone_reminders=account.notify_milestone_reminders,
        broadcasts=account.notify_broadcasts,
        digest=account.digest_frequency,
    )


def _unread_for(db: Session, participation_id: uuid.UUID) -> int:
    """Unread messages across every strand this participation holds.

    One query rather than one per strand: this list is the account's whole
    membership, and a person in six programmes should not cost six round trips.
    """
    read = select(MessageRead.message_id).where(
        MessageRead.participation_id == participation_id
    )
    mine = select(StrandMember.strand_id).where(
        StrandMember.participation_id == participation_id
    )
    return (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.strand_id.in_(mine),
                Message.author_participation_id != participation_id,
                Message.id.not_in(read),
            )
        )
        or 0
    )


def account_programs(db: Session, account: Account) -> list[AccountProgramOut]:
    today = datetime.now(UTC).date()
    rows = db.execute(
        select(Participation, Program, Organisation)
        .join(Program, Participation.program_id == Program.id)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(
            Participation.account_id == account.id,
            # Somebody who left is gone from their own list. The record stays in
            # the database because the strand's history refers to it.
            Participation.status != ParticipationStatus.REMOVED,
        )
        .order_by(Organisation.name, Program.name)
    ).all()

    return [
        AccountProgramOut(
            participation_id=participation.id,
            program_id=program.id,
            program_name=program.name,
            organisation_name=org.name,
            org_slug=org.slug,
            program_slug=program.slug,
            role=participation.role,
            status=participation.status,
            is_coordinator=participation.is_coordinator,
            muted=participation.muted,
            unread_count=_unread_for(db, participation.id),
            # The cohort being over, not applications being shut. A programme
            # closed to new applicants is still running for the people in it.
            # A finished one stays readable rather than disappearing.
            read_only=(
                program.cohort_end is not None and program.cohort_end < today
            ),
        )
        for participation, program, org in rows
    ]


@router.get("/account/settings", response_model=AccountSettingsOut)
def get_account_settings(db: DbSession, account: CurrentAccount) -> AccountSettingsOut:
    return AccountSettingsOut(
        account=AccountOut.model_validate(account),
        notifications=_preferences(account),
        programs=account_programs(db, account),
    )


@router.put("/account/settings", response_model=AccountSettingsOut)
def save_account_settings(
    body: AccountSettingsSaveIn, db: DbSession, account: CurrentAccount
) -> AccountSettingsOut:
    # Each section of the screen saves on its own, so an absent field means
    # "unchanged" rather than "empty". Reading them as empty is how a settings
    # form quietly wipes the half of itself that was not on screen.
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise Problem(400, "invalid_name", "Your name cannot be empty.")
        account.name = name

    if body.notifications is not None:
        prefs = body.notifications
        account.notify_new_message = prefs.new_message
        account.notify_match_published = prefs.match_published
        account.notify_milestone_reminders = prefs.milestone_reminders
        account.notify_broadcasts = prefs.broadcasts
        account.digest_frequency = prefs.digest

    db.commit()
    db.refresh(account)
    return AccountSettingsOut(
        account=AccountOut.model_validate(account),
        notifications=_preferences(account),
        programs=account_programs(db, account),
    )


@router.get("/account/programs", response_model=list[AccountProgramOut])
def list_account_programs(
    db: DbSession, account: CurrentAccount
) -> list[AccountProgramOut]:
    return account_programs(db, account)


def _own_participation(
    db: Session, account: Account, participation_id: uuid.UUID
) -> Participation:
    """404 rather than 403 for somebody else's participation.

    Unlike a programme, which is advertised publicly, the existence of another
    person's membership is not something an outsider is entitled to confirm.
    """
    participation = db.scalar(
        select(Participation).where(
            Participation.id == participation_id,
            Participation.account_id == account.id,
        )
    )
    if participation is None:
        raise not_found("participation")
    return participation


@router.put("/participations/{participation_id}/mute", response_model=AccountProgramOut)
def mute_participation(
    participation_id: uuid.UUID,
    body: MuteChangeIn,
    db: DbSession,
    account: CurrentAccount,
) -> AccountProgramOut:
    participation = _own_participation(db, account, participation_id)
    participation.muted = body.muted
    db.commit()

    updated = next(
        (
            p
            for p in account_programs(db, account)
            if p.participation_id == participation.id
        ),
        None,
    )
    if updated is None:
        raise not_found("participation")
    return updated


@router.post("/participations/{participation_id}/leave", status_code=204)
def leave_program(
    participation_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> Response:
    participation = _own_participation(db, account, participation_id)

    # A coordinator leaving would take the programme's only administrator with
    # her. Handing over is a different action with a different screen, and
    # refusing here is more honest than silently doing half of it.
    if participation.is_coordinator:
        raise Problem(
            409,
            "coordinator_cannot_leave",
            "You coordinate this programme, so you cannot leave it here. Hand "
            "the programme over first.",
        )

    now = datetime.now(UTC)
    strand_ids = db.scalars(
        select(StrandMember.strand_id).where(
            StrandMember.participation_id == participation.id
        )
    ).all()

    for strand in db.scalars(
        select(Strand).where(
            Strand.id.in_(strand_ids), Strand.state != StrandState.ENDED
        )
    ).all():
        # The strand ends, the conversation is kept, and the other side can
        # still read it. A thread that vanished would leave the mentor unable
        # to tell being left from a fault in the product.
        strand.state = StrandState.ENDED
        strand.ended_at = now

    participation.status = ParticipationStatus.REMOVED
    participation.matched = False
    db.commit()
    return Response(status_code=204)
