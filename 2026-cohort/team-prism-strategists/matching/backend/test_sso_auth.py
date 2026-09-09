"""
Unit Test Suite for Single Sign-On (SSO) Authentication (Google & Facebook)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import uuid
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, get_db
from backend import models, auth

client = TestClient(app)

def test_sso_auth_flow():
    print("\n--- Test Suite: Google & Facebook Single Sign-On (SSO) ---")
    
    # 0. Test that Unregistered Google User cannot Sign-In without prior Sign-Up
    unreg_email = f"unreg_user_{uuid.uuid4().hex[:6]}@gmail.com"
    sso_unreg_signin = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": unreg_email,
            "mode": "signin"
        }
    )
    assert sso_unreg_signin.status_code == 404
    assert "No account found for this Google email" in sso_unreg_signin.json()["detail"]
    print("PASS: Unregistered Google user attempting sign-in is properly blocked with 404.")

    # 1. Test Google SSO Sign-Up as Mentee (Create Account mode)
    g_email = f"google_user_{uuid.uuid4().hex[:6]}@gmail.com"
    g_name = "Maya Google User"
    g_pic = "https://lh3.googleusercontent.com/a/mock_avatar_google"
    g_oauth_id = f"google_oauth_{uuid.uuid4().hex[:8]}"
    
    sso_g_signup = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": g_email,
            "name": g_name,
            "picture": g_pic,
            "oauth_id": g_oauth_id,
            "role": "MENTEE",
            "mode": "signup"
        }
    )
    assert sso_g_signup.status_code == 200, f"Google SSO Sign-up failed: {sso_g_signup.text}"
    g_data = sso_g_signup.json()
    assert g_data["is_new_user"] is True
    assert g_data["provider"] == "Google"
    assert g_data["role"] == "MENTEE"
    assert "access_token" in g_data
    g_token = g_data["access_token"]
    print(f"PASS: Google SSO Sign-Up created Mentee: {g_email}")
    
    # 2. Test Google SSO Sign-In (Existing User)
    sso_g_signin = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": g_email,
            "oauth_id": g_oauth_id,
            "mode": "signin"
        }
    )
    assert sso_g_signin.status_code == 200
    g_signin_data = sso_g_signin.json()
    assert g_signin_data["is_new_user"] is False
    assert g_signin_data["email"] == g_email
    print(f"PASS: Google SSO Sign-In successfully authenticated existing user.")
    
    # 3. Test accessing /api/v1/users/me with Google SSO token
    me_resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {g_token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == g_email
    assert me_data["user"]["auth_provider"] == "GOOGLE"
    assert me_data["mentee"]["name"] == g_name
    print(f"PASS: Mentee profile auto-populated with Google name and avatar.")
    
    # 4. Test Facebook SSO Sign-Up as Mentor
    fb_email = f"fb_mentor_{uuid.uuid4().hex[:6]}@facebook.com"
    fb_name = "Sarah Facebook Mentor"
    fb_pic = "https://graph.facebook.com/v12.0/mock_avatar/picture"
    fb_oauth_id = f"fb_oauth_{uuid.uuid4().hex[:8]}"
    
    sso_fb_signup = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "facebook",
            "email": fb_email,
            "name": fb_name,
            "picture": fb_pic,
            "oauth_id": fb_oauth_id,
            "role": "MENTOR",
            "mode": "signup"
        }
    )
    assert sso_fb_signup.status_code == 200, f"Facebook SSO Sign-up failed: {sso_fb_signup.text}"
    fb_data = sso_fb_signup.json()
    assert fb_data["is_new_user"] is True
    assert fb_data["provider"] == "Facebook"
    assert fb_data["role"] == "MENTOR"
    fb_token = fb_data["access_token"]
    print(f"PASS: Facebook SSO Sign-Up created Mentor: {fb_email}")
    
    # 5. Test Facebook SSO Sign-In (Existing Mentor)
    sso_fb_signin = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "facebook",
            "email": fb_email,
            "oauth_id": fb_oauth_id,
            "mode": "signin"
        }
    )
    assert sso_fb_signin.status_code == 200
    assert sso_fb_signin.json()["is_new_user"] is False
    print(f"PASS: Facebook SSO Sign-In successfully authenticated existing mentor.")
    
    # 6. Test OAuth Authorize URL generation (Google & Facebook)
    g_url_resp = client.get("/api/v1/auth/sso/authorize-url?provider=google&role=MENTEE&mode=signup")
    assert g_url_resp.status_code == 200
    assert "google" in g_url_resp.json()["auth_url"].lower()
    print("PASS: Google OAuth redirection URL successfully generated.")

    fb_url_resp = client.get("/api/v1/auth/sso/authorize-url?provider=facebook&role=MENTOR&mode=signup")
    assert fb_url_resp.status_code == 200
    assert "facebook" in fb_url_resp.json()["auth_url"].lower()
    print("PASS: Facebook OAuth redirection URL successfully generated.")

    # 7. Test OAuth Redirection Callback endpoint with mocked Google exchange
    from unittest.mock import patch, MagicMock
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "mock_google_access_token"}
        mock_post.return_value = mock_token_resp

        cb_email = f"cb_user_{uuid.uuid4().hex[:6]}@gmail.com"
        cb_oauth_id = f"google_cb_{uuid.uuid4().hex[:8]}"
        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "email": cb_email,
            "name": "Callback User",
            "picture": "https://lh3.googleusercontent.com/mock",
            "sub": cb_oauth_id
        }
        mock_get.return_value = mock_userinfo_resp

        cb_resp = client.post(
            "/api/v1/auth/sso/callback",
            json={
                "provider": "google",
                "code": "4/0AbCdEf1234567890",
                "redirect_uri": "http://localhost:8501",
                "role": "MENTEE",
                "mode": "signup"
            }
        )
        assert cb_resp.status_code == 200
        assert "access_token" in cb_resp.json()
        print("PASS: OAuth Callback exchange successfully issued JWT token without manual inputs.")

    # 9. Test Google SSO Sign-Up as Mentor (Create Account mode)
    g_mentor_email = f"google_mentor_{uuid.uuid4().hex[:6]}@gmail.com"
    g_mentor_name = "Alex Google Mentor"
    g_mentor_pic = "https://lh3.googleusercontent.com/a/mock_mentor_avatar"
    g_mentor_oauth_id = f"google_oauth_{uuid.uuid4().hex[:8]}"
    
    sso_g_mentor_signup = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": g_mentor_email,
            "name": g_mentor_name,
            "picture": g_mentor_pic,
            "oauth_id": g_mentor_oauth_id,
            "role": "MENTOR",
            "mode": "signup"
        }
    )
    assert sso_g_mentor_signup.status_code == 200, f"Google Mentor Sign-up failed: {sso_g_mentor_signup.text}"
    gm_data = sso_g_mentor_signup.json()
    assert gm_data["is_new_user"] is True
    assert gm_data["provider"] == "Google"
    assert gm_data["role"] == "MENTOR"
    assert "access_token" in gm_data
    gm_token = gm_data["access_token"]
    
    gm_me_resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {gm_token}"}
    )
    assert gm_me_resp.status_code == 200
    gm_me_data = gm_me_resp.json()
    assert gm_me_data["user"]["role"] == "MENTOR"
    assert gm_me_data["mentor"] is not None
    assert gm_me_data["mentor"]["name"] == g_mentor_name
    print(f"PASS: Google SSO Sign-Up created Mentor with Mentor profile: {g_mentor_email}")

    # 10. Test Google SSO Sign-In as Mentor
    sso_gm_signin = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": g_mentor_email,
            "oauth_id": g_mentor_oauth_id,
            "role": "MENTOR",
            "mode": "signin"
        }
    )
    assert sso_gm_signin.status_code == 200
    gm_signin_data = sso_gm_signin.json()
    assert gm_signin_data["is_new_user"] is False
    assert gm_signin_data["role"] == "MENTOR"
    print(f"PASS: Google SSO Sign-In as Mentor preserved/returned MENTOR role.")

    # 11. Test strict role separation: A Mentee cannot re-register as a Mentor using the same Google email
    existing_mentee_email = f"strict_mentee_{uuid.uuid4().hex[:6]}@gmail.com"
    # First register as Mentee
    s1 = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": existing_mentee_email,
            "name": "Strict Mentee",
            "role": "MENTEE",
            "mode": "signup"
        }
    )
    assert s1.status_code == 200
    assert s1.json()["role"] == "MENTEE"
    
    # Now user tries to register as Mentor with the same email
    s2 = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": existing_mentee_email,
            "name": "Strict Mentee",
            "role": "MENTOR",
            "mode": "signup"
        }
    )
    assert s2.status_code == 400
    assert "already registered as a Mentee" in s2.json()["detail"]
    print(f"PASS: Re-registering Mentee as Mentor strictly blocked: {s2.json()['detail']}")

    # 12. Test strict role separation on sign-in: Mentee attempting to sign in selecting Mentor role
    s3 = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": existing_mentee_email,
            "role": "MENTOR",
            "mode": "signin"
        }
    )
    assert s3.status_code == 400
    assert "registered as a Mentee, not a Mentor" in s3.json()["detail"]
    print(f"PASS: Signing in with wrong role mismatch strictly blocked: {s3.json()['detail']}")

    # 13. Signing in with correct Mentee role succeeds
    s4 = client.post(
        "/api/v1/auth/sso",
        json={
            "provider": "google",
            "email": existing_mentee_email,
            "role": "MENTEE",
            "mode": "signin"
        }
    )
    assert s4.status_code == 200
    assert s4.json()["role"] == "MENTEE"
    print("PASS: Signing in with matching Mentee role succeeds.")

    print("\nAll Google & Facebook SSO test cases passed successfully!\n")

if __name__ == "__main__":
    test_sso_auth_flow()

