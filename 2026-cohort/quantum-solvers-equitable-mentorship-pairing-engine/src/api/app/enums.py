"""Value sets fixed by ../openapi.yaml.

These are plain Python enums stored as strings, not native Postgres enum types.
The API is the only writer and every input is validated against the contract
before it reaches the database, so a database-level enum adds little; what it
does add is an ALTER TYPE on every migration that touches a value set, which is
friction on exactly the kind of change this project makes often.
"""

from enum import StrEnum


class Role(StrEnum):
    MENTOR = "mentor"
    MENTEE = "mentee"


class ParticipationStatus(StrEnum):
    INVITED = "invited"
    APPLIED = "applied"
    APPROVED = "approved"
    WAITLISTED = "waitlisted"
    REMOVED = "removed"


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    WAITLISTED = "waitlisted"
    REJECTED = "rejected"


class ProgramState(StrEnum):
    NOT_YET_OPEN = "not_yet_open"
    OPEN = "open"
    CLOSED = "closed"
    FULL = "full"


class RunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DRAFTED = "drafted"
    PUBLISHED = "published"
    DISCARDED = "discarded"


class StrandState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    DISCARDED = "discarded"


class OriginMode(StrEnum):
    """How a strand came about. Stored because reports have to answer whether
    the algorithm did better than the coordinator's hand-picks."""

    MANUAL = "manual"
    SELF = "self"
    BATCH = "batch"


class PriorityBand(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Provenance(StrEnum):
    """Where an answer's words came from.

    Recorded because scoring free text rewards writing fluency, which tracks
    schooling and language background. Reports have to be able to ask whether
    coverage improved without guided answers quietly becoming a ranking feature.
    """

    SELF = "self"
    GUIDED = "guided"


class UnmatchedReason(StrEnum):
    """Each value has a different remedy, which is why the queue stores a code
    rather than a sentence."""

    NO_MENTOR_CAPACITY = "no_mentor_capacity"
    NO_SKILL_OVERLAP = "no_skill_overlap"
    JOINED_AFTER_RUN = "joined_after_run"
    INCOMPLETE_PROFILE = "incomplete_profile"
    ALL_CANDIDATES_DECLINED = "all_candidates_declined"


class TemplateKind(StrEnum):
    WELCOME = "welcome"
    MATCH_NOTIFICATION = "match_notification"
    NUDGE = "nudge"
    MID_POINT_CHECK_IN = "mid_point_check_in"
    CLOSING = "closing"


class BroadcastSegment(StrEnum):
    EVERYONE = "everyone"
    MENTORS = "mentors"
    MENTEES = "mentees"
    UNMATCHED = "unmatched"
    QUIET_STRANDS = "quiet_strands"
    INCOMPLETE_PROFILES = "incomplete_profiles"


class BroadcastState(StrEnum):
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"


class ResourceKind(StrEnum):
    HANDBOOK = "handbook"
    EXPECTATIONS = "expectations"
    CONVERSATION_STARTERS = "conversation_starters"
    CODE_OF_CONDUCT = "code_of_conduct"
    OTHER = "other"


class InviteState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class DigestFrequency(StrEnum):
    OFF = "off"
    DAILY = "daily"
    WEEKLY = "weekly"


class DeliveryState(StrEnum):
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class AuditAction(StrEnum):
    CRITERIA_SAVED = "criteria_saved"
    FORM_PUBLISHED = "form_published"
    RUN_PUBLISHED = "run_published"
    PAIR_OVERRIDDEN = "pair_overridden"
    MANUAL_PAIRING = "manual_pairing"
    APPLICATION_DECIDED = "application_decided"
    PARTICIPANT_EDITED = "participant_edited"
    STRAND_ENDED = "strand_ended"
    BROADCAST_SENT = "broadcast_sent"
    TEMPLATE_EDITED = "template_edited"
    DATA_EXPORTED = "data_exported"


class DecisionKind(StrEnum):
    APPROVE = "approve"
    WAITLIST = "waitlist"
    REJECT = "reject"
