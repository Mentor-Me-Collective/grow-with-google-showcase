import os
import uuid
import pytest
from fastapi.testclient import TestClient

os.environ["DEBUG_OTP"] = "true"
from backend.main import app

client = TestClient(app)
API_URL = "/api/v1"


def get_token(user_email, user_password):
    resp = client.post(f"{API_URL}/auth/token", data={
        "username": user_email,
        "password": user_password
    })
    if resp.status_code != 200:
        return None, resp
    data = resp.json()
    if data.get("two_factor_required"):
        v_resp = client.post(f"{API_URL}/auth/2fa/verify", json={
            "challenge_token": data["challenge_token"],
            "code": data["otp_code_preview"]
        })
        return v_resp.json().get("access_token"), v_resp
    return data.get("access_token"), resp


def test_mentorship_notes_flow():
    suffix = uuid.uuid4().hex[:6]
    mentor_email = f"lead_mentor_{suffix}@example.com"
    mentee_email = f"growth_mentee_{suffix}@example.com"
    pwd = "Password123!"

    # 1. Register Mentor
    resp_m = client.post(f"{API_URL}/auth/signup", json={
        "email": mentor_email,
        "password": pwd,
        "role": "MENTOR",
        "name": "Senior Coach Alan",
        "country": "United Kingdom",
        "dev_type": "Engineering manager;Developer, full-stack",
        "years_code_pro": 12.0
    })
    assert resp_m.status_code == 201

    # 2. Register Mentee
    resp_e = client.post(f"{API_URL}/auth/signup", json={
        "email": mentee_email,
        "password": pwd,
        "role": "MENTEE",
        "name": "Junior Dev Clara",
        "country": "United Kingdom",
        "dev_type": "Developer, full-stack",
        "years_code_pro": 1.0,
        "target_mentor_expertise": "System Design, Microservices, Python"
    })
    assert resp_e.status_code == 201

    # 3. Log in
    m_token, _ = get_token(mentor_email, pwd)
    e_token, _ = get_token(mentee_email, pwd)
    m_headers = {"Authorization": f"Bearer {m_token}"}
    e_headers = {"Authorization": f"Bearer {e_token}"}

    e_profile = client.get(f"{API_URL}/users/me", headers=e_headers).json()
    mentee_id = e_profile["user"]["id"]

    # 4. Create a Session Note
    create_resp = client.post(f"{API_URL}/notes", json={
        "mentee_id": mentee_id,
        "title": "Kickoff 1-on-1: Career Vision & Roadmap",
        "topics_covered": "Discussed 6-month goals, transition to cloud architecture, and imposter syndrome.",
        "action_items": "- [ ] Read Clean Architecture Ch. 1-3\n- [ ] Set up Docker on local dev machine",
        "milestone_status": "IN_PROGRESS",
        "key_takeaways": "Clara is highly motivated; focus next on real-world system design exercises.",
        "next_meeting_date": "2026-09-15 15:00 UTC"
    }, headers=m_headers)

    assert create_resp.status_code == 201, f"Failed to create note: {create_resp.text}"
    note_data = create_resp.json()
    note_id = note_data["id"]
    assert note_data["title"] == "Kickoff 1-on-1: Career Vision & Roadmap"
    assert note_data["milestone_status"] == "IN_PROGRESS"

    # 5. Retrieve Notes as Mentor
    get_m_resp = client.get(f"{API_URL}/notes?mentee_id={mentee_id}", headers=m_headers)
    assert get_m_resp.status_code == 200
    notes_list = get_m_resp.json()
    assert len(notes_list) >= 1
    assert any(n["id"] == note_id for n in notes_list)

    # 6. Retrieve Notes as Mentee
    get_e_resp = client.get(f"{API_URL}/notes", headers=e_headers)
    assert get_e_resp.status_code == 200
    e_notes = get_e_resp.json()
    assert any(n["id"] == note_id for n in e_notes)

    # 7. Update Note (e.g. mark COMPLETED)
    update_resp = client.put(f"{API_URL}/notes/{note_id}", json={
        "milestone_status": "COMPLETED",
        "action_items": "- [x] Read Clean Architecture Ch. 1-3\n- [x] Set up Docker on local dev machine"
    }, headers=m_headers)
    assert update_resp.status_code == 200
    updated_note = update_resp.json()
    assert updated_note["milestone_status"] == "COMPLETED"

    # 8. Delete Note
    del_resp = client.delete(f"{API_URL}/notes/{note_id}", headers=m_headers)
    assert del_resp.status_code == 200

    # 9. Verify Deletion
    verify_get = client.get(f"{API_URL}/notes", headers=m_headers)
    assert all(n["id"] != note_id for n in verify_get.json())
