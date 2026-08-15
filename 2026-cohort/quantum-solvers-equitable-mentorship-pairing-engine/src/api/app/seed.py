"""Load seed_data.json into Postgres.

seed_data.json is the MSW fixture database, exported verbatim from the frontend
(`GET /api/seeddump` in development). Using the same rows the frontend was built
against is what makes verification possible: a screen served by this API can be
put beside the same screen served by the mock, and any difference is a bug
rather than a question about whether the data was ported faithfully.

Idempotent. Running it twice leaves the same database, so it is safe to call on
a fresh deploy without guarding it.

    uv run python -m app.seed
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import seed_applications, seed_research
from app.db import SessionLocal
from app.matching import normalise
from app.models import (
    Account,
    Application,
    ApplicationDraft,
    ApplicationResumeToken,
    AuditEvent,
    Broadcast,
    DraftPair,
    FormVersion,
    Invite,
    MagicLinkToken,
    MatchingRecipe,
    Message,
    MessageRead,
    MessageTemplate,
    NotificationPreference,
    Organisation,
    ParticipantAttribute,
    Participation,
    Program,
    ProgramMilestone,
    Resource,
    Run,
    RunUnmatched,
    SessionToken,
    Strand,
    StrandMember,
    WaitlistEntry,
)

DATA = Path(__file__).resolve().parent.parent / "seed_data.json"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    # The fixtures emit ISO strings ending in Z, which fromisoformat rejects
    # before 3.11 and accepts after; normalising keeps it explicit either way.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_date(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def uid(value: str) -> uuid.UUID:
    """Fixture ids are already valid UUIDs, so they are kept.

    Keeping them means a URL that worked against the mock — including the run id
    in the README — still works against the real API.
    """
    return uuid.UUID(value)


def wipe(db: Session) -> None:
    """Clear in dependency order. Seeding is a reset, not an append.

    Sessions and tokens go too. They reference accounts, so leaving them behind
    breaks the wipe with a foreign-key violation the moment anybody has signed
    in — and a session pointing at an account that no longer exists would be
    worse than being signed out.
    """
    for model in (
        ApplicationResumeToken,
        # Drafts hold a form_version_id, so they have to go before the versions
        # they point at — and before the resume tokens that point at them.
        ApplicationDraft,
        WaitlistEntry,
        SessionToken,
        MagicLinkToken,
        RunUnmatched,
        DraftPair,
        ParticipantAttribute,
        Run,
        MessageRead,
        Message,
        StrandMember,
        Strand,
        Application,
        FormVersion,
        MatchingRecipe,
        ProgramMilestone,
        MessageTemplate,
        Broadcast,
        Resource,
        AuditEvent,
        Invite,
        NotificationPreference,
        Participation,
        Account,
        Program,
        Organisation,
    ):
        db.execute(delete(model))
    db.flush()


def seed(db: Session, data: dict[str, Any]) -> dict[str, int]:
    wipe(db)

    program_data = data["program"]
    org_data = program_data["organisation"]

    org = Organisation(
        id=uid(org_data["id"]),
        slug=org_data["slug"],
        name=org_data["name"],
        logo_url=org_data.get("logoUrl"),
    )
    db.add(org)

    program = Program(
        id=uid(program_data["id"]),
        organisation_id=org.id,
        slug=program_data["slug"],
        name=program_data["name"],
        description=program_data.get("description"),
        state=program_data.get("state", "open"),
        cohort_start=parse_date(program_data.get("cohortStart")),
        cohort_end=parse_date(program_data.get("cohortEnd")),
        applications_close_at=parse_dt(program_data.get("applicationsCloseAt")),
        matching_opens_at=parse_dt(program_data.get("matchingOpensAt")),
        time_commitment=program_data.get("timeCommitment"),
        eligibility=program_data.get("eligibility"),
        open_roles=program_data.get("openRoles", []),
        recruitment_goal=20,
        self_matching_enabled=bool(data.get("selfMatchingEnabled", True)),
    )
    db.add(program)
    db.flush()

    # --- accounts and participations -------------------------------------
    # The fixture roster carries the account inline, because on the wire a
    # roster entry is a participation with its person attached.
    coordinator_ids = {p["id"] for p in data["session"]["participations"]}
    me_id = data["session"]["account"]["id"]
    headlines, skills = _member_details(data)

    for entry in data["roster"]:
        account_data = entry["account"]
        account = Account(
            id=uid(account_data["id"]),
            name=account_data["name"],
            email=account_data["email"],
            email_verified=bool(account_data.get("emailVerified")),
            photo_url=account_data.get("photoUrl"),
        )
        db.add(account)

        db.add(
            Participation(
                id=uid(entry["id"]),
                account_id=account.id,
                program_id=program.id,
                role=entry["role"],
                status=entry["status"],
                is_coordinator=entry["id"] in coordinator_ids,
                capacity=entry.get("capacity"),
                load=entry.get("load"),
                profile_completeness=entry.get("profileCompleteness", 0.0),
                timezone=entry.get("timezone"),
                headline=headlines.get(entry["id"]),
                skills=skills.get(entry["id"], []),
                matched=bool(entry.get("matched")),
                joined_at=parse_dt(entry.get("joinedAt")),
            )
        )
    db.flush()

    # A membership in another organisation, with no roster, strands or runs
    # behind it. The fixtures carry one deliberately: it is what proves role
    # lives on the participation — the same person is a coordinator and mentor
    # here and a mentee there — and it is the only thing that exercises the
    # programme switcher and the "my programmes" screen.
    for other in data["session"]["participations"]:
        if uid(other["id"]) in {uid(e["id"]) for e in data["roster"]}:
            continue
        other_org = Organisation(
            slug=other["orgSlug"],
            name=other.get("organisationName") or other["orgSlug"],
        )
        db.add(other_org)
        db.flush()
        other_program = Program(
            id=uid(other["programId"]),
            organisation_id=other_org.id,
            slug=other["programSlug"],
            name=other["programName"],
            state="open",
            open_roles=[],
        )
        db.add(other_program)
        db.flush()
        db.add(
            Participation(
                id=uid(other["id"]),
                account_id=uid(me_id),
                program_id=other_program.id,
                role=other["role"],
                status=other["status"],
                is_coordinator=other.get("isCoordinator", False),
            )
        )
    db.flush()

    known = {p.id for p in db.scalars(select(Participation)).all()}

    # The seeded coordinator's own notification preferences.
    me = data["session"]["account"]
    db.add(
        NotificationPreference(
            account_id=uid(me["id"]),
            new_message=data["notifications"]["newMessage"],
            match_published=data["notifications"]["matchPublished"],
            milestone_reminders=data["notifications"]["milestoneReminders"],
            broadcasts=data["notifications"]["broadcasts"],
            digest=data["notifications"]["digest"],
        )
    )

    # --- forms ------------------------------------------------------------
    for version in data["formVersions"]:
        db.add(
            FormVersion(
                id=uid(version["id"]),
                program_id=program.id,
                role=version["role"],
                version=version["version"],
                published_at=parse_dt(version.get("publishedAt")),
                sections=version["sections"],
            )
        )
    db.flush()

    for application in data["applications"]:
        db.add(
            Application(
                id=uid(application["id"]),
                program_id=program.id,
                form_version_id=uid(application["formVersionId"]),
                role=application["role"],
                name=application["name"],
                email=application["email"],
                status=application["status"],
                submitted_at=parse_dt(application["submittedAt"]),
                decided_at=parse_dt(application.get("decidedAt")),
                decided_by=application.get("decidedBy"),
                editable_until=parse_dt(application.get("editableUntil")),
                matching_opens_at=parse_dt(application.get("matchingOpensAt")),
                answers=application.get("answers", {}),
            )
        )

    # --- strands ----------------------------------------------------------
    summaries = {s["id"]: s for s in data["strandSummaries"]}
    metrics = data.get("strandMetrics", {})

    for strand_data in data["strands"]:
        summary = summaries.get(strand_data["id"], {})
        metric = metrics.get(strand_data["id"], {})

        strand = Strand(
            id=uid(strand_data["id"]),
            program_id=program.id,
            state=strand_data["state"],
            origin_mode=strand_data["originMode"],
            match_rationale=strand_data.get("matchRationale"),
            last_activity_at=parse_dt(summary.get("lastActivityAt")),
            next_session_at=parse_dt(summary.get("nextSessionAt")),
            ended_at=parse_dt(strand_data.get("endedAt")),
            sessions_logged=metric.get("sessionsLogged", 0),
            milestones_completed=metric.get("milestonesCompleted", 0),
            # The fixture's own date, not the moment of seeding. Without it
            # every strand in a two-month cohort is created today, and anything
            # that reads a strand against a calendar — coverage over time, the
            # drop-off funnel — sees a programme where nothing happened until
            # this morning.
            created_at=parse_dt(strand_data.get("createdAt")),
        )
        db.add(strand)

        for member in strand_data["members"]:
            participation_id = uid(member["participationId"])
            if participation_id not in known:
                continue
            db.add(
                StrandMember(
                    strand_id=strand.id,
                    participation_id=participation_id,
                    role=member["role"],
                )
            )
    db.flush()

    for strand_id, thread in data["messages"].items():
        for message in thread:
            author = uid(message["author"]["participationId"])
            if author not in known:
                continue
            db.add(
                Message(
                    id=uid(message["id"]),
                    strand_id=uid(strand_id),
                    author_participation_id=author,
                    body=message["body"],
                    sent_at=parse_dt(message["sentAt"]),
                    delivery_state=message.get("deliveryState", "sent"),
                )
            )

    # --- matching ---------------------------------------------------------
    recipe = data["recipe"]
    db.add(
        MatchingRecipe(
            program_id=program.id,
            name=recipe["name"],
            version=recipe["version"],
            hard_constraints=recipe["hardConstraints"],
            weights=recipe["weights"],
            fairness=recipe["fairness"],
            updated_by=recipe.get("updatedBy"),
        )
    )

    for run_data in data["runs"]:
        run = Run(
            id=uid(run_data["id"]),
            program_id=program.id,
            state=run_data["state"],
            progress=run_data["progress"],
            recipe_version=run_data.get("recipeVersion"),
            created_at=parse_dt(run_data["createdAt"]),
            created_by=run_data["createdBy"],
            published_at=parse_dt(run_data.get("publishedAt")),
            published_by=run_data.get("publishedBy"),
            drafted_count=run_data.get("draftedCount", 0),
            published_count=run_data.get("publishedCount", 0),
            coverage_rate=run_data.get("coverageRate"),
            fairness_summary=run_data.get("fairnessSummary"),
        )
        db.add(run)

        for pair in run_data.get("pairs", []):
            mentee = uid(pair["mentee"]["participationId"])
            mentor = uid(pair["mentor"]["participationId"])
            if mentee not in known or mentor not in known:
                continue
            db.add(
                DraftPair(
                    id=uid(pair["id"]),
                    run_id=run.id,
                    mentee_participation_id=mentee,
                    mentor_participation_id=mentor,
                    score=pair["score"],
                    priority_band=pair["priorityBand"],
                )
            )
    db.flush()

    # The unmatched queue belongs to the run that produced it.
    latest_run = max(
        (r for r in data["runs"] if r.get("publishedAt")),
        key=lambda r: r["createdAt"],
        default=None,
    )
    if latest_run:
        for entry in data["unmatched"]:
            participation_id = uid(entry["participationId"])
            if participation_id not in known:
                continue
            db.add(
                RunUnmatched(
                    run_id=uid(latest_run["id"]),
                    participation_id=participation_id,
                    reason=entry["reason"],
                )
            )

    # --- programme setup --------------------------------------------------
    for milestone in data["milestones"]:
        db.add(
            ProgramMilestone(
                id=uid(milestone["id"]),
                program_id=program.id,
                title=milestone["title"],
                description=milestone.get("description"),
                week_offset=milestone["weekOffset"],
                strand_prompt=milestone.get("strandPrompt"),
                reminder_days_before=milestone.get("reminderDaysBefore"),
                position=milestone["position"],
            )
        )

    for template in data["templates"]:
        db.add(
            MessageTemplate(
                program_id=program.id,
                kind=template["kind"],
                subject=template["subject"],
                body=template["body"],
                is_default=template.get("isDefault", True),
                updated_by=template.get("updatedBy"),
            )
        )

    for broadcast in data["broadcasts"]:
        db.add(
            Broadcast(
                id=uid(broadcast["id"]),
                program_id=program.id,
                segment=broadcast["segment"],
                subject=broadcast["subject"],
                body=broadcast["body"],
                recipient_count=broadcast["recipientCount"],
                delivered_count=broadcast.get("deliveredCount", 0),
                failed_count=broadcast.get("failedCount", 0),
                state=broadcast["state"],
                created_at=parse_dt(broadcast["createdAt"]),
                created_by=broadcast["createdBy"],
                scheduled_for=parse_dt(broadcast.get("scheduledFor")),
            )
        )

    for resource in data["resources"]:
        db.add(
            Resource(
                id=uid(resource["id"]),
                program_id=program.id,
                title=resource["title"],
                description=resource.get("description"),
                kind=resource["kind"],
                url=resource["url"],
                size_bytes=resource.get("sizeBytes"),
            )
        )

    for event in data["auditEvents"]:
        db.add(
            AuditEvent(
                id=uid(event["id"]),
                organisation_id=org.id,
                at=parse_dt(event["at"]),
                actor_name=event["actorName"],
                action=event["action"],
                summary=event["summary"],
                subject_label=event.get("subjectLabel"),
            )
        )

    for invite in data["invites"]:
        db.add(
            Invite(
                token=invite["token"],
                program_id=program.id,
                email=invite["email"],
                role=invite["role"],
                invited_by_name=invite["invitedByName"],
                message=invite.get("message"),
                state=invite["state"],
                expires_at=parse_dt(invite.get("expiresAt")),
            )
        )

    # Derive load and matched from the strands actually seeded rather than
    # trusting the figures in the fixtures. Those were display data — they add
    # up to fourteen against five strands — and a mentor recorded as full while
    # holding nothing would make every later run look broken while behaving
    # correctly.
    db.flush()
    for participation in db.scalars(
        select(Participation).where(Participation.program_id == program.id)
    ).all():
        held = db.scalar(
            select(func.count())
            .select_from(StrandMember)
            .join(Strand, Strand.id == StrandMember.strand_id)
            .where(
                StrandMember.participation_id == participation.id,
                Strand.state == "active",
            )
        ) or 0
        participation.matched = held > 0
        if participation.role == "mentor":
            participation.load = held

    # Priority bands come from the run's draft pairs, which is where the
    # fixtures record them.
    bands = {}
    for run in data["runs"]:
        for pair in run.get("pairs", []):
            bands[pair["mentee"]["name"]] = pair["priorityBand"]

    backfilled = seed_applications.backfill(db, program.id, bands)

    # The second programme, filled in so every screen inside it is real. It asks
    # entirely different questions, which is the dynamic form schema working
    # rather than being claimed.
    research = seed_research.seed(db, uid(me_id))

    # The projection is derived data, so a fresh database has none until
    # something rebuilds it — and until then the report has no equity answers to
    # break down. Building it here means a seeded database is a *complete* one
    # rather than one that only completes itself after somebody starts a run.
    projected = normalise.rebuild(db, program.id)
    if research:
        projected += normalise.rebuild(db, seed_research.PROGRAM_ID)

    db.commit()

    return {
        "organisations": 1,
        "applications_backfilled": backfilled,
        "attributes_projected": projected,
        **research,
        "programs": 1,
        "accounts": len(data["roster"]),
        "participations": len(data["roster"]),
        "form_versions": len(data["formVersions"]),
        "applications": len(data["applications"]),
        "strands": len(data["strands"]),
        "messages": sum(len(t) for t in data["messages"].values()),
        "runs": len(data["runs"]),
        "milestones": len(data["milestones"]),
        "templates": len(data["templates"]),
        "broadcasts": len(data["broadcasts"]),
        "resources": len(data["resources"]),
        "audit_events": len(data["auditEvents"]),
        "invites": len(data["invites"]),
    }


def _member_details(
    data: dict[str, Any],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Headline and skills live on strand members in the fixtures, because that
    is where the wire shape needs them. On a participation they are columns, so
    they are lifted out here."""
    headlines: dict[str, str] = {}
    skills: dict[str, list[str]] = {}
    for strand in data["strands"]:
        for member in strand["members"]:
            pid = member["participationId"]
            if member.get("headline"):
                headlines[pid] = member["headline"]
            if member.get("skills"):
                skills[pid] = member["skills"]
    return headlines, skills


def main() -> None:
    data = json.loads(DATA.read_text())
    with SessionLocal() as db:
        counts = seed(db, data)
    width = max(len(k) for k in counts)
    for key, value in counts.items():
        print(f"{key:<{width}}  {value}")


if __name__ == "__main__":
    main()
