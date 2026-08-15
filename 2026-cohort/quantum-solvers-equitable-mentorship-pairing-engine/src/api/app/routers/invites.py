"""Invitations, drafts and the waitlist — the three doors that open without one.

None of these carries a session, and that is deliberate rather than an
oversight. Somebody arriving from an email has not signed in yet, and a
half-typed application belongs to whoever is holding the browser that started
it. What each one grants is scoped to match: an invite grants the programme it
names, a draft grants the answers already typed on that device, and the
waitlist grants nothing at all.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import DbSession
from app.enums import InviteState, ParticipationStatus, ProgramState
from app.errors import Problem, not_found
from app.mail import send
from app.models import (
    Account,
    ApplicationDraft,
    Invite,
    Organisation,
    Participation,
    Program,
    WaitlistEntry,
)
from app.routers.auth import session_for
from app.schemas.account import (
    ApplicationDraftOut,
    ApplicationDraftSaveIn,
    InviteAcceptedOut,
    InviteOut,
    InviteResponseIn,
    WaitlistJoinIn,
)
from app.security import open_session, set_session_cookie

router = APIRouter(tags=["Public"])


def _load_invite(db: Session, token: str) -> tuple[Invite, Program, Organisation]:
    invite = db.scalar(select(Invite).where(Invite.token == token))
    if invite is None:
        raise not_found("invitation")
    row = db.execute(
        select(Program, Organisation)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(Program.id == invite.program_id)
    ).first()
    if row is None:
        raise not_found("invitation")
    return invite, row[0], row[1]


def _expired(invite: Invite) -> bool:
    return invite.expires_at is not None and invite.expires_at < datetime.now(UTC)


def _to_invite(
    db: Session, invite: Invite, program: Program, org: Organisation
) -> InviteOut:
    has_account = (
        db.scalar(select(Account.id).where(Account.email == invite.email)) is not None
    )
    # Expiry is worked out on read rather than swept by a job. A token that
    # lapsed an hour ago is expired whether or not anything has run since.
    state = (
        InviteState.EXPIRED
        if invite.state == InviteState.PENDING and _expired(invite)
        else invite.state
    )
    return InviteOut(
        token=invite.token,
        state=state,
        email=invite.email,
        organisation_name=org.name,
        program_name=program.name,
        org_slug=org.slug,
        program_slug=program.slug,
        role=invite.role,
        invited_by_name=invite.invited_by_name,
        message=invite.message,
        expires_at=invite.expires_at,
        has_account=has_account,
    )


@router.get("/invites/{token}", response_model=InviteOut)
def get_invite(token: str, db: DbSession) -> InviteOut:
    """Readable even once spent, because the screen has to explain what
    happened. A 404 here would tell somebody holding a real invitation that it
    never existed."""
    invite, program, org = _load_invite(db, token)
    return _to_invite(db, invite, program, org)


@router.post("/invites/{token}", response_model=InviteAcceptedOut | None)
def respond_to_invite(
    token: str, body: InviteResponseIn, db: DbSession, response: Response
) -> InviteAcceptedOut | Response:
    invite, program, org = _load_invite(db, token)

    if invite.state != InviteState.PENDING or _expired(invite):
        raise Problem(
            410,
            "invite_spent",
            "This invitation has already been used or has expired. Ask for a "
            "new one and it will be sent to the same address.",
        )

    if not body.accept:
        invite.state = InviteState.DECLINED
        db.commit()
        return Response(status_code=204)

    account = db.scalar(select(Account).where(Account.email == invite.email))
    if account is None:
        name = (body.name or "").strip()
        if not name:
            raise Problem(
                400,
                "name_required",
                "Tell us what to call you so your mentor knows who they are "
                "writing to.",
            )
        # The invitation is itself proof the address works — somebody read the
        # mail sent to it — so this account starts verified rather than sending
        # a second link to the same inbox.
        account = Account(name=name, email=invite.email, email_verified=True)
        db.add(account)
        db.flush()

    existing = db.scalar(
        select(Participation).where(
            Participation.account_id == account.id,
            Participation.program_id == program.id,
        )
    )
    if existing is None:
        db.add(
            Participation(
                account_id=account.id,
                program_id=program.id,
                role=invite.role,
                status=ParticipationStatus.APPROVED,
                joined_at=datetime.now(UTC),
            )
        )
    else:
        # Re-invited after leaving, or invited for something they already hold.
        # Restoring beats a second membership, which would split their strands.
        existing.status = ParticipationStatus.APPROVED

    invite.state = InviteState.ACCEPTED

    # One commit, after the session is opened. Committing the membership first
    # and the session afterwards leaves the token unflushed, and the person
    # lands on the programme holding a cookie that resolves to nobody.
    session = open_session(db, account)
    db.commit()

    set_session_cookie(response, session.token)
    return InviteAcceptedOut(
        session=session_for(db, account),
        org_slug=org.slug,
        program_slug=program.slug,
    )


@router.post("/invites/{token}/reissue", status_code=202)
def request_new_invite(token: str, db: DbSession) -> Response:
    """Ask the coordinator for a fresh one.

    Deliberately does not mint a new token here: an expired invitation is the
    one moment the programme gets to check whether it still means to invite this
    person. Self-service renewal would make expiry decorative.
    """
    invite, program, _org = _load_invite(db, token)
    send(
        to=invite.email,
        subject=f"A new invitation to {program.name} has been requested",
        body=(
            f"{invite.email} asked for a fresh invitation to {program.name}. "
            f"{invite.invited_by_name} has been told and will send one."
        ),
    )
    return Response(status_code=202)


def _open_program(db: Session, org_slug: str, program_slug: str) -> Program:
    row = db.execute(
        select(Program, Organisation)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(Organisation.slug == org_slug, Program.slug == program_slug)
    ).first()
    if row is None:
        raise not_found("program")
    return row[0]


@router.get(
    "/orgs/{org_slug}/programs/{program_slug}/application-draft",
    response_model=ApplicationDraftOut,
)
def get_application_draft(
    org_slug: str,
    program_slug: str,
    db: DbSession,
    draft_id: uuid.UUID = Query(..., alias="draftId"),
) -> ApplicationDraftOut:
    program = _open_program(db, org_slug, program_slug)
    draft = db.scalar(
        select(ApplicationDraft).where(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.program_id == program.id,
        )
    )
    if draft is None or draft.form_version_id is None:
        raise not_found("draft")
    return ApplicationDraftOut(
        draft_id=draft.id,
        role=draft.role,
        form_version_id=draft.form_version_id,
        answers=draft.answers or {},
        saved_at=draft.updated_at,
    )


@router.put(
    "/orgs/{org_slug}/programs/{program_slug}/application-draft",
    response_model=ApplicationDraftOut,
)
def save_application_draft(
    org_slug: str,
    program_slug: str,
    body: ApplicationDraftSaveIn,
    db: DbSession,
) -> ApplicationDraftOut:
    program = _open_program(db, org_slug, program_slug)

    if program.state not in (ProgramState.OPEN, ProgramState.FULL):
        raise Problem(
            409,
            "applications_closed",
            "Applications for this programme are closed, so this cannot be "
            "saved. Your answers are still on this device.",
        )

    draft = None
    if body.draft_id is not None:
        draft = db.scalar(
            select(ApplicationDraft).where(
                ApplicationDraft.id == body.draft_id,
                ApplicationDraft.program_id == program.id,
            )
        )
        # An id the server does not recognise starts a new draft rather than
        # failing. The alternative is an autosave that errors forever on a
        # browser holding a stale id, with nowhere for the applicant to go.

    if draft is None:
        draft = ApplicationDraft(program_id=program.id, role=body.role)
        db.add(draft)

    draft.role = body.role
    draft.form_version_id = body.form_version_id
    draft.answers = body.answers
    # Touched by hand: only the answers column changed, and SQLAlchemy would
    # otherwise leave updated_at where it was — which is the one field the
    # autosave indicator actually shows.
    draft.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(draft)

    return ApplicationDraftOut(
        draft_id=draft.id,
        role=draft.role,
        form_version_id=draft.form_version_id or body.form_version_id,
        answers=draft.answers or {},
        saved_at=draft.updated_at,
    )


@router.post("/orgs/{org_slug}/programs/{program_slug}/waitlist", status_code=202)
def join_waitlist(
    org_slug: str, program_slug: str, body: WaitlistJoinIn, db: DbSession
) -> Response:
    """Ask to be told when the next round opens.

    202 whether or not the address was already on the list. Answering
    differently would turn this open endpoint into a way to test which
    addresses a programme holds.
    """
    program = _open_program(db, org_slug, program_slug)
    email = body.email.strip().lower()

    already = db.scalar(
        select(WaitlistEntry).where(
            WaitlistEntry.program_id == program.id,
            WaitlistEntry.email == email,
        )
    )
    if already is None:
        db.add(
            WaitlistEntry(
                program_id=program.id,
                email=email,
                role=body.role,
            )
        )
        db.commit()
    return Response(status_code=202)
