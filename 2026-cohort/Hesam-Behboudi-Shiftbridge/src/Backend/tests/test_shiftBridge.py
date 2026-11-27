import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models
# Assuming your main FastAPI application instance is imported from 'main.py'
# from main import app

# Setup in-memory SQLite database for testing
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

# If using app.dependency_overrides, bind it here:
# app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    # Replace `app` with your actual imported FastAPI app instance
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

def test_signup_and_login(client):
    # 1. Test User Signup
    signup_payload = {
        "email": "nurse.jane@shiftbridge.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Doe"
    }
    response = client.post("/auth/signup", json=signup_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == signup_payload["email"]
    assert data["full_name"] == signup_payload["full_name"]

    # 2. Test User Login
    login_payload = {
        "email": "nurse.jane@shiftbridge.com",
        "password": "SecurePassword123!"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_data_retrieval_endpoints(client):
    db = TestingSessionLocal()
    
    # Seed mock project, worker, shift, and proposal data
    worker = models.Worker(
        id="worker-1",
        email="jane@shiftbridge.com",
        hashed_password="hashed_dummy_password",
        name="Jane Doe",
        role="RN",
        department="Emergency"
    )
    project = models.Project(
        id="proj-1",
        manager_id="mgr-1",
        title="Emergency Ward Schedule"
    )
    shift = models.Shift(
        id="shift-101",
        project_id="proj-1",
        worker_id="worker-1",
        day="Monday",
        type="regular",
        shift_time="08:00 - 16:00",
        hours=8.0
    )
    proposal = models.Proposal(
        id="prop-001",
        worker_1_new_shift={"shift_id": "shift-101", "proposed_start_date": "2026-11-12T09:00:00"},
        isManagerApproved=False,
        isWorkerApproved=True
    )
    db.add_all([worker, project, shift, proposal])
    db.commit()
    db.close()

    # Login to get bearer token
    login_res = client.post("/auth/login", json={
        "email": "jane@shiftbridge.com",
        "password": "SecurePassword123!"
    })
    # If login requires exact seeded password match in security utils, 
    # alternatively sign up via API first:
    client.post("/auth/signup", json={
        "email": "jane@shiftbridge.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Doe"
    })
    login_res = client.post("/auth/login", json={
        "email": "jane@shiftbridge.com",
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /data/projects
    res = client.get("/data/projects", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Test GET /data/workers
    res = client.get("/data/workers", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Test GET /data/shifts
    res = client.get("/data/shifts?project_id=proj-1", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == "shift-101"

    # Test GET /data/proposals (Chat Messages / Proposals endpoint)
    res = client.get("/data/proposals", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_ai_chat_and_reschedule_proposal_flow(client):
    db = TestingSessionLocal()
    worker = models.Worker(
        id="worker-2",
        email="john.nurse@shiftbridge.com",
        hashed_password="password123",
        name="John Smith",
        role="Charge Nurse",
        department="ICU"
    )
    shift = models.Shift(
        id="shift-202",
        project_id="proj-2",
        worker_id="worker-2",
        day="Tuesday",
        type="regular",
        shift_time="07:00 - 15:00",
        hours=8.0
    )
    db.add_all([worker, shift])
    db.commit()
    db.close()

    # Register and login user
    client.post("/auth/signup", json={
        "email": "john.nurse@shiftbridge.com",
        "password": "password123",
        "full_name": "John Smith"
    })
    login_res = client.post("/auth/login", json={
        "email": "john.nurse@shiftbridge.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify shift exists via data endpoint
    shifts_res = client.get("/data/shifts", headers=headers)
    assert shifts_res.status_code == 200
    user_shifts = shifts_res.json()
    assert len(user_shifts) > 0
    target_shift_id = user_shifts[0]["id"]

    # Test Proposal creation directly via tool/service logic or chat endpoint if exposed
    db_verify = TestingSessionLocal()
    from tools import tool_create_reschedule_proposal
    proposal_result = tool_create_reschedule_proposal(
        db=db_verify,
        current_user_id="worker-2",
        shift_id=target_shift_id,
        new_start_date="2026-11-15T08:00:00",
        new_length=8.0,
        note="Need to attend a medical conference"
    )
    db_verify.close()

    assert proposal_result["success"] is True
    created_prop = proposal_result["proposal"]
    assert created_prop["isManagerApproved"] is False
    assert created_prop["worker_1_new_shift"]["shift_id"] == target_shift_id

    # Verify proposal is retrievable in the database
    db_verify = TestingSessionLocal()
    db_proposal = db_verify.query(models.Proposal).filter(models.Proposal.id == created_prop["proposal_id"]).first()
    assert db_proposal is not None
    db_verify.close()