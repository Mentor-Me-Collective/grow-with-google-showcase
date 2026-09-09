import os
import re
import html
import requests
import datetime
import urllib.parse
import urllib3
from dotenv import load_dotenv

load_dotenv()
from . import models, profile_evaluator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Seed directory of realistic public technical profiles for fallback / demo mode
DEMO_LINKEDIN_MENTORS = [
    {
        "name": "Dr. Amina Bello",
        "title": "VP of Engineering & Cloud Infrastructure",
        "company": "Flutterwave",
        "country": "Nigeria",
        "contact": "https://www.linkedin.com/in/amina-bello-eng",
        "skills": ["Cloud Architecture", "DevOps", "Kubernetes", "Engineering Leadership", "GCP", "Distributed Systems"],
        "years_experience": 14.0,
        "bio": "14+ years scaling high-availability fintech platforms across EMEA. Passionate about empowering women in technical leadership and cloud engineering."
    },
    {
        "name": "Sarah Jenkins",
        "title": "Principal Technical Program Manager (TPM)",
        "company": "Amazon Web Services (AWS)",
        "country": "United Kingdom",
        "contact": "https://www.linkedin.com/in/sarah-jenkins-tpm",
        "skills": ["Technical Program Management", "Cloud Architecture", "Agile", "Enterprise Systems", "AWS"],
        "years_experience": 11.0,
        "bio": "Leading multi-region cloud infrastructure migration programs. Mentor for early-career women transitioning into technical program management."
    },
    {
        "name": "Elena Rostova",
        "title": "Head of Data Engineering & AI Strategy",
        "company": "DeepMind Partner Lab",
        "country": "United Kingdom",
        "contact": "https://www.linkedin.com/in/elena-rostova-data",
        "skills": ["Data Engineering", "Machine Learning", "Python", "Data Governance", "Spark", "AI Strategy"],
        "years_experience": 9.5,
        "bio": "Specialized in large-scale ETL pipelines, streaming architectures, and ML lifecycle. Active mentor for women entering data science and engineering."
    },
    {
        "name": "Ngozi Eze",
        "title": "Chief Information Security Officer (CISO)",
        "company": "Interswitch Group",
        "country": "Nigeria",
        "contact": "https://www.linkedin.com/in/ngozi-eze-security",
        "skills": ["Cybersecurity", "Cloud Security", "DevSecOps", "Compliance", "Identity Management", "Risk Assessment"],
        "years_experience": 13.0,
        "bio": "Building robust cyber defense and compliance postures for financial infrastructure. Advocate for women in cybersecurity and threat intelligence."
    },
    {
        "name": "Maya Patel",
        "title": "Director of Product Architecture & Mobile Systems",
        "company": "Revolut",
        "country": "United Kingdom",
        "contact": "https://www.linkedin.com/in/maya-patel-arch",
        "skills": ["System Architecture", "Microservices", "Product Strategy", "Mobile Architecture", "Fintech"],
        "years_experience": 10.0,
        "bio": "Guiding cross-functional engineering teams in building microservice backends. Passionate about helping women land senior and lead technical roles."
    },
    {
        "name": "Folake Adeleke",
        "title": "Senior Solutions Architect",
        "company": "Microsoft",
        "country": "Nigeria",
        "contact": "https://www.linkedin.com/in/folake-adeleke-azure",
        "skills": ["Azure", "Cloud Architecture", "Enterprise Architecture", "DevOps", "Terraform"],
        "years_experience": 8.0,
        "bio": "Designing modern enterprise cloud solutions and hybrid migrations. Dedicated mentor supporting women in STEM and cloud certifications."
    },
    {
        "name": "Clara Dubois",
        "title": "Staff Site Reliability Engineer (SRE)",
        "company": "Spotify",
        "country": "France",
        "contact": "https://www.linkedin.com/in/clara-dubois-sre",
        "skills": ["Site Reliability Engineering", "Observability", "Linux", "Kubernetes", "Go", "Incident Management"],
        "years_experience": 8.5,
        "bio": "SRE practitioner focused on latency reduction, chaos engineering, and system resilience. Regular speaker and mentor for women in tech."
    },
    {
        "name": "Zainab Al-Hassan",
        "title": "Lead Quality Assurance & Test Automation Architect",
        "company": "Paystack",
        "country": "Ghana",
        "contact": "https://www.linkedin.com/in/zainab-alhassan-qa",
        "skills": ["Test Automation", "CI/CD", "Quality Assurance", "Selenium", "API Testing", "Python"],
        "years_experience": 7.0,
        "bio": "Architecting automated testing frameworks for high-volume payments. Dedicated to mentoring women beginning tech careers in quality engineering."
    }
]

def parse_linkedin_title(raw_title: str):
    """
    Extracts name, role and company from a standard LinkedIn Google title format:
    e.g. "Amaka Okonkwo - Senior Cloud Engineer - MTN Group | LinkedIn"
    """
    cleaned = raw_title.replace(" | LinkedIn", "").replace(" - LinkedIn", "")
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if not parts:
        parts = [p.strip() for p in cleaned.split(" – ") if p.strip()]
        
    name = parts[0] if parts else "LinkedIn Professional"
    role_company = " · ".join(parts[1:]) if len(parts) > 1 else "Technical Leader"
    return name, role_company

def generate_linkedin_outreach_templates(
    mentee_name: str = "Mentee",
    mentee_role: str = "Software Engineer",
    mentor_name: str = "Mentor",
    tech_focus: str = "Tech Leadership",
    invite_link: str = None
):
    """
    Generates ready-to-use LinkedIn outreach messages:
    1. Short Connection Request Note (strictly within LinkedIn's 300 character limit).
    2. Full InMail / Direct Message template for deeper engagement.
    """
    if not invite_link:
        base = os.getenv("APP_BASE_URL") or os.getenv("FRONTEND_URL") or "http://localhost:8501"
        invite_link = f"{base.rstrip('/')}/?invite_code=PENDING"
    m_name = mentor_name.strip() if mentor_name else "there"
    me_name = mentee_name.strip() if mentee_name else "A Mentee"
    focus = tech_focus.strip() if tech_focus else "your field"
    role = mentee_role.strip() if mentee_role else "Software Engineering"
    
    # 1. Connection Request Note (LinkedIn max is 300 characters)
    # Draft a concise, high-conversion note:
    note_candidate = f"Hi {m_name}, inspired by your work in {focus}. I'm an early-career {role} and would love to connect to learn from your career journey. Best, {me_name}"
    if len(note_candidate) > 295:
        note_candidate = f"Hi {m_name}, inspired by your work in {focus}. I'd value connecting with experienced leaders in this field. Best, {me_name}"
    if len(note_candidate) > 295:
        note_candidate = f"Hi {m_name}, I'd love to connect and follow your work in {focus}. Best, {me_name}"
        
    # 2. Comprehensive InMail / Message Template
    inmail_candidate = (
        f"Hi {m_name},\n\n"
        f"I came across your profile and was really inspired by your leadership and expertise in {focus}.\n\n"
        f"I am currently an early-career technologist developing my skills in {role}, and I am seeking guidance from experienced mentors to navigate this career path effectively.\n\n"
        f"If your schedule permits, I would be deeply grateful for the opportunity to connect for a brief 15-20 minute chat or periodic mentoring.\n\n"
        f"I am also using the Mentor Me platform to organise mentoring goals and scheduling:\n"
        f"{invite_link}\n\n"
        f"Thank you so much for your time and for giving back to the community!\n\n"
        f"Warm regards,\n{me_name}"
    )

    return {
        "connection_note": note_candidate,
        "connection_note_length": len(note_candidate),
        "inmail_message": inmail_candidate
    }

def build_direct_linkedin_deep_link(
    role: str = "",
    skills: list = None,
    country: str = None,
    seniority: str = None,
    mentorship_intent: bool = True,
    women_in_tech: bool = False,
    custom_keywords: str = ""
) -> dict:
    """
    Constructs a precision LinkedIn People Search Deep Link URL with Boolean query filters.
    
    A LinkedIn Deep Link dynamically opens LinkedIn's native search engine with pre-filled filters
    based on the mentee's exact profile and goals (Target Role, Country, Skills, Seniority, Diversity).
    """
    query_parts = []
    breakdown = {}

    # 1. Role / Title filter
    clean_roles = []
    if role and role.strip():
        # Split on commas or semicolons
        raw_roles = [r.strip() for r in role.replace(";", ",").split(",") if r.strip()]
        for r in raw_roles:
            if " " in r:
                clean_roles.append(f'"{r}"')
            else:
                clean_roles.append(r)
        if clean_roles:
            if len(clean_roles) == 1:
                query_parts.append(clean_roles[0])
            else:
                query_parts.append(f"({' OR '.join(clean_roles[:3])})")
    breakdown["roles"] = clean_roles

    # 2. Skills / Technologies
    clean_skills = []
    if skills:
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.replace(";", ",").split(",") if s.strip()]
        for s in skills:
            s_clean = s.strip()
            if s_clean:
                clean_skills.append(f'"{s_clean}"' if " " in s_clean else s_clean)
        if clean_skills:
            if len(clean_skills) == 1:
                query_parts.append(clean_skills[0])
            else:
                query_parts.append(f"({' OR '.join(clean_skills[:4])})")
    breakdown["skills"] = clean_skills

    # 3. Seniority level
    if seniority and seniority.strip() and seniority.strip().lower() not in ("any", "none", "all"):
        sen_clean = seniority.strip()
        if sen_clean.lower() in ("senior", "lead", "principal", "director", "vp", "head of"):
            query_parts.append(f'"{sen_clean}"' if " " in sen_clean else sen_clean)
            breakdown["seniority"] = sen_clean
        else:
            query_parts.append(sen_clean)
            breakdown["seniority"] = sen_clean
    else:
        breakdown["seniority"] = None

    # 4. Women in Tech / Diversity focus (SDG 5)
    if women_in_tech:
        query_parts.append('("women in tech" OR "female leader" OR "women who code")')
        breakdown["women_in_tech"] = True
    else:
        breakdown["women_in_tech"] = False

    # 5. Country / Location
    if country and country.strip() and country.strip().lower() not in ("any", "international", "global", "all"):
        c_clean = country.strip()
        query_parts.append(f'"{c_clean}"')
        breakdown["country"] = c_clean
    else:
        breakdown["country"] = None

    # 6. Custom additional keywords
    if custom_keywords and custom_keywords.strip():
        ck_clean = custom_keywords.strip()
        query_parts.append(ck_clean)
        breakdown["custom_keywords"] = ck_clean
    else:
        breakdown["custom_keywords"] = None

    # 7. Mentorship Intent keywords
    if mentorship_intent:
        query_parts.append("(mentor OR mentoring OR mentorship)")
        breakdown["mentorship_intent"] = True
    else:
        breakdown["mentorship_intent"] = False

    raw_query = " ".join(query_parts).strip()
    if not raw_query:
        raw_query = "software engineer mentor"

    encoded = urllib.parse.quote_plus(raw_query)
    deep_link_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded}"

    outreach = generate_linkedin_outreach_templates(
        tech_focus=clean_roles[0].replace('"', '') if clean_roles else (clean_skills[0].replace('"', '') if clean_skills else "Engineering Leadership")
    )

    return {
        "deep_link_url": deep_link_url,
        "raw_query": raw_query,
        "query_breakdown": breakdown,
        "outreach_templates": outreach
    }

def generate_linkedin_search_url(
    keyword: str = "",
    country: str = None,
    skills: list = None,
    seniority: str = None,
    women_in_tech: bool = False
) -> str:
    """
    Generates a targeted, direct LinkedIn People Search Deep Link URL
    with pre-filled search parameters for live, real-time mentor candidate discovery.
    """
    result = build_direct_linkedin_deep_link(
        role=keyword,
        skills=skills,
        country=country,
        seniority=seniority,
        women_in_tech=women_in_tech
    )
    return result["deep_link_url"]

def search_linkedin_mentors(keyword: str, country: str, mentee: models.Mentee):
    """
    Public LinkedIn discovery engine: searches public LinkedIn profiles via search index
    and evaluates match compatibility with mentee goals and preferences.
    """
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_CX")
    deep_link = generate_linkedin_search_url(keyword=keyword, country=country)

    # If Google Custom Search is configured, query live API
    if api_key and cse_id:
        try:
            q_clean = keyword.replace(",", " ").replace(";", " ")
            query = f'site:linkedin.com/in "{q_clean}"'
            if country and country.lower() != "any":
                query += f' "{country}"'
                
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": cse_id,
                "q": query,
                "num": 5
            }
            res = requests.get(search_url, params=params, timeout=10, verify=False)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                candidates = []
                for it in items:
                    raw_title = it.get("title", "")
                    link = it.get("link", "")
                    snippet = it.get("snippet", "")
                    
                    if "linkedin.com/in/" not in link:
                        continue
                        
                    name, role_info = parse_linkedin_title(raw_title)
                    
                    # Extract skills from snippet + title
                    full_text = f"{raw_title} {snippet}".lower()
                    possible_skills = [
                        "cloud architecture", "devops", "kubernetes", "aws", "gcp", "azure", 
                        "python", "javascript", "react", "machine learning", "data engineering", 
                        "cybersecurity", "technical program management", "agile", "microservices", 
                        "system architecture", "fintech", "test automation", "engineering leadership"
                    ]
                    found_skills = [s.title() for s in possible_skills if s in full_text]
                    if not found_skills:
                        found_skills = [role_info]
                        
                    cand_obj = {
                        "name": name,
                        "contact": link,
                        "country": country if country else "International",
                        "skills": found_skills,
                        "years_experience": 7.0
                    }
                    
                    pct, justs = profile_evaluator.calculate_match_score_and_justifications(cand_obj, mentee)
                    
                    candidates.append({
                        "name": name,
                        "contact": link,
                        "country": cand_obj["country"],
                        "tech_focus": f"{role_info} ({', '.join(found_skills[:3])})",
                        "match_percentage": pct,
                        "justifications": justs,
                        "public_email": None,
                        "linkedin_url": link,
                        "direct_search_url": deep_link,
                        "other_urls": []
                    })
                    
                if candidates:
                    return candidates
        except Exception as e:
            print(f"[LinkedIn Search Live API Error]: {e}")

    # Fallback / Built-in curated search over technical leaders
    kw_words = [w.strip().lower() for w in keyword.replace(",", " ").replace(";", " ").split() if w.strip()]
    c_target = country.strip().lower() if (country and country.lower() != "any") else None

    scored_list = []
    for cand in DEMO_LINKEDIN_MENTORS:
        cand_text = f"{cand['name']} {cand['title']} {cand['company']} {' '.join(cand['skills'])} {cand['bio']}".lower()
        
        # Check keyword match
        kw_match = any(w in cand_text for w in kw_words) if kw_words else True
        # Check country filter
        country_match = True
        if c_target:
            cand_country = cand["country"].lower()
            country_match = (c_target in cand_country) or (cand_country in c_target)
            
        cand_score_base = 0
        if kw_match:
            cand_score_base += 50
        if country_match:
            cand_score_base += 30

        cand_obj = {
            "name": cand["name"],
            "contact": cand["contact"],
            "country": cand["country"],
            "skills": cand["skills"],
            "years_experience": cand["years_experience"]
        }
        pct, justs = profile_evaluator.calculate_match_score_and_justifications(cand_obj, mentee)
        
        scored_list.append({
            "name": cand["name"],
            "contact": cand["contact"],
            "country": cand["country"],
            "tech_focus": f"{cand['title']} @ {cand['company']}",
            "match_percentage": pct,
            "justifications": justs,
            "public_email": None,
            "linkedin_url": cand["contact"],
            "direct_search_url": deep_link,
            "other_urls": [],
            "_sort_key": pct + (20 if kw_match else 0) + (10 if country_match else 0)
        })

    # Sort candidates by best compatibility
    scored_list.sort(key=lambda x: x["_sort_key"], reverse=True)
    
    # Return top matches
    cleaned_results = []
    for item in scored_list[:5]:
        res_item = item.copy()
        res_item.pop("_sort_key", None)
        cleaned_results.append(res_item)
        
    return cleaned_results
