import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import limits
from app.deps import CurrentAccount, DbSession, participation_in
from app.enums import StrandState
from app.errors import Problem, forbidden, not_found
from app.models import Message, MessageRead, Participation, Strand, StrandMember
from app.schemas.reads import (
    MessageCreateIn,
    MessageOut,
    MessagePageOut,
    StrandOut,
    StrandSummaryOut,
)
from app.services import strands as svc

router = APIRouter(tags=["Strands"])


def _my_participation(db: Session, account, strand: Strand) -> Participation:
    """The reader's own membership of this strand, or 403.

    Membership of the strand, not of the programme: a coordinator is in the
    programme but is not a party to other people's conversations, and this
    endpoint serves the participant's view.
    """
    mine = db.scalar(
        select(Participation)
        .join(StrandMember, StrandMember.participation_id == Participation.id)
        .where(
            StrandMember.strand_id == strand.id,
            Participation.account_id == account.id,
        )
    )
    if mine is None:
        raise forbidden("This strand is not yours.")
    return mine


@router.get("/programs/{program_id}/strands")
def list_strands(
    program_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    state: StrandState | None = Query(None),
) -> list[StrandSummaryOut]:
    me = participation_in(db, account, program_id)

    query = (
        select(Strand)
        .join(StrandMember, StrandMember.strand_id == Strand.id)
        .where(
            Strand.program_id == program_id,
            StrandMember.participation_id == me.id,
        )
        .order_by(Strand.last_activity_at.desc().nullslast())
    )
    if state is not None:
        query = query.where(Strand.state == state)

    return [svc.to_summary(db, strand, me.id) for strand in db.scalars(query).all()]


@router.get("/strands/{strand_id}")
def get_strand(
    strand_id: uuid.UUID, db: DbSession, account: CurrentAccount
) -> StrandOut:
    strand = db.get(Strand, strand_id)
    if strand is None:
        raise not_found("strand")
    _my_participation(db, account, strand)
    return svc.to_strand(db, strand)


@router.get("/strands/{strand_id}/messages")
def list_messages(
    strand_id: uuid.UUID,
    db: DbSession,
    account: CurrentAccount,
    before: uuid.UUID | None = Query(None),
    since: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> MessagePageOut:
    """Newest last, paged backwards with `before` or forwards with `since`.

    Reading the thread marks it read, which is what makes the unread count on
    the strands list mean anything.
    """
    if before is not None and since is not None:
        raise Problem(
            400,
            "conflicting_cursors",
            "Ask for messages before a point or after one, not both.",
        )

    strand = db.get(Strand, strand_id)
    if strand is None:
        raise not_found("strand")
    me = _my_participation(db, account, strand)

    query = select(Message).where(Message.strand_id == strand_id)
    if before is not None:
        anchor = db.get(Message, before)
        if anchor is not None:
            query = query.where(Message.sent_at < anchor.sent_at)

    if since is not None:
        # An unknown anchor falls through to the newest page below rather than
        # answering empty. A poller holding a cursor the server has never heard
        # of is out of sync, and the recent window is how it recovers — the
        # client merges by id, so nothing arrives twice.
        anchor = db.get(Message, since)
        if anchor is not None:
            # Ordered forwards and taken from the oldest end, so a poll that
            # falls behind catches up in order instead of skipping the middle.
            ordered = list(
                db.scalars(
                    query.where(Message.sent_at > anchor.sent_at)
                    .order_by(Message.sent_at.asc())
                    .limit(limit)
                ).all()
            )
            _mark_read(db, ordered, me.id)
            db.commit()
            accounts = svc.author_accounts(db, strand)
            return MessagePageOut(
                items=[svc.to_message(db, m, accounts) for m in ordered],
                # Only meaningful walking backwards. A forwards page has no
                # older page to offer.
                next_cursor=None,
            )

    # Take the newest `limit`, then reverse: the thread reads oldest-first but
    # a page is anchored at the recent end.
    newest = list(db.scalars(query.order_by(Message.sent_at.desc()).limit(limit)).all())
    ordered = list(reversed(newest))

    _mark_read(db, ordered, me.id)
    db.commit()

    accounts = svc.author_accounts(db, strand)
    return MessagePageOut(
        items=[svc.to_message(db, m, accounts) for m in ordered],
        next_cursor=str(ordered[0].id) if len(newest) == limit and ordered else None,
    )


@router.post("/strands/{strand_id}/messages", status_code=201)
def send_message(
    strand_id: uuid.UUID,
    body: MessageCreateIn,
    db: DbSession,
    account: CurrentAccount,
) -> MessageOut:
    strand = db.get(Strand, strand_id)
    if strand is None:
        raise not_found("strand")
    me = _my_participation(db, account, strand)

    # Keyed on the participation rather than the source: the sender is
    # authenticated here, so there is something better to count than an address
    # they can change.
    limits.enforce("message_send", str(me.id), limits.MESSAGE_SEND)

    text = body.body.strip()
    if not text:
        raise Problem(400, "empty_message", "Write something to send.")
    if strand.state == StrandState.ENDED:
        raise Problem(
            409,
            "strand_ended",
            "This strand has ended. The conversation stays readable, but nothing "
            "new can be sent.",
        )

    # A retry after a dropped response is the same send, not a second one. The
    # client token is what makes that decidable, and this is the case that
    # actually happens: somebody on a phone taps send, the connection stalls,
    # and the app tries again. Without this the mentor reads the same sentence
    # twice and neither of them knows why.
    if body.client_token:
        already_sent = db.scalar(
            select(Message).where(
                Message.strand_id == strand.id,
                Message.author_participation_id == me.id,
                Message.client_token == body.client_token,
            )
        )
        if already_sent is not None:
            return svc.to_message(db, already_sent, svc.author_accounts(db, strand))

    now = datetime.now(UTC)
    message = Message(
        strand_id=strand.id,
        author_participation_id=me.id,
        body=text,
        sent_at=now,
        delivery_state="sent",
        client_token=body.client_token,
    )
    db.add(message)
    # Flush before referencing message.id: the UUID default is applied by
    # SQLAlchemy at flush, so until then the id is None and the read receipt
    # below would point at nothing.
    db.flush()

    # The strand's activity is what the quiet-strand health signal reads, so it
    # has to move with the conversation rather than be recomputed later.
    strand.last_activity_at = now

    # Your own message is not unread to you.
    db.add(MessageRead(message_id=message.id, participation_id=me.id, read_at=now))
    db.commit()

    accounts = svc.author_accounts(db, strand)
    return svc.to_message(db, message, accounts)


def _mark_read(
    db: Session, messages: list[Message], reader_id: uuid.UUID
) -> None:
    if not messages:
        return
    already = set(
        db.scalars(
            select(MessageRead.message_id).where(
                MessageRead.participation_id == reader_id,
                MessageRead.message_id.in_([m.id for m in messages]),
            )
        ).all()
    )
    now = datetime.now(UTC)
    for message in messages:
        if message.id in already or message.author_participation_id == reader_id:
            continue
        db.add(
            MessageRead(message_id=message.id, participation_id=reader_id, read_at=now)
        )
