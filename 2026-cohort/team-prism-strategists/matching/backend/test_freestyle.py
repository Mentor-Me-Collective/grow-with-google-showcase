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

def test_freestyle_matching():
    print("="*70)
    print("TESTING DYNAMIC REGISTRATION AND FREESTYLE TEXT MATCHING")
    print("="*70)

    suffix = uuid.uuid4().hex[:6]
    mentor_password = "password123"

    # 1. Register a new mentor with detailed bio text
    mentor_email = f"cloud_mentor_{suffix}@example.com"
    print(f"\n1. Registering new Cloud Mentor: {mentor_email}...")
    response = client.post(f"{API_URL}/auth/signup", json={
        "email": mentor_email,
        "password": mentor_password,
        "role": "MENTOR",
        "name": "Cloud Mentor Dave",
        "country": "United States",
        "dev_type": "DevOps specialist;Engineer, site reliability",
        "years_code_pro": 10.0,
        "job_factors": "Remote work options;Opportunities for professional development",
        "org_size": "100 to 499 employees",
        "additional_details": "I can help with AWS cloud architecture, Docker containers, Kubernetes deployments, and Python backend scripts."
    })
    assert response.status_code in [201, 400], f"FAIL: Mentor registration failed: {response.text}"
        
    # Log in as the new mentor
    mentor_token, _ = get_token(mentor_email, mentor_password)
    mentor_headers = {"Authorization": f"Bearer {mentor_token}"}
    mentor_profile = client.get(f"{API_URL}/users/me", headers=mentor_headers).json()
    mentor_user_id = mentor_profile["user"]["id"]
    print(f"Mentor Registered & Logged in. ID: {mentor_user_id}")

    # 2. Register a mentee specifically looking for Docker and Kubernetes in their freestyle bio
    mentee_email = f"cloud_seeking_mentee_{suffix}@example.com"
    mentee_password = "password123"
    print(f"\n2. Registering new Cloud Mentee: {mentee_email}...")
    response = client.post(f"{API_URL}/auth/signup", json={
        "email": mentee_email,
        "password": mentee_password,
        "role": "MENTEE",
        "name": "Cloud Mentee Sarah",
        "country": "United States",
        "dev_type": "Developer, full-stack",
        "years_code_pro": 1.0,
        "job_factors": "Remote work options;Opportunities for professional development",
        "org_size": "100 to 499 employees",
        "target_mentor_expertise": "AWS, Docker, Kubernetes",
        "additional_details": "Looking for guidance in AWS cloud services, Docker containerization, and learning Kubernetes."
    })
    assert response.status_code in [201, 400], f"FAIL: Mentee registration failed: {response.text}"

    # Log in as the new mentee
    mentee_token, _ = get_token(mentee_email, mentee_password)
    mentee_headers = {"Authorization": f"Bearer {mentee_token}"}
    mentee_profile = client.get(f"{API_URL}/users/me", headers=mentee_headers).json()
    print(f"Mentee Registered & Logged in. ID: {mentee_profile['user']['id']}")

    # 3. Fetch Matches for the Mentee
    print("\n3. Querying match recommendations for Cloud Mentee Sarah...")
    response = client.get(f"{API_URL}/matches?limit=100", headers=mentee_headers)
    assert response.status_code == 200, f"FAIL: Matching request failed: {response.text}"
    matches = response.json()
    print(f"Found {len(matches)} match recommendations.")

    # 4. Verify that Cloud Mentor Dave is matched with high synergy
    matched_dave = None
    for m in matches:
        if m["mentor_id"] == mentor_user_id:
            matched_dave = m
            break

    assert matched_dave is not None, "FAIL: Cloud Mentor Dave was not found in match recommendations!"
    print(f"PASS: Cloud Mentor Dave successfully matched!")
    print(f"  Match Score: {matched_dave['total_score']} ({matched_dave['match_quality']})")
    print(f"  Goals/Synergy Score: {matched_dave['goals_score']}")

    # Check that goals_score reflects the semantic text overlap
    assert matched_dave['goals_score'] > 0.4, f"FAIL: Expected significant synergy score due to Docker/Kubernetes/AWS overlap, got {matched_dave['goals_score']}"
    print("PASS: Freestyle bio text keyword synergy contributed positively to the match score.")

    print("\n" + "="*70)
    print("ALL DYNAMIC & FREESTYLE TEXT MATCHING TESTS PASSED SUCCESSFULLY!")
    print("="*70)

if __name__ == '__main__':
    test_freestyle_matching()
