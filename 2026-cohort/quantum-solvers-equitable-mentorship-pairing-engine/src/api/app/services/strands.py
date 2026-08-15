"""Assembling strands for the screens that read them."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Message, MessageRead, Participation, Strand
from app.schemas.reads import (
    MessageAuthorOut,
    MessageOut,
    MessagePreviewOut,
    StrandMemberOut,
    StrandOut,
    StrandSummaryOut,
)


def member_rows(db: Session, strand: Strand) -> list[tuple[Participation, Account]]:
    return list(
        db.execute(
            select(Participation, Account)
            .join(Account, Participation.account_id == Account.id)
            .where(
                Participation.id.in_([m.participation_id for m in strand.members])
            )
        ).all()
    )


def to_member(participation: Participation, account: Account) -> StrandMemberOut:
    return StrandMemberOut(
        participation_id=participation.id,
        name=account.name,
        role=participation.role,
        headline=participation.headline,
        photo_url=account.photo_url,
        timezone=participation.timezone,
        skills=participation.skills or [],
    )


def last_message(db: Session, strand_id: uuid.UUID) -> Message | None:
    return db.scalar(
        select(Message)
        .where(Message.strand_id == strand_id)
        .order_by(Message.sent_at.desc())
        .limit(1)
    )


def unread_count(db: Session, strand_id: uuid.UUID, reader_id: uuid.UUID) -> int:
    """Messages in this strand the reader has not opened and did not write.

    Counted rather than stored: a stored counter is one more thing to keep
    true, and at a strand's message volume this is a cheap query.
    """
    read = select(MessageRead.message_id).where(
        MessageRead.participation_id == reader_id
    )
    return (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.strand_id == strand_id,
                Message.author_participation_id != reader_id,
                Message.id.not_in(read),
            )
        )
        or 0
    )


def to_summary(
    db: Session, strand: Strand, reader_id: uuid.UUID | None
) -> StrandSummaryOut:
    """`members` excludes the reader: a participant's own screens are about the
    other person. Pass reader_id=None for an admin view, which needs everybody."""
    members = [
        to_member(p, a)
        for p, a in member_rows(db, strand)
        if reader_id is None or p.id != reader_id
    ]
    latest = last_message(db, strand.id)
    author_name = None
    if latest is not None:
        author_name = db.scalar(
            select(Account.name)
            .join(Participation, Participation.account_id == Account.id)
            .where(Participation.id == latest.author_participation_id)
        )

    return StrandSummaryOut(
        id=strand.id,
        program_id=strand.program_id,
        state=strand.state,
        origin_mode=strand.origin_mode,
        members=members,
        last_message=(
            MessagePreviewOut(
                author_name=author_name or "Someone",
                body=latest.body,
                sent_at=latest.sent_at,
            )
            if latest
            else None
        ),
        last_activity_at=strand.last_activity_at,
        unread_count=(
            unread_count(db, strand.id, reader_id) if reader_id is not None else 0
        ),
        next_session_at=strand.next_session_at,
        ended_at=strand.ended_at,
    )


def to_strand(db: Session, strand: Strand) -> StrandOut:
    return StrandOut(
        id=strand.id,
        program_id=strand.program_id,
        state=strand.state,
        origin_mode=strand.origin_mode,
        members=[to_member(p, a) for p, a in member_rows(db, strand)],
        match_rationale=strand.match_rationale,
        created_at=strand.created_at,
        ended_at=strand.ended_at,
    )


def to_message(
    db: Session, message: Message, names: dict[uuid.UUID, Account]
) -> MessageOut:
    account = names.get(message.author_participation_id)
    return MessageOut(
        id=message.id,
        strand_id=message.strand_id,
        author=MessageAuthorOut(
            participation_id=message.author_participation_id,
            name=account.name if account else "Someone",
            photo_url=account.photo_url if account else None,
        ),
        body=message.body,
        sent_at=message.sent_at,
        delivery_state=message.delivery_state,
        client_token=message.client_token,
    )


def author_accounts(db: Session, strand: Strand) -> dict[uuid.UUID, Account]:
    """Participation id -> account, for naming message authors in one query
    rather than one per message."""
    return {
        participation.id: account for participation, account in member_rows(db, strand)
    }
