import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict

from app.enums import (
    ApplicationStatus,
    DecisionKind,
    PriorityBand,
    Role,
    TemplateKind,
)
from app.schemas.common import Wire
from app.schemas.reads import FormVersionOut

# --- applications -------------------------------------------------------


class ApplicationSummaryOut(Wire):
    """The review table's row.

    Not the whole application: somebody scanning a morning's intake does not
    need every answer loaded, and the detail screen reads the full record when
    one is opened.
    """

    id: uuid.UUID
    program_id: uuid.UUID
    role: Role
    name: str
    email: str
    status: ApplicationStatus
    submitted_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None
    completeness: float
    flags: list[str] = []


class ApplicationCountsOut(Wire):
    """The whole queue's shape, independent of the current filter, so the tabs
    can carry counts without a request each.

    Keys stay snake_case: they are ApplicationStatus values, not field names,
    and the contract spells them the way the enum does. Camel-casing them turns
    `under_review` into `underReview`, which the frontend then reads as
    undefined and renders as a blank count.
    """

    model_config = ConfigDict(
        alias_generator=None,
        serialize_by_alias=False,
        populate_by_name=True,
        from_attributes=True,
    )

    submitted: int = 0
    under_review: int = 0
    approved: int = 0
    waitlisted: int = 0
    rejected: int = 0


class ApplicationPageOut(Wire):
    items: list[ApplicationSummaryOut]
    page: int
    page_size: int
    total: int
    counts: ApplicationCountsOut


class ApplicationOut(Wire):
    id: uuid.UUID
    program_id: uuid.UUID
    program_name: str | None = None
    role: Role
    name: str
    email: str
    status: ApplicationStatus
    submitted_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None
    editable_until: datetime | None = None
    matching_opens_at: datetime | None = None
    form_version_id: uuid.UUID
    answers: dict[str, Any] = {}


class ApplicationCreateIn(Wire):
    role: Role
    name: str
    email: str
    form_version_id: uuid.UUID
    answers: dict[str, Any] = {}


class ApplicationDecisionIn(Wire):
    decision: DecisionKind
    note: str | None = None


class BulkDecisionIn(Wire):
    application_ids: list[uuid.UUID]
    decision: DecisionKind
    note: str | None = None


class SkippedDecisionOut(Wire):
    application_id: uuid.UUID
    reason: str


class BulkDecisionResultOut(Wire):
    decided: int
    #: Partial success is reported rather than swallowed: somebody who selected
    #: twelve and moved nine needs to know which three did not move, and why.
    skipped: list[SkippedDecisionOut] = []


# --- form builder -------------------------------------------------------


class FormVersionSummaryOut(Wire):
    id: uuid.UUID
    version: int
    published_at: datetime | None = None
    question_count: int
    #: How many applications were answered against this version. The reason an
    #: old version cannot be deleted.
    application_count: int = 0


class FormEditorStateOut(Wire):
    role: Role
    #: The working copy. Null when nothing is being edited.
    draft: FormVersionOut | None = None
    #: What applicants are answering now. Null before the first publish.
    published: FormVersionOut | None = None
    history: list[FormVersionSummaryOut] = []


class FormDraftSaveIn(Wire):
    sections: list[dict[str, Any]]


# --- milestones ---------------------------------------------------------


class ProgramMilestoneOut(Wire):
    id: uuid.UUID
    title: str
    description: str | None = None
    week_offset: int
    strand_prompt: str | None = None
    reminder_days_before: int | None = None
    position: int


class ProgramMilestoneIn(Wire):
    #: Null for a milestone being added.
    id: uuid.UUID | None = None
    title: str
    description: str | None = None
    week_offset: int
    strand_prompt: str | None = None
    reminder_days_before: int | None = None
    position: int


class ProgramMilestonesSaveIn(Wire):
    items: list[ProgramMilestoneIn]


# --- templates ----------------------------------------------------------


class MessageTemplateOut(Wire):
    kind: TemplateKind
    subject: str
    body: str
    #: True while the programme has not overridden the wording, so the screen
    #: can tell what was written from what was inherited.
    is_default: bool = True
    updated_at: datetime | None = None
    updated_by: str | None = None


class MessageTemplateSaveIn(Wire):
    subject: str
    body: str


class MergeCodeOut(Wire):
    code: str
    description: str
    #: Carried by the API so a preview performs the same substitution the sender
    #: will, rather than one the browser invented.
    sample: str


class TemplateSetOut(Wire):
    items: list[MessageTemplateOut]
    merge_codes: list[MergeCodeOut]


# --- criteria -----------------------------------------------------------


class HardConstraintOut(Wire):
    kind: str
    enabled: bool


class FieldWeightOut(Wire):
    field_id: str
    weight: int
    direction: Literal["similar", "complementary"]


class PriorityWeightOut(Wire):
    field_id: str
    weight: int


class FairnessRulesOut(Wire):
    mentor_capacity_cap: int | None = None
    coverage_floor: float = 0.0
    priority_weights: list[PriorityWeightOut] = []


class MatchingRecipeOut(Wire):
    name: str
    version: int
    hard_constraints: list[HardConstraintOut] = []
    weights: list[FieldWeightOut] = []
    fairness: FairnessRulesOut
    updated_at: datetime | None = None
    updated_by: str | None = None


class MatchingRecipeSaveIn(Wire):
    name: str
    hard_constraints: list[HardConstraintOut] = []
    weights: list[FieldWeightOut] = []
    fairness: FairnessRulesOut


class CriteriaFieldOut(Wire):
    """A published question a weight may refer to."""

    field_id: str
    label: str
    role: Role
    type: str


class CriteriaEditorStateOut(Wire):
    recipe: MatchingRecipeOut
    matching_fields: list[CriteriaFieldOut] = []
    equity_fields: list[CriteriaFieldOut] = []


class PriorityBandStatOut(Wire):
    band: PriorityBand
    mentee_count: int
    mean_score: float
    median_score: float
