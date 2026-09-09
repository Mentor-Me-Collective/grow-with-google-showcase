import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend import models, database, auth

client = TestClient(app)

class TestOutreachHubAPIs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = database.SessionLocal()
        cls.test_email = "outreach_test_mentee@example.com"
        cls.test_password = "Password123!"
        
        # Cleanup
        existing_user = db.query(models.User).filter(models.User.email == cls.test_email).first()
        if existing_user:
            db.query(models.Mentee).filter(models.Mentee.id == existing_user.id).delete()
            db.query(models.User).filter(models.User.id == existing_user.id).delete()
            db.commit()
        
        # Create Mentee
        user = models.User(
            email=cls.test_email,
            password_hash=auth.get_password_hash(cls.test_password),
            role="MENTEE",
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        mentee = models.Mentee(
            id=user.id,
            name="Test Outreach Mentee",
            country="United Kingdom",
            dev_type="Developer, full-stack;Developer, back-end",
            years_code_pro=2,
            target_mentor_expertise="Python;Cloud;AI",
            target_mentor_country="United Kingdom",
            target_mentor_min_years=5
        )
        db.add(mentee)
        db.commit()
        
        cls.token = auth.create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        db.close()

    def test_01_github_outreach_search(self):
        resp = client.get("/api/v1/github/search?q=python+cloud&country=United+Kingdom", headers=self.headers)
        self.assertEqual(resp.status_code, 200, f"GitHub search failed: {resp.text}")
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("name", data[0])
        self.assertIn("match_percentage", data[0])
        print(f"PASS: GitHub Outreach returned {len(data)} candidates. Sample: {data[0]['name']} ({data[0]['match_percentage']}%)")

    def test_02_orcid_outreach_search(self):
        resp = client.get("/api/v1/orcid/search?q=machine+learning&country=United+Kingdom", headers=self.headers)
        self.assertEqual(resp.status_code, 200, f"ORCID search failed: {resp.text}")
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("name", data[0])
        self.assertIn("match_percentage", data[0])
        print(f"PASS: ORCID Outreach returned {len(data)} researchers. Sample: {data[0]['name']} ({data[0]['match_percentage']}%)")

    def test_03_linkedin_outreach_search(self):
        resp = client.get("/api/v1/linkedin/search?q=data+science&country=United+Kingdom", headers=self.headers)
        self.assertEqual(resp.status_code, 200, f"LinkedIn search failed: {resp.text}")
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("name", data[0])
        self.assertIn("match_percentage", data[0])
        print(f"PASS: LinkedIn Outreach returned {len(data)} mentors. Sample: {data[0]['name']} ({data[0]['match_percentage']}%)")

    def test_04_linkedin_deep_link_generation(self):
        resp = client.get("/api/v1/linkedin/deep-link", headers=self.headers)
        self.assertEqual(resp.status_code, 200, f"LinkedIn deep link failed: {resp.text}")
        data = resp.json()
        self.assertIn("deep_link_url", data)
        self.assertIn("outreach_templates", data)
        self.assertIn("https://www.linkedin.com/search/results/people/", data["deep_link_url"])
        print(f"PASS: LinkedIn 1-Click Deep Link URL: {data['deep_link_url'][:65]}...")
        print(f"PASS: Connection Note generated ({len(data['outreach_templates']['connection_note'])} chars)")

if __name__ == "__main__":
    unittest.main()
