from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    is_manager: bool = False

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class WorkerResponse(BaseModel):
    id: str
    name: str
    role: str
    department: str
    max_hours: float
    current_hours: float
    avatar: Optional[str] = None
    is_manager: bool

    model_config = ConfigDict(from_attributes=True)

class ShiftBase(BaseModel):
    day: str
    type: str = "regular"
    start_time: str
    length: float
    note: Optional[str] = None

class ShiftCreate(ShiftBase):
    project_id: str
    worker_id: str

class ShiftResponse(ShiftBase):
    id: str
    project_id: str
    worker_id: str
    updated_by_ai: bool
    conflict_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    title: str

class ProjectCreate(ProjectBase):
    manager_id: str

class ProjectResponse(BaseModel):
    id: str
    manager_id: str
    title: str
    workers: List[WorkerResponse] = []
    shifts: List[ShiftResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ProposalResponse(BaseModel):
    id: str
    worker_id: str
    new_shift_data: Optional[Dict[str, Any]] = None
    isManagerApproved: bool
    isWorkerApproved: bool
    worker_name: Optional[str] = None
    worker_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    reply: str
    tools_used: List[Dict[str, Any]] = []
    updated_shift: Optional[Dict[str, Any]] = None
    created_proposal: Optional[Dict[str, Any]]=None

class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Dict[str, Any]

class RescheduleRequest(BaseModel):
    day: str
    start_time: str
    length: float
    note: Optional[str] = None

class ScenarioResponse(BaseModel):
    id: str
    affected_worker_id: str
    affected_worker_name: str
    conflict_day: str
    original_shift: str
    reason: str
    constraint: str
    prompt_text: str

    model_config = ConfigDict(from_attributes=True)

class ChatMessageResponse(BaseModel):
    id: str
    sender: str
    role_name: Optional[str] = None
    text: str
    timestamp: str
    is_pending_approval: Optional[bool] = None
    proposal_id: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    approval_state: Optional[List[Dict[str, Any]]] = None # type: ignore

    model_config = ConfigDict(from_attributes=True)

class ProposalApprovalRequest(BaseModel):
    proposal_id: str
    model_config = ConfigDict(from_attributes=True)



class ProposalApprovalResponse(BaseModel):
    success: bool
    message: str
    deleted: bool = False
    new_shift: Optional[ShiftResponse] = None
    proposal: Optional[ProposalResponse] = None