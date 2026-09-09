import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

# Enable OTP debug preview for testing
os.environ["DEBUG_OTP"] = "true"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.main import app
from backend.database import get_db, Base, engine
from backend import models, auth

client = TestClient(app)

class TestInAppMessagingFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        suffix = uuid.uuid4().hex[:6]
        cls.mentee_email = f"mentee_msg_{suffix}@example.com"
        cls.mentor_email = f"mentor_msg_{suffix}@example.com"
        cls.third_party_email = f"other_user_{suffix}@example.com"
        cls.pwd = "Password123!"

        # Create mentee
        resp1 = client.post("/api/v1/auth/signup", json={
            "email": cls.mentee_email,
            "password": cls.pwd,
            "role": "MENTEE",
            "name": "Alice Mentee"
        })
        assert resp1.status_code == 201

        # Create mentor
        resp2 = client.post("/api/v1/auth/signup", json={
            "email": cls.mentor_email,
            "password": cls.pwd,
            "role": "MENTOR",
            "name": "Dr. Bob Mentor"
        })
        assert resp2.status_code == 201

        # Create third party
        resp3 = client.post("/api/v1/auth/signup", json={
            "email": cls.third_party_email,
            "password": cls.pwd,
            "role": "MENTEE",
            "name": "Charlie Outsider"
        })
        assert resp3.status_code == 201

        # Log in and obtain tokens
        # Mentee token
        r_tok1 = client.post("/api/v1/auth/token", data={"username": cls.mentee_email, "password": cls.pwd})
        if r_tok1.json().get("two_factor_required"):
            t_tok1 = client.post("/api/v1/auth/2fa/verify", json={"challenge_token": r_tok1.json()["challenge_token"], "code": r_tok1.json()["otp_code_preview"]})
            cls.mentee_token = t_tok1.json()["access_token"]
        else:
            cls.mentee_token = r_tok1.json()["access_token"]

        # Mentor token
        r_tok2 = client.post("/api/v1/auth/token", data={"username": cls.mentor_email, "password": cls.pwd})
        if r_tok2.json().get("two_factor_required"):
            t_tok2 = client.post("/api/v1/auth/2fa/verify", json={"challenge_token": r_tok2.json()["challenge_token"], "code": r_tok2.json()["otp_code_preview"]})
            cls.mentor_token = t_tok2.json()["access_token"]
        else:
            cls.mentor_token = r_tok2.json()["access_token"]

        # Third party token
        r_tok3 = client.post("/api/v1/auth/token", data={"username": cls.third_party_email, "password": cls.pwd})
        if r_tok3.json().get("two_factor_required"):
            t_tok3 = client.post("/api/v1/auth/2fa/verify", json={"challenge_token": r_tok3.json()["challenge_token"], "code": r_tok3.json()["otp_code_preview"]})
            cls.third_token = t_tok3.json()["access_token"]
        else:
            cls.third_token = r_tok3.json()["access_token"]

        # Create an accepted Match between mentee and mentor
        db = next(get_db())
        u_mentee = db.query(models.User).filter(models.User.email == cls.mentee_email).first()
        u_mentor = db.query(models.User).filter(models.User.email == cls.mentor_email).first()
        
        match = models.Match(
            mentee_id=u_mentee.id,
            mentor_id=u_mentor.id,
            role_score=0.9,
            experience_score=0.9,
            career_stage_score=0.9,
            goals_score=0.9,
            practical_score=0.9,
            total_score=0.9,
            match_quality="Strong",
            status="ACCEPTED"
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        cls.match_id = match.id
        db.close()

    def test_01_send_message_from_mentee(self):
        resp = client.post(
            "/api/v1/messages/send",
            json={"match_id": self.match_id, "content": "Hi Dr. Bob, looking forward to our session!"},
            headers={"Authorization": f"Bearer {self.mentee_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["content"], "Hi Dr. Bob, looking forward to our session!")
        self.assertTrue(data["is_mine"])
        self.assertEqual(data["sender_name"], "Alice Mentee")
        print("PASS: Mentee sent message successfully.")

    def test_02_mentor_receives_and_checks_unread(self):
        # Check unread summary for mentor
        resp = client.get(
            "/api/v1/messages/unread-summary",
            headers={"Authorization": f"Bearer {self.mentor_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_unread"], 1)
        self.assertEqual(data["by_match"].get(self.match_id), 1)
        print("PASS: Mentor received unread notification summary.")

    def test_03_mentor_reads_and_replies(self):
        # Mentor opens conversation
        resp = client.get(
            f"/api/v1/messages/{self.match_id}",
            headers={"Authorization": f"Bearer {self.mentor_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        msgs = resp.json()
        self.assertEqual(len(msgs), 1)
        self.assertFalse(msgs[0]["is_mine"])  # Sent by mentee, not mentor

        # Mentor replies
        reply_resp = client.post(
            "/api/v1/messages/send",
            json={"match_id": self.match_id, "content": "Welcome Alice! Excited to collaborate."},
            headers={"Authorization": f"Bearer {self.mentor_token}"}
        )
        self.assertEqual(reply_resp.status_code, 200)
        self.assertTrue(reply_resp.json()["is_mine"])
        print("PASS: Mentor read message (clearing unread flag) and replied successfully.")

    def test_04_unauthorized_user_cannot_access_chat(self):
        # Charlie (third party) attempts to access chat
        resp = client.get(
            f"/api/v1/messages/{self.match_id}",
            headers={"Authorization": f"Bearer {self.third_token}"}
        )
        self.assertEqual(resp.status_code, 403)

        # Charlie attempts to send message
        send_resp = client.post(
            "/api/v1/messages/send",
            json={"match_id": self.match_id, "content": "I should not be allowed here."},
            headers={"Authorization": f"Bearer {self.third_token}"}
        )
        self.assertEqual(send_resp.status_code, 403)
        print("PASS: Unauthorized third party strictly blocked with 403 Forbidden.")

    def test_05_direct_match_email_dispatch(self):
        # Mentee sends direct email to mentor via platform
        email_resp = client.post(
            f"/api/v1/matches/{self.match_id}/send-email",
            json={
                "subject": "Scheduling: First Mentorship Session",
                "body_text": "Hi Dr. Bob, looking forward to our session next Tuesday at 2 PM UTC."
            },
            headers={"Authorization": f"Bearer {self.mentee_token}"}
        )
        self.assertEqual(email_resp.status_code, 200)
        self.assertEqual(email_resp.json()["status"], "success")
        self.assertEqual(email_resp.json()["recipient_email"], self.mentor_email)
        print("PASS: Mentee seamlessly dispatched direct email to mentor through platform backend.")

        # Mentor sends direct reply email to mentee via platform
        mentor_email_resp = client.post(
            f"/api/v1/matches/{self.match_id}/send-email",
            json={
                "subject": "Re: Scheduling: First Mentorship Session",
                "body_text": "Hi Alice, Tuesday at 2 PM UTC works perfectly. See you then!"
            },
            headers={"Authorization": f"Bearer {self.mentor_token}"}
        )
        self.assertEqual(mentor_email_resp.status_code, 200)
        self.assertEqual(mentor_email_resp.json()["status"], "success")
        self.assertEqual(mentor_email_resp.json()["recipient_email"], self.mentee_email)
        print("PASS: Mentor seamlessly dispatched direct reply email to mentee through platform backend.")

    def test_06_unauthorized_direct_email_blocked(self):
        # Charlie attempts to send email on Alice and Bob's match
        unauth_resp = client.post(
            f"/api/v1/matches/{self.match_id}/send-email",
            json={"subject": "Spam", "body_text": "Unauthorized message"},
            headers={"Authorization": f"Bearer {self.third_token}"}
        )
        self.assertEqual(unauth_resp.status_code, 403)
        print("PASS: Unauthorized user strictly blocked from sending match emails.")

if __name__ == "__main__":
    print("\n--- Test Suite: In-App Direct Messaging & Email Dispatch ---")
    unittest.main()

