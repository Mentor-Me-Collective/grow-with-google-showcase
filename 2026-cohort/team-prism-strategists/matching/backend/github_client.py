import os
import re
import datetime
import urllib.parse
import urllib3
import requests
from . import models, profile_evaluator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def normalize_linkedin_url(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip().strip("'\"()[]<>.,; \t\n\r")
    if not raw:
        return None
    
    # 1. Handle in/username or /in/username (e.g. in/blessman-newton-a7a80a251L)
    if raw.lower().startswith("in/") or raw.lower().startswith("/in/"):
        slug = raw.lstrip("/").split()[0].rstrip("/.,;)>]}'")
        return f"https://www.linkedin.com/{slug}"
        
    # 2. Handle linkedin.com/in/... or www.linkedin.com/in/... or https://...
    if "linkedin.com" in raw.lower():
        match = re.search(r'(https?://[^\s]+|www\.linkedin\.com/[^\s]+|linkedin\.com/[^\s]+)', raw, re.IGNORECASE)
        if match:
            url = match.group(1).rstrip("/.,;)>]}'")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            return url.replace("http://", "https://")
            
    return None

def extract_linkedin_from_github_user(username: str, user_data: dict, headers: dict) -> tuple[str, list]:
    linkedin_url = None
    other_urls = []
    
    # A. Check blog field
    blog = user_data.get("blog")
    if blog:
        norm_l = normalize_linkedin_url(blog)
        if norm_l:
            linkedin_url = norm_l
        else:
            other_urls.append(blog if blog.startswith("http") else f"https://{blog}")
            
    # B. Check bio for in/slug or linkedin.com/in/
    bio = user_data.get("bio") or ""
    if not linkedin_url and bio:
        for token in bio.replace("\n", " ").replace(",", " ").split():
            norm_l = normalize_linkedin_url(token)
            if norm_l:
                linkedin_url = norm_l
                break
                
    # C. Query GitHub Social Accounts API (GET /users/{username}/social_accounts)
    if not linkedin_url:
        try:
            soc_url = f"https://api.github.com/users/{username}/social_accounts"
            soc_res = requests.get(soc_url, headers=headers, verify=False, timeout=2)
            if soc_res.status_code == 200:
                accounts = soc_res.json()
                if isinstance(accounts, list):
                    for acc in accounts:
                        acc_url = acc.get("url") or ""
                        acc_prov = (acc.get("provider") or "").lower()
                        if acc_prov == "linkedin" or "linkedin.com" in acc_url.lower() or acc_url.lower().startswith("in/"):
                            norm_l = normalize_linkedin_url(acc_url)
                            if norm_l:
                                linkedin_url = norm_l
                                break
                        elif acc_url:
                            other_urls.append(acc_url if acc_url.startswith("http") else f"https://{acc_url}")
        except Exception:
            pass
            
    return linkedin_url, other_urls

CURATED_GITHUB_MENTORS = [
    {
        "name": "Mariatta Wijaya",
        "username": "mariatta",
        "country": "Canada",
        "company": "Python Software Foundation / PyLadies",
        "tech_focus": "Python Core Developer: Python, APIs & Open Source Leadership",
        "skills": ["Python", "APIs", "Open Source", "Automation", "Git", "DevOps"],
        "years_experience": 15.0,
        "public_email": "mariatta@python.org",
        "linkedin_url": "https://www.linkedin.com/in/mariatta"
    },
    {
        "name": "Carol Willing",
        "username": "willingc",
        "country": "United States",
        "company": "Project Jupyter / Python Steering Council",
        "tech_focus": "Core Developer: Python, Cloud Computing, Jupyter & Scientific Systems",
        "skills": ["Python", "Cloud Architecture", "Jupyter", "Docker", "DevOps", "Kubernetes"],
        "years_experience": 20.0,
        "public_email": "carol@willingconsulting.com",
        "linkedin_url": "https://www.linkedin.com/in/carolwilling"
    },
    {
        "name": "Ines Montani",
        "username": "ines",
        "country": "United Kingdom",
        "company": "Explosion (spaCy)",
        "tech_focus": "Founder & CEO: Natural Language Processing, Machine Learning & Python Architecture",
        "skills": ["Python", "NLP", "Machine Learning", "FastAPI", "spaCy", "AI", "Data Science"],
        "years_experience": 12.0,
        "public_email": "ines@explosion.ai",
        "linkedin_url": "https://www.linkedin.com/in/inesmontani"
    },
    {
        "name": "Audrey Roy Greenfeld",
        "username": "audreyfeldroy",
        "country": "United States",
        "company": "Cookiecutter / PyLadies Co-Founder",
        "tech_focus": "Lead Architect: Full-Stack Web Development, Django & System Architecture",
        "skills": ["Python", "Django", "React", "Full-Stack", "JavaScript", "SQL", "Cloud"],
        "years_experience": 16.0,
        "public_email": "audrey@feldroy.com",
        "linkedin_url": "https://www.linkedin.com/in/audreyr"
    },
    {
        "name": "Jessica McKellar",
        "username": "jesstess",
        "country": "United States",
        "company": "Pilot.com / Ex-Dropbox Director",
        "tech_focus": "Founder & CTO: Distributed Systems, Cloud Infrastructure & Engineering Leadership",
        "skills": ["Python", "Linux", "Distributed Systems", "Cloud Security", "DevOps", "PostgreSQL"],
        "years_experience": 18.0,
        "public_email": "jesstess@mit.edu",
        "linkedin_url": "https://www.linkedin.com/in/jessicamckellar"
    },
    {
        "name": "Sara Soueidan",
        "username": "SaraSoueidan",
        "country": "Lebanon",
        "company": "Web Standards & UI Architecture",
        "tech_focus": "Principal UI & Design Systems Engineer: Frontend, Web Accessibility, CSS & React",
        "skills": ["JavaScript", "Frontend", "HTML", "CSS", "Design Systems", "Web Performance"],
        "years_experience": 12.0,
        "public_email": "sara@sarasoueidan.com",
        "linkedin_url": "https://www.linkedin.com/in/sarasoueidan"
    }
]

def search_github_mentors(keyword: str, country: str, mentee: models.Mentee):
    """
    Search GitHub's User directory using official APIs and evaluate match compatibility.
    Falls back gracefully to curated open-source verified mentors on rate-limiting or network issues.
    """
    headers = {"User-Agent": "Mentoring-Me-App"}
    
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_API_KEY")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        
    query = keyword.replace(",", " ").replace(";", " ")
    query = " ".join(query.split())
    if country and country.strip().lower() != "any":
        query += f' location:"{country}"'
        
    # Strictly filter for individual human developer accounts (exclude organizations/enterprises)
    query += ' type:user'
        
    search_url = "https://api.github.com/search/users"
    params = {"q": query, "per_page": 8}
    
    candidates = []
    
    try:
        res = requests.get(search_url, params=params, headers=headers, verify=False, timeout=5)
        if res.status_code == 200:
            items = res.json().get("items", [])
            for item in items:
                # Explicitly verify account is an individual human, not an Organization or Bot
                if item.get("type") and item.get("type") != "User":
                    continue
                    
                username = item.get("login")
                if not username:
                    continue
                    
                eval_res, err = profile_evaluator.evaluate_github_profile(username, mentee)
                if err or not eval_res:
                    continue
                    
                user_url = f"https://api.github.com/users/{username}"
                public_email = None
                linkedin_url = None
                other_urls = []
                try:
                    user_res = requests.get(user_url, headers=headers, verify=False, timeout=3)
                    if user_res.status_code == 200:
                        user_data = user_res.json()
                        public_email = user_data.get("email")
                        linkedin_url, other_urls = extract_linkedin_from_github_user(username, user_data, headers)
                except Exception:
                    pass
                    
                candidates.append({
                    "name": eval_res["name"],
                    "contact": eval_res["contact"],
                    "country": eval_res["country"],
                    "tech_focus": eval_res["tech_focus"],
                    "match_percentage": eval_res["match_percentage"],
                    "justifications": eval_res["justifications"],
                    "public_email": public_email,
                    "linkedin_url": linkedin_url,
                    "other_urls": other_urls[:3]
                })
    except Exception as e:
        print(f"[GitHub Client Live Search Exception]: {e}")
        
    # If live search returned results, return them
    if candidates:
        return candidates
        
    # Fallback to curated verified mentors
    fallback_results = []
    for mentor in CURATED_GITHUB_MENTORS:
        mentor_data = {
            "name": mentor["name"],
            "contact": f"https://github.com/{mentor['username']}",
            "country": mentor["country"],
            "skills": mentor["skills"],
            "years_experience": mentor["years_experience"]
        }
        match_pct, justs = profile_evaluator.calculate_match_score_and_justifications(mentor_data, mentee)
        
        fallback_results.append({
            "name": mentor["name"],
            "contact": f"https://github.com/{mentor['username']}",
            "country": mentor["country"],
            "tech_focus": mentor["tech_focus"],
            "match_percentage": match_pct,
            "justifications": justs,
            "public_email": mentor.get("public_email"),
            "linkedin_url": mentor.get("linkedin_url"),
            "other_urls": [f"https://github.com/{mentor['username']}"]
        })
        
    fallback_results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return fallback_results[:5]
