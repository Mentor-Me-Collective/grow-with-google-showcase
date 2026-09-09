import os
import requests
import datetime
import urllib3
from sqlalchemy.orm import Session
from . import models

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def calculate_match_score_and_justifications(mentor_data: dict, mentee: models.Mentee):
    """
    Computes external matching percentage and justification bullet points based on desired preferences.
    Weights:
      - Skills overlap: 40%
      - Location match: 30%
      - Experience gap: 30%
    """
    justifications = []
    
    # 1. Skills Match (40% weight)
    pref_skills_str = mentee.target_mentor_expertise or ""
    pref_skills = set([s.strip().lower() for s in pref_skills_str.replace(",", ";").split(";") if s.strip()])
    if not pref_skills:
        pref_skills = set([s.strip().lower() for s in mentee.dev_type.split(";") if s.strip()])
        
    mentor_skills = set([s.strip().lower() for s in mentor_data.get("skills", [])])
    
    if not pref_skills:
        skills_score = 0.5
    else:
        intersection = pref_skills.intersection(mentor_skills)
        union = pref_skills.union(mentor_skills)
        skills_score = len(intersection) / len(union) if union else 0.0
        
    top_matches = [s.capitalize() for s in intersection]
    if skills_score > 0.6:
        justifications.append(f"🟢 **Strong Skill Alignment**: Overlaps on your preferred tech focus: {', '.join(top_matches)}.")
    elif skills_score > 0.2:
        justifications.append(f"🟡 **Moderate Skill Alignment**: Overlaps on some of your preferred focus skills: {', '.join(top_matches)}.")
    else:
        justifications.append("🔴 **Low Skill Alignment**: Does not explicitly list your preferred focus roles/technologies.")
        
    # 2. Location Match (30% weight)
    mentor_country = mentor_data.get("country", "").strip().lower()
    raw_pref_country = (mentee.target_mentor_country or "").strip()
    pref_countries = [c.strip().lower() for c in raw_pref_country.replace(";", ",").split(",") if c.strip()]
    
    if not pref_countries:
        location_score = 1.0
        justifications.append("🟢 **Location Match**: Matches your preference for any location.")
    elif mentor_country and any(c in mentor_country or mentor_country in c for c in pref_countries):
        location_score = 1.0
        matched_c = next((c for c in pref_countries if c in mentor_country or mentor_country in c), raw_pref_country)
        justifications.append(f"🟢 **Preferred Location**: Nominee is located in your preferred location ({mentor_data.get('country') or matched_c.title()}).")
    else:
        location_score = 0.3
        justifications.append(f"🟡 **Different Location**: Located in {mentor_data.get('country') or 'International'} vs your preferences ({raw_pref_country}).")
        
    # 3. Experience Match (30% weight)
    mentor_years = float(mentor_data.get("years_experience", 5.0))
    pref_min_years = float(mentee.target_mentor_min_years or 0.0)
    
    if mentor_years >= pref_min_years:
        experience_score = 1.0
        justifications.append(f"🟢 **Experience Met**: Nominee has {int(mentor_years)} years of experience, meeting your preferred minimum of {int(pref_min_years)}+ years.")
    else:
        experience_score = 0.5
        justifications.append(f"🟡 **Slightly Under Experience Preference**: Nominee has {int(mentor_years)} years of experience vs your preferred minimum of {int(pref_min_years)} years.")

    # Calculate final percentage
    total_score = (skills_score * 0.4) + (location_score * 0.3) + (experience_score * 0.3)
    match_percentage = round(total_score * 100)
    
    return match_percentage, justifications

def evaluate_github_profile(username: str, mentee: models.Mentee):
    headers = {"User-Agent": "Mentoring-Me-App"}
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_API_KEY")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    # Fetch user metadata
    user_url = f"https://api.github.com/users/{username}"
    try:
        user_res = requests.get(user_url, headers=headers, verify=False, timeout=4)
        if user_res.status_code != 200:
            return None, "GitHub username not found."
        user_data = user_res.json()
    except Exception as e:
        return None, f"GitHub connection error: {e}"
    
    # Fetch public repositories to aggregate coding languages
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=30"
    languages = set()
    try:
        repos_res = requests.get(repos_url, headers=headers, verify=False, timeout=4)
        if repos_res.status_code == 200:
            for r in repos_res.json():
                lang = r.get("language")
                if lang:
                    languages.add(lang.strip())
    except Exception:
        pass
                
    # Parse bio words for skill tags
    bio = user_data.get("bio") or ""
    bio_words = set(bio.lower().replace(",", " ").replace(".", " ").split())
    possible_skills = {"docker", "kubernetes", "react", "vue", "angular", "node", "django", "flask", "fastapi", "spring", "aws", "gcp", "azure", "devops", "ci/cd"}
    skills_found = possible_skills.intersection(bio_words)
    
    for skill in skills_found:
        languages.add(skill.capitalize())
        
    # Estimate experience based on repository count & account age
    created_at_str = user_data.get("created_at", "")
    years_experience = 5.0
    if created_at_str:
        try:
            created_year = int(created_at_str.split("-")[0])
            current_year = datetime.datetime.utcnow().year
            years_experience = float(max(1, current_year - created_year))
        except Exception:
            pass
            
    mentor_parsed = {
        "name": user_data.get("name") or username,
        "contact": f"https://github.com/{username}",
        "country": user_data.get("location") or "International",
        "skills": list(languages),
        "years_experience": years_experience
    }
    
    match_percentage, justifications = calculate_match_score_and_justifications(mentor_parsed, mentee)
    
    return {
        "name": mentor_parsed["name"],
        "contact": mentor_parsed["contact"],
        "country": mentor_parsed["country"],
        "tech_focus": ", ".join(mentor_parsed["skills"][:5]) or "General Development",
        "match_percentage": match_percentage,
        "justifications": justifications
    }, None

def evaluate_linkedin_profile(url: str, mentee: models.Mentee):
    api_key = os.getenv("PROXYCURL_API_KEY", "").strip()
    
    # DEMO / MOCK FALLBACK MODE
    if not api_key:
        print("[PROXYCURL MOCK] Running evaluation in demo mode.")
        username = url.split("/in/")[-1].split("/")[0] if "/in/" in url else "expert"
        
        # Generate a highly aligned mock profile based on mentee's requirements for a flawless demo
        mentee_roles = [r.strip() for r in mentee.dev_type.split(";") if r.strip()]
        top_skill = mentee_roles[0] if mentee_roles else "Full-stack Developer"
        
        mock_skills = [top_skill]
        if len(mentee_roles) > 1:
            mock_skills.append(mentee_roles[1])
        mock_skills.extend(["Git", "Agile", "API Design"])
        
        mentor_parsed = {
            "name": f"Expert {username.capitalize()}",
            "contact": url,
            "country": mentee.country, # Default match
            "skills": mock_skills,
            "years_experience": float(mentee.years_code_pro or 1.0) + 4.0
        }
        
        match_percentage, justifications = calculate_match_score_and_justifications(mentor_parsed, mentee)
        
        # Prepend notification that this is mock data
        justifications.insert(0, "ℹ️ **Demo Mode**: Real LinkedIn profiles require a Proxycurl API Key. This score is simulated based on your matching profile requirements.")
        
        return {
            "name": mentor_parsed["name"],
            "contact": mentor_parsed["contact"],
            "country": mentor_parsed["country"],
            "tech_focus": ", ".join(mentor_parsed["skills"][:4]),
            "match_percentage": match_percentage,
            "justifications": justifications
        }, None

    # Real Proxycurl Connection
    proxycurl_url = "https://nubela.co/proxycurl/api/v2/linkedin"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"url": url, "fallback_to_cache": "on-cache"}
    
    try:
        res = requests.get(proxycurl_url, params=params, headers=headers, timeout=15, verify=False)
        if res.status_code != 200:
            return None, f"Proxycurl LinkedIn Scraping failed: {res.text}"
            
        data = res.json()
        
        # Extract skills
        skills = data.get("skills", [])
        headline = data.get("headline", "")
        summary = data.get("summary", "")
        
        # Aggregate text for skills
        all_text = (headline + " " + summary).lower()
        possible_skills = {"python", "javascript", "docker", "kubernetes", "react", "typescript", "devops", "cloud", "aws", "gcp", "go", "java"}
        for s in possible_skills:
            if s in all_text:
                skills.append(s.capitalize())
                
        # Calculate experience from job durations
        years_experience = 5.0
        experiences = data.get("experiences", [])
        if experiences:
            total_months = 0
            for exp in experiences:
                start = exp.get("starts_at")
                end = exp.get("ends_at")
                if start:
                    sy, sm = start.get("year", 2020), start.get("month", 1)
                    if end:
                        ey, em = end.get("year", 2026), end.get("month", 1)
                    else:
                        ey, em = datetime.datetime.utcnow().year, datetime.datetime.utcnow().month
                    total_months += (ey - sy) * 12 + (em - sm)
            years_experience = max(1.0, total_months / 12.0)
            
        mentor_parsed = {
            "name": data.get("full_name") or "LinkedIn Professional",
            "contact": url,
            "country": data.get("country_full_name") or "United States",
            "skills": skills,
            "years_experience": years_experience
        }
        
        match_percentage, justifications = calculate_match_score_and_justifications(mentor_parsed, mentee)
        
        return {
            "name": mentor_parsed["name"],
            "contact": mentor_parsed["contact"],
            "country": mentor_parsed["country"],
            "tech_focus": ", ".join(mentor_parsed["skills"][:5]) or "General Mentoring",
            "match_percentage": match_percentage,
            "justifications": justifications
        }, None
        
    except Exception as e:
        return None, f"Network error contacting Proxycurl: {str(e)}"
