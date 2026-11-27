import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models

# 1. Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    # Replace `app` with your actual FastAPI app instance import (e.g., from main import app)
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
authenticated_user_token(client):
    """Helper fixture to signup, login, and return an authorization header."""
    signup_payload = {
        "email": "nurse.sarah@shiftbridge.com",
        "password": "SecurePassword123!",
        "full_name": "Sarah Jenkins"
    }
    client.post("/auth/signup", json=signup_payload)
    
    login_res = client.post("/auth/login", json={
        "email": "nurse.sarah@shiftbridge.com",
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_available_tools(client, authenticated_user_token):
    """Test GET /chat/tools exposes the tool definitions successfully."""
    response = client.get("/chat/tools", headers=authenticated_user_token)
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 3
    tool_names = [t["name"] for t in data["tools"]]
    assert "create_reschedule_proposal" in tool_names
    assert "get_my_shifts" in tool_names

def test_chat_endpoint_with_ai_mock(client, authenticated_user_token):
    """Test POST /chat endpoint with mocked ai_engine response for rescheduling proposal."""
    # Seed a test shift in the database so tool execution references a valid record if needed
    db = TestingSessionLocal()
    # Note: auth/signup creates a Worker record. Let's match the email or insert worker/shift directly.
    worker = db.query(models.Worker).filter(models.Worker.email == "nurse.sarah@shiftbridge.com").first()
    
    shift = models.Shift(
        id="shift-777",
        project_id="proj-1",
        worker_id=worker.id,
        day="Monday",
        type="regular",
        shift_time="08:00 - 16:00",
        hours=8.0
    )
    db.add(shift)
    db.commit()
    db.close()

    # Mock `ai_engine.chat` to simulate tool calling & response generation without hitting a live LLM
    with patch("ai_service.LocalLLMShiftAssistant.chat") as mock_chat:
        mock_chat.return_value = {
            "reply": "I've created a proposal to reschedule your shift to November 15.",
            "tools_used": [
                {
                    "tool": "create_reschedule_proposal",
                    "arguments": {
                        "shift_id": "shift-777",
                        "new_start_date": "2026-11-15T09:00:00",
                        "new_length": 8.0,
                        "note": "Doctor appointment"
                    },
                    "result": {
                        "success": True,
                        "proposal": {
                            "proposal_id": "prop-uuid-123",
                            "worker_1_new_shift": {"shift_id": "shift-777"},
                            "isManagerApproved": False,
                            "isWorkerApproved": False
                        }
                    }
                }
            ],
            "created_proposal": {
                "proposal_id": "prop-uuid-123",
                "worker_1_new_shift": {"shift_id": "shift-777"},
                "isManagerApproved": False,
                "isWorkerApproved": False
            }
        }

        chat_payload = {
            "message": "Can you propose moving shift-777 to November 15 at 9 AM?",
            "history": []
        }

        response = client.post("/chat", json=chat_payload, headers=authenticated_user_token)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["tools_used"]) == 1
        assert data["tools_used"][0]["tool"] == "create_reschedule_proposal"
        assert data["created_proposal"]["proposal_id"] == "prop-uuid-123"

def test_execute_tool_endpoint_directly(client, authenticated_user_token):
    """Test POST /chat/tools/execute endpoint for direct tool execution testing."""
    db = TestingSessionLocal()
    worker = db.query(models.Worker).filter(models.Worker.email == "nurse.sarah@shiftbridge.com").first()
    
    shift = models.Shift(
        id="shift-888",
        project_id="proj-1",
        worker_id=worker.id,
        day="Tuesday",
        type="regular",
        shift_time="09:00 - 17:00",
        hours=8.0
    )
    db.add(shift)
    db.commit()
    db.close()

    tool_execution_payload = {
        "tool_name": "create_reschedule_proposal",
        "arguments": {
            "shift_id": "shift-888",
            "new_start_date": "2026-11-18T08:00:00",
            "new_length": 8.0,
            "note": "Family event"
        }
    }

    response = client.post("/chat/tools/execute", json=tool_execution_payload, headers=authenticated_user_token)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "result" in data
    assert "proposal" in data["result"]
    assert data["result"]["proposal"]["worker_1_new_shift"]["shift_id"] == "shift-888"

    # Verify Proposal was successfully written into the database
    db_verify = TestingSessionLocal()
    proposal_id = data["result"]["proposal"]["proposal_id"]
    saved_proposal = db_verify.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    assert saved_proposal is not None
    assert saved_proposal.isManagerApproved is False
    db_verify.close()