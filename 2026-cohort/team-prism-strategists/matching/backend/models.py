from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    role = Column(String, default="MENTEE")  # 'MENTEE', 'MENTOR', 'ADMIN'
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=True)
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    otp_failed_attempts = Column(Integer, default=0)
    otp_last_sent_at = Column(DateTime, nullable=True)
    auth_provider = Column(String, default="LOCAL")
    oauth_id = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    two_factor_secret = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    mentee_profile = relationship("Mentee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentor_profile = relationship("Mentor", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Mentee(Base):
    __tablename__ = "mentees"
    
    id = Column(String, ForeignKey("users.id"), primary_key=True)
    name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    ed_level = Column(String, nullable=True)
    dev_type = Column(String, nullable=True)  # semicolon-separated string of roles
    years_code_pro = Column(Float, nullable=True)
    exp_tier = Column(String, nullable=True)
    job_factors = Column(String, nullable=True)  # semicolon-separated string
    org_size = Column(String, nullable=True)
    additional_details = Column(String, nullable=True)  # freestyle bio/interests text
    cv_path = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    prefer_diversity_ally = Column(Boolean, default=False)
    target_mentor_expertise = Column(String, nullable=True)
    target_mentor_country = Column(String, nullable=True)
    target_mentor_min_years = Column(Float, nullable=True)
    alternative_emails = Column(String, nullable=True)
    timezone = Column(String, default="Europe/London")
    linkedin_link = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mentee_profile")
    matches = relationship("Match", foreign_keys="[Match.mentee_id]", back_populates="mentee", cascade="all, delete-orphan")


class Mentor(Base):
    __tablename__ = "mentors"
    
    id = Column(String, ForeignKey("users.id"), primary_key=True)
    name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    ed_level = Column(String, nullable=True)
    dev_type = Column(String, nullable=True)  # semicolon-separated string of roles
    years_code_pro = Column(Float, nullable=True)
    exp_tier = Column(String, nullable=True)
    job_factors = Column(String, nullable=True)  # semicolon-separated string
    org_size = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    max_mentees = Column(Integer, default=3)
    additional_details = Column(String, nullable=True)  # freestyle bio/interests text
    contact_link = Column(String, nullable=True)  # booking/scheduling/profile link
    cv_path = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    is_diversity_ally = Column(Boolean, default=False)
    timezone = Column(String, default="Europe/London")
    linkedin_link = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mentor_profile")
    matches = relationship("Match", foreign_keys="[Match.mentor_id]", back_populates="mentor", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mentee_id = Column(String, ForeignKey("mentees.id"), nullable=False)
    mentor_id = Column(String, ForeignKey("mentors.id"), nullable=False)
    
    role_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    career_stage_score = Column(Float, nullable=False)
    goals_score = Column(Float, nullable=False)
    practical_score = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    match_quality = Column(String, nullable=False)  # 'Strong', 'Good', 'Fair', 'Weak'
    status = Column(String, default="PROPOSED")  # 'PROPOSED', 'ACCEPTED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    availability_note = Column(String, nullable=True)
    mentee_notified = Column(Boolean, default=False)
    mentor_notified = Column(Boolean, default=False)
    
    # Relationships
    mentee = relationship("Mentee", foreign_keys=[mentee_id], back_populates="matches")
    mentor = relationship("Mentor", foreign_keys=[mentor_id], back_populates="matches")


class ExternalNomination(Base):
    __tablename__ = "external_nominations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mentee_id = Column(String, ForeignKey("mentees.id"), nullable=False)
    mentor_name = Column(String, nullable=False)
    mentor_contact = Column(String, nullable=False)
    tech_focus = Column(String, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_contacted_at = Column(DateTime, default=datetime.datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False)  # 6-digit OTP or secure string
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False)  # 'LOGIN_SUCCESS', 'LOGIN_FAILED', '2FA_OTP_SENT', '2FA_VERIFIED', '2FA_FAILED', 'PASSWORD_RESET', 'USER_DELETED', 'DB_RESET', 'CONFIG_UPDATE'
    user_email = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    status = Column(String, default="SUCCESS")  # 'SUCCESS', 'WARNING', 'FAILED'
    ip_address = Column(String, nullable=True)
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class MentorshipNote(Base):
    __tablename__ = "mentorship_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mentor_id = Column(String, ForeignKey("users.id"), nullable=False)
    mentee_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    session_date = Column(DateTime, default=datetime.datetime.utcnow)
    topics_covered = Column(Text, nullable=True)
    action_items = Column(Text, nullable=True)
    milestone_status = Column(String, default="IN_PROGRESS")  # 'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'
    key_takeaways = Column(Text, nullable=True)
    next_meeting_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


