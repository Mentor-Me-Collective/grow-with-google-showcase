import pytest
from datetime import datetime
import models
import security

def get_auth_token(client, email="alice@test.com", password="password123"):
    # Signup user
    client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Alice Worker"}
    )
    # Login
    res = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    return res.json()["access_token"]

def seed_project_and_shifts(db):
    manager = models.Worker(email="manager@test.com", hashed_password="hash", full_name="Boss Man")
    worker1 = models.Worker(email="alice@test.com", hashed_password=security.get_password_hash("password123"), full_name="Alice Worker")
    worker2 = models.Worker(email="bob@test.com", hashed_password="hash", full_name="Bob Builder")
    worker3 = models.Worker(email="carol@test.com", hashed_password="hash", full_name="Carol Mason")
    db.add_all([manager, worker1, worker2, worker3])
    db.commit()

    proj = models.Project(
        manager_id=manager.id,
        title="Skyline Tower",
        workers=[worker1, worker2, worker3]
    )
    db.add(proj)
    db.commit()

    # Shift for Alice (worker1)
    shift_alice = models.Shift(
        project_id=proj.id,
        owner_id=worker1.id,
        start_date=datetime(2026, 11, 10, 8, 0, 0),
        length=8
    )
    # Shifts for Bob and Carol (coworkers)
    shift_bob = models.Shift(
        project_id=proj.id,
        owner_id=worker2.id,
        start_date=datetime(2026, 11, 10, 16, 0, 0),
        length=8
    )
    shift_carol = models.Shift(
        project_id=proj.id,
        owner_id=worker3.id,
        start_date=datetime(2026, 11, 11, 8, 0, 0),
        length=6
    )
    db.add_all([shift_alice, shift_bob, shift_carol])
    db.commit()
    db.refresh(proj)
    db.refresh(shift_alice)
    return proj, shift_alice, worker1

def test_get_available_tools(client, db):
    token = get_auth_token(client, "tool_user@test.com")
    res = client.get("/chat/tools", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_other_workers_shifts" in tool_names
    assert "get_my_shifts" in tool_names
    assert "reschedule_shift" in tool_names

def test_direct_tool_execution(client, db):
    proj, shift_alice, alice = seed_project_and_shifts(db)
    
    # Login as Alice
    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Execute get_other_workers_shifts
    res = client.post(
        "/chat/tools/execute",
        headers=headers,
        json={
            "tool_name": "get_other_workers_shifts",
            "arguments": {"project_id": proj.id}
        }
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    shifts = res_data["result"]["shifts"]
    assert len(shifts) == 2  # Bob and Carol
    worker_emails = [s["worker_email"] for s in shifts]
    assert "bob@test.com" in worker_emails
    assert "carol@test.com" in worker_emails
    assert "alice@test.com" not in worker_emails

    # 2. Execute reschedule_shift
    res2 = client.post(
        "/chat/tools/execute",
        headers=headers,
        json={
            "tool_name": "reschedule_shift",
            "arguments": {
                "shift_id": shift_alice.id,
                "new_start_date": "2026-11-15 10:00:00",
                "new_length": 6
            }
        }
    )
    assert res2.status_code == 200
    res2_data = res2.json()
    assert res2_data["success"] is True
    updated = res2_data["result"]["shift"]
    assert "2026-11-15" in updated["new_start_date"]
    assert updated["new_length"] == 6

def test_chat_get_other_workers_shifts(client, db):
    proj, shift_alice, alice = seed_project_and_shifts(db)
    
    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ask the AI model in chat
    res = client.post(
        "/chat",
        headers=headers,
        json={"message": f"Can you show me other workers shifts for project {proj.id}?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "Bob Builder" in data["reply"] or "Bob" in data["reply"]
    assert "Carol Mason" in data["reply"] or "Carol" in data["reply"]
    assert len(data["tools_used"]) >= 1
    assert data["tools_used"][0]["tool"] == "get_other_workers_shifts"

def test_chat_reschedule_shift(client, db):
    proj, shift_alice, alice = seed_project_and_shifts(db)
    
    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Chat requesting reschedule
    res = client.post(
        "/chat",
        headers=headers,
        json={"message": f"Please reschedule shift {shift_alice.id} to 2026-11-18 09:00 for 7 hours"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "successfully rescheduled" in data["reply"].lower()
    assert data["updated_shift"] is not None
    assert "2026-11-18" in data["updated_shift"]["new_start_date"]
    assert data["updated_shift"]["new_length"] == 7

    # Verify shift in database was updated
    updated_shift = db.query(models.Shift).filter(models.Shift.id == shift_alice.id).first()
    assert updated_shift.start_date.day == 18
    assert updated_shift.start_date.hour == 9
    assert updated_shift.length == 7

def test_chat_multi_turn_reschedule(client, db):
    proj, shift_alice, alice = seed_project_and_shifts(db)
    
    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Turn 1: user expresses desire to reschedule without providing date
    res1 = client.post(
        "/chat",
        headers=headers,
        json={"message": "I would like to reschedule my shift."}
    )
    assert res1.status_code == 200
    reply1 = res1.json()["reply"]
    assert "what new date and time" in reply1.lower() or "here are your current shifts" in reply1.lower()

    # Turn 2: user replies with date and time
    res2 = client.post(
        "/chat",
        headers=headers,
        json={
            "message": f"Please reschedule shift {shift_alice.id} to 2026-11-22 14:00",
            "history": [
                {"role": "user", "content": "I would like to reschedule my shift."},
                {"role": "assistant", "content": reply1}
            ]
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "successfully rescheduled" in data2["reply"].lower() or "rescheduled" in data2["reply"].lower()
    assert data2["updated_shift"] is not None
    assert "2026-11-22" in data2["updated_shift"]["new_start_date"]

def test_shifts_direct_endpoints(client, db):
    proj, shift_alice, alice = seed_project_and_shifts(db)
    
    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /shifts/my-shifts
    res1 = client.get("/shifts/my-shifts", headers=headers)
    assert res1.status_code == 200
    assert len(res1.json()["shifts"]) == 1
    assert res1.json()["shifts"][0]["shift_id"] == shift_alice.id

    # 2. GET /shifts/project/{id}/workers
    res2 = client.get(f"/shifts/project/{proj.id}/workers", headers=headers)
    assert res2.status_code == 200
    assert len(res2.json()["shifts"]) == 2

    # 3. PATCH /shifts/{id}/reschedule
    res3 = client.patch(
        f"/shifts/{shift_alice.id}/reschedule",
        headers=headers,
        json={"new_start_date": "2026-11-25 11:00:00", "new_length": 5}
    )
    assert res3.status_code == 200
    assert res3.json()["success"] is True
    assert res3.json()["shift"]["new_length"] == 5

def test_local_llm_openai_tool_calling_mock(client, db, monkeypatch):
    from unittest.mock import MagicMock
    import json
    from ai_service import ai_engine

    proj, shift_alice, alice = seed_project_and_shifts(db)

    # Mock tool call object mimicking OpenAI response
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_abc123"
    mock_tool_call.function.name = "reschedule_shift"
    mock_tool_call.function.arguments = json.dumps({
        "shift_id": shift_alice.id,
        "new_start_date": "2026-11-30 08:00:00",
        "new_length": 8
    })

    # First completion returns tool_calls
    mock_first_msg = MagicMock()
    mock_first_msg.tool_calls = [mock_tool_call]
    mock_first_msg.content = None
    mock_first_choice = MagicMock()
    mock_first_choice.message = mock_first_msg
    mock_first_resp = MagicMock()
    mock_first_resp.choices = [mock_first_choice]

    # Second completion returns final text
    mock_second_msg = MagicMock()
    mock_second_msg.tool_calls = None
    mock_second_msg.content = "I have rescheduled your shift to Nov 30 at 08:00."
    mock_second_choice = MagicMock()
    mock_second_choice.message = mock_second_msg
    mock_second_resp = MagicMock()
    mock_second_resp.choices = [mock_second_choice]

    mock_create = MagicMock(side_effect=[mock_first_resp, mock_second_resp])
    monkeypatch.setattr(ai_engine.client.chat.completions, "create", mock_create)

    login_res = client.post("/auth/login", json={"email": "alice@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/chat",
        headers=headers,
        json={"message": "Please reschedule my shift"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "Nov 30" in data["reply"]
    assert len(data["tools_used"]) == 1
    assert data["tools_used"][0]["tool"] == "reschedule_shift"
    assert data["updated_shift"] is not None
    assert "2026-11-30" in data["updated_shift"]["new_start_date"]
