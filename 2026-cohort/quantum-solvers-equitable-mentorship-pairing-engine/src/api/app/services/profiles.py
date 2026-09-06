"""Turning stored answers into the shapes the screens read.

Kept out of the routers because three of them need the same rules — the
participant's own profile, a public profile, and the coordinator's view of an
application — and the rule that matters most is the one about `admin` fields.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FormVersion, Participation
from app.schemas.reads import (
    PublicProfileEntryOut,
    PublicProfileSectionOut,
)

#: Below this, a long answer has nothing in it to match on. Guided completion
#: exists for exactly these, so the profile screen names them rather than
#: showing a bare percentage.
THIN_TEXT_LENGTH = 40


def all_fields(version: FormVersion) -> list[dict[str, Any]]:
    return [field for section in version.sections for field in section["fields"]]


def published_version(
    db: Session, program_id, role: str
) -> FormVersion | None:
    """The live form for a role: the newest published version.

    Newest, not merely published — taking the first would leave applicants on
    the old questions forever after a second version went out.
    """
    return db.scalar(
        select(FormVersion)
        .where(
            FormVersion.program_id == program_id,
            FormVersion.role == role,
            FormVersion.published_at.is_not(None),
        )
        .order_by(FormVersion.version.desc())
        .limit(1)
    )


def is_thin(field: dict[str, Any], record: dict[str, Any] | None) -> bool:
    if not record:
        return True
    value = record.get("value")
    if isinstance(value, str):
        if field.get("type") == "long_text":
            return len(value.strip()) < THIN_TEXT_LENGTH
        return not value.strip()
    if isinstance(value, list):
        return not value
    return value is None


def completeness(version: FormVersion, answers: dict[str, Any]) -> float:
    fields = all_fields(version)
    if not fields:
        return 1.0
    answered = sum(1 for f in fields if not is_thin(f, answers.get(f["id"])))
    return round(answered / len(fields), 3)


def thin_field_ids(version: FormVersion, answers: dict[str, Any]) -> list[str]:
    return [f["id"] for f in all_fields(version) if is_thin(f, answers.get(f["id"]))]


def readable(field: dict[str, Any], record: dict[str, Any]) -> str:
    """One answer as a person would read it.

    Options are stored by id, so they are resolved back to labels here — the
    label is editable copy and was never the key.
    """
    options = {o["id"]: o["label"] for o in (field.get("options") or [])}
    value = record.get("value")

    if isinstance(value, list):
        return ", ".join(options.get(v, str(v)) for v in value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str) and options:
        return options.get(value, value)
    return str(value)


def shareable_sections(
    version: FormVersion, answers: dict[str, Any]
) -> list[PublicProfileSectionOut]:
    """Answers grouped and labelled, with every `admin` question dropped.

    Those are collected for the coordinator, and a profile screen is the easiest
    place to leak them by accident — so the filter lives here rather than in
    each caller.
    """
    sections: list[PublicProfileSectionOut] = []
    for section in version.sections:
        entries = [
            PublicProfileEntryOut(
                label=field["label"], value=readable(field, answers[field["id"]])
            )
            for field in section["fields"]
            if not field.get("admin") and answers.get(field["id"])
        ]
        if entries:
            sections.append(
                PublicProfileSectionOut(title=section["title"], entries=entries)
            )
    return sections


def is_available(participation: Participation) -> bool:
    """A mentor at the capacity they set is not taking anybody new."""
    if participation.capacity is None:
        return True
    return (participation.load or 0) < participation.capacity
