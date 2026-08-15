"""Give every roster member an application to be matched on.

The MSW fixtures carry applications for only five of the twenty-four people,
because the mock's run had its scores written by hand — it never derived them
from answers, so nobody noticed the rest had none. With a real engine that gap
is the difference between a cohort that scores and one that does not.

These are synthesised, not invented at random: each person's answers are
derived deterministically from what the fixtures already say about them — their
skills, timezone, and priority band — so the same person always produces the
same application and the matching outcome is reproducible.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import Role
from app.models import Account, Application, FormVersion, Participation
from app.services.profiles import all_fields, published_version

#: Their own words, mapped onto the fixed list the form actually offers. This
#: is the taxonomy step in miniature: "Django" and "Flask" are both backend
#: fundamentals, and without a mapping like this the two vocabularies never meet.
SKILL_TO_FOCUS: dict[str, str] = {
    "Python": "Backend fundamentals",
    "Django": "Backend fundamentals",
    "Flask": "Backend fundamentals",
    "Node.js": "Backend fundamentals",
    "Express": "Backend fundamentals",
    "Java": "Backend fundamentals",
    "Spring": "Backend fundamentals",
    "Go": "Backend fundamentals",
    "SQL": "Backend fundamentals",
    "PostgreSQL": "Backend fundamentals",
    "Pandas": "Backend fundamentals",
    "API design": "System design",
    "System design": "System design",
    "Kubernetes": "System design",
    "Docker": "System design",
    "AWS": "System design",
    "Terraform": "System design",
    "Airflow": "System design",
    "Data engineering": "System design",
    "Observability": "Testing",
    "Reliability": "Testing",
    "Security": "Testing",
    "Threat modelling": "Testing",
    "TypeScript": "Open source",
    "JavaScript": "Open source",
    "React": "Open source",
    "GraphQL": "Open source",
    "HTML": "Career direction",
    "CSS": "Career direction",
}


def _stable_index(seed: str, size: int) -> int:
    """Deterministic, so re-seeding produces the same cohort and a matching run
    can be compared with the last one."""
    return sum(ord(c) for c in seed) % max(size, 1)


def _focus_options(
    field: dict[str, Any], skills: list[str], name: str
) -> list[str]:
    options = field.get("options") or []
    by_label = {o["label"]: o["id"] for o in options}

    wanted = [
        by_label[SKILL_TO_FOCUS[skill]]
        for skill in skills
        if skill in SKILL_TO_FOCUS and SKILL_TO_FOCUS[skill] in by_label
    ]
    if not wanted and options:
        wanted = [options[_stable_index(name, len(options))]["id"]]

    # Deduplicate, keep order, cap at what the question allows.
    seen: list[str] = []
    for option in wanted:
        if option not in seen:
            seen.append(option)
    limit = (field.get("selection") or {}).get("max") or len(seen)
    return seen[:limit]


def _answer(value: Any, days_ago: int) -> dict[str, Any]:
    return {
        "value": value,
        "provenance": "self",
        "answeredAt": (datetime.now(UTC) - timedelta(days=days_ago)).isoformat(),
    }


def _build(
    version: FormVersion,
    name: str,
    timezone: str | None,
    skills: list[str],
    band: str,
    days_ago: int,
) -> dict[str, Any]:
    answers: dict[str, Any] = {}

    # Priority band drives the equity answers, so the bands the fairness summary
    # reports are the ones the data actually supports.
    years = {"high": 1, "medium": 3, "low": 6}.get(band, 3)
    confidence = {"high": 2, "medium": 3, "low": 4}.get(band, 3)

    for field in all_fields(version):
        kind = field["type"]
        label = field["label"].lower()
        options = field.get("options") or []

        if kind == "short_text":
            answers[field["id"]] = _answer(
                name.split()[0] if "call you" in label else (timezone or "Remote"),
                days_ago,
            )
        elif kind == "multi_select":
            chosen = _focus_options(field, skills, name)
            if chosen:
                answers[field["id"]] = _answer(chosen, days_ago)
        elif kind == "single_select" and options:
            index = (
                0
                if "mentored before" in label and band == "high"
                else _stable_index(name + label, len(options))
            )
            answers[field["id"]] = _answer(options[index]["id"], days_ago)
        elif kind == "number":
            answers[field["id"]] = _answer(years, days_ago)
        elif kind == "scale":
            answers[field["id"]] = _answer(confidence, days_ago)
        elif kind == "long_text":
            answers[field["id"]] = _answer(
                f"{name.split()[0]} works with "
                f"{', '.join(skills) or 'backend systems'} "
                "and wants to get better at the parts nobody explains.",
                days_ago,
            )
        elif kind == "consent":
            # A required consent is a condition of applying, so everybody who
            # got in ticked it. An optional one is a real choice, and roughly a
            # quarter of people say no — which is the whole point of seeding it
            # unevenly: a report where everybody consented never exercises the
            # gate that withholds the ones who did not.
            optional = not field.get("required")
            agreed = not optional or _stable_index(name + label, 4) != 0
            answers[field["id"]] = _answer(agreed, days_ago)

    return answers


def _is_usable(application: Application, version: FormVersion) -> bool:
    """Whether an application's choices can be compared with anybody else's.

    Some of the fixture applications were generated with the literal string
    "Answered" in every field, including the select questions — placeholder text
    where an option id belongs. Those answers look present and compare with
    nothing, which is worse than being absent, so they are replaced rather than
    scored as a genuine zero.
    """
    options_by_field = {
        field["id"]: {o["id"] for o in (field.get("options") or [])}
        for field in all_fields(version)
        if field["type"] in ("single_select", "multi_select")
    }
    if not options_by_field:
        return True

    for field_id, valid in options_by_field.items():
        record = application.answers.get(field_id)
        if not record:
            continue
        value = record.get("value")
        chosen = set(value) if isinstance(value, list) else {value}
        if valid & chosen:
            return True
    return False


def backfill(db: Session, program_id: uuid.UUID, bands: dict[str, str]) -> int:
    """An application for every roster member who lacks a usable one."""
    rows = db.execute(
        select(Participation, Account)
        .join(Account, Participation.account_id == Account.id)
        .where(Participation.program_id == program_id)
    ).all()

    usable: set[str] = set()
    for application in db.scalars(
        select(Application).where(Application.program_id == program_id)
    ).all():
        version = db.get(FormVersion, application.form_version_id)
        if version is not None and _is_usable(application, version):
            usable.add(application.email)
        elif version is not None:
            # Placeholder answers are dropped so a real application can replace
            # them; leaving both would give the person two and score neither.
            db.delete(application)
    db.flush()
    existing = usable

    versions: dict[str, FormVersion | None] = {
        Role.MENTEE: published_version(db, program_id, Role.MENTEE),
        Role.MENTOR: published_version(db, program_id, Role.MENTOR),
    }

    written = 0
    for participation, account in rows:
        if account.email in existing:
            continue
        version = versions.get(participation.role)
        if version is None:
            continue

        db.add(
            Application(
                program_id=program_id,
                form_version_id=version.id,
                role=participation.role,
                name=account.name,
                email=account.email,
                status="approved",
                submitted_at=participation.joined_at or datetime.now(UTC),
                decided_at=participation.joined_at,
                decided_by="Amara Okonkwo",
                answers=_build(
                    version,
                    account.name,
                    participation.timezone,
                    participation.skills or [],
                    bands.get(account.name, "medium"),
                    days_ago=30,
                ),
            )
        )
        written += 1

    db.flush()
    return written
