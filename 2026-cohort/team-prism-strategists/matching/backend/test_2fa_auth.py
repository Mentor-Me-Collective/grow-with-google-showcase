import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable OTP debug preview for testing
os.environ["DEBUG_OTP"] = "true"

import datetime
import uuid
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, get_db
from backend import models, auth

client = TestClient(app)

def test_two_factor_auth_flow():
    print("\n--- Test Suite: Double Authentication (2FA) Sign-In ---")
    
    # 1. Sign up a new test user
    test_email = f"test_2fa_{uuid.uuid4().hex[:6]}@example.com"
    test_password = "password123!"
    
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={
            "email": test_email,
            "password": test_password,
            "role": "MENTEE",
            "name": "2FA Tester"
        }
    )
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    user_data = signup_resp.json()
    print(f"PASS: User created successfully with email: {test_email}")
    assert user_data.get("two_factor_enabled") is True
    
    # 2. Test Step 1: Sign in with correct password -> triggers 2FA challenge
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": test_email, "password": test_password}
    )
    assert login_resp.status_code == 200, f"Login step 1 failed: {login_resp.text}"
    login_data = login_resp.json()
    assert login_data.get("two_factor_required") is True, "Expected 2FA challenge requirement"
    assert "challenge_token" in login_data
    assert "otp_code_preview" in login_data
    challenge_token = login_data["challenge_token"]
    otp_code = login_data["otp_code_preview"]
    print(f"PASS: Step 1 Sign In issued 2FA challenge with OTP: {otp_code}")
    
    # 3. Test Step 2: Verify with INVALID OTP code -> should fail with 401
    bad_verify_resp = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_token": challenge_token, "code": "000000"}
    )
    assert bad_verify_resp.status_code == 401, "Expected 401 for incorrect code"
    print("PASS: Invalid 6-digit code correctly rejected with 401 Unauthorized.")
    
    # 4. Test Step 2: Verify with VALID OTP code -> returns JWT access token
    good_verify_resp = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_token": challenge_token, "code": otp_code}
    )
    assert good_verify_resp.status_code == 200, f"2FA verify failed: {good_verify_resp.text}"
    token_data = good_verify_resp.json()
    assert "access_token" in token_data
    jwt_token = token_data["access_token"]
    print(f"PASS: Step 2 2FA verification succeeded. Issued JWT access token.")
    
    # 5. Access authenticated endpoint /api/v1/users/me with JWT token
    me_resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == test_email
    print("PASS: Successfully accessed /api/v1/users/me with 2FA-verified JWT token.")
    
    # 6. Test Resend 2FA code
    resend_resp = client.post(
        "/api/v1/auth/2fa/resend",
        json={"challenge_token": challenge_token}
    )
    assert resend_resp.status_code == 200
    resend_data = resend_resp.json()
    new_challenge = resend_data["challenge_token"]
    new_otp = resend_data["otp_code_preview"]
    assert new_challenge != challenge_token
    print(f"PASS: Successfully requested new 2FA code ({new_otp}).")
    
    # 7. Test Toggle 2FA off
    toggle_resp = client.post(
        "/api/v1/auth/2fa/toggle",
        json={"enabled": False},
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert toggle_resp.status_code == 200
    assert toggle_resp.json().get("two_factor_enabled") is False
    print("PASS: Successfully toggled Double Authentication OFF.")
    
    # 8. Test Login with 2FA disabled -> directly returns JWT access token without 2FA step
    direct_login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": test_email, "password": test_password}
    )
    assert direct_login_resp.status_code == 200
    direct_data = direct_login_resp.json()
    assert direct_data.get("two_factor_required") is False
    assert direct_data.get("access_token") is not None
    print("PASS: Direct sign-in without 2FA works seamlessly when disabled.")
    
    print("\nAll Double Authentication (2FA) test cases passed successfully!\n")

if __name__ == "__main__":
    test_two_factor_auth_flow()
