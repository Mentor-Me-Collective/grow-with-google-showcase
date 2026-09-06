"""Project flagged answers into a fixed typed shape.

Architecture 3.1 and 3.2. The application form is unknown at compile time, so
without this step the unknown shape would leak into matching, reporting and
export. Everything downstream reads `participant_attribute`, which always has
the same columns, and the form stops here.

What is deliberately *not* here yet: a taxonomy. "Backend engineering",
"back-end dev" and "server-side" should collapse to one canonical skill, and
free text that does not map cleanly should go to a coordinator's review queue
rather than being silently discarded or silently guessed. Option-based answers
already compare exactly because they are stored by id; free text does not, and
that gap is the difference between matches that are good and matches that are
merely plausible.
"""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.enums import ParticipationStatus
from app.models import Account, Application, FormVersion, Participation
from app.models.matching import ParticipantAttribute
from app.services.profiles import all_fields, published_version


def _value_columns(field: dict[str, Any], value: Any) -> dict[str, Any]:
    """Put the answer in whichever column its type calls for.

    Options are kept as ids, never labels: an id is stable for the life of the
    question, and a label is editable copy that would silently break every
    comparison the moment somebody fixed a typo in it.
    """
    kind = field.get("type")

    if kind in ("single_select", "multi_select"):
        options = value if isinstance(value, list) else [value]
        return {"option_values": [str(v) for v in options if v is not None]}

    if kind in ("number", "scale"):
        try:
            return {"number_value": float(value)}
        except (TypeError, ValueError):
            return {}

    if kind == "consent":
        return {"number_value": 1.0 if value else 0.0}

    if isinstance(value, str):
        return {"text_value": value}
    return {}


def rebuild(db: Session, program_id: uuid.UUID) -> int:
    """Recompute the whole projection for a programme.

    A full rebuild rather than an incremental update. The projection is derived
    data, so throwing it away and recomputing is always correct — and it is what
    makes changing a question's flags safe, since the answer to "which fields
    feed matching" changes for everybody at once.
    """
    db.execute(
        delete(ParticipantAttribute).where(
            ParticipantAttribute.program_id == program_id
        )
    )

    versions: dict[uuid.UUID, FormVersion] = {}
    written = 0

    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(
            Participation.program_id == program_id,
            Participation.status == ParticipationStatus.APPROVED,
        )
    ).all()

    for participation, account in rows:
        application = db.scalar(
            select(Application)
            .where(
                Application.program_id == program_id,
                Application.email == account.email,
            )
            .order_by(Application.submitted_at.desc())
            .limit(1)
        )

        # Answers are read against the version they were given on, not the
        # current one: a question added since is a question this person was
        # never asked.
        if application is not None:
            version = versions.get(application.form_version_id)
            if version is None:
                version = db.get(FormVersion, application.form_version_id)
                if version is not None:
                    versions[version.id] = version
            answers = application.answers or {}
        else:
            version = published_version(db, program_id, participation.role)
            answers = {}

        if version is None:
            continue

        for field in all_fields(version):
            if not (field.get("matching") or field.get("equity")):
                continue
            record = answers.get(field["id"])
            if not record:
                continue

            columns = _value_columns(field, record.get("value"))
            if not columns:
                continue

            db.add(
                ParticipantAttribute(
                    participation_id=participation.id,
                    program_id=program_id,
                    field_id=uuid.UUID(field["id"]),
                    matching=bool(field.get("matching")),
                    equity=bool(field.get("equity")),
                    field_type=field["type"],
                    **columns,
                )
            )
            written += 1

    db.flush()
    return written


def load(
    db: Session, program_id: uuid.UUID
) -> dict[uuid.UUID, dict[str, ParticipantAttribute]]:
    """The projection as {participation_id: {field_id: attribute}}.

    Read once per run rather than per pair: a cohort is a few hundred rows and
    the alternative is a query inside the scoring loop.
    """
    out: dict[uuid.UUID, dict[str, ParticipantAttribute]] = {}
    for attribute in db.scalars(
        select(ParticipantAttribute).where(
            ParticipantAttribute.program_id == program_id
        )
    ).all():
        out.setdefault(attribute.participation_id, {})[str(attribute.field_id)] = (
            attribute
        )
    return out
