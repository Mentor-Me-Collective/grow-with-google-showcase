from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db
from routes.auth import get_current_user
import models
import schemas
import tools
from ai_service import ai_engine

router = APIRouter(prefix="/chat", tags=["AI Chat & Tools"])

@router.post("", response_model=schemas.ChatResponse)
def chat_with_ai(
    request: schemas.ChatRequest,
    current_user: models.Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with the local AI model to reschedule shifts and inspect other workers' schedules."""
    history_dicts = None
    if request.history:
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    result = ai_engine.chat(
        message=request.message,
        db=db,
        current_user=current_user,
        chat_history=history_dicts
    )

    return result

@router.get("/tools")
def get_available_tools(current_user: models.Worker = Depends(get_current_user)):
    """Exposes tool definitions for the local AI model to perform function calling."""
    return {
        "tools": tools.AVAILABLE_TOOLS
    }

@router.post("/tools/execute", response_model=schemas.ToolExecutionResponse)
def execute_tool(
    request: schemas.ToolExecutionRequest,
    current_user: models.Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a specific tool by name with arguments for the local AI model."""
    result = tools.execute_tool_by_name(
        tool_name=request.tool_name,
        args=request.arguments,
        db=db,
        current_user_id=current_user.id
    )
    is_success = result.get("success", True)
    return {
        "success": is_success,
        "result": result
    }
