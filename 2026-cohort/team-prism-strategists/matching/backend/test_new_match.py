import os
import sys
import uuid

os.environ["DEBUG_OTP"] = "true"

from fastapi.testclient import TestClient
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

def test_new_user_matching():
    print("="*70)
    print("TESTING DYNAMIC MATCHING FOR NEW MENTEES AND NEW MENTORS")
    print("="*70)

    suffix = uuid.uuid4().hex[:6]
    mentor_password = "password123"

    # 1. Register a new mentor
    mentor_email = f"dynamic_mentor_{suffix}@example.com"
    print(f"\n1. Registering new mentor: {mentor_email}...")
    response = client.post(f"{API_URL}/auth/signup", json={
        "email": mentor_email,
        "password": mentor_password,
        "role": "MENTOR"
    })
    assert response.status_code in [201, 400], f"FAIL: Mentor registration failed: {response.text}"
        
    # Log in as the new mentor
    mentor_token, _ = get_token(mentor_email, mentor_password)
    mentor_headers = {"Authorization": f"Bearer {mentor_token}"}
    
    # Update mentor profile to unique specifications
    print("Updating new mentor profile details...")
    client.put(f"{API_URL}/profile", json={
        "name": "Expert Mobile Mentor",
        "country": "Canada",
        "dev_type": "Developer, mobile;Engineering manager",
        "years_code_pro": 9.0,
        "job_factors": "Flex time or a flexible schedule;Remote work options",
        "org_size": "100 to 499 employees",
        "is_active": True,
        "max_mentees": 2
    }, headers=mentor_headers)

    # Fetch mentor profile to retrieve their user ID
    mentor_profile = client.get(f"{API_URL}/users/me", headers=mentor_headers).json()
    mentor_id = mentor_profile["user"]["id"]
    print(f"PASS: Mentor profile set up. DB ID: {mentor_id}")

    # 2. Register a new mentee
    mentee_email = f"dynamic_mentee_{suffix}@example.com"
    mentee_password = "password123"
    print(f"\n2. Registering new mentee: {mentee_email}...")
    response = client.post(f"{API_URL}/auth/signup", json={
        "email": mentee_email,
        "password": mentee_password,
        "role": "MENTEE"
    })
    assert response.status_code in [201, 400], f"FAIL: Mentee registration failed: {response.text}"
        
    # Log in as the new mentee
    mentee_token, _ = get_token(mentee_email, mentee_password)
    mentee_headers = {"Authorization": f"Bearer {mentee_token}"}
    
    # Update mentee profile to match the mentor's spec
    print("Updating new mentee profile details...")
    client.put(f"{API_URL}/profile", json={
        "name": "Junior Mobile Mentee",
        "country": "Canada",
        "dev_type": "Developer, mobile",  # Role matches mentor's dev_type
        "years_code_pro": 1.0,            # Experience gap is 8 years (ideal)
        "job_factors": "Remote work options",  # Goal priority matches
        "org_size": "100 to 499 employees"   # Practical fit matches
    }, headers=mentee_headers)
    print("PASS: Mentee profile set up.")

    # 3. Fetch Matches
    print("\n3. Fetching matches for the new mentee...")
    response = client.get(f"{API_URL}/matches?limit=1500", headers=mentee_headers)
    assert response.status_code == 200, f"FAIL: Fetch matches failed: {response.text}"
        
    matches = response.json()
    
    # Find our new mentor in the matches
    matched_mentor = None
    for m in matches:
        if m["mentor_id"] == mentor_id:
            matched_mentor = m
            break
            
    assert matched_mentor is not None, "FAIL: The newly registered mentor was not found in the match list."
    print(f"PASS: Brand-new mentor '{matched_mentor['mentor_name']}' was found in matches!")
    print(f"  Match Score: {matched_mentor['total_score']} | Confidence: {matched_mentor['match_quality']}")
    print(f"  Breakdown: Role: {matched_mentor['role_score']}, Exp: {matched_mentor['experience_score']}, Goals: {matched_mentor['goals_score']}, Practical: {matched_mentor['practical_score']}")
    
    # Verify score
    assert abs(matched_mentor['total_score'] - 0.775) < 1e-4, f"Expected score 0.775, got {matched_mentor['total_score']}"
    print("PASS: Match score matches the weighted scoring model calculations precisely!")
        
    # 4. Propose and accept match
    print("\n4. Proposing and accepting the connection...")
    match_id = matched_mentor["id"]
    response = client.post(f"{API_URL}/matches/action", json={
        "match_id": match_id,
        "action": "ACCEPT"
    }, headers=mentee_headers)
    assert response.status_code == 200, f"FAIL: Match acceptance failed: {response.text}"
    print("PASS: Mentee successfully accepted connection.")
        
    # 5. Check Mentor Requests Panel
    print("\n5. Checking requests history on the mentor's account...")
    response = client.get(f"{API_URL}/matches/history", headers=mentor_headers)
    assert response.status_code == 200
    history = response.json()
    mentor_received = [h for h in history if h["id"] == match_id]
    assert mentor_received and mentor_received[0]["status"] == "REQUESTED", "FAIL: Mentor did not receive requested connection."
    print(f"PASS: Mentor successfully sees connection from '{mentor_received[0]['mentee_name']}' with status 'REQUESTED'.")
        
    # 6. Mentor accepts request
    print("\n6. Mentor accepting the connection request...")
    response = client.post(f"{API_URL}/matches/action", json={
        "match_id": match_id,
        "action": "ACCEPT",
        "availability_note": "UTC_DTS:2026-08-20T14:00/2026-08-20T14:30"
    }, headers=mentor_headers)
    assert response.status_code == 200, f"FAIL: Mentor match acceptance failed: {response.text}"
    print("PASS: Mentor successfully accepted connection request.")
        
    # 7. Check final status
    response = client.get(f"{API_URL}/matches/history", headers=mentee_headers)
    assert response.status_code == 200
    history = response.json()
    final_match = [h for h in history if h["id"] == match_id]
    assert final_match and final_match[0]["status"] == "ACCEPTED", "FAIL: Match status is not ACCEPTED."
    print("PASS: Connection is now fully ACCEPTED by both parties!")
        
    print("\n" + "="*70)
    print("ALL DYNAMIC NEW USER MATCHING TESTS PASSED SUCCESSFULLY!")
    print("="*70)

if __name__ == '__main__':
    test_new_user_matching()
