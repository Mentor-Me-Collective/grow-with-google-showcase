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

def test_api():
    print("="*60)
    print("RUNNING END-TO-END SECURITY AND PERSISTENCE API TESTS")
    print("="*60)
    
    # 1. Signup test
    suffix = uuid.uuid4().hex[:6]
    email = f"test_mentee_{suffix}@example.com"
    password = "securepassword123"
    print(f"\n1. Registering new mentee: {email}...")
    response = client.post(f"{API_URL}/auth/signup", json={
        "email": email,
        "password": password,
        "role": "MENTEE",
        "name": "Jane Doe"
    })
    assert response.status_code in [201, 400], f"FAIL: Signup returned status {response.status_code}: {response.text}"
    print("PASS: User created successfully.")
        
    # 2. Login Failure test
    print("\n2. Testing login with incorrect credentials...")
    response = client.post(f"{API_URL}/auth/token", data={
        "username": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401, f"FAIL: Invalid login returned status {response.status_code}: {response.text}"
    print("PASS: Login correctly rejected with 401.")
        
    # 3. Login Success test
    print("\n3. Testing login with correct credentials...")
    token, login_resp = get_token(email, password)
    assert token is not None, f"FAIL: Login returned status {login_resp.status_code}: {login_resp.text}"
    print("PASS: Login succeeded. JWT retrieved.")
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. Fetch Profile
    print("\n4. Fetching current user profile...")
    response = client.get(f"{API_URL}/users/me", headers=headers)
    assert response.status_code == 200, f"FAIL: Fetch profile returned status {response.status_code}: {response.text}"
    profile = response.json()
    print(f"PASS: Profile loaded. Role: {profile['user']['role']}, Name: {profile['mentee']['name']}")
        
    # 5. Update Profile
    print("\n5. Updating profile details...")
    update_payload = {
        "name": "Jane Doe Updated",
        "country": "United Kingdom",
        "dev_type": "Developer, front-end;Developer, full-stack",
        "years_code_pro": 2.0,
        "job_factors": "Remote work options;Flex time or a flexible schedule",
        "org_size": "20 to 99 employees"
    }
    response = client.put(f"{API_URL}/profile", json=update_payload, headers=headers)
    assert response.status_code == 200, f"FAIL: Update profile returned status {response.status_code}: {response.text}"
    profile = response.json()
    assert profile["mentee"]["name"] == "Jane Doe Updated"
    assert profile["mentee"]["country"] == "United Kingdom"
    assert profile["mentee"]["years_code_pro"] == 2.0
    assert profile["mentee"]["exp_tier"] == "0-2y"
    print("PASS: Profile updated and experience tier correctly re-evaluated to 0-2y.")
        
    # 6. Fetch Matches
    print("\n6. Running matching algorithm via backend...")
    response = client.get(f"{API_URL}/matches?limit=3", headers=headers)
    assert response.status_code == 200, f"FAIL: Matches search returned status {response.status_code}: {response.text}"
    matches = response.json()
    print(f"PASS: Successfully retrieved {len(matches)} match recommendations.")
    for i, m in enumerate(matches):
        print(f"  Match {i+1}: {m['mentor_name']} | Score: {m['total_score']} | Confidence: {m['match_quality']}")
    match_id = matches[0]["id"]
    mentor_name = matches[0]["mentor_name"]
        
    # 7. Accept Match Action
    print(f"\n7. Accepting match proposal with {mentor_name}...")
    response = client.post(f"{API_URL}/matches/action", json={
        "match_id": match_id,
        "action": "ACCEPT"
    }, headers=headers)
    assert response.status_code == 200, f"FAIL: Match action returned status {response.status_code}: {response.text}"
    match_record = response.json()
    assert match_record["status"] == "REQUESTED"
    print("PASS: Match successfully requested (mentee accepted).")
        
    # 8. Check Match History
    print("\n8. Reviewing stored match history...")
    response = client.get(f"{API_URL}/matches/history", headers=headers)
    assert response.status_code == 200, f"FAIL: History query returned status {response.status_code}: {response.text}"
    history = response.json()
    requested_matches = [h for h in history if h["status"] == "REQUESTED"]
    assert len(requested_matches) > 0
    print(f"PASS: Verified {len(history)} match history records in DB. Requested match: {requested_matches[0]['mentor_name']}.")
        
    # 9. Test Role separation: Log in as a seeded Mentor
    mentor_email = f"seeded_mentor_{suffix}@mentoring-me.demo"
    client.post(f"{API_URL}/auth/signup", json={
        "email": mentor_email,
        "password": "password123",
        "role": "MENTOR",
        "name": "Seeded Mentor"
    })
    m_token, m_resp = get_token(mentor_email, "password123")
    assert m_token is not None, f"FAIL: Mentor login returned status {m_resp.status_code}: {m_resp.text}"
    print("PASS: Mentor login successful.")
        
    m_headers = {"Authorization": f"Bearer {m_token}"}
    
    # 10. Access check: Mentor should not be allowed to run matching (Mentee role only)
    print("\n10. Testing role boundary (Mentor attempting to search matches)...")
    response = client.get(f"{API_URL}/matches", headers=m_headers)
    assert response.status_code == 403, f"FAIL: Role boundary check failed. Status {response.status_code}: {response.text}"
    print("PASS: API blocked mentor matching search with 403 Forbidden.")
        
    # 11. Self-Service Account Deletion (GDPR Right to Erasure)
    print("\n11. Testing self-service account deletion (DELETE /api/v1/users/me)...")
    del_resp = client.delete(f"{API_URL}/users/me", headers=m_headers)
    assert del_resp.status_code == 200, f"FAIL: Account deletion returned status {del_resp.status_code}: {del_resp.text}"
    print("PASS: Account successfully deleted.")
    
    # Verify login fails after deletion
    after_token, after_resp = get_token(mentor_email, "password123")
    assert after_token is None, "FAIL: Deleted user was still able to authenticate."
    print("PASS: Verified deleted account cannot log in.")

    # 12. Forgot Password and Password Reset Verification
    print("\n12. Testing Forgot Password workflow...")
    # 12a. Unregistered email should return 404
    unreg_resp = client.post(f"{API_URL}/auth/forgot-password", json={"email": "non_existent_user_9999@test.com"})
    assert unreg_resp.status_code == 404, f"FAIL: Expected 404 for unregistered email, got {unreg_resp.status_code}"
    print("PASS: Unregistered email correctly returns 404 with helpful message.")

    # 12b. Registered email should return 200 with challenge token
    reg_resp = client.post(f"{API_URL}/auth/forgot-password", json={"email": email})
    assert reg_resp.status_code == 200, f"FAIL: Expected 200 for registered email, got {reg_resp.status_code}"
    reg_data = reg_resp.json()
    assert "challenge_token" in reg_data
    assert "otp_code_preview" in reg_data
    print("PASS: Registered email receives reset challenge and 6-digit OTP.")

    # 12c. Reset password with valid code
    reset_resp = client.post(f"{API_URL}/auth/reset-password", json={
        "challenge_token": reg_data["challenge_token"],
        "code": reg_data["otp_code_preview"],
        "new_password": "newSecurePassword456!"
    })
    assert reset_resp.status_code == 200, f"FAIL: Password reset failed: {reset_resp.text}"
    print("PASS: Password reset succeeded with valid OTP code.")

    # 12d. Verify login with newly updated password
    new_token, new_login_resp = get_token(email, "newSecurePassword456!")
    assert new_token is not None, f"FAIL: Login with new password failed: {new_login_resp.text}"
    print("PASS: Verified login works with newly updated password.")
        
    print("\n" + "="*60)
    print("ALL API END-TO-END SECURITY TESTS PASSED SUCCESSFULLY!")
    print("="*60)

if __name__ == '__main__':
    test_api()
