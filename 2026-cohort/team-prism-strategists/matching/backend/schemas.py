from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # 'MENTEE', 'MENTOR'
    name: Optional[str] = None
    country: Optional[str] = None
    ed_level: Optional[str] = None
    dev_type: Optional[str] = None
    years_code_pro: Optional[float] = None
    job_factors: Optional[str] = None
    org_size: Optional[str] = None
    additional_details: Optional[str] = None
    contact_link: Optional[str] = None
    cv_path: Optional[str] = None
    profile_pic: Optional[str] = None
    invite_code: Optional[str] = None
    gender: Optional[str] = None
    target_mentor_expertise: Optional[str] = None
    target_mentor_country: Optional[str] = None
    target_mentor_min_years: Optional[float] = None
    prefer_diversity_ally: Optional[bool] = False
    is_diversity_ally: Optional[bool] = False
    linkedin_link: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    auth_provider: str = "LOCAL"
    oauth_id: Optional[str] = None
    avatar_url: Optional[str] = None
    two_factor_enabled: bool = True
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class SSOLoginRequest(BaseModel):
    provider: str  # "google" or "facebook"
    token_or_code: Optional[str] = None
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    oauth_id: Optional[str] = None
    role: Optional[str] = None
    mode: Optional[str] = "signin"  # "signin" or "signup"
    invite_code: Optional[str] = None

class SSOCallbackRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: Optional[str] = None
    role: Optional[str] = None
    mode: Optional[str] = "signin"  # "signin" or "signup"
    invite_code: Optional[str] = None

class SSOAuthUrlResponse(BaseModel):
    provider: str
    auth_url: str
    is_live_oauth: bool

class SSOResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    provider: str
    email: str
    name: Optional[str] = None
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenOrTwoFactorResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    two_factor_required: bool = False
    two_factor_enabled: Optional[bool] = True
    challenge_token: Optional[str] = None
    email: Optional[str] = None
    delivery_hint: Optional[str] = None
    otp_code_preview: Optional[str] = None
    is_signup: Optional[bool] = False

class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str
    code: str

class TwoFactorResendRequest(BaseModel):
    challenge_token: str

class TwoFactorToggleRequest(BaseModel):
    enabled: bool

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class MenteeProfileUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    ed_level: Optional[str] = None
    dev_type: Optional[str] = None
    years_code_pro: Optional[float] = None
    job_factors: Optional[str] = None
    org_size: Optional[str] = None
    additional_details: Optional[str] = None
    gender: Optional[str] = None
    target_mentor_expertise: Optional[str] = None
    target_mentor_country: Optional[str] = None
    target_mentor_min_years: Optional[float] = None
    alternative_emails: Optional[str] = None
    prefer_diversity_ally: Optional[bool] = None
    timezone: Optional[str] = None
    linkedin_link: Optional[str] = None

class MenteeProfileResponse(BaseModel):
    id: str
    name: Optional[str] = None
    country: Optional[str] = None
    ed_level: Optional[str] = None
    dev_type: Optional[str] = None
    years_code_pro: Optional[float] = None
    exp_tier: Optional[str] = None
    job_factors: Optional[str] = None
    org_size: Optional[str] = None
    additional_details: Optional[str] = None
    cv_path: Optional[str] = None
    profile_pic: Optional[str] = None
    gender: Optional[str] = None
    target_mentor_expertise: Optional[str] = None
    target_mentor_country: Optional[str] = None
    target_mentor_min_years: Optional[float] = None
    alternative_emails: Optional[str] = None
    prefer_diversity_ally: Optional[bool] = False
    timezone: Optional[str] = None
    linkedin_link: Optional[str] = None

    class Config:
        from_attributes = True

class MentorProfileUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    ed_level: Optional[str] = None
    dev_type: Optional[str] = None
    years_code_pro: Optional[float] = None
    job_factors: Optional[str] = None
    org_size: Optional[str] = None
    is_active: Optional[bool] = None
    max_mentees: Optional[int] = None
    contact_link: Optional[str] = None
    additional_details: Optional[str] = None
    gender: Optional[str] = None
    is_diversity_ally: Optional[bool] = None
    timezone: Optional[str] = None
    linkedin_link: Optional[str] = None

class MentorProfileResponse(BaseModel):
    id: str
    name: Optional[str] = None
    country: Optional[str] = None
    ed_level: Optional[str] = None
    dev_type: Optional[str] = None
    years_code_pro: Optional[float] = None
    exp_tier: Optional[str] = None
    job_factors: Optional[str] = None
    org_size: Optional[str] = None
    is_active: bool
    max_mentees: int
    additional_details: Optional[str] = None
    contact_link: Optional[str] = None
    cv_path: Optional[str] = None
    profile_pic: Optional[str] = None
    gender: Optional[str] = None
    is_diversity_ally: bool = False
    timezone: Optional[str] = None
    linkedin_link: Optional[str] = None

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: str
    mentee_id: str
    mentor_id: str
    role_score: float
    experience_score: float
    career_stage_score: float
    goals_score: float
    practical_score: float
    total_score: float
    match_quality: str
    status: str
    created_at: datetime.datetime
    availability_note: Optional[str] = None
    mentee_notified: Optional[bool] = False
    mentor_notified: Optional[bool] = False
    
    mentor_name: Optional[str] = None
    mentor_timezone: Optional[str] = None
    mentee_timezone: Optional[str] = None
    mentor_devtype: Optional[str] = None
    mentor_years: Optional[float] = None
    mentor_country: Optional[str] = None
    mentor_org_size: Optional[str] = None
    mentor_email: Optional[str] = None
    mentor_contact_link: Optional[str] = None
    mentor_cv_path: Optional[str] = None
    mentor_ed_level: Optional[str] = None
    mentor_profile_pic: Optional[str] = None
    mentor_job_factors: Optional[str] = None
    mentor_additional_details: Optional[str] = None
    mentor_gender: Optional[str] = None
    mentee_gender: Optional[str] = None
    is_representation_boosted: Optional[bool] = False
    is_ally_boosted: Optional[bool] = False
    is_real_user: Optional[bool] = False
    mentor_linkedin_link: Optional[str] = None
    mentee_linkedin_link: Optional[str] = None

    mentee_name: Optional[str] = None
    mentee_devtype: Optional[str] = None
    mentee_years: Optional[float] = None
    mentee_country: Optional[str] = None
    mentee_org_size: Optional[str] = None
    mentee_email: Optional[str] = None
    mentee_cv_path: Optional[str] = None
    mentee_ed_level: Optional[str] = None
    mentee_profile_pic: Optional[str] = None
    mentee_job_factors: Optional[str] = None
    mentee_additional_details: Optional[str] = None
    mentee_alternative_emails: Optional[str] = None
    
    class Config:
        from_attributes = True

class MatchAction(BaseModel):
    match_id: str
    action: str  # 'ACCEPT', 'DECLINE'
    availability_note: Optional[str] = None

class UserProfileResponse(BaseModel):
    user: UserResponse
    mentee: Optional[MenteeProfileResponse] = None
    mentor: Optional[MentorProfileResponse] = None

class NominationCreate(BaseModel):
    mentor_name: str
    mentor_contact: str
    tech_focus: str
    custom_message: Optional[str] = None

class NominationResponse(BaseModel):
    id: str
    mentee_id: str
    mentor_name: str
    mentor_contact: str
    tech_focus: str
    invite_code: str
    status: str
    created_at: datetime.datetime
    last_contacted_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class FollowUpEmailRequest(BaseModel):
    custom_message: Optional[str] = None
    subject: Optional[str] = None

class LinkedInOutreachTemplates(BaseModel):
    connection_note: str
    connection_note_length: int
    inmail_message: str

class LinkedInDeepLinkRequest(BaseModel):
    role: Optional[str] = None
    skills: Optional[List[str]] = None
    country: Optional[str] = None
    seniority: Optional[str] = None
    mentorship_intent: Optional[bool] = True
    women_in_tech: Optional[bool] = False
    custom_keywords: Optional[str] = None

class LinkedInDeepLinkResponse(BaseModel):
    deep_link_url: str
    raw_query: str
    query_breakdown: dict
    outreach_templates: LinkedInOutreachTemplates


# ── Password Reset Schemas ──────────────────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    challenge_token: str
    delivery_hint: str
    otp_code_preview: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    challenge_token: str
    code: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


# ── In-App Messaging Schemas ────────────────────────────────────────────
class MessageCreate(BaseModel):
    match_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    match_id: str
    sender_id: str
    sender_name: Optional[str] = None
    recipient_id: str
    content: str
    is_read: bool
    created_at: datetime.datetime
    is_mine: Optional[bool] = False

    class Config:
        from_attributes = True

class UnreadMessagesSummary(BaseModel):
    total_unread: int
    by_match: dict


# ── Direct Match Email Schemas ──────────────────────────────────────────
class DirectEmailRequest(BaseModel):
    subject: str = "Mentoring-Me Connection Update"
    body_text: str

class DirectEmailResponse(BaseModel):
    status: str
    message: str
    recipient_email: str


# ── Admin Dynamic Algorithm & Telemetry Schemas ─────────────────────────
class AlgorithmConfigRequest(BaseModel):
    w_role: float = 0.30
    w_exp: float = 0.25
    w_stage: float = 0.20
    w_goals: float = 0.15
    w_practical: float = 0.10
    ally_boost: float = 0.10
    rep_boost: float = 0.05

class SecurityAuditLogResponse(BaseModel):
    id: str
    event_type: str
    user_email: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ── Mentorship Milestones & Session Notes Schemas ───────────────────────
class MentorshipNoteCreate(BaseModel):
    mentee_id: str
    title: str
    session_date: Optional[datetime.datetime] = None
    topics_covered: Optional[str] = None
    action_items: Optional[str] = None
    milestone_status: Optional[str] = "IN_PROGRESS"  # NOT_STARTED, IN_PROGRESS, COMPLETED
    key_takeaways: Optional[str] = None
    next_meeting_date: Optional[str] = None


class MentorshipNoteUpdate(BaseModel):
    title: Optional[str] = None
    session_date: Optional[datetime.datetime] = None
    topics_covered: Optional[str] = None
    action_items: Optional[str] = None
    milestone_status: Optional[str] = None
    key_takeaways: Optional[str] = None
    next_meeting_date: Optional[str] = None


class MentorshipNoteResponse(BaseModel):
    id: str
    mentor_id: str
    mentee_id: str
    mentor_name: Optional[str] = None
    mentee_name: Optional[str] = None
    title: str
    session_date: datetime.datetime
    topics_covered: Optional[str] = None
    action_items: Optional[str] = None
    milestone_status: str
    key_takeaways: Optional[str] = None
    next_meeting_date: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


