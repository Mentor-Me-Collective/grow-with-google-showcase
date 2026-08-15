"""Every model, imported so Base.metadata is complete.

Alembic autogenerate reads Base.metadata. A model that is defined but never
imported is invisible to it, and the migration it writes will happily drop the
table — so this file exists to make forgetting an import impossible.
"""

from app.models.auth import (
    ApplicationResumeToken,
    Invite,
    MagicLinkToken,
    NotificationPreference,
    SessionToken,
)
from app.models.core import Account, Organisation, Participation, Program
from app.models.forms import (
    Application,
    ApplicationDraft,
    FormVersion,
    WaitlistEntry,
)
from app.models.matching import (
    DraftPair,
    MatchingRecipe,
    ParticipantAttribute,
    Run,
    RunUnmatched,
)
from app.models.programme import (
    AuditEvent,
    Broadcast,
    MessageTemplate,
    ProgramMilestone,
    Resource,
)
from app.models.strands import Message, MessageRead, Strand, StrandMember

__all__ = [
    "WaitlistEntry",
    "Account",
    "Application",
    "ApplicationDraft",
    "ApplicationResumeToken",
    "AuditEvent",
    "Broadcast",
    "DraftPair",
    "FormVersion",
    "Invite",
    "MagicLinkToken",
    "MatchingRecipe",
    "Message",
    "MessageRead",
    "MessageTemplate",
    "NotificationPreference",
    "Organisation",
    "ParticipantAttribute",
    "Participation",
    "Program",
    "ProgramMilestone",
    "Resource",
    "Run",
    "RunUnmatched",
    "SessionToken",
    "Strand",
    "StrandMember",
]
