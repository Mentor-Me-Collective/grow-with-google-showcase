from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for Many-to-Many relationship between Projects and Workers
project_workers = Table(
    "project_workers",
    Base.metadata,
    Column("project_id", String, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("worker_id", String, ForeignKey("workers.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    manager_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    manager = relationship("Worker", foreign_keys=[manager_id], back_populates="managed_projects")
    workers = relationship("Worker", secondary=project_workers, back_populates="projects")
    shifts = relationship("Shift", back_populates="project", cascade="all, delete-orphan")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'Senior RN' | 'Charge Nurse' | 'RN' | 'LPN' | 'Support Specialist' | 'Project Manager'
    department = Column(String, nullable=False)
    max_hours = Column(Float, nullable=False, default=40.0)
    current_hours = Column(Float, nullable=False, default=0.0)
    avatar = Column(String, nullable=True)
    is_manager = Column(Boolean, default=False, nullable=False)

    # Relationships
    projects = relationship("Project", secondary=project_workers, back_populates="workers")
    managed_projects = relationship("Project", foreign_keys=[Project.manager_id], back_populates="manager", cascade="all, delete-orphan")
    shifts = relationship("Shift", back_populates="worker", cascade="all, delete-orphan")

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    day = Column(String, nullable=False)  # 'Monday' | 'Tuesday' | ... | 'Sunday'
    type = Column(String, nullable=False, default="regular")  # 'regular' | 'conflict' | 'updated' | 'off'
    start_time = Column(String, nullable=False)
    length = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    updated_by_ai = Column(Boolean, default=False)
    conflict_reason = Column(String, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="shifts")
    worker = relationship("Worker", back_populates="shifts")

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(String, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    new_shift_data = Column(JSON, nullable=True)  
    isManagerApproved = Column(Boolean, default=False)
    isWorkerApproved = Column(Boolean, default=False)
    worker = relationship("Worker")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True)
    sender = Column(String, nullable=False)  # 'user' | 'assistant' | 'system'
    role_name = Column(String, nullable=True)
    text = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    is_pending_approval = Column(Boolean, nullable=True)
    proposal_id = Column(String, nullable=True)
    
    # Complex fields stored as JSON
    options = Column(JSON, nullable=True)
    approval_state = Column(JSON, nullable=True)