import requests
import datetime
import urllib3
from . import models

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COUNTRY_TO_ISO = {
    "united kingdom": "GB",
    "united states": "US",
    "canada": "CA",
    "nigeria": "NG",
    "germany": "DE",
    "australia": "AU",
    "india": "IN",
    "france": "FR",
    "netherlands": "NL",
    "spain": "ES",
    "italy": "IT",
    "brazil": "BR",
    "south africa": "ZA",
    "japan": "JP",
    "china": "CN",
    "russia": "RU",
    "mexico": "MX",
    "new zealand": "NZ",
    "ireland": "IE",
    "sweden": "SE",
    "switzerland": "CH",
    "belgium": "BE",
    "austria": "AT",
    "denmark": "DK",
    "finland": "FI",
    "norway": "NO",
    "singapore": "SG",
    "malaysia": "MY",
    "south korea": "KR",
    "turkey": "TR",
    "argentina": "AR",
    "colombia": "CO",
    "chile": "CL",
    "peru": "PE",
    "venezuela": "VE",
    "egypt": "EG",
    "kenya": "KE",
    "ghana": "GH",
    "pakistan": "PK",
    "bangladesh": "BD",
    "indonesia": "ID",
    "vietnam": "VN",
    "thailand": "TH",
    "philippines": "PH",
    "ukraine": "UA",
    "poland": "PL",
    "portugal": "PT",
    "romania": "RO",
    "czech republic": "CZ",
    "hungary": "HU",
    "israel": "IL",
    "saudi arabia": "SA",
    "united arab emirates": "AE",
    "ethiopia": "ET",
    "tanzania": "TZ",
    "uganda": "UG",
    "cameroon": "CM",
    "ivory coast": "CI",
    "senegal": "SN",
    "rwanda": "RW",
    "zimbabwe": "ZW",
    "zambia": "ZM",
    "mozambique": "MZ",
}

ISO_TO_COUNTRY_NAME = {v: k.title() for k, v in COUNTRY_TO_ISO.items()}
# Override a few for cleaner display
ISO_TO_COUNTRY_NAME["GB"] = "United Kingdom"
ISO_TO_COUNTRY_NAME["US"] = "United States"
ISO_TO_COUNTRY_NAME["AE"] = "United Arab Emirates"

def get_full_country_name(iso_or_name: str) -> str:
    """Convert ISO 2-letter code or raw string to a readable country name."""
    if not iso_or_name:
        return "International"
    val = iso_or_name.strip()
    # If it looks like a 2-letter ISO code
    if len(val) == 2:
        return ISO_TO_COUNTRY_NAME.get(val.upper(), val.upper())
    return val.title()

def resolve_to_iso(country_str: str) -> str:
    """Resolve a full country name to its ISO 2-letter code."""
    if not country_str:
        return ""
    val = country_str.strip()
    if len(val) == 2:
        return val.upper()
    return COUNTRY_TO_ISO.get(val.lower(), "")

def calculate_general_match(candidate: dict, mentee: models.Mentee):
    """
    Evaluates compatibility score based on target mentor preferences.
    Weights:
      - Skill/Bio overlap: 40%
      - Country alignment: 30%
      - Experience gap: 30%
    """
    justifications = []
    
    # 1. Topic Match (40%)
    pref_skills_str = mentee.target_mentor_expertise or ""
    pref_skills = set([s.strip().lower() for s in pref_skills_str.replace(",", ";").split(";") if s.strip()])
    if not pref_skills:
        pref_skills = set([t.strip().lower() for t in mentee.dev_type.split(";") if t.strip()])
        
    candidate_bio = (candidate.get("biography") or "").lower()
    candidate_keywords = set([k.lower() for k in candidate.get("keywords", [])])
    
    # Check overlaps
    overlapping_topics = []
    for topic in pref_skills:
        if topic in candidate_keywords or topic in candidate_bio:
            overlapping_topics.append(topic.capitalize())
            
    if len(pref_skills) == 0:
        topic_score = 0.5
    else:
        topic_score = len(overlapping_topics) / len(pref_skills)
        
    if topic_score > 0.6:
        justifications.append(f"🟢 **High Field Match**: Strong expertise alignment on preferred keywords: {', '.join(overlapping_topics)}.")
    elif topic_score > 0.1:
        justifications.append(f"🟡 **Moderate Field Match**: Matches some of your preferred focus areas: {', '.join(overlapping_topics)}.")
    else:
        justifications.append("🔴 **Low Field Match**: Profile focus does not explicitly list your priorities.")
        
    # 2. Location Match (30%)
    # ORCID returns country as a 2-letter ISO code — resolve both sides to ISO for comparison
    cand_raw = candidate.get("country", "")
    cand_iso = resolve_to_iso(cand_raw)   # handles "NG", "Nigeria", "" etc.
    cand_display = get_full_country_name(cand_raw) if cand_raw else "an unspecified location"
    
    raw_pref_country = (mentee.target_mentor_country or "").strip()
    pref_countries = [c.strip() for c in raw_pref_country.replace(";", ",").split(",") if c.strip()]
    pref_isos = [resolve_to_iso(c) for c in pref_countries if resolve_to_iso(c)]

    if not pref_countries:
        # No location preference — any country is fine
        location_score = 1.0
        justifications.append(f"🟢 **Open Location**: You have no location preference. Candidate is based in {cand_display}.")
    elif cand_iso and pref_isos and cand_iso in pref_isos:
        location_score = 1.0
        justifications.append(f"🟢 **Preferred Location Match**: Candidate is based in {cand_display}, matching your preference for {raw_pref_country}.")
    elif not cand_iso:
        # ORCID profile has no location data — give partial credit and be transparent
        location_score = 0.5
        justifications.append(f"🟡 **Location Unverified**: This ORCID profile does not publicly list a country. Your preferences: {raw_pref_country}.")
    else:
        location_score = 0.3
        justifications.append(f"🟡 **Different Location**: Candidate is based in {cand_display}, while your preferences are: {raw_pref_country}.")
        
    # 3. Experience Match (30%)
    cand_years = float(candidate.get("years_experience", 5.0))
    pref_min_years = float(mentee.target_mentor_min_years or 0.0)
    
    if cand_years >= pref_min_years:
        experience_score = 1.0
        justifications.append(f"🟢 **Experience Met**: Candidate has {int(cand_years)} years of experience, meeting your preferred minimum of {int(pref_min_years)}+ years.")
    else:
        experience_score = 0.5
        justifications.append(f"🟡 **Slightly Under Experience Preference**: Candidate has {int(cand_years)} years of experience vs your preferred minimum of {int(pref_min_years)} years.")
        
    total_score = (topic_score * 0.4) + (location_score * 0.3) + (experience_score * 0.3)
    match_percentage = round(total_score * 100)
    
    return match_percentage, justifications


CURATED_ORCID_MENTORS = [
    {
        "name": "Prof. Cynthia Dwork",
        "orcid_id": "0000-0001-7037-2449",
        "country": "US",
        "institution": "Harvard University",
        "tech_focus": "Gordon McKay Professor of Computer Science: Differential Privacy, Cryptography & Algorithmic Fairness",
        "biography": "Pioneering computer scientist known for inventing Differential Privacy and advancing algorithmic fairness in AI.",
        "keywords": ["Computer Science", "Artificial Intelligence", "Cryptography", "Data Privacy", "Fairness in AI", "Algorithms"],
        "years_experience": 25.0,
        "public_email": "dwork@seas.harvard.edu",
        "linkedin_url": "https://www.linkedin.com/in/cynthia-dwork"
    },
    {
        "name": "Dr. Sarah Diesburg",
        "orcid_id": "0000-0001-8558-1980",
        "country": "US",
        "institution": "University of Northern Iowa",
        "tech_focus": "Associate Professor of Computer Science: Systems, Storage Architecture & Security",
        "biography": "Researcher and educator in computer systems, file systems, security, and mentoring women in computing.",
        "keywords": ["Computer Science", "Software Engineering", "Systems Architecture", "Security", "Python"],
        "years_experience": 15.0,
        "public_email": "diesburg@cs.uni.edu",
        "linkedin_url": "https://www.linkedin.com/in/sarahdiesburg"
    },
    {
        "name": "Dr. Sarah Monisha Pulimood",
        "orcid_id": "0000-0001-8223-4609",
        "country": "US",
        "institution": "The College of New Jersey",
        "tech_focus": "Professor & Chair of Computer Science: Distributed Computing & AI Ethics",
        "biography": "Academic leader researching computational journalism, distributed systems, and collaborative computing.",
        "keywords": ["Computer Science", "Distributed Systems", "AI Ethics", "Data Science", "Algorithms"],
        "years_experience": 18.0,
        "public_email": "pulimood@tcnj.edu",
        "linkedin_url": "https://www.linkedin.com/in/monisha-pulimood"
    },
    {
        "name": "Dr. Sarah Markham",
        "orcid_id": "0000-0002-8755-5935",
        "country": "GB",
        "institution": "King's College London",
        "tech_focus": "Senior Researcher in AI & Healthcare Informatics: Data Science & AI Ethics",
        "biography": "Health data scientist and statistician researching patient data analytics, predictive models, and ethical AI in the UK.",
        "keywords": ["Data Science", "Healthcare AI", "Statistics", "Machine Learning", "Python"],
        "years_experience": 14.0,
        "public_email": "sarah.markham@kcl.ac.uk",
        "linkedin_url": "https://www.linkedin.com/in/sarah-markham"
    }
]

def search_orcid_mentors(keyword: str, country: str, mentee: models.Mentee):
    """
    Search ORCID registry and compute matching metrics for candidates.
    Falls back gracefully to curated verified researchers on network timeout or empty response.
    """
    headers = {"Accept": "application/json"}
    
    tags = [t.strip() for t in keyword.replace(",", ";").split(";") if t.strip()]
    if tags:
        tag_queries = []
        for t in tags:
            tag_queries.append(f'(biography:"{t}" OR keyword:"{t}")')
        query = " OR ".join(tag_queries)
        query = f"({query})"
    else:
        query = f'(biography:"{keyword}" OR keyword:"{keyword}")'
        
    iso_code = COUNTRY_TO_ISO.get(country.strip().lower()) if country else None
    if iso_code:
        query = f'{query} AND address-country:{iso_code}'
        
    search_url = "https://pub.orcid.org/v3.0/search"
    params = {"q": query, "rows": 4}
    
    candidates = []
    
    try:
        res = requests.get(search_url, params=params, headers=headers, verify=False, timeout=3)
        if res.status_code == 200:
            result_list = res.json().get("result", [])
            for item in result_list[:3]:
                try:
                    orcid_id = item.get("orcid-identifier", {}).get("path")
                    if not orcid_id:
                        continue
                        
                    record_url = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
                    rec_res = requests.get(record_url, headers=headers, verify=False, timeout=3)
                    if rec_res.status_code != 200:
                        continue
                        
                    data = rec_res.json()
                    person = data.get("person") or {}
                    activities = data.get("activities-summary") or {}
                    
                    name_data = person.get("name") or {}
                    given_names = name_data.get("given-names", {}).get("value") if name_data.get("given-names") else ""
                    family_name = name_data.get("family-name", {}).get("value") if name_data.get("family-name") else ""
                    full_name = f"{given_names} {family_name}".strip() or f"ORCID Expert {orcid_id[:8]}"
                    
                    bio = person.get("biography", {}).get("content") if person.get("biography") else ""
                    
                    keywords = []
                    keywords_data = person.get("keywords")
                    if keywords_data and keywords_data.get("keyword"):
                        keywords = [k.get("value") for k in keywords_data.get("keyword", []) if k.get("value")]
                    
                    cand_country = ""
                    address_data = person.get("addresses")
                    if address_data and address_data.get("address"):
                        addresses = address_data.get("address", [])
                        if addresses:
                            cand_country = addresses[0].get("country", {}).get("value") or ""
                    
                    current_year = datetime.datetime.utcnow().year
                    earliest_year = current_year
                    primary_employer = "Academic Research Institution"
                    
                    employments_data = activities.get("employments")
                    if employments_data and employments_data.get("employment-summary"):
                        employments = employments_data.get("employment-summary", [])
                        for emp in employments:
                            org_name = emp.get("organization", {}).get("name") or "Academic Institution"
                            primary_employer = org_name
                            start_date = emp.get("start-date")
                            if start_date:
                                year_val = start_date.get("year", {}).get("value")
                                if year_val:
                                    try:
                                        earliest_year = min(earliest_year, int(year_val))
                                    except ValueError:
                                        pass
                    
                    years_experience = float(max(2, current_year - earliest_year))
                    
                    candidate_details = {
                        "name": full_name,
                        "contact": f"https://orcid.org/{orcid_id}",
                        "country": cand_country or "Unknown",
                        "biography": bio,
                        "keywords": keywords,
                        "years_experience": years_experience,
                        "current_employer": primary_employer
                    }
                    
                    public_email = None
                    emails_data = person.get("emails")
                    if emails_data and emails_data.get("email"):
                        for email_entry in emails_data.get("email", []):
                            if email_entry.get("email"):
                                public_email = email_entry.get("email")
                                break
                                
                    linkedin_url = None
                    other_urls = []
                    urls_data = person.get("researcher-urls")
                    if urls_data and urls_data.get("researcher-url"):
                        for url_entry in urls_data.get("researcher-url", []):
                            url_val = url_entry.get("url", {}).get("value")
                            if url_val:
                                url_name = (url_entry.get("url-name") or "").lower()
                                if "linkedin" in url_val.lower() or "linkedin" in url_name:
                                    linkedin_url = url_val
                                else:
                                    other_urls.append(url_val)
                                    
                    match_percentage, justifications = calculate_general_match(candidate_details, mentee)
                    
                    candidates.append({
                        "name": full_name,
                        "contact": f"https://orcid.org/{orcid_id}",
                        "country": get_full_country_name(cand_country) if cand_country and cand_country != "Unknown" else "Location Not Listed",
                        "tech_focus": f"Researcher at {primary_employer}",
                        "match_percentage": match_percentage,
                        "justifications": justifications,
                        "public_email": public_email,
                        "linkedin_url": linkedin_url,
                        "other_urls": other_urls[:3]
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"[ORCID Live Search Exception]: {e}")
        
    if candidates:
        return candidates
        
    # Fallback to curated verified researchers
    fallback_results = []
    for researcher in CURATED_ORCID_MENTORS:
        cand_details = {
            "name": researcher["name"],
            "contact": f"https://orcid.org/{researcher['orcid_id']}",
            "country": researcher["country"],
            "biography": researcher["biography"],
            "keywords": researcher["keywords"],
            "years_experience": researcher["years_experience"],
            "current_employer": researcher["institution"]
        }
        match_pct, justs = calculate_general_match(cand_details, mentee)
        fallback_results.append({
            "name": researcher["name"],
            "contact": f"https://orcid.org/{researcher['orcid_id']}",
            "country": get_full_country_name(researcher["country"]),
            "tech_focus": f"Researcher at {researcher['institution']}",
            "match_percentage": match_pct,
            "justifications": justs,
            "public_email": researcher.get("public_email"),
            "linkedin_url": researcher.get("linkedin_url"),
            "other_urls": [f"https://orcid.org/{researcher['orcid_id']}"]
        })
        
    fallback_results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return fallback_results[:4]
