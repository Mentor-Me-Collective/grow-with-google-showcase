"""Fill in the second programme: Research writing, 2026.

The fixtures created it as a bare membership, existing only to prove that role
lives on the participation — the same person coordinates one programme and is
mentored in another. That was enough for the programme switcher and nothing
else, so every screen inside it was empty.

Seeding it properly does something the first programme cannot: it asks
completely different questions. A different organisation, a different form, and
the same renderer, matching engine and profile screens working against it
without a line of code that knows what "a thesis chapter" is. That is the claim
the dynamic schema makes, demonstrated rather than asserted.
"""

from __future__ import annotations

import uuid as uuidlib
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Account,
    Application,
    FormVersion,
    MatchingRecipe,
    Message,
    Organisation,
    Participation,
    Program,
    ProgramMilestone,
    Resource,
    Strand,
    StrandMember,
)

PROGRAM_ID = uuidlib.UUID("00000002-0000-4000-8000-000000000002")


def _id(kind: int, n: int) -> uuidlib.UUID:
    return uuidlib.UUID(f"{kind:08d}-0000-4000-8000-{n:012d}")


# Shared between both forms, so a mentee's "what are you writing" and a
# mentor's "what do you supervise" compare directly. Option ids are the
# vocabulary the matching engine works in.
WRITING = [
    (_id(30, 1), "A thesis chapter"),
    (_id(30, 2), "A journal article"),
    (_id(30, 3), "A conference paper"),
    (_id(30, 4), "A grant proposal"),
    (_id(30, 5), "A literature review"),
]

MENTEE_FORM = {
    "id": str(_id(31, 1)),
    "sections": [
        {
            "id": str(_id(32, 1)),
            "title": "About you",
            "description": "Nothing here is scored.",
            "fields": [
                {
                    "id": str(_id(33, 1)),
                    "type": "short_text",
                    "label": "What should we call you?",
                    "required": True,
                    "matching": False,
                    "equity": False,
                    "admin": True,
                    "visibleWhen": None,
                    "options": None,
                },
                {
                    "id": str(_id(33, 2)),
                    "type": "short_text",
                    "label": "Which department are you in?",
                    "required": True,
                    "matching": False,
                    "equity": False,
                    "admin": True,
                    "visibleWhen": None,
                    "options": None,
                },
            ],
        },
        {
            "id": str(_id(32, 2)),
            "title": "Your writing",
            "description": None,
            "fields": [
                {
                    "id": str(_id(33, 3)),
                    "type": "multi_select",
                    "label": "What are you working on?",
                    "help": "Pick everything you expect to write this year.",
                    "required": True,
                    "matching": True,
                    "equity": False,
                    "admin": False,
                    "visibleWhen": None,
                    "options": [{"id": str(i), "label": lbl} for i, lbl in WRITING],
                    "selection": {"min": 1, "max": 3},
                },
                {
                    "id": str(_id(33, 4)),
                    "type": "number",
                    "label": "How many pieces have you published?",
                    "help": "Nought is a normal answer and not a disadvantage here.",
                    "required": True,
                    "matching": False,
                    "equity": True,
                    "admin": False,
                    "visibleWhen": None,
                    "options": None,
                    "number": {"min": 0, "max": 50, "step": 1},
                },
                {
                    "id": str(_id(33, 5)),
                    "type": "scale",
                    "label": "How confident do you feel writing for a journal?",
                    "required": True,
                    "matching": False,
                    "equity": True,
                    "admin": False,
                    "visibleWhen": None,
                    "options": None,
                    "scale": {
                        "min": 1,
                        "max": 5,
                        "minLabel": "Not at all",
                        "maxLabel": "Very",
                    },
                },
                {
                    "id": str(_id(33, 6)),
                    "type": "long_text",
                    "label": "What has been hardest about writing so far?",
                    "required": False,
                    "matching": False,
                    "equity": True,
                    "admin": False,
                    "visibleWhen": None,
                    "options": None,
                    "text": {"minLength": 30},
                },
            ],
        },
    ],
}

MENTOR_FORM = {
    "id": str(_id(31, 2)),
    "sections": [
        {
            "id": str(_id(32, 3)),
            "title": "About you",
            "description": None,
            "fields": [
                {
                    "id": str(_id(33, 7)),
                    "type": "short_text",
                    "label": "What should we call you?",
                    "required": True,
                    "matching": False,
                    "equity": False,
                    "admin": True,
                    "visibleWhen": None,
                    "options": None,
                },
                {
                    "id": str(_id(33, 8)),
                    "type": "multi_select",
                    "label": "What can you help someone write?",
                    "required": True,
                    "matching": True,
                    "equity": False,
                    "admin": False,
                    "visibleWhen": None,
                    "options": [{"id": str(i), "label": lbl} for i, lbl in WRITING],
                    "selection": {"min": 1, "max": 5},
                },
            ],
        }
    ],
}

# name, email, role, department, what they write (indices into WRITING),
# published count, confidence
PEOPLE = [
    ("Dr Kemi Balogun", "kemi.balogun@unilag.example.org", "mentor",
     "Sociology", [0, 1, 4], 0, 0),
    ("Prof Ada Nwankwo", "ada.nwankwo@unilag.example.org", "mentor",
     "Public Health", [1, 3], 0, 0),
    ("Ifeanyi Obiora", "ifeanyi.obiora@unilag.example.org", "mentee",
     "Sociology", [0, 4], 0, 2),
    ("Sade Adeyinka", "sade.adeyinka@unilag.example.org", "mentee",
     "Public Health", [1, 3], 2, 3),
]


def _answer(value, days_ago: int = 40):
    return {
        "value": value,
        "provenance": "self",
        "answeredAt": (datetime.now(UTC) - timedelta(days=days_ago)).isoformat(),
    }


def _mentee_answers(name: str, dept: str, writes: list[int], published: int, conf: int):
    return {
        str(_id(33, 1)): _answer(name.split()[0]),
        str(_id(33, 2)): _answer(dept),
        str(_id(33, 3)): _answer([str(WRITING[i][0]) for i in writes]),
        str(_id(33, 4)): _answer(published),
        str(_id(33, 5)): _answer(conf),
        str(_id(33, 6)): _answer(
            "Getting from a pile of notes to a first paragraph. I can read the "
            "literature but I freeze at the blank page."
        ),
    }


def _mentor_answers(name: str, writes: list[int]):
    return {
        str(_id(33, 7)): _answer(name.split()[0]),
        str(_id(33, 8)): _answer([str(WRITING[i][0]) for i in writes]),
    }


def seed(db: Session, coordinator_account_id: uuidlib.UUID) -> dict[str, int]:
    program = db.get(Program, PROGRAM_ID)
    if program is None:
        return {}

    org = db.get(Organisation, program.organisation_id)
    if org is not None:
        org.slug = "unilag"
        org.name = "University of Lagos"

    program.description = (
        "A writing programme for postgraduate researchers. Pairs meet monthly "
        "and work towards one finished piece — a chapter, an article, or a "
        "proposal."
    )
    program.state = "open"
    program.cohort_start = date(2026, 9, 1)
    program.cohort_end = date(2027, 6, 1)
    program.applications_close_at = datetime.now(UTC) + timedelta(days=28)
    program.matching_opens_at = datetime.now(UTC) + timedelta(days=42)
    program.time_commitment = "About ninety minutes a month for nine months."
    program.eligibility = (
        "Open to postgraduate researchers at the University of Lagos who are "
        "writing for publication for the first time."
    )
    program.open_roles = ["mentee", "mentor"]
    program.recruitment_goal = 12
    program.self_matching_enabled = False

    now = datetime.now(UTC)

    for spec, blob in ((("mentee", MENTEE_FORM)), (("mentor", MENTOR_FORM))):
        role, form = spec, blob
        db.add(
            FormVersion(
                id=uuidlib.UUID(form["id"]),
                program_id=program.id,
                role=role,
                version=1,
                published_at=now - timedelta(days=60),
                sections=form["sections"],
            )
        )
    db.flush()

    people: dict[str, Participation] = {}
    for name, email, role, dept, writes, published, conf in PEOPLE:
        account = Account(
            name=name,
            email=email,
            email_verified=True,
        )
        db.add(account)
        db.flush()

        participation = Participation(
            account_id=account.id,
            program_id=program.id,
            role=role,
            status="approved",
            is_coordinator=(name == "Dr Kemi Balogun"),
            capacity=2 if role == "mentor" else None,
            load=0 if role == "mentor" else None,
            profile_completeness=1.0,
            timezone="Africa/Lagos",
            headline=(
                f"Supervises writing in {dept}"
                if role == "mentor"
                else f"Postgraduate researcher, {dept}"
            ),
            skills=[WRITING[i][1] for i in writes],
            matched=False,
            joined_at=now - timedelta(days=45),
        )
        db.add(participation)
        db.flush()
        people[name] = participation

        db.add(
            Application(
                program_id=program.id,
                form_version_id=uuidlib.UUID(
                    MENTOR_FORM["id"] if role == "mentor" else MENTEE_FORM["id"]
                ),
                role=role,
                name=name,
                email=email,
                status="approved",
                submitted_at=now - timedelta(days=45),
                decided_at=now - timedelta(days=40),
                decided_by="Dr Kemi Balogun",
                answers=(
                    _mentor_answers(name, writes)
                    if role == "mentor"
                    else _mentee_answers(name, dept, writes, published, conf)
                ),
            )
        )

    # The coordinator of the other programme, mentored here. Her application is
    # what makes her profile and home screen real rather than empty.
    amara = db.scalar(
        select(Participation).where(
            Participation.program_id == program.id,
            Participation.account_id == coordinator_account_id,
        )
    )
    amara_account = db.get(Account, coordinator_account_id)
    if amara is not None and amara_account is not None:
        amara.status = "approved"
        amara.profile_completeness = 1.0
        amara.timezone = "Africa/Lagos"
        amara.headline = "Writing up a decade of platform engineering"
        amara.skills = [WRITING[1][1], WRITING[2][1]]
        amara.joined_at = now - timedelta(days=44)
        amara.matched = True

        db.add(
            Application(
                program_id=program.id,
                form_version_id=uuidlib.UUID(MENTEE_FORM["id"]),
                role="mentee",
                name=amara_account.name,
                email=amara_account.email,
                status="approved",
                submitted_at=now - timedelta(days=44),
                decided_at=now - timedelta(days=40),
                decided_by="Dr Kemi Balogun",
                answers=_mentee_answers(
                    amara_account.name, "Computer Science", [1, 2], 1, 2
                ),
            )
        )

        # One live strand, so the strand screens have something in them.
        kemi = people["Dr Kemi Balogun"]
        strand = Strand(
            program_id=program.id,
            state="active",
            origin_mode="manual",
            match_rationale=(
                "Paired on journal articles and conference papers, which is what "
                "you both named. This names the strongest signal; the outcome "
                "also depended on who else was available."
            ),
            last_activity_at=now - timedelta(days=3),
            sessions_logged=2,
            milestones_completed=1,
        )
        db.add(strand)
        db.flush()
        db.add(
            StrandMember(
                strand_id=strand.id, participation_id=amara.id, role="mentee"
            )
        )
        db.add(
            StrandMember(strand_id=strand.id, participation_id=kemi.id, role="mentor")
        )
        kemi.load = 1
        kemi.matched = True

        for days, author, body in (
            (
                12,
                kemi,
                "Welcome Amara. Send me the abstract when you have one — even "
                "three sentences is enough to work from.",
            ),
            (
                9,
                amara,
                "Thank you. I have a draft abstract but it reads like a release "
                "note rather than a paper.",
            ),
            (
                3,
                kemi,
                "That is a good problem to have. Engineers write to inform; "
                "papers argue. Bring it next month and we will turn the "
                "statements into a claim.",
            ),
        ):
            db.add(
                Message(
                    strand_id=strand.id,
                    author_participation_id=author.id,
                    body=body,
                    sent_at=now - timedelta(days=days),
                    delivery_state="sent",
                )
            )

    for offset, title, prompt in (
        (2, "First conversation", "Have you agreed what you are writing and by when?"),
        (
            16,
            "A full draft exists",
            "A bad complete draft beats a perfect half. Is there one yet?",
        ),
        (32, "Submitted somewhere", "Where has it gone, and what did they say?"),
    ):
        db.add(
            ProgramMilestone(
                program_id=program.id,
                title=title,
                week_offset=offset,
                strand_prompt=prompt,
                reminder_days_before=7,
                position=offset,
            )
        )

    for title, description, kind in (
        (
            "Writing programme handbook",
            "How the nine months are structured and what a monthly session "
            "should contain.",
            "handbook",
        ),
        (
            "Turning a chapter into an article",
            "The guide most people say they wish they had read first.",
            "other",
        ),
    ):
        db.add(
            Resource(
                program_id=program.id,
                title=title,
                description=description,
                kind=kind,
                url=f"/resources/{title.lower().replace(' ', '-')}.pdf",
                size_bytes=420_000,
            )
        )

    db.add(
        MatchingRecipe(
            program_id=program.id,
            name="Writing cohort recipe",
            version=1,
            hard_constraints=[
                {"kind": "role_compatible", "enabled": True},
                {"kind": "shared_skill", "enabled": True},
                {"kind": "same_timezone_band", "enabled": False},
                {"kind": "different_team", "enabled": False},
            ],
            weights=[
                {
                    "fieldId": str(_id(33, 3)),
                    "weight": 95,
                    "direction": "complementary",
                },
                {
                    "fieldId": str(_id(33, 8)),
                    "weight": 60,
                    "direction": "complementary",
                },
            ],
            fairness={
                "mentorCapacityCap": None,
                "coverageFloor": 0.9,
                "priorityWeights": [
                    {"fieldId": str(_id(33, 4)), "weight": 70},
                    {"fieldId": str(_id(33, 5)), "weight": 50},
                ],
            },
            updated_by="Dr Kemi Balogun",
        )
    )

    db.flush()
    return {"research_people": len(PEOPLE) + 1, "research_forms": 2}
