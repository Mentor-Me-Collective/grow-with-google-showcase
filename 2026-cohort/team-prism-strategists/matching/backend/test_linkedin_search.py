import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from backend.database import SessionLocal, engine, Base
from backend import models, schemas
from backend.main import search_linkedin, get_mentee_linkedin_deep_link, generate_custom_linkedin_deep_link
from backend.linkedin_client import (
    build_direct_linkedin_deep_link,
    generate_linkedin_search_url,
    generate_linkedin_outreach_templates
)

def test_linkedin_deep_link_generator():
    print("\n--- Test Suite 1: Direct LinkedIn Deep Link Query Construction ---")
    
    # Case 1: Standard profile with role, skills, country, and seniority
    res1 = build_direct_linkedin_deep_link(
        role="Cloud Architect, DevOps Engineer",
        skills=["AWS", "Kubernetes", "Terraform"],
        country="United Kingdom",
        seniority="Principal",
        mentorship_intent=True,
        women_in_tech=False
    )
    print(f"Case 1 Deep Link URL: {res1['deep_link_url']}")
    print(f"Case 1 Raw Query: {res1['raw_query']}")
    assert "https://www.linkedin.com/search/results/people/?keywords=" in res1["deep_link_url"]
    assert '("Cloud Architect" OR "DevOps Engineer")' in res1["raw_query"]
    assert '(AWS OR Kubernetes OR Terraform)' in res1["raw_query"]
    assert '"United Kingdom"' in res1["raw_query"]
    assert 'Principal' in res1["raw_query"]
    assert "(mentor OR mentoring OR mentorship)" in res1["raw_query"]
    print("PASS: Case 1 correctly structured Boolean query terms.")

    # Case 2: Women in Tech / Diversity focus
    res2 = build_direct_linkedin_deep_link(
        role="Engineering Manager",
        skills=["Python", "Machine Learning"],
        country="Nigeria",
        seniority="Director",
        women_in_tech=True
    )
    print(f"Case 2 Deep Link (Women in Tech): {res2['deep_link_url']}")
    print(f"Case 2 Raw Query: {res2['raw_query']}")
    assert '"Engineering Manager"' in res2["raw_query"]
    assert '("women in tech" OR "female leader" OR "women who code")' in res2["raw_query"]
    assert '"Nigeria"' in res2["raw_query"]
    assert 'Director' in res2["raw_query"]
    print("PASS: Case 2 correctly embedded SDG 5 Women in Tech filters.")

    # Case 2b: Multi-word seniority quotes check
    res2b = build_direct_linkedin_deep_link(
        role="Product Manager",
        seniority="Head of"
    )
    assert '"Head of"' in res2b["raw_query"]
    print("PASS: Case 2b correctly quoted multi-word seniority.")

    # Case 3: Global / Any country fallback
    res3 = build_direct_linkedin_deep_link(
        role="Full Stack Developer",
        country="Any",
        mentorship_intent=True
    )
    assert '"Any"' not in res3["raw_query"]
    assert '"Full Stack Developer"' in res3["raw_query"]
    print("PASS: Case 3 correctly handled 'Any' country without polluting query.")

    # Case 4: Custom keywords & empty safety fallback
    res4 = build_direct_linkedin_deep_link(
        role="",
        skills=[],
        country=None,
        custom_keywords="fintech startups",
        mentorship_intent=False
    )
    assert "fintech startups" in res4["raw_query"]
    assert "(mentor OR mentoring OR mentorship)" not in res4["raw_query"]
    print("PASS: Case 4 handled custom keywords and disabled mentorship intent properly.")

    print("\n--- Test Suite 2: LinkedIn Outreach Message Templates ---")
    templates = generate_linkedin_outreach_templates(
        mentee_name="Ada Lovelace",
        mentee_role="Data Scientist",
        mentor_name="Dr. Amina Bello",
        tech_focus="Cloud Infrastructure & AI",
        invite_link="http://localhost:8501/?invite_code=TESTINVITE123"
    )
    
    conn_note = templates["connection_note"]
    note_len = templates["connection_note_length"]
    print(f"Connection Note ({note_len} chars): '{conn_note}'")
    assert note_len <= 300, f"Error: Connection note exceeded LinkedIn 300 char limit! Length: {note_len}"
    assert "Ada Lovelace" in conn_note
    assert "Dr. Amina Bello" in conn_note
    assert "Cloud Infrastructure & AI" in conn_note
    
    inmail = templates["inmail_message"]
    assert "TESTINVITE123" in inmail
    assert "Ada Lovelace" in inmail
    print(f"InMail Message Length: {len(inmail)} chars.")
    print("PASS: Outreach templates generated within strict LinkedIn character constraints.")

def test_linkedin_api_endpoints():
    print("\n--- Test Suite 3: FastAPI Backend Deep Link Endpoints ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    test_email = 'test_linkedin_mentee@example.com'
    user = db.query(models.User).filter(models.User.email == test_email).first()
    if not user:
        user = models.User(id='test-uuid-mentee-li', email=test_email, password_hash='hash', role='MENTEE')
        mentee = models.Mentee(
            id='test-uuid-mentee-li',
            name='Test Li Mentee',
            gender='Female',
            dev_type='Developer, back-end',
            years_code_pro=2.0,
            target_mentor_expertise='Cloud Architecture, DevOps',
            target_mentor_country='United Kingdom'
        )
        db.add(user)
        db.add(mentee)
        db.commit()

    # Test GET endpoint
    deep_link_res = get_mentee_linkedin_deep_link(
        current_user=user,
        db=db
    )
    print(f"API GET /linkedin/deep-link URL: {deep_link_res['deep_link_url']}")
    assert "https://www.linkedin.com/search/results/people/?keywords=" in deep_link_res["deep_link_url"]
    assert deep_link_res["outreach_templates"]["connection_note_length"] <= 300

    # Test POST endpoint with custom payload
    req = schemas.LinkedInDeepLinkRequest(
        role="Site Reliability Engineer",
        skills=["Kubernetes", "Go"],
        country="United Kingdom",
        seniority="Senior",
        women_in_tech=True
    )
    custom_res = generate_custom_linkedin_deep_link(req=req, current_user=user, db=db)
    print(f"API POST /linkedin/deep-link/generate URL: {custom_res['deep_link_url']}")
    assert '"Site Reliability Engineer"' in custom_res["raw_query"]
    assert '(Kubernetes OR Go)' in custom_res["raw_query"]

    # Test candidate search
    results = search_linkedin(q='Cloud Architecture', country='United Kingdom', current_user=user, db=db)
    print(f"\nRetrieved {len(results)} LinkedIn mentor candidates via curated fallback:")
    for r in results:
        print(f"  * {r['name']} ({r['tech_focus']}) - Country: {r['country']} - Compatibility: {r['match_percentage']}%")
        assert "direct_search_url" in r
    
    print("\nAll LinkedIn Deep Link and API tests passed successfully!")

if __name__ == '__main__':
    test_linkedin_deep_link_generator()
    test_linkedin_api_endpoints()
