import os
import sys
import unittest
import uuid
import jwt
from fastapi.testclient import TestClient

# Enable OTP debug preview for testing
os.environ["DEBUG_OTP"] = "true"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.main import app
from backend.database import get_db, Base, engine
from backend import models, auth

client = TestClient(app)

class TestPasswordResetFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.test_email = f"reset_test_{uuid.uuid4().hex[:6]}@example.com"
        cls.initial_pass = "InitialPass123!"
        cls.new_pass = "NewSecurePass456@"
        
        # Create test user
        resp = client.post("/api/v1/auth/signup", json={
            "email": cls.test_email,
            "password": cls.initial_pass,
            "role": "MENTEE",
            "name": "Reset Test User"
        })
        assert resp.status_code == 201, f"User creation failed: {resp.text}"

    def test_01_forgot_password_unknown_email(self):
        resp = client.post("/api/v1/auth/forgot-password", json={
            "email": "nonexistent_user_999@example.com"
        })
        # Should return 200 with generic message to prevent user enumeration
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("If an account exists", data.get("message", ""))
        self.assertEqual(data.get("challenge_token"), "")
        print("PASS: Unknown email returns generic 200 response (anti-enumeration).")

    def test_02_forgot_password_success(self):
        resp = client.post("/api/v1/auth/forgot-password", json={
            "email": self.test_email
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("challenge_token", data)
        self.assertIn("otp_code_preview", data)
        TestPasswordResetFlow.challenge_token = data["challenge_token"]
        TestPasswordResetFlow.otp_code = data["otp_code_preview"]
        print(f"PASS: Forgot password initiated. OTP: {data['otp_code_preview']}")

    def test_03_reset_password_invalid_code(self):
        resp = client.post("/api/v1/auth/reset-password", json={
            "challenge_token": self.challenge_token,
            "code": "000000",
            "new_password": self.new_pass
        })
        self.assertEqual(resp.status_code, 400)
        print("PASS: Invalid 6-digit reset code correctly rejected with 400 Bad Request.")

    def test_04_reset_password_success(self):
        resp = client.post("/api/v1/auth/reset-password", json={
            "challenge_token": self.challenge_token,
            "code": self.otp_code,
            "new_password": self.new_pass
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        print("PASS: Password successfully reset with valid OTP.")

    def test_05_login_with_new_password(self):
        # Old password should fail
        resp_old = client.post("/api/v1/auth/token", data={
            "username": self.test_email,
            "password": self.initial_pass
        })
        self.assertEqual(resp_old.status_code, 401)
        print("PASS: Old password rejected.")

        # New password should succeed
        resp_new = client.post("/api/v1/auth/token", data={
            "username": self.test_email,
            "password": self.new_pass
        })
        self.assertEqual(resp_new.status_code, 200)
        print("PASS: Successfully authenticated with newly reset password.")

if __name__ == "__main__":
    print("\n--- Test Suite: Password Reset Flow ---")
    unittest.main()
