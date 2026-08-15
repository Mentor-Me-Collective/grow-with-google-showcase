from urllib.parse import urlencode

from fastapi import APIRouter, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import mail
from app.config import get_settings
from app.deps import CurrentAccount, DbSession, RawSession
from app.errors import Problem, not_found
from app.models import Account, Organisation, Participation, Program
from app.schemas.auth import (
    AccountOut,
    DemoSignInRequest,
    MagicLinkRequest,
    ParticipationSummaryOut,
    SessionOut,
    VerifyRequest,
)
from app.security import (
    clear_session_cookie,
    consume_magic_link,
    issue_magic_link,
    open_session,
    revoke_session,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


def session_for(db: Session, account: Account) -> SessionOut:
    """The account with every membership it holds, which is what the frontend's
    guards, programme switcher and role checks all read."""
    rows = db.execute(
        select(Participation, Program, Organisation)
        .join(Program, Participation.program_id == Program.id)
        .join(Organisation, Program.organisation_id == Organisation.id)
        .where(Participation.account_id == account.id)
        .order_by(Program.name)
    ).all()

    return SessionOut(
        account=AccountOut.model_validate(account),
        participations=[
            ParticipationSummaryOut(
                id=participation.id,
                program_id=program.id,
                program_name=program.name,
                organisation_name=org.name,
                org_slug=org.slug,
                program_slug=program.slug,
                role=participation.role,
                status=participation.status,
                is_coordinator=participation.is_coordinator,
            )
            for participation, program, org in rows
        ],
    )


@router.post("/magic-link", status_code=202)
def request_magic_link(body: MagicLinkRequest, db: DbSession) -> Response:
    """Always 202, whether or not the address has an account.

    Answering differently would turn this into an account-enumeration oracle:
    anybody could learn who is in a programme by posting addresses at it. A link
    is minted only for a real account, and the caller cannot tell which happened.
    """
    email = body.email.lower().strip()
    account = db.scalar(select(Account).where(Account.email == email))

    if account is not None:
        token = issue_magic_link(db, email)
        db.commit()

        # Carried through the link so somebody who started at a programme is
        # returned to it rather than dropped on a generic landing.
        suffix = ""
        if body.org_slug and body.program_slug:
            suffix = "?" + urlencode(
                {"org": body.org_slug, "program": body.program_slug}
            )
        mail.send_magic_link(
            email, f"{settings.web_origin}/verify/{token.token}{suffix}"
        )

    return Response(status_code=202)


@router.post("/verify")
def verify(body: VerifyRequest, db: DbSession, response: Response) -> SessionOut:
    token = consume_magic_link(db, body.token)
    if token is None:
        # 410 rather than 404 or 401: the contract distinguishes a link that has
        # expired or been used from one that never existed, and the screen shows
        # a recovery path for the first.
        raise Problem(410, "token_spent", "That link has expired or was already used.")

    account = db.scalar(select(Account).where(Account.email == token.email))
    if account is None:
        raise Problem(410, "token_spent", "That link has expired or was already used.")

    # Following a link from an inbox is the proof the address is reachable.
    account.email_verified = True

    session = open_session(db, account)
    db.commit()

    set_session_cookie(response, session.token)
    return session_for(db, account)


@router.post("/demo")
def sign_in_as_demo(
    body: DemoSignInRequest, db: DbSession, response: Response
) -> SessionOut:
    """Sign in as a seeded account so a reviewer can see the product.

    404 when demo mode is off, so it is absent rather than merely
    undocumented — an endpoint that answers differently is an endpoint that
    can be found.

    It never creates an account. If the seed is not loaded there is nobody to
    be, and that is a 404 too.
    """
    if not settings.demo_mode:
        raise not_found("route")

    wanted_coordinator = body.as_ == "coordinator"
    participation = db.scalar(
        select(Participation)
        .where(Participation.is_coordinator.is_(wanted_coordinator))
        .where(Participation.role == ("mentor" if wanted_coordinator else "mentee"))
        .order_by(Participation.joined_at)
    )
    if participation is None:
        raise not_found("demo account")

    account = db.get(Account, participation.account_id)
    if account is None:
        raise not_found("demo account")

    session = open_session(db, account)
    db.commit()

    set_session_cookie(response, session.token)
    return session_for(db, account)


@router.post("/signout", status_code=204)
def signout(db: DbSession, raw: RawSession, response: Response) -> Response:
    """Safe without a session: signing out twice is not an error, and the
    contract declares no security requirement here for that reason."""
    revoke_session(db, raw)
    db.commit()

    out = Response(status_code=204)
    clear_session_cookie(out)
    return out


@router.get("/session")
def read_session(db: DbSession, account: CurrentAccount) -> SessionOut:
    return session_for(db, account)
