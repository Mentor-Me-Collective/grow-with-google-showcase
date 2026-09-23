"""Scoring and report generation for the Business Readiness Check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


YES = "Yes"
NO = "No"
NOT_APPLICABLE = "Not applicable"
VALID_ANSWERS = {YES, NO, NOT_APPLICABLE}

MANAGEMENT_METHODS = (
    "One connected system",
    "Several separate applications",
    "Spreadsheets",
    "Paper or mostly manual processes",
    "I am not sure",
)

MANUAL_COPY_FREQUENCIES = (
    "Never",
    "Less than once a month",
    "Several times a month",
    "Several times a week",
    "Every day",
)


@dataclass(frozen=True)
class Question:
    """One diagnostic question and its project-defined risk weight."""

    label: str
    prompt: str
    weight: int
    recommendation: str
    next_step_note: str
    explanation: str
    immediate_action: str
    thirty_day_action: str
    success_measure: str
    provider_questions: tuple[str, ...]


@dataclass(frozen=True)
class AssessmentResult:
    """Calculated assessment values used by both the UI and report."""

    risk_points: int
    applicable_points: int
    risk_percentage: float | None
    risk_level: str


@dataclass(frozen=True)
class AreaReadiness:
    """One area's answer translated into a plain-language readiness status."""

    key: str
    question: Question
    answer: str
    status: str
    summary: str


@dataclass(frozen=True)
class ModernizationStep:
    """Action-plan content for one failed diagnostic area."""

    key: str
    label: str
    immediate_action: str
    thirty_day_action: str
    success_measure: str
    provider_questions: tuple[str, ...]


SECURITY_CHECKPOINTS = (
    "Require multifactor authentication for administrator accounts.",
    "Give each employee only the access needed for their work and remove stale accounts.",
    "Export or back up important business data before changing systems.",
    "Test changes with sample records or transactions before a full switch.",
    "Confirm how to export or delete data and how the provider handles security incidents.",
)


QUESTIONS: dict[str, Question] = {
    "inventory": Question(
        label="Inventory synchronization",
        prompt=(
            "Does your POS automatically synchronize inventory with your "
            "online store?"
        ),
        weight=5,
        recommendation="Prioritize POS and online inventory synchronization.",
        next_step_note=(
            "Aim for one reliable inventory count that every sales channel uses."
        ),
        explanation=(
            "Disconnected inventory systems can cause incorrect stock counts, "
            "overselling, and manual reconciliation."
        ),
        immediate_action=(
            "List every system that changes stock counts and mark where staff "
            "re-enter quantities by hand."
        ),
        thirty_day_action=(
            "Test one POS-to-store synchronization with a small product set and "
            "define how staff will handle synchronization failures."
        ),
        success_measure=(
            "Fewer stock discrepancies, overselling incidents, and manual "
            "reconciliations."
        ),
        provider_questions=(
            "Does inventory synchronize in both directions, and how often?",
            "What happens when synchronization fails or products do not match?",
            "Can the business export complete inventory and transaction data?",
        ),
    ),
    "payments": Question(
        label="Payments and checkout",
        prompt="Does checkout support digital wallets and guest checkout?",
        weight=4,
        recommendation="Add digital-wallet support and guest checkout.",
        next_step_note=(
            "Aim for a checkout that lets customers pay quickly without creating "
            "an account."
        ),
        explanation=(
            "Limited checkout options can create avoidable friction for customers."
        ),
        immediate_action=(
            "Review checkout on a phone and computer and record which wallet, "
            "guest-checkout, or payment steps are unavailable."
        ),
        thirty_day_action=(
            "Enable and test selected checkout options with test transactions "
            "before making them available to every customer."
        ),
        success_measure=(
            "Fewer checkout steps, payment-related support requests, and abandoned "
            "purchases."
        ),
        provider_questions=(
            "Which transaction, refund, dispute, and wallet fees apply?",
            "How are payment data and checkout responsibilities divided?",
            "Can the business export transaction and refund records?",
        ),
    ),
    "customers": Question(
        label="Customer email capture",
        prompt="Are customer emails captured at the point of sale?",
        weight=3,
        recommendation="Add customer email capture and follow-up automation.",
        next_step_note=(
            "Build a permissioned customer contact list that supports consistent "
            "follow-up."
        ),
        explanation=(
            "Missing contact information limits customer follow-up and retention "
            "workflows."
        ),
        immediate_action=(
            "Map where an email address can be requested with consent and how "
            "duplicate or invalid addresses are handled."
        ),
        thirty_day_action=(
            "Pilot a consent-based capture and follow-up process and assign who "
            "reviews opt-outs and address errors."
        ),
        success_measure=(
            "A higher share of valid, permissioned customer emails and fewer "
            "manual follow-up steps."
        ),
        provider_questions=(
            "How does the tool record consent, opt-outs, and deletion requests?",
            "Which staff roles can view or export customer information?",
            "Can the business export and remove customer data when needed?",
        ),
    ),
    "booking": Question(
        label="Online booking",
        prompt="Can customers book appointments online at any time?",
        weight=2,
        recommendation="Add a secure 24/7 online booking system.",
        next_step_note=(
            "Give customers a reliable self-service way to schedule outside "
            "business hours."
        ),
        explanation=(
            "Manual scheduling can prevent customers from booking outside business "
            "hours."
        ),
        immediate_action=(
            "Document the current scheduling steps, available hours, cancellation "
            "rules, and information staff need for each appointment."
        ),
        thirty_day_action=(
            "Pilot online booking for a limited appointment type and test "
            "confirmations, cancellations, and time-zone handling."
        ),
        success_measure=(
            "Fewer scheduling messages, missed appointments, and duplicate bookings."
        ),
        provider_questions=(
            "How are staff access, calendar connections, and customer details secured?",
            "How does the system handle confirmations, cancellations, and time zones?",
            "Can the business export appointments and customer information?",
        ),
    ),
}


def clean_user_text(value: str, max_length: int) -> str:
    """Normalize optional report text and remove control characters."""

    printable = "".join(
        character if character.isprintable() else " " for character in value
    )
    return " ".join(printable.split())[:max_length]


def _validate_answers(answers: Mapping[str, str]) -> None:
    """Reject missing, unknown, or invalid answers before calculating a score."""

    expected = set(QUESTIONS)
    provided = set(answers)

    missing = expected - provided
    unknown = provided - expected
    if missing:
        raise ValueError(f"Missing answers for: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"Unknown question keys: {', '.join(sorted(unknown))}")

    invalid = {
        key: answer for key, answer in answers.items() if answer not in VALID_ANSWERS
    }
    if invalid:
        details = ", ".join(f"{key}={answer!r}" for key, answer in invalid.items())
        raise ValueError(f"Invalid answers: {details}")


def classify_risk(risk_percentage: float | None) -> str:
    """Return the project-designed risk category for a percentage."""

    if risk_percentage is None:
        return "Not calculated"
    if risk_percentage < 25:
        return "Low"
    if risk_percentage < 50:
        return "Moderate"
    if risk_percentage < 75:
        return "High"
    return "Critical"


def calculate_risk(answers: Mapping[str, str]) -> AssessmentResult:
    """Calculate weighted risk while excluding not-applicable questions."""

    _validate_answers(answers)
    risk_points = 0
    applicable_points = 0

    for key, question in QUESTIONS.items():
        answer = answers[key]
        if answer == NOT_APPLICABLE:
            continue
        applicable_points += question.weight
        if answer == NO:
            risk_points += question.weight

    risk_percentage = (
        round(risk_points / applicable_points * 100, 1)
        if applicable_points
        else None
    )
    return AssessmentResult(
        risk_points=risk_points,
        applicable_points=applicable_points,
        risk_percentage=risk_percentage,
        risk_level=classify_risk(risk_percentage),
    )


def find_priorities(answers: Mapping[str, str]) -> list[tuple[str, Question]]:
    """Return failed areas ordered by highest project-defined weight first."""

    _validate_answers(answers)
    failed = [(key, QUESTIONS[key]) for key, answer in answers.items() if answer == NO]
    return sorted(failed, key=lambda item: item[1].weight, reverse=True)


def build_readiness_breakdown(
    answers: Mapping[str, str],
) -> list[AreaReadiness]:
    """Translate every answer into an ordered status and explanation."""

    _validate_answers(answers)
    statuses = {
        YES: "Ready",
        NO: "Needs attention",
        NOT_APPLICABLE: "Not applicable",
    }
    breakdown = []

    for key, question in QUESTIONS.items():
        answer = answers[key]
        if answer == YES:
            summary = (
                "This capability is reported as available. Continue monitoring it "
                "as the business and its systems change."
            )
        elif answer == NO:
            summary = question.explanation
        else:
            summary = (
                "This area was excluded from the score because it was marked "
                "Not applicable."
            )
        breakdown.append(
            AreaReadiness(
                key=key,
                question=question,
                answer=answer,
                status=statuses[answer],
                summary=summary,
            )
        )

    return breakdown


def build_modernization_plan(
    answers: Mapping[str, str],
) -> list[ModernizationStep]:
    """Create ordered action-plan steps for areas answered No."""

    return [
        ModernizationStep(
            key=key,
            label=question.label,
            immediate_action=question.immediate_action,
            thirty_day_action=question.thirty_day_action,
            success_measure=question.success_measure,
            provider_questions=question.provider_questions,
        )
        for key, question in find_priorities(answers)
    ]


def build_context_guidance(
    management_method: str = "",
    manual_copy_frequency: str = "",
) -> list[str]:
    """Personalize guidance without changing the weighted risk score."""

    if management_method and management_method not in MANAGEMENT_METHODS:
        raise ValueError("Invalid management method")
    if (
        manual_copy_frequency
        and manual_copy_frequency not in MANUAL_COPY_FREQUENCIES
    ):
        raise ValueError("Invalid manual copy frequency")

    guidance = []
    management_guidance = {
        "One connected system": (
            "Confirm that the connected system supports data exports, backups, "
            "role-based access, and a clear process for failed integrations."
        ),
        "Several separate applications": (
            "Map which application owns inventory, orders, and customer information, "
            "then identify one repeated handoff that could be integrated."
        ),
        "Spreadsheets": (
            "Choose the spreadsheet process with the most repeated updates and test "
            "one small automated import, export, or synchronization step."
        ),
        "Paper or mostly manual processes": (
            "Document one repeated administrative process before selecting software, "
            "including who performs it and where errors or delays occur."
        ),
        "I am not sure": (
            "Create a simple list of the tools, spreadsheets, and paper records used "
            "for orders, inventory, and customer information."
        ),
    }
    frequency_guidance = {
        "Never": (
            "Repeated data entry is not a reported concern; continue checking for "
            "manual work as the business changes."
        ),
        "Less than once a month": (
            "Record the occasional data handoff so it can be reviewed before it "
            "becomes a larger recurring task."
        ),
        "Several times a month": (
            "Track one month of repeated entries and prioritize the task that takes "
            "the most time or creates the most errors."
        ),
        "Several times a week": (
            "Prioritize one frequent data handoff for a small automation or system "
            "integration test."
        ),
        "Every day": (
            "Treat daily duplicate entry as an immediate modernization opportunity; "
            "start with the highest-volume or most error-prone handoff."
        ),
    }

    if management_method:
        guidance.append(management_guidance[management_method])
    if manual_copy_frequency:
        guidance.append(frequency_guidance[manual_copy_frequency])
    return guidance


def generate_report(
    answers: Mapping[str, str],
    result: AssessmentResult,
    business_name: str = "",
    business_type: str = "",
    management_method: str = "",
    manual_copy_frequency: str = "",
) -> str:
    """Create a plain-text report without retaining or transmitting user input."""

    _validate_answers(answers)
    priorities = find_priorities(answers)
    breakdown = build_readiness_breakdown(answers)
    action_plan = build_modernization_plan(answers)
    name = clean_user_text(business_name, max_length=80) or "Not provided"
    kind = clean_user_text(business_type, max_length=60) or "Not provided"
    management = management_method or "Not provided"
    copy_frequency = manual_copy_frequency or "Not provided"
    context_guidance = build_context_guidance(
        management_method,
        manual_copy_frequency,
    )
    lines = [
        "BUSINESS READINESS CHECK",
        "========================",
        f"Business name: {name}",
        f"Business type: {kind}",
        "",
    ]

    lines.extend(
        [
            "BUSINESS CONTEXT",
            "----------------",
            f"Operations management: {management}",
            f"Repeated data entry: {copy_frequency}",
            "These optional answers personalize guidance and do not affect the score.",
        ]
    )
    if context_guidance:
        lines.extend(f"- {item}" for item in context_guidance)
    lines.append("")

    if result.risk_percentage is None:
        lines.extend(
            [
                "Overall result: Not calculated",
                (
                    "A score could not be calculated because every diagnostic "
                    "area was marked Not applicable."
                ),
            ]
        )
    else:
        lines.extend(
            [
                f"Overall risk: {result.risk_percentage:.1f}% ({result.risk_level})",
                f"Risk points: {result.risk_points} of {result.applicable_points}",
            ]
        )

    lines.extend(["", "AREA RESULTS", "------------"])
    for area in breakdown:
        lines.append(
            f"{area.question.label}: {area.status} ({area.answer})"
        )
        lines.append(f"   {area.summary}")

    lines.extend(["", "RECOMMENDED NEXT STEPS", "----------------------"])
    if priorities:
        for index, (_, question) in enumerate(priorities, start=1):
            lines.append(f"{index}. {question.recommendation}")
            lines.append(f"   {question.next_step_note}")
    elif result.risk_percentage is None:
        lines.append("Complete at least one applicable area to receive recommendations.")
    else:
        lines.append("No priority gaps were identified from the answers provided.")

    lines.extend(["", "MODERNIZATION ACTION PLAN", "-------------------------"])
    if action_plan:
        lines.extend(["", "THIS WEEK", "---------"])
        for index, step in enumerate(action_plan, start=1):
            lines.append(f"{index}. {step.label}: {step.immediate_action}")

        lines.extend(["", "NEXT 30 DAYS", "------------"])
        for index, step in enumerate(action_plan, start=1):
            lines.append(f"{index}. {step.label}: {step.thirty_day_action}")

        lines.extend(["", "HOW TO MEASURE PROGRESS", "-----------------------"])
        for index, step in enumerate(action_plan, start=1):
            lines.append(f"{index}. {step.label}: {step.success_measure}")

        lines.extend(["", "QUESTIONS TO ASK PROVIDERS", "--------------------------"])
        for step in action_plan:
            lines.append(f"{step.label}:")
            for question in step.provider_questions:
                lines.append(f"- {question}")
    elif result.risk_percentage is None:
        lines.append("Complete at least one applicable area to receive an action plan.")
    else:
        lines.append(
            "No immediate modernization actions were generated because no gaps "
            "were identified."
        )

    lines.extend(["", "SECURITY CHECKPOINTS", "--------------------"])
    for checkpoint in SECURITY_CHECKPOINTS:
        lines.append(f"- {checkpoint}")

    lines.extend(
        [
            "",
            "IMPORTANT",
            "---------",
            (
                "This educational tool provides general guidance. It is not a "
                "formal security, financial, compliance, or technology audit."
            ),
        ]
    )
    return "\n".join(lines) + "\n"
