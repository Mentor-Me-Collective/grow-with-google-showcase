from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import models

# Tool definitions metadata (compatible with OpenAI/Gemini/local function calling standards)
AVAILABLE_TOOLS = [
    {
        "name": "get_other_workers_shifts",
        "description": "Fetch shifts of other workers/coworkers in the specified project to check their schedules, availability, and avoid conflicts.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The ID of the project. If not provided, coworkers' shifts across all user's projects will be retrieved."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_my_shifts",
        "description": "Fetch the current user's scheduled shifts.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Optional project ID to filter user's shifts."
                }
            },
            "required": []
        }
    },
    {
        "name": "create_reschedule_proposal",
        "description": "Create a reschedule proposal for the worker shift, storing the new shift details as a JSON payload in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "shift_id": {
                    "type": "string",
                    "description": "The ID of the shift to reschedule."
                },
                "day": {
                    "type": "string",
                    "description": "The proposed day of the week (e.g. 'Monday', 'Tuesday')."
                },
                "start_time": {
                    "type": "string",
                    "description": "The proposed start time (e.g. '07:00')."
                },
                "length": {
                    "type": "number",
                    "description": "The proposed duration/length of the shift in hours (e.g. 8.0)."
                },
                "note": {
                    "type": "string",
                    "description": "Optional note or reason for the reschedule proposal."
                }
            },
            "required": ["shift_id", "day", "start_time", "length"]
        }
    }
]

# OpenAI-compatible function calling tool schemas
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"]
        }
    }
    for t in AVAILABLE_TOOLS
]


def tool_get_other_workers_shifts(
    db: Session,
    current_user_id: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve other workers' shifts for a project or all projects the user is involved in."""
    query = db.query(models.Shift).filter(models.Shift.worker_id != current_user_id)
    
    if project_id is not None:
        query = query.filter(models.Shift.project_id == project_id)
    else:
        user = db.query(models.Worker).filter(models.Worker.id == current_user_id).first()
        if user:
            user_project_ids = [p.id for p in user.projects]
            if user_project_ids:
                query = query.filter(models.Shift.project_id.in_(user_project_ids))

    shifts = query.all()
    
    results = []
    for s in shifts:
        worker = db.query(models.Worker).filter(models.Worker.id == s.worker_id).first()
        project = db.query(models.Project).filter(models.Project.id == s.project_id).first()
        results.append({
            "shift_id": s.id,
            "project_id": s.project_id,
            "project_title": project.title if project else "Unknown",
            "worker_id": s.worker_id,
            "worker_name": worker.name if worker else "Unknown",
            "worker_email": worker.email if worker else "",
            "day": s.day,
            "type": s.type,
            "start_time": s.start_time,
            "length": s.length,
            "note": s.note
        })
        
    return {
        "success": True,
        "count": len(results),
        "shifts": results
    }


def tool_get_my_shifts(
    db: Session,
    current_user_id: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve all shifts belonging to the current user."""
    query = db.query(models.Shift).filter(models.Shift.worker_id == current_user_id)
    
    # if project_id is not None:
    #     query = query.filter(models.Shift.project_id == project_id)
        
    shifts = query.all()
    results = []
    for s in shifts:
        project = db.query(models.Project).filter(models.Project.id == s.project_id).first()
        results.append({
            "shift_id": s.id,
            "project_id": s.project_id,
            "project_title": project.title if project else "Unknown",
            "day": s.day,
            "type": s.type,
            "start_time": s.start_time,
            "length": s.length,
            "note": s.note
        })
        
    return {
        "success": True,
        "count": len(results),
        "shifts": results
    }


def tool_create_reschedule_proposal(
    db: Session,
    current_user_id: str,
    shift_id: str,
    day: str,
    start_time: str,
    length: float,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new reschedule proposal record in the database using the updated model schema."""
    shift = db.query(models.Shift).filter(
        models.Shift.id == shift_id,
        models.Shift.worker_id == current_user_id
    ).first()
    if not shift:
        return {
            "success": False,
            "error": f"Shift with ID {shift_id} not found or does not belong to you."
        }
    proposal_id = str(uuid.uuid4())
    new_shift_data_payload = {
        "shift_id": shift.id,
        "project_id": shift.project_id,
        "worker_id": current_user_id,
        "current_day": shift.day,
        "current_start_time": shift.start_time,
        "current_length": shift.length,
        "proposed_day": day,
        "proposed_start_time": start_time,
        "proposed_length": length,
        "note": note or shift.note
    }

    proposal = models.Proposal(
        id=proposal_id,
        worker_id=current_user_id,
        new_shift_data=new_shift_data_payload,
        isManagerApproved=False,
        isWorkerApproved=False
    )
    print(proposal)
    try :
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
    except Exception as e:
        print('proposal added' ,e)

    

    return {
        "success": True,
        "message": f"Successfully created reschedule proposal #{proposal.id}.",
        "proposal": {
            "id": proposal.id,
            "worker_id": proposal.worker_id,
            "new_shift_data": proposal.new_shift_data,
            "isManagerApproved": proposal.isManagerApproved,
            "isWorkerApproved": proposal.isWorkerApproved
        }
    }


def execute_tool_by_name(
    tool_name: str,
    args: Dict[str, Any],
    db: Session,
    current_user_id: str
) -> Dict[str, Any]:
    print('args, tool_name:', args, tool_name)
    """Execute a tool by name with arguments."""
    if tool_name == "get_other_workers_shifts":
        return tool_get_other_workers_shifts(db, current_user_id, project_id=args.get("project_id"))
    elif tool_name == "get_my_shifts":
        return tool_get_my_shifts(db, current_user_id, project_id=args.get("project_id"))
    elif tool_name == "create_reschedule_proposal":
        return tool_create_reschedule_proposal(
            db=db,
            current_user_id=current_user_id,
            shift_id=args.get("shift_id", ""),
            day=args.get("day", ""),
            start_time=args.get("start_time", ""),
            length=args.get("length", 8.0),
            note=args.get("note")
        )
    else:
        return {
            "success": False,
            "error": f"Unknown tool: '{tool_name}'"
        }