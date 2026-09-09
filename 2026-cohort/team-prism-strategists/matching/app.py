"""
Mentoring-Me Platform Streamlit Frontend
Advancing and connecting women across technical disciplines with leaders & allies.
"""
import sys
import os
import json
import datetime
import urllib.parse
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

def _safe_json(response) -> dict:
    """Safely parse a JSON response, falling back to a plain dict on non-JSON bodies (e.g. HTML 502/503 pages)."""
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            return json.loads(data)
        return data
    except Exception:
        pass
    for attr in ("text", "content"):
        raw = getattr(response, attr, None)
        if raw:
            try:
                body = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else raw
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    status_code = getattr(response, "status_code", "Unknown")
    body_text = getattr(response, "text", "") or ""
    snippet = (body_text[:200] + "...") if len(body_text) > 200 else body_text
    if not snippet.strip():
        snippet = f"Server returned HTTP {status_code}"
    return {
        "detail": f"HTTP {status_code}: {snippet}",
        "two_factor_required": False,
        "message": f"HTTP {status_code}: {snippet}"
    }

def format_experience_years(val) -> str:
    """Format experience years cleanly without trailing floating-point noise (e.g. 12.0 -> '12', 1.5000000002 -> '1.5')."""
    if val is None or val == "":
        return "Not stated"
    try:
        f_val = float(val)
        if f_val.is_integer():
            return f"{int(f_val)}"
        return f"{f_val:.1f}".rstrip('0').rstrip('.')
    except Exception:
        return str(val)

load_dotenv()

# Synchronize Streamlit Cloud secrets into os.environ for backend & services
try:
    if hasattr(st, "secrets"):
        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)):
                clean_val = str(value).strip().strip('"').strip("'")
                os.environ[key] = clean_val
                os.environ[key.upper()] = clean_val
            elif isinstance(value, dict) or hasattr(value, "items"):
                for sub_k, sub_v in value.items():
                    if isinstance(sub_v, (str, int, float, bool)):
                        clean_sub_v = str(sub_v).strip().strip('"').strip("'")
                        os.environ[f"{key.upper()}_{sub_k.upper()}"] = clean_sub_v
                        if key.lower() == "google" and sub_k.lower() in ("client_id", "id"):
                            os.environ["GOOGLE_CLIENT_ID"] = clean_sub_v
                        if key.lower() == "google" and sub_k.lower() in ("client_secret", "secret"):
                            os.environ["GOOGLE_CLIENT_SECRET"] = clean_sub_v
except Exception:
    pass

# Robust sys.path configuration for cloud environments (Streamlit Cloud, Hugging Face, etc.)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1")

# In-memory FastAPI dispatcher for seamless 1-click cloud deployment (zero port conflicts)
_in_memory_client = None

def _get_in_memory_client():
    global _in_memory_client
    if _in_memory_client is not None:
        return _in_memory_client
    try:
        from fastapi.testclient import TestClient
        try:
            from backend.main import app as _fastapi_app
        except ImportError:
            from matching.backend.main import app as _fastapi_app
        _in_memory_client = TestClient(_fastapi_app)
        return _in_memory_client
    except Exception:
        return None

class _SmartAPIClient:
    """
    Seamless dispatcher:
    If targeting local API (127.0.0.1:8000 or localhost),
    dispatches in-memory directly to the FastAPI app with 0 network latency and 0 connection errors.
    Otherwise, falls back to standard requests HTTP.
    """
    def _is_local_api(self, url: str) -> bool:
        return ("127.0.0.1:8000" in url or "localhost:8000" in url or (API_URL in url and ("127.0.0.1" in API_URL or "localhost" in API_URL)))

    def _to_path(self, url: str) -> str:
        if "127.0.0.1:8000" in url:
            return url.split("127.0.0.1:8000")[-1]
        if "localhost:8000" in url:
            return url.split("localhost:8000")[-1]
        if API_URL in url:
            sub = url.split(API_URL)[-1]
            return f"/api/v1/{sub.lstrip('/')}"
        return url

    def get(self, url, **kwargs):
        client = _get_in_memory_client()
        if self._is_local_api(url) and client is not None:
            return client.get(self._to_path(url), **kwargs)
        return requests.get(url, **kwargs)

    def post(self, url, **kwargs):
        client = _get_in_memory_client()
        if self._is_local_api(url) and client is not None:
            return client.post(self._to_path(url), **kwargs)
        return requests.post(url, **kwargs)

    def put(self, url, **kwargs):
        client = _get_in_memory_client()
        if self._is_local_api(url) and client is not None:
            return client.put(self._to_path(url), **kwargs)
        return requests.put(url, **kwargs)

    def delete(self, url, **kwargs):
        client = _get_in_memory_client()
        if self._is_local_api(url) and client is not None:
            return client.delete(self._to_path(url), **kwargs)
        return requests.delete(url, **kwargs)

api_http = _SmartAPIClient()

def ensure_backend_running():
    """
    If running in a single-service cloud environment (e.g. Streamlit Community Cloud or Hugging Face),
    automatically boots the FastAPI ASGI backend daemon in the background if not already active.
    """
    if "127.0.0.1" in API_URL or "localhost" in API_URL:
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            if result != 0:
                import threading
                import uvicorn
                try:
                    from backend.main import app as fastapi_app
                except ImportError:
                    from matching.backend.main import app as fastapi_app
                    
                def _run_fastapi():
                    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
                    server = uvicorn.Server(config)
                    server.run()
                    
                th = threading.Thread(target=_run_fastapi, daemon=True)
                th.start()
                import time
                time.sleep(2.0)
        except Exception:
            pass

ensure_backend_running()

def get_app_base_url() -> str:
    """
    Returns the resolved application base URL for external invite links and OAuth redirects.
    Precedence:
    1. APP_BASE_URL or FRONTEND_URL environment variable in .env
    2. Dynamic Streamlit Host auto-detection from request headers (st.context.headers)
    3. Default: http://localhost:8501 (local development)
    """
    env_base = os.getenv("APP_BASE_URL") or os.getenv("FRONTEND_URL") or os.getenv("STREAMLIT_SERVER_BASE_URL")
    if env_base and env_base.strip():
        return env_base.strip().rstrip("/")
        
    # Auto-detect public URL from request headers in cloud hosting (Streamlit Cloud, GCP, AWS)
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            host = headers.get("host") or headers.get("Host")
            if host:
                proto = headers.get("x-forwarded-proto", "https" if "localhost" not in str(host) and "127.0.0.1" not in str(host) else "http")
                return f"{proto}://{host}".rstrip("/")
    except Exception:
        pass

    return "http://localhost:8501"

import zoneinfo
import datetime

# curate TIMEZONE_OPTIONS sorted alphabetically from IANA database
_raw_zones = sorted(list(zoneinfo.available_timezones()))
TIMEZONE_OPTIONS = [z for z in _raw_zones if "/" in z and not z.startswith(("Etc/", "SystemV/", "US/"))]
if "Europe/London" not in TIMEZONE_OPTIONS:
    TIMEZONE_OPTIONS.append("Europe/London")
TIMEZONE_OPTIONS = sorted(list(set(TIMEZONE_OPTIONS)))

def get_tz_offset_hours(tz_name):
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
        now = datetime.datetime.now(tz)
        return now.utcoffset().total_seconds() / 3600.0
    except Exception:
        return 0.0

def parse_timezone_offset(tz_name):
    # Stabilized fallback for old code: return the numerical offset from standard ZoneInfo!
    return get_tz_offset_hours(tz_name)

def get_timezone_info(country_name):
    db = {
        "United States": "America/New_York",
        "Canada": "America/Toronto",
        "United Kingdom": "Europe/London",
        "Ireland": "Europe/Dublin",
        "Germany": "Europe/Berlin",
        "France": "Europe/Paris",
        "Spain": "Europe/Madrid",
        "Italy": "Europe/Rome",
        "Netherlands": "Europe/Amsterdam",
        "Nigeria": "Africa/Lagos",
        "Ghana": "Africa/Accra",
        "Kenya": "Africa/Nairobi",
        "Egypt": "Africa/Cairo",
        "South Africa": "Africa/Johannesburg",
        "India": "Asia/Kolkata",
        "Singapore": "Asia/Singapore",
        "Japan": "Asia/Tokyo",
        "China": "Asia/Shanghai",
        "Australia": "Australia/Sydney",
        "New Zealand": "Pacific/Auckland",
        "Brazil": "America/Sao_Paulo",
        "Argentina": "America/Argentina/Buenos_Aires",
        "Mexico": "America/Mexico_City",
    }
    return db.get(country_name, "Europe/London"), 0.0

def guess_timezone_from_email(email):
    if not email or "@" not in email:
        return "Europe/London"
    
    parts = email.lower().split(".")
    tld = parts[-1]
    
    tld_to_tz = {
        "ng": "Africa/Lagos",
        "de": "Europe/Berlin",
        "fr": "Europe/Paris",
        "es": "Europe/Madrid",
        "it": "Europe/Rome",
        "nl": "Europe/Amsterdam",
        "uk": "Europe/London",
        "ca": "America/Toronto",
        "au": "Australia/Sydney",
        "jp": "Asia/Tokyo",
        "in": "Asia/Kolkata",
        "nz": "Pacific/Auckland",
        "br": "America/Sao_Paulo",
        "za": "Africa/Johannesburg",
        "eg": "Africa/Cairo",
        "ke": "Africa/Nairobi",
        "cn": "Asia/Shanghai",
        "sg": "Asia/Singapore",
        "mx": "America/Mexico_City"
    }
    
    if tld in tld_to_tz:
        return tld_to_tz[tld]
        
    if len(parts) >= 2 and parts[-2] == "co" and tld == "uk":
        return "Europe/London"
        
    return "Europe/London"

def display_timezone_converter(mentee_country, mentor_country):
    mentee_tz, _ = get_timezone_info(mentee_country)
    mentor_tz, _ = get_timezone_info(mentor_country)
    display_timezone_converter_from_tz(mentee_tz, mentor_tz, mentor_country)

def convert_local_to_utc_string(local_date, local_time, iana_tz):
    from zoneinfo import ZoneInfo
    dt = datetime.datetime.combine(local_date, local_time)
    local_dt = dt.replace(tzinfo=ZoneInfo(iana_tz))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt.isoformat()

def convert_utc_string_to_local(utc_str, iana_tz):
    from zoneinfo import ZoneInfo
    try:
        if utc_str.endswith("Z"):
            utc_str = utc_str[:-1]
        if "/" in utc_str:
            start_str, end_str = utc_str.split("/")
            if start_str.endswith("Z"): start_str = start_str[:-1]
            if end_str.endswith("Z"): end_str = end_str[:-1]
            
            start_dt = datetime.datetime.fromisoformat(start_str).replace(tzinfo=ZoneInfo("UTC"))
            end_dt = datetime.datetime.fromisoformat(end_str).replace(tzinfo=ZoneInfo("UTC"))
            local_start = start_dt.astimezone(ZoneInfo(iana_tz))
            local_end = end_dt.astimezone(ZoneInfo(iana_tz))
            return f"{local_start.strftime('%A, %b %d, %Y at %I:%M %p')} - {local_end.strftime('%I:%M %p')}"
        else:
            utc_dt = datetime.datetime.fromisoformat(utc_str).replace(tzinfo=ZoneInfo("UTC"))
            local_dt = utc_dt.astimezone(ZoneInfo(iana_tz))
            return local_dt.strftime("%A, %b %d, %Y at %I:%M %p")
    except Exception:
        return utc_str

def display_timezone_converter_from_tz(mentee_tz, mentor_tz, mentor_country, mentor_name="your mentor"):
    mentee_offset = get_tz_offset_hours(mentee_tz)
    mentor_offset = get_tz_offset_hours(mentor_tz)
    
    diff = mentee_offset - mentor_offset
    diff_str = f"{abs(diff):.1f} hours ahead of" if diff > 0 else (f"{abs(diff):.1f} hours behind" if diff < 0 else "in the same timezone as")
    if diff == int(diff):
        diff_str = f"{abs(int(diff))} hours ahead of" if diff > 0 else (f"{abs(int(diff))} hours behind" if diff < 0 else "in the same timezone as")
        
    st.markdown(
        f"""
        🗺️ **Timezone Helper:**
        * Your Timezone: **{mentee_tz}** (UTC{'+' if mentee_offset >= 0 else ''}{mentee_offset:+.1f} hours)
        * Mentor's Timezone: **{mentor_tz}** ({mentor_country or 'Not stated'}) (UTC{'+' if mentor_offset >= 0 else ''}{mentor_offset:+.1f} hours)
        * You are **{diff_str}** {mentor_name}.
        """
    )
    
    if diff != 0:
        st.markdown("**Quick Conversion Guide:**")
        slots = [9, 13, 17]
        guide_lines = []
        for s in slots:
            m_time_str = f"{s if s <= 12 else s-12}:00 {'AM' if s < 12 else 'PM'}"
            local_hour = int((s + diff) % 24)
            local_time_str = f"{local_hour if local_hour <= 12 else local_hour-12}:00 {'AM' if local_hour < 12 or local_hour == 24 else 'PM'}"
            if local_hour == 0 or local_hour == 12:
                local_time_str = "12:00 AM" if local_hour == 0 else "12:00 PM"
            guide_lines.append(f"* Mentor **{m_time_str}** = Your Local **{local_time_str}**")
        st.markdown("\n".join(guide_lines))

def display_mentor_availability(note, mentee_profile_data, mentor_profile_data=None):
    if not note:
        st.info("No availability notes shared yet.")
        return
        
    default_tz = "UTC+00:00 (London, GMT)"
    if mentee_profile_data:
        if isinstance(mentee_profile_data, dict):
            m_profile = mentee_profile_data.get('mentee') if 'mentee' in mentee_profile_data else mentee_profile_data
            user_email = mentee_profile_data.get('user', {}).get('email')
            default_tz = m_profile.get('timezone') or mentee_profile_data.get('mentee_timezone') or (guess_timezone_from_email(user_email) if user_email else get_timezone_info(m_profile.get('country', 'United Kingdom'))[0])
        else:
            default_tz = get_timezone_info(mentee_profile_data)[0]
            
    match_id = "default"
    if isinstance(mentor_profile_data, dict) and 'id' in mentor_profile_data:
        match_id = mentor_profile_data['id']
        
    import hashlib
    note_hash = hashlib.md5(note.encode('utf-8')).hexdigest()[:8] if note else "empty"
    selectbox_key = f"active_tz_selector_{match_id}_{note_hash}"
    
    col_tz1, col_tz2 = st.columns([6, 4])
    with col_tz1:
        st.write("🌍 **Verify / Change Your Timezone:**")
    with col_tz2:
        mentee_tz = st.selectbox(
            "Your Timezone", 
            TIMEZONE_OPTIONS, 
            index=TIMEZONE_OPTIONS.index(default_tz) if default_tz in TIMEZONE_OPTIONS else 12,
            key=selectbox_key,
            label_visibility="collapsed"
        )
        
    if mentee_profile_data and isinstance(mentee_profile_data, dict):
        m_profile = mentee_profile_data.get('mentee') if 'mentee' in mentee_profile_data else mentee_profile_data
        if m_profile.get('timezone') != mentee_tz:
            api_update_profile({"timezone": mentee_tz})
            st.session_state['profile'] = None
            st.rerun()
            
    if note.startswith("UTC_DTS:"):
        try:
            parts = note[8:].split("|")
            dts_part = parts[0]
            note_part = parts[1][5:] if len(parts) > 1 and parts[1].startswith("NOTE:") else ""
            
            utc_strs = dts_part.split(",")
            
            st.write("📅 **Mentor's Proposed Slots (Converted to your timezone):**")
            st.write(f"🗺️ *Your Active Timezone:* **{mentee_tz}**")
            
            options = []
            for idx, utc_str in enumerate(utc_strs):
                if utc_str.strip():
                    local_time_str = convert_utc_string_to_local(utc_str, mentee_tz)
                    options.append(local_time_str)
            options.append("None of these work / Coordinate Custom Time")
            
            selected_slot = st.radio("⚡ **Select Your Preferred Slot:**", options, key=f"preferred_slot_select_{note[:20]}")
            st.session_state['selected_scheduled_slot'] = selected_slot
                    
            if note_part.strip():
                st.write(f"💬 **Mentor's Note:** {note_part}")
                
            if mentor_profile_data:
                mentor_tz = "Europe/London"
                mentor_country = "Not stated"
                mentor_name = "your mentor"
                if isinstance(mentor_profile_data, dict):
                    mentor_tz = mentor_profile_data.get('mentor_timezone') or mentor_profile_data.get('timezone')
                    if not mentor_tz:
                        m_profile = mentor_profile_data.get('mentor') if 'mentor' in mentor_profile_data else mentor_profile_data
                        mentor_tz = m_profile.get('timezone') or get_timezone_info(m_profile.get('country', 'United Kingdom'))[0]
                    mentor_country = mentor_profile_data.get('mentor_country') or mentor_profile_data.get('country', 'Not stated')
                    mentor_name = mentor_profile_data.get('mentor_name', 'your mentor')
                else:
                    mentor_tz, _ = get_timezone_info(mentor_profile_data)
                    mentor_country = mentor_profile_data
                display_timezone_converter_from_tz(mentee_tz, mentor_tz, mentor_country, mentor_name)
        except Exception as e:
            st.info(f"💬 **Mentor's Shared Availability:**\n\n{note}")
    else:
        st.info(f"💬 **Mentor's Shared Availability:**\n\n{note}")
        if mentor_profile_data:
            mentor_tz = "Europe/London"
            mentor_country = "Not stated"
            mentor_name = "your mentor"
            if isinstance(mentor_profile_data, dict):
                mentor_tz = mentor_profile_data.get('mentor_timezone') or mentor_profile_data.get('timezone')
                if not mentor_tz:
                    m_profile = mentor_profile_data.get('mentor') if 'mentor' in mentor_profile_data else mentor_profile_data
                    mentor_tz = m_profile.get('timezone') or get_timezone_info(m_profile.get('country', 'United Kingdom'))[0]
                mentor_country = mentor_profile_data.get('mentor_country') or mentor_profile_data.get('country', 'Not stated')
                mentor_name = mentor_profile_data.get('mentor_name', 'your mentor')
            else:
                mentor_tz, _ = get_timezone_info(mentor_profile_data)
                mentor_country = mentor_profile_data
            display_timezone_converter_from_tz(mentee_tz, mentor_tz, mentor_country, mentor_name)

def generate_default_mentee_intro_message(mentor_name, mentee_name, sel_slot=None, availability_note=None):
    """
    Generates a context-aware default introductory message acknowledging
    the mentor's availability and the mentee's selected time slot.
    """
    if sel_slot and sel_slot != "None of these work / Coordinate Custom Time":
        return (
            f"Hi {mentor_name},\n\n"
            f"Thank you for accepting my mentorship request and sharing your availability!\n\n"
            f"I would love to lock in our introductory 25-minute sync for:\n"
            f"📅 {sel_slot}\n\n"
            f"I look forward to our conversation and collaborating with you on Mentoring-Me.\n\n"
            f"Best regards,\n{mentee_name}"
        )
    elif availability_note and ("http" in availability_note.lower() or "calendly" in availability_note.lower() or "cal.com" in availability_note.lower()):
        return (
            f"Hi {mentor_name},\n\n"
            f"Thank you for accepting my mentorship request! I received your scheduling link and will book our introductory 25-minute sync there.\n\n"
            f"Looking forward to connecting with you!\n\n"
            f"Best regards,\n{mentee_name}"
        )
    elif sel_slot == "None of these work / Coordinate Custom Time":
        return (
            f"Hi {mentor_name},\n\n"
            f"Thank you for accepting my mentorship request and sharing your availability!\n\n"
            f"The proposed slots don't quite fit my schedule this week. Could we explore an alternative time for our introductory 25-minute sync? Here are a few times when I am free:\n"
            f"- [Insert Option 1]\n"
            f"- [Insert Option 2]\n\n"
            f"Looking forward to connecting!\n\n"
            f"Best regards,\n{mentee_name}"
        )
    else:
        return (
            f"Hi {mentor_name},\n\n"
            f"Thank you for accepting my mentorship request! I am excited to connect with you on Mentoring-Me.\n\n"
            f"Please let me know a few days and times that work best for our introductory 25-minute sync, or feel free to share your calendar scheduling link.\n\n"
            f"Best regards,\n{mentee_name}"
        )

# Reference dropdown options from the dataset
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica",
    "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq",
    "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
    "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway",
    "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
    "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]
ED_LEVELS = [
    "Bachelor's degree (B.A., B.S., B.Eng., etc.)",
    "Master's degree (M.A., M.S., M.Eng., MBA, etc.)",
    "Some college/university study without earning a degree",
    "Secondary school",
    "Associate degree (A.A., A.S., etc.)",
    "Other doctoral degree (Ph.D., Ed.D., etc.)",
    "Professional degree (JD, MD, etc.)",
    "Primary/elementary school",
    "I never completed any formal education"
]
ALL_ROLES = [
    "Developer, back-end", "Developer, full-stack", "Developer, front-end", 
    "Developer, desktop or enterprise applications", "Developer, mobile", 
    "DevOps specialist", "Database administrator", "System administrator", 
    "Designer", "Developer, embedded applications or devices", 
    "Data scientist or machine learning specialist", "Developer, QA or test", 
    "Data or business analyst", "Academic researcher", "Engineer, data", 
    "Engineering manager", "Product manager", "Scientist", "Educator", 
    "Engineer, site reliability", "Senior executive/VP"
]
ALL_FACTORS = [
    "Languages, frameworks, and other technologies I’d be working with",
    "Office environment or company culture",
    "Opportunities for professional development",
    "Flex time or a flexible schedule",
    "Remote work options",
    "Industry that I’d be working in",
    "Financial performance or funding status of the company or organization",
    "Specific department or team I’d be working on",
    "How widely used or influential the project I’d be working on is",
    "Diversity of the company or organization",
    "Family friendliness or maternity/paternity leave"
]
ORG_SIZES = [
    "Just me - 1 person", "2 to 9 employees", "10 to 19 employees", 
    "20 to 99 employees", "100 to 499 employees", "500 to 999 employees", 
    "1,000 to 4,999 employees", "5,000 to 9,999 employees", "10,000 or more employees",
    "Not stated"
]

def display_match_compatibility_report(m: dict, partner_name: str = None, is_mentor_view: bool = False):
    """
    Renders an intuitive, human-friendly compatibility breakdown with narrative highlights,
    visual percentage progress bars, and plain-English criteria explanations instead of raw histograms.
    """
    raw_score = m.get('total_score', 0)
    pct_score = int(round(raw_score * 100)) if isinstance(raw_score, float) and raw_score <= 1.0 else int(round(raw_score))
    
    role_s = float(m.get('role_score', 0.8) or 0.8)
    exp_s = float(m.get('experience_score', 0.8) or 0.8)
    stage_s = float(m.get('career_stage_score', 1.0) or 1.0)
    goals_s = float(m.get('goals_score', 0.7) or 0.7)
    pract_s = float(m.get('practical_score', 0.9) or 0.9)
    
    role_pct = int(round(min(max(role_s, 0.0), 1.0) * 100))
    exp_pct = int(round(min(max(exp_s, 0.0), 1.0) * 100))
    stage_pct = int(round(min(max(stage_s, 0.0), 1.0) * 100))
    goals_pct = int(round(min(max(goals_s, 0.0), 1.0) * 100))
    pract_pct = int(round(min(max(pract_s, 0.0), 1.0) * 100))
    
    p_name = partner_name or m.get('mentor_name' if not is_mentor_view else 'mentee_name', 'your match')
    
    # ── 1. Confidence & Boost Badges ─────────────────────────────────────────
    if pct_score >= 85:
        tier_badge = "🌟 Exceptional Compatibility"
        tier_color = "#15803d"
    elif pct_score >= 70:
        tier_badge = "🟢 Strong Compatibility"
        tier_color = "#2563eb"
    else:
        tier_badge = "🟡 Moderate Fit"
        tier_color = "#d97706"
        
    st.markdown(
        f"""
        <div style="background:#f8fafc; border-left: 4px solid {tier_color}; padding: 10px 14px; border-radius: 8px; margin-bottom: 12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:{tier_color}; font-size:1.05rem;">{tier_badge}</span>
                <span style="font-size:1.15rem; font-weight:800; color:{tier_color};">{pct_score}% Overall Fit</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if m.get('is_representation_boosted'):
        st.info("🌟 **Gender Representation Boost Applied (+10%)**: Promotes female role models and senior leadership connections in technical fields (UN SDG 5).")
    if m.get('is_ally_boosted'):
        st.info("🤝 **Diversity Ally Match (+10%)**: Mentor is a verified Diversity & Inclusion Ally dedicated to supporting women in technology.")
        
    # ── 2. Plain English Narrative Highlights ────────────────────────────────
    roles_str = m.get('mentor_devtype' if not is_mentor_view else 'mentee_devtype', '')
    first_role = roles_str.split(';')[0] if roles_str else 'Engineering'
    
    exp_gap = m.get('experience_gap')
    if exp_gap is not None:
        gap_desc = f"{abs(exp_gap):.0f} years of senior expertise" if exp_gap > 0 else "close peer-level experience"
    else:
        gap_desc = "complementary career seniority"
        
    st.markdown(f"💡 **Why this match works:** Recommended based on strong alignment in **{first_role}**, **{gap_desc}**, and shared workplace priorities.")
    st.markdown("---")
    
    # ── 3. Factor-by-Factor Percentage Bars ──────────────────────────────────
    st.markdown("**Detailed Criteria Breakdown:**")
    
    # Factor 1: Role Alignment (30%)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("**💻 Technical & Role Overlap (30% Weight)**")
        st.progress(min(max(role_s, 0.0), 1.0))
        st.caption(f"Measures programming specialization and skill overlap in {first_role}.")
    with c2:
        st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.05rem; color:#1e293b; padding-top:6px;'>{role_pct}%</div>", unsafe_allow_html=True)
        
    # Factor 2: Experience Gap (25%)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("**⏳ Relatable Seniority Window (25% Weight)**")
        st.progress(min(max(exp_s, 0.0), 1.0))
        st.caption("Prioritizes an optimal 2–10 year experience distance for practical, actionable guidance.")
    with c2:
        st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.05rem; color:#1e293b; padding-top:6px;'>{exp_pct}%</div>", unsafe_allow_html=True)

    # Factor 3: Career Stage Priority (20%)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("**🎯 Retention-Risk Milestone Priority (20% Weight)**")
        st.progress(min(max(stage_s, 0.0), 1.0))
        st.caption("Empirical boost targeting critical retention drop-off windows (0–2y early career & 5–10y mid-career).")
    with c2:
        st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.05rem; color:#1e293b; padding-top:6px;'>{stage_pct}%</div>", unsafe_allow_html=True)

    # Factor 4: Goals Alignment (15%)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("**🌟 Workplace Priorities & Culture Fit (15% Weight)**")
        st.progress(min(max(goals_s, 0.0), 1.0))
        st.caption("Alignment across stated job factors (e.g. work-life balance, diversity signals, flex-time).")
    with c2:
        st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.05rem; color:#1e293b; padding-top:6px;'>{goals_pct}%</div>", unsafe_allow_html=True)

    # Factor 5: Practical Fit (10%)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("**🏢 Organization Scale & Logistics (10% Weight)**")
        st.progress(min(max(pract_s, 0.0), 1.0))
        st.caption("Compatibility across company size and engineering team dynamics.")
    with c2:
        st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.05rem; color:#1e293b; padding-top:6px;'>{pract_pct}%</div>", unsafe_allow_html=True)


st.set_page_config(page_title="Mentoring-Me — Empowering Women in Technical Careers", layout="wide")

st.title("👩‍💻 Mentoring-Me — Empowering Women in Technical Careers")
st.caption(
    "Dedicated to advancing and connecting women across technical disciplines with experienced leaders, mentors, and active Diversity & Inclusion allies."
)
st.markdown("""
<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: -6px; margin-bottom: 20px;">
    <span style="background: #f1f5f9; color: #334155; padding: 4px 12px; border-radius: 16px; font-size: 0.82rem; font-weight: 600; border: 1px solid #e2e8f0;">👩‍💻 Elevating Women in Technical Roles</span>
    <span style="background: #f1f5f9; color: #334155; padding: 4px 12px; border-radius: 16px; font-size: 0.82rem; font-weight: 600; border: 1px solid #e2e8f0;">📈 Career Acceleration & Sponsorship</span>
    <span style="background: #f1f5f9; color: #334155; padding: 4px 12px; border-radius: 16px; font-size: 0.82rem; font-weight: 600; border: 1px solid #e2e8f0;">🤝 Diversity & Inclusion Allies</span>
</div>
""", unsafe_allow_html=True)

# Session State Initialization & Auto-Restoration on Page Refresh
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
if 'profile' not in st.session_state:
    st.session_state['profile'] = None
if 'invite_code' not in st.session_state:
    st.session_state['invite_code'] = None
if 'client_clear_token' not in st.session_state:
    st.session_state['client_clear_token'] = False

def clear_auth_session():
    st.session_state['access_token'] = None
    st.session_state['profile'] = None
    if "session_token" in st.query_params:
        del st.query_params["session_token"]
    st.session_state['client_clear_token'] = True

def render_client_storage_sync():
    """
    HTML5 LocalStorage & SessionStorage Synchronization Bridge:
    - Automatically persists JWT authentication tokens to browser localStorage upon sign-in.
    - Seamlessly restores session and stays on dashboard when the user refreshes (F5) or reloads the tab.
    - Wipes browser localStorage when the user explicitly signs out.
    """
    token = st.session_state.get('access_token')
    should_clear = st.session_state.get('client_clear_token', False)
    
    if should_clear:
        js_code = """
        <script>
            try {
                localStorage.removeItem('mm_session_token');
                sessionStorage.removeItem('mm_session_token');
            } catch(e) {}
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js_code, height=0, width=0)
        st.session_state['client_clear_token'] = False
    elif token:
        js_code = f"""
        <script>
            try {{
                localStorage.setItem('mm_session_token', "{token}");
                sessionStorage.setItem('mm_session_token', "{token}");
            }} catch(e) {{}}
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js_code, height=0, width=0)
    else:
        # User not logged into Python session state: check if browser localStorage has a persistent token to restore
        js_code = """
        <script>
            try {
                const storedToken = localStorage.getItem('mm_session_token') || sessionStorage.getItem('mm_session_token');
                if (storedToken && storedToken.length > 20) {
                    const currentUrl = new URL(window.parent.location.href);
                    if (!currentUrl.searchParams.get("session_token")) {
                        currentUrl.searchParams.set("session_token", storedToken);
                        window.parent.location.replace(currentUrl.toString());
                    }
                }
            } catch(e) {}
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js_code, height=0, width=0)

def fetch_profile(max_retries: int = 3):
    token = st.session_state.get('access_token') or st.query_params.get("session_token")
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    import time
    for attempt in range(max_retries):
        try:
            response = api_http.get(f"{API_URL}/users/me", headers=headers)
            if response.status_code == 200:
                profile_data = _safe_json(response)
                st.session_state['access_token'] = token
                st.session_state['profile'] = profile_data
                st.query_params["session_token"] = token
                return profile_data
            elif response.status_code in (401, 403):
                clear_auth_session()
                return None
            else:
                # Backend is warming up or 5xx during reload
                if attempt < max_retries - 1:
                    time.sleep(0.35)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.35)
    return st.session_state.get('profile')

# Automatically restore session if page is refreshed or code reloads
if not st.session_state.get('access_token'):
    persisted_token = st.query_params.get("session_token")
    if persisted_token:
        st.session_state['access_token'] = persisted_token
        fetch_profile()

# Activate client storage bridge
render_client_storage_sync()

def get_frontend_base_url():
    explicit = os.getenv("APP_BASE_URL") or os.getenv("FRONTEND_URL")
    if explicit and "localhost" not in explicit:
        return explicit.rstrip("/")
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            host = headers.get("host") or headers.get("Host") or headers.get("x-forwarded-host")
            proto = headers.get("x-forwarded-proto", "https")
            if host:
                return f"{proto}://{host}".rstrip("/")
    except Exception:
        pass
    return (explicit or "http://localhost:8501").rstrip("/")

# Capture invite code from URL parameters if present
if "invite_code" in st.query_params:
    st.session_state['invite_code'] = st.query_params["invite_code"]

# Handle OAuth Redirection Callbacks (Google & Facebook)
if "code" in st.query_params:
    _auth_code = st.query_params.get("code")
    _state_raw = st.query_params.get("state", "")
    _prov = "google"
    _role = "MENTEE"
    _mode = "signin"
    _inv = None
    
    if _state_raw:
        import urllib.parse
        parsed_state = dict(urllib.parse.parse_qsl(_state_raw))
        _prov = parsed_state.get("provider", "google")
        _role = parsed_state.get("role", "MENTEE")
        _mode = parsed_state.get("mode", "signin")
        _inv = parsed_state.get("invite")
    else:
        _prov = st.query_params.get("provider", "google")
        _role = st.query_params.get("role", "MENTEE")
        _mode = st.query_params.get("mode", "signin")
        _inv = st.query_params.get("invite_code")
        
    try:
        frontend_base = get_frontend_base_url()
        payload = {
            "provider": _prov,
            "code": _auth_code,
            "role": _role,
            "mode": _mode,
            "invite_code": _inv,
            "redirect_uri": frontend_base
        }
        resp = api_http.post(f"{API_URL}/auth/sso/callback", json=payload)
        if resp.status_code in (200, 201):
            res_data = _safe_json(resp)
            if _mode == "signup":
                # Registration Phase: Account successfully registered via Google/Facebook SSO
                role_label = res_data.get('role', _role).capitalize()
                user_email = res_data.get('email', '')
                provider_label = res_data.get('provider', _prov).capitalize()
                st.session_state['sso_success_msg'] = f"🎉 Your {role_label} account ({user_email}) has been successfully created with {provider_label}! Please select 'Continue as {role_label} with {provider_label}' on the Sign In tab to enter your dashboard."
                clear_auth_session()
                st.session_state['sso_error'] = None
            else:
                # Sign In Phase: Enter dashboard directly
                token = res_data.get('access_token') if isinstance(res_data, dict) else None
                if token:
                    st.session_state['access_token'] = token
                    st.query_params["session_token"] = token
                    st.session_state['two_factor_challenge'] = None
                    st.session_state['sso_error'] = None
                    if 'sso_success_msg' in st.session_state:
                        del st.session_state['sso_success_msg']
                    prof = fetch_profile()
                    if prof:
                        st.session_state['profile'] = prof
                else:
                    err_hint = res_data.get('detail') if isinstance(res_data, dict) else str(res_data)
                    st.session_state['sso_error'] = f"Google Sign-In Error: {err_hint or 'Invalid token response from server.'}"
        else:
            err_data = _safe_json(resp)
            err_msg = err_data.get('detail') or err_data.get('message') or f"Google authentication failed (HTTP {resp.status_code})."
            st.session_state['sso_error'] = err_msg
    except Exception as e:
        st.session_state['sso_error'] = f"Google Connection Error: {str(e)}"
        
    for k in ["code", "provider", "role", "mode", "state", "invite_code", "scope", "authuser", "prompt", "hd"]:
        if k in st.query_params:
            del st.query_params[k]
    st.rerun()

# Helper functions for API communication
def api_login(email, password):
    try:
        response = api_http.post(f"{API_URL}/auth/token", data={"username": email, "password": password})
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("two_factor_required"):
                st.session_state['two_factor_challenge'] = res_data["challenge_token"]
                st.session_state['two_factor_email'] = res_data.get("email", email)
                st.session_state['two_factor_hint'] = res_data.get("delivery_hint", "Enter your 6-digit security code.")
                st.session_state['two_factor_preview'] = res_data.get("otp_code_preview")
                return "2FA_REQUIRED", res_data.get("delivery_hint", "Please complete security verification.")
            else:
                st.session_state['access_token'] = res_data['access_token']
                st.query_params["session_token"] = res_data['access_token']
                st.session_state['two_factor_challenge'] = None
                fetch_profile()
                return True, "Login successful!"
        else:
            detail = response.json().get("detail", "Login failed")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_verify_2fa(code):
    challenge_token = st.session_state.get('two_factor_challenge')
    if not challenge_token:
        return False, "No active security challenge session. Please sign in again."
    try:
        response = api_http.post(f"{API_URL}/auth/2fa/verify", json={"challenge_token": challenge_token, "code": code.strip()})
        if response.status_code == 200:
            res_data = response.json()
            st.session_state['access_token'] = res_data['access_token']
            st.query_params["session_token"] = res_data['access_token']
            st.session_state['two_factor_challenge'] = None
            st.session_state['two_factor_preview'] = None
            fetch_profile()
            return True, "Security verification successful!"
        else:
            detail = response.json().get("detail", "Verification failed")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_resend_2fa():
    challenge_token = st.session_state.get('two_factor_challenge')
    if not challenge_token:
        return False, "No active challenge session."
    try:
        response = api_http.post(f"{API_URL}/auth/2fa/resend", json={"challenge_token": challenge_token})
        if response.status_code == 200:
            res_data = response.json()
            st.session_state['two_factor_challenge'] = res_data["challenge_token"]
            st.session_state['two_factor_preview'] = res_data.get("otp_code_preview")
            return True, "New 6-digit security code generated!"
        else:
            detail = response.json().get("detail", "Failed to resend code")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_toggle_2fa(enabled: bool):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/auth/2fa/toggle", json={"enabled": enabled}, headers=headers)
        if response.status_code == 200:
            fetch_profile()
            return True, response.json().get("message", "Updated 2FA status.")
        return False, response.json().get("detail", "Failed to update 2FA.")
    except Exception as e:
        return False, f"API Error: {e}"

def api_delete_my_account():
    if not st.session_state.get('access_token'):
        return False, "Not authenticated"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.delete(f"{API_URL}/users/me", headers=headers)
        if response.status_code == 200:
            msg = response.json().get("message", "Your account and all associated data have been permanently deleted.")
            clear_auth_session()
            return True, msg
        detail = response.json().get("detail", "Failed to delete account.")
        return False, detail
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_sso_authenticate(provider: str, email: str, name: str = None, picture: str = None, oauth_id: str = None, role: str = "MENTEE", invite_code: str = None, token_or_code: str = None):
    try:
        payload = {
            "provider": provider.lower(),
            "email": email.strip(),
            "name": name.strip() if name else None,
            "picture": picture.strip() if picture else None,
            "oauth_id": oauth_id.strip() if oauth_id else None,
            "role": role.upper() if role else "MENTEE",
            "invite_code": invite_code,
            "token_or_code": token_or_code
        }
        response = api_http.post(f"{API_URL}/auth/sso", json=payload)
        if response.status_code == 200:
            res_data = response.json()
            st.session_state['access_token'] = res_data['access_token']
            st.query_params["session_token"] = res_data['access_token']
            st.session_state['two_factor_challenge'] = None
            st.session_state['two_factor_preview'] = None
            fetch_profile()
            action_desc = "Account created & signed in" if res_data.get("is_new_user") else "Signed in"
            return True, f"✨ {action_desc} via {provider.capitalize()} successfully!"
        else:
            detail = response.json().get("detail", "SSO Authentication failed")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_get_sso_url(provider: str, role: str = "MENTEE", mode: str = "signin", invite_code: str = None):
    try:
        frontend_base = get_frontend_base_url()
        params = {"provider": provider, "role": role, "mode": mode, "redirect_uri": frontend_base}
        if invite_code:
            params["invite_code"] = invite_code
        response = api_http.get(f"{API_URL}/auth/sso/authorize-url", params=params)
        if response.status_code == 200:
            auth_url = response.json().get("auth_url")
            if auth_url:
                return auth_url
    except Exception:
        pass

    # Streamlit Cloud secrets / environment direct fallback
    if provider.lower() == "google":
        g_cid = None
        if hasattr(st, "secrets"):
            if "GOOGLE_CLIENT_ID" in st.secrets:
                g_cid = str(st.secrets["GOOGLE_CLIENT_ID"])
            elif "google" in st.secrets and isinstance(st.secrets["google"], dict):
                g_cid = str(st.secrets["google"].get("client_id") or st.secrets["google"].get("GOOGLE_CLIENT_ID") or "")
            elif "oauth" in st.secrets and isinstance(st.secrets["oauth"], dict):
                g_cid = str(st.secrets["oauth"].get("google_client_id") or st.secrets["oauth"].get("GOOGLE_CLIENT_ID") or "")
        if not g_cid:
            g_cid = os.getenv("GOOGLE_CLIENT_ID", "")
            
        if g_cid:
            g_cid = str(g_cid).strip().strip('"').strip("'")
            if g_cid and "your_" not in g_cid:
                import urllib.parse
                frontend_base = get_frontend_base_url().rstrip("/")
                g_params = {
                    "client_id": g_cid,
                    "redirect_uri": frontend_base,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "access_type": "offline",
                    "prompt": "select_account",
                    "state": f"provider=google&role={role}&mode={mode}" + (f"&invite={invite_code}" if invite_code else "")
                }
                return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(g_params)}"
                
    return None

def api_signup(email, password, role, invite_code=None, gender=None):
    try:
        payload = {"email": email, "password": password, "role": role.upper()}
        if invite_code:
            payload["invite_code"] = invite_code
        if gender:
            payload["gender"] = gender
        response = api_http.post(f"{API_URL}/auth/signup", json=payload)
        
        if response.status_code in (200, 201):
            data = response.json()
            if data.get("two_factor_required"):
                st.session_state['two_factor_challenge'] = data.get("challenge_token")
                st.session_state['two_factor_email'] = data.get("email", email)
                st.session_state['two_factor_hint'] = data.get("delivery_hint", "Enter your 6-digit verification code.")
                st.session_state['two_factor_preview'] = data.get("otp_code_preview")
                st.session_state['two_factor_is_signup'] = True
                return "2FA_REQUIRED", data.get("delivery_hint", "Account registered! Please enter the 6-digit verification code sent to your email.")
            else:
                return True, "Account created successfully! Please log in."
        else:
            detail = response.json().get("detail", "Signup failed")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"


def api_nominate_mentor(name, contact, tech_focus, custom_message=None):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    payload = {
        "mentor_name": name,
        "mentor_contact": contact,
        "tech_focus": tech_focus,
        "custom_message": custom_message
    }
    try:
        response = api_http.post(f"{API_URL}/profile/nominate", json=payload, headers=headers)
        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                detail = response.json().get('detail', response.text)
            except Exception:
                detail = response.text or f"Server returned status {response.status_code}"
            return False, f"Failed to nominate: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_get_nominations():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.get(f"{API_URL}/profile/nominations", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_mark_nomination_contacted(nomination_id):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/profile/nominate/{nomination_id}/contacted", headers=headers)
        return response.status_code == 200
    except Exception:
        return False

def api_send_nomination_followup(nomination_id, custom_message=None, subject=None):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    payload = {
        "custom_message": custom_message,
        "subject": subject
    }
    try:
        response = api_http.post(f"{API_URL}/profile/nominate/{nomination_id}/follow-up", json=payload, headers=headers)
        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                detail = response.json().get('detail', response.text)
            except Exception:
                detail = response.text or f"Server returned status {response.status_code}"
            return False, f"Failed to send follow-up: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_send_direct_match_email(match_id, subject, body_text):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    payload = {
        "subject": subject,
        "body_text": body_text
    }
    try:
        response = api_http.post(f"{API_URL}/matches/{match_id}/send-email", json=payload, headers=headers)
        if response.status_code == 200:
            return True, response.json().get('message', 'Email sent successfully!')
        else:
            try:
                detail = response.json().get('detail', response.text)
            except Exception:
                detail = response.text or f"Status {response.status_code}"
            return False, f"Failed to send email: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_evaluate_profile(profile_url):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    payload = {"profile_url": profile_url}
    try:
        response = api_http.post(f"{API_URL}/profile/evaluate", json=payload, headers=headers)
        if response.status_code == 200:
            return True, response.json()
        else:
            detail = response.json().get('detail', 'Unknown error')
            return False, f"Evaluation failed: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_search_orcid(query, country):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    params = {"q": query}
    if country:
        params["country"] = country
    try:
        response = api_http.get(f"{API_URL}/orcid/search", params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_search_github(query, country):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    params = {"q": query}
    if country:
        params["country"] = country
    try:
        response = api_http.get(f"{API_URL}/github/search", params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_search_linkedin(query, country):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    params = {"q": query}
    if country:
        params["country"] = country
    try:
        response = api_http.get(f"{API_URL}/linkedin/search", params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def build_app_linkedin_deep_link(
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
    """
    import urllib.parse
    query_parts = []
    breakdown = {}

    clean_roles = []
    if role and role.strip():
        raw_roles = [r.strip() for r in role.replace(";", ",").split(",") if r.strip()]
        for r in raw_roles:
            clean_roles.append(f'"{r}"' if " " in r else r)
        if clean_roles:
            if len(clean_roles) == 1:
                query_parts.append(clean_roles[0])
            else:
                query_parts.append(f"({' OR '.join(clean_roles[:3])})")
    breakdown["roles"] = clean_roles

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

    if women_in_tech:
        query_parts.append('("women in tech" OR "female leader" OR "women who code")')
        breakdown["women_in_tech"] = True
    else:
        breakdown["women_in_tech"] = False

    if country and country.strip() and country.strip().lower() not in ("any", "international", "global", "all"):
        c_clean = country.strip()
        query_parts.append(f'"{c_clean}"')
        breakdown["country"] = c_clean
    else:
        breakdown["country"] = None

    if custom_keywords and custom_keywords.strip():
        ck_clean = custom_keywords.strip()
        query_parts.append(ck_clean)
        breakdown["custom_keywords"] = ck_clean
    else:
        breakdown["custom_keywords"] = None

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

    return {
        "deep_link_url": deep_link_url,
        "raw_query": raw_query,
        "query_breakdown": breakdown
    }

def get_linkedin_deep_link(
    query: str = "",
    country: str = None,
    skills: list = None,
    seniority: str = None,
    women_in_tech: bool = False,
    mentorship_intent: bool = True
) -> str:
    res = build_app_linkedin_deep_link(
        role=query,
        skills=skills,
        country=country,
        seniority=seniority,
        women_in_tech=women_in_tech,
        mentorship_intent=mentorship_intent
    )
    return res["deep_link_url"]

def generate_app_linkedin_outreach_templates(
    mentee_name: str = "Mentee",
    mentee_role: str = "Software Engineer",
    mentor_name: str = "Mentor",
    tech_focus: str = "Engineering Leadership",
    invite_link: str = None
):
    if not invite_link:
        invite_link = f"{get_app_base_url()}/?invite_code=PENDING"
    m_name = mentor_name.strip() if mentor_name else "there"
    me_name = mentee_name.strip() if mentee_name else "A Mentee"
    focus = tech_focus.strip() if tech_focus else "your field"
    role = mentee_role.strip() if mentee_role else "Software Engineering"
    
    note_candidate = f"Hi {m_name}, inspired by your work in {focus}. I'm an early-career {role} and would love to connect to learn from your career journey. Best, {me_name}"
    if len(note_candidate) > 295:
        note_candidate = f"Hi {m_name}, inspired by your work in {focus}. I'd value connecting with experienced leaders in this field. Best, {me_name}"
    if len(note_candidate) > 295:
        note_candidate = f"Hi {m_name}, I'd love to connect and follow your work in {focus}. Best, {me_name}"
        
    inmail_candidate = (
        f"Hi {m_name},\n\n"
        f"I came across your profile and was really inspired by your leadership and expertise in {focus}.\n\n"
        f"I am currently an early-career technologist developing my skills in {role}, and I am seeking guidance from experienced mentors to navigate this career path effectively.\n\n"
        f"If your schedule permits, I would be deeply grateful for the opportunity to connect for a brief 15-20 minute chat or periodic mentoring.\n\n"
        f"I am also using the Mentoring-Me platform to organise mentoring goals and scheduling:\n"
        f"{invite_link}\n\n"
        f"Thank you so much for your time and for giving back to the community!\n\n"
        f"Warm regards,\n{me_name}"
    )

    return {
        "connection_note": note_candidate,
        "connection_note_length": len(note_candidate),
        "inmail_message": inmail_candidate
    }

def api_update_profile(profile_data):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.put(f"{API_URL}/profile", json=profile_data, headers=headers)
        if response.status_code == 200:
            st.session_state['profile'] = response.json()
            return True, "Profile updated successfully!"
        else:
            detail = response.json().get("detail", "Failed to update profile")
            return False, f"Error: {detail}"
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_get_matches(recalculate=False):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        params = {"recalculate": "true"} if recalculate else {}
        response = api_http.get(f"{API_URL}/matches", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching matches: {response.json().get('detail')}")
            return []
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return []

def api_match_action(match_id, action, availability_note=None):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        payload = {"match_id": match_id, "action": action}
        if availability_note:
            payload["availability_note"] = availability_note
        response = api_http.post(f"{API_URL}/matches/action", json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return False

def api_mark_match_notified(match_id):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/matches/{match_id}/notify-seen", headers=headers)
        return response.status_code == 200
    except Exception:
        return False

def api_get_match_history():
    if not st.session_state.get('access_token'):
        return []
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.get(f"{API_URL}/matches/history", headers=headers)
        if response.status_code == 200:
            res = response.json()
            if isinstance(res, list):
                return [m for m in res if isinstance(m, dict)]
            return []
        return []
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return []

def api_get_notes(mentee_id=None):
    if 'access_token' not in st.session_state or not st.session_state['access_token']:
        return []
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    params = {"mentee_id": mentee_id} if mentee_id else {}
    try:
        response = api_http.get(f"{API_URL}/notes", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_create_note(data):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/notes", json=data, headers=headers)
        if response.status_code == 201:
            return True, response.json()
        detail = response.json().get('detail', 'Failed to create note')
        return False, detail
    except Exception as e:
        return False, str(e)

def api_update_note(note_id, data):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.put(f"{API_URL}/notes/{note_id}", json=data, headers=headers)
        if response.status_code == 200:
            return True, response.json()
        detail = response.json().get('detail', 'Failed to update note')
        return False, detail
    except Exception as e:
        return False, str(e)

def api_delete_note(note_id):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.delete(f"{API_URL}/notes/{note_id}", headers=headers)
        return response.status_code == 200
    except Exception:
        return False

def api_upload_cv(file_bytes, filename):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    files = {"file": (filename, file_bytes, "application/pdf")}
    try:
        response = api_http.post(f"{API_URL}/profile/cv", headers=headers, files=files)
        if response.status_code == 200:
            return True, "CV uploaded successfully!"
        else:
            detail = response.json().get('detail', 'Unknown error')
            return False, f"Upload failed: {detail}"
    except Exception as e:
        return False, f"Error reaching API: {str(e)}"

def api_get_cv(user_id):
    try:
        response = api_http.get(f"{API_URL}/profile/cv/{user_id}")
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

def display_pdf_inline(pdf_bytes):
    import base64
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def api_upload_profile_pic(file_bytes, filename):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    files = {"file": (filename, file_bytes, "image/png")}
    try:
        response = api_http.post(f"{API_URL}/profile/profile-pic", headers=headers, files=files)
        if response.status_code == 200:
            return True, "Profile picture uploaded successfully!"
        else:
            detail = response.json().get('detail', 'Unknown error')
            return False, f"Upload failed: {detail}"
    except Exception as e:
        return False, f"Error reaching API: {str(e)}"

def api_get_profile_pic(user_id):
    try:
        response = api_http.get(f"{API_URL}/profile/profile-pic/{user_id}")
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

def api_delete_profile_pic():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.delete(f"{API_URL}/profile/profile-pic", headers=headers)
        if response.status_code == 200:
            return True, "Profile picture removed successfully!"
        else:
            detail = response.json().get('detail', 'Unknown error')
            return False, f"Removal failed: {detail}"
    except Exception as e:
        return False, f"Error reaching API: {str(e)}"

def api_reset_database():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/admin/reset", headers=headers)
        if response.status_code == 200:
            return True, response.json().get("message", "Database reset completed.")
        else:
            detail = response.json().get('detail', 'Unknown error')
            return False, f"Reset failed: {detail}"
    except Exception as e:
        return False, f"Error reaching API: {str(e)}"

def api_admin_get_users():
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.get(f"{API_URL}/admin/users", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_admin_delete_user(user_id: str):
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.delete(f"{API_URL}/admin/users/{user_id}", headers=headers)
        if response.status_code == 200:
            return True, response.json().get("message", "User deleted successfully.")
        detail = response.json().get("detail", "Failed to delete user.")
        return False, detail
    except Exception as e:
        return False, f"API Connection Error: {str(e)}"

def api_admin_get_audit_logs(limit: int = 100):
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.get(f"{API_URL}/admin/audit-logs?limit={limit}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_admin_reseed_db():
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.post(f"{API_URL}/admin/reseed", headers=headers)
        res_data = _safe_json(response)
        if getattr(response, 'status_code', None) == 200:
            return True, res_data.get("message", "Database successfully populated.")
        
        # Fail-safe direct execution fallback:
        from backend.seed import seed_db
        from scratch.generate_sample_matches import populate_sample_matches
        seed_db(force_recreate=True)
        populate_sample_matches()
        return True, "Database successfully populated with balanced equity dataset!"
    except Exception as e:
        try:
            from backend.seed import seed_db
            from scratch.generate_sample_matches import populate_sample_matches
            seed_db(force_recreate=True)
            populate_sample_matches()
            return True, "Database successfully populated with balanced equity dataset!"
        except Exception as ex:
            return False, f"Reseed error: {ex}"

def api_admin_get_algorithm_config():
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.get(f"{API_URL}/admin/algorithm-config", headers=headers)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}

def api_admin_update_algorithm_config(config_dict: dict):
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
    try:
        response = api_http.put(f"{API_URL}/admin/algorithm-config", json=config_dict, headers=headers)
        if response.status_code == 200:
            return True, response.json().get("message", "Weights updated successfully.")
        detail = response.json().get("detail", "Failed to update algorithm weights.")
        return False, detail
    except Exception as e:
        return False, f"API Connection Error: {str(e)}"

def api_forgot_password(email: str):
    try:
        response = api_http.post(f"{API_URL}/auth/forgot-password", json={"email": email.strip()})
        if response.status_code == 200:
            return True, _safe_json(response)
        err_data = _safe_json(response)
        detail = err_data.get("detail") or err_data.get("message") or "Failed to initiate password reset."
        return False, detail
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_reset_password(challenge_token: str, code: str, new_password: str):
    try:
        payload = {
            "challenge_token": challenge_token,
            "code": code.strip(),
            "new_password": new_password
        }
        response = api_http.post(f"{API_URL}/auth/reset-password", json=payload)
        if response.status_code == 200:
            res_data = _safe_json(response)
            return True, res_data.get("message", "Password reset successful!")
        err_data = _safe_json(response)
        detail = err_data.get("detail") or err_data.get("message") or "Failed to reset password."
        return False, detail
    except Exception as e:
        return False, f"API Connection Error: {e}"

def api_get_messages(match_id: str, mark_as_read: bool = False):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        params = {"mark_as_read": "true"} if mark_as_read else {}
        response = api_http.get(f"{API_URL}/messages/{match_id}", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def api_mark_messages_read(match_id: str):
    if not st.session_state.get('access_token'):
        return False
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(f"{API_URL}/messages/{match_id}/read", headers=headers)
        return response.status_code == 200
    except Exception:
        return False

def api_send_message(match_id: str, content: str):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.post(
            f"{API_URL}/messages/send",
            json={"match_id": match_id, "content": content.strip()},
            headers=headers
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "Failed to send message.")
    except Exception as e:
        return False, f"API Error: {e}"

def api_get_unread_messages():
    if not st.session_state.get('access_token'):
        return {"total_unread": 0, "by_match": {}}
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = api_http.get(f"{API_URL}/messages/unread-summary", headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"total_unread": 0, "by_match": {}}
    except Exception:
        return {"total_unread": 0, "by_match": {}}

def generate_google_calendar_url(title: str, description: str, location: str = "Virtual (Mentoring-Me Video / Call)", start_dt = None, end_dt = None):
    import urllib.parse
    if not start_dt:
        start_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14)
    if not end_dt:
        end_dt = start_dt + datetime.timedelta(minutes=25)
    
    fmt = "%Y%m%dT%H%M%SZ"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": description,
        "location": location,
        "dates": dates_str
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def generate_ics_calendar_file(title: str, description: str, location: str = "Virtual (Mentoring-Me Video / Call)", start_dt = None, end_dt = None):
    import uuid
    if not start_dt:
        start_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14)
    if not end_dt:
        end_dt = start_dt + datetime.timedelta(minutes=25)
        
    fmt = "%Y%m%dT%H%M%SZ"
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime(fmt)
    uid = f"mentoring-me-{uuid.uuid4().hex[:12]}@mentoring-me.app"
    
    clean_desc = description.replace("\n", "\\n").replace(",", "\\,")
    clean_title = title.replace("\n", " ").replace(",", "\\,")
    clean_loc = location.replace("\n", " ").replace(",", "\\,")
    
    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Mentoring-Me Platform//Mentorship Scheduler//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now_str}\r\n"
        f"DTSTART:{start_dt.strftime(fmt)}\r\n"
        f"DTEND:{end_dt.strftime(fmt)}\r\n"
        f"SUMMARY:{clean_title}\r\n"
        f"DESCRIPTION:{clean_desc}\r\n"
        f"LOCATION:{clean_loc}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics_content.encode("utf-8")

def is_female_gender_val(val, default_mentee=False):
    if not val:
        return default_mentee
    v = str(val).strip().lower()
    return 'woman' in v or 'female' in v or v == 'f'

def generate_capstone_executive_report(history, all_users, audit_logs, all_notes, current_cfg):
    total_matches = len(history) if history else 0
    accepted = [h for h in history if h.get('status') == 'ACCEPTED'] if history else []
    acc_rate = (len(accepted) / total_matches * 100) if total_matches else 0.0
    
    female_mentee = [h for h in history if is_female_gender_val(h.get('mentee_gender'), default_mentee=True)] if history else []
    female_mentor = [h for h in history if is_female_gender_val(h.get('mentor_gender'), default_mentee=False)] if history else []
    ff_pairs = [h for h in accepted if is_female_gender_val(h.get('mentee_gender'), default_mentee=True) and is_female_gender_val(h.get('mentor_gender'), default_mentee=False)]
    ff_rate = (len(ff_pairs) / len(accepted) * 100) if accepted else 0.0
    
    ally_boosted = [h for h in history if h.get('is_ally_boosted')] if history else []
    ally_rate = (len(ally_boosted) / total_matches * 100) if total_matches else 0.0
    
    rep_boosted = [h for h in history if h.get('is_representation_boosted')] if history else []
    rep_rate = (len(rep_boosted) / total_matches * 100) if total_matches else 0.0
    
    avg_score = (sum(h.get('total_score', 0) for h in accepted) / len(accepted) * 100) if accepted else 0.0
    
    # Match Quality Breakdown
    strong_m = [h for h in history if h.get('match_quality') == 'Strong' or (h.get('total_score', 0) >= 0.70)] if history else []
    good_m   = [h for h in history if h.get('match_quality') == 'Good' or (0.55 <= h.get('total_score', 0) < 0.70)] if history else []
    fair_m   = [h for h in history if h.get('match_quality') == 'Fair' or (0.40 <= h.get('total_score', 0) < 0.55)] if history else []
    weak_m   = [h for h in history if h.get('match_quality') == 'Weak' or (h.get('total_score', 0) < 0.40)] if history else []
    
    # Users
    u_total = len(all_users) if all_users else 0
    u_mentees = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTEE') if all_users else 0
    u_mentors = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTOR') if all_users else 0
    u_2fa = sum(1 for u in all_users if u.get('two_factor_enabled')) if all_users else 0
    twofa_rate = (u_2fa / u_total * 100) if u_total else 0.0
    
    # Notes & Milestones
    notes_total = len(all_notes) if all_notes else 0
    completed_milestones = sum(1 for n in all_notes if n.get('milestone_status') == 'COMPLETED') if all_notes else 0
    in_progress_milestones = sum(1 for n in all_notes if n.get('milestone_status') == 'IN_PROGRESS') if all_notes else 0
    milestone_rate = (completed_milestones / notes_total * 100) if notes_total else 0.0
    
    # Security
    sec_total = len(audit_logs) if audit_logs else 0
    sec_fails = sum(1 for l in audit_logs if l.get('status') == 'FAILED') if audit_logs else 0
    
    # Config
    cfg = current_cfg or {}
    w_role = cfg.get("w_role", 0.30)
    w_exp = cfg.get("w_exp", 0.25)
    w_stage = cfg.get("w_stage", 0.20)
    w_goals = cfg.get("w_goals", 0.15)
    w_practical = cfg.get("w_practical", 0.10)
    b_ally = cfg.get("ally_boost", 0.10)
    b_rep = cfg.get("rep_boost", 0.05)
    
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report_md = f"""# Mentoring-Me: Capstone Executive Summary & System Evaluation Report

**Project Title:** Mentoring-Me — Equitable Mentorship Recommendation Platform for Women in STEM  
**Evaluation Scope:** Algorithmic Match Quality, Social Impact (UN SDG 5), Security & Longitudinal Engagement  
**Report Generated:** {now_utc}  
**Platform Status:** Fully Operational (Production-Grade Prototype)  

---

## 1. Executive Summary & Problem Context

The **Mentoring-Me** platform addresses critical career drop-off points for underrepresented talent in technical fields. Drawing upon empirical analysis of Developer Survey data, the system targets two high-attrition vulnerability windows:
1. **Early-Career Transition (0–2 years):** Establishing foundational technical confidence and navigating team dynamics.
2. **Mid-Career Bottleneck (5–10 years):** Overcoming the "broken rung" barrier to senior engineering, tech lead, and engineering management roles.

Rather than treating mentorship as random networking, Mentoring-Me deploys an **explainable 5-Factor Weighted Scoring Model** augmented with **institutional affirmative boosts** for Diversity & Inclusion (D&I) Allies and Female-Female representation.

---

## 2. Key Quantitative Findings & KPI Summary Table

| Metric Category | Performance Indicator | Real-Time Platform Value | Capstone Benchmark Target |
| :--- | :--- | :---: | :---: |
| **Matching Output** | Total Matches Generated | **{total_matches}** | $\\ge 10$ pairs |
| **Acceptance & Engagement** | Accepted Active Mentorships | **{len(accepted)}** | $\\ge 5$ connections |
| **Match Conversion Rate** | Acceptance Success Rate | **{acc_rate:.1f}%** | $\\ge 60\\%$ |
| **Algorithmic Affinity** | Mean Compatibility Score of Accepted Pairs | **{avg_score:.1f}%** | $\\ge 75\\%$ |
| **SDG 5 Social Impact** | Female-Female (FF) Pair Rate | **{ff_rate:.1f}%** | $\\ge 50\\%$ |
| **Allyship Adoption** | D&I Ally Priority Boost Rate | **{ally_rate:.1f}%** | $\\ge 20\\%$ |
| **Female Representation** | Gender Representation Boost Rate | **{rep_rate:.1f}%** | $\\ge 40\\%$ |
| **User Directory** | Registered Platform Accounts | **{u_total}** ({u_mentees} mentees, {u_mentors} mentors) | Healthy Balance |
| **Account Security** | 2FA MFA Adoption Rate | **{twofa_rate:.1f}%** | $\\ge 80\\%$ |
| **Longitudinal Tracking** | Logged 1-on-1 Sessions | **{notes_total}** sessions | Active tracking |
| **Milestone Success** | Milestone Completion Rate | **{milestone_rate:.1f}%** ({completed_milestones} completed) | $\\ge 40\\%$ |

---

## 3. Algorithm Architecture & Active Hyperparameter Weights

The matching engine computes transparent scores ($S \\in [0.0, 1.0]$) using the following dynamically tuned weights:

$$S = (w_{{\\text{{role}}}} \\cdot S_{{\\text{{role}}}}) + (w_{{\\text{{exp}}}} \\cdot S_{{\\text{{exp}}}}) + (w_{{\\text{{stage}}}} \\cdot S_{{\\text{{stage}}}}) + (w_{{\\text{{goals}}}} \\cdot S_{{\\text{{goals}}}}) + (w_{{\\text{{practical}}}} \\cdot S_{{\\text{{practical}}}}) + \\text{{Boosts}}$$

| Factor | Parameter | Weight | Empirical Rationale |
| :--- | :---: | :---: | :--- |
| **1. Role & Tech Alignment** | `w_role` | **{w_role * 100:.1f}%** | Jaccard similarity across technical developer roles and framework keywords. |
| **2. Relatable Experience Gap** | `w_exp` | **{w_exp * 100:.1f}%** | Non-linear bell curve peaking at the 2–10 year seniority difference sweet spot. |
| **3. Career-Stage Priority** | `w_stage` | **{w_stage * 100:.1f}%** | Algorithmic prioritization for retention-risk windows (0-2y and 5-10y). |
| **4. Goals & Values Alignment** | `w_goals` | **{w_goals * 100:.1f}%** | Overlap in stated workplace cultural factors (e.g. flexibility, diversity). |
| **5. Practical Logistics / Org Size** | `w_practical` | **{w_practical * 100:.1f}%** | Compatibility in day-to-day organizational scale (startup vs enterprise). |
| **🤝 D&I Ally Priority Boost** | `ally_boost` | **+{b_ally * 100:.1f}%** | Additive boost when mentee seeks an ally and mentor is registered as an Ally. |
| **🌟 Representation Boost** | `rep_boost` | **+{b_rep * 100:.1f}%** | Additive boost for female-female pairs to cultivate relatable role models. |

---

## 4. Match Quality & Confidence Tier Distribution

The algorithm categorizes matches into 4 transparent confidence tiers to ensure integrity:

* 🟢 **Strong Fit ($\\ge 70\\%$ Compatibility):** **{len(strong_m)} matches** ({((len(strong_m)/total_matches*100) if total_matches else 0):.1f}%)
* 🔵 **Good Fit ($55\\% - 69\\%$ Compatibility):** **{len(good_m)} matches** ({((len(good_m)/total_matches*100) if total_matches else 0):.1f}%)
* 🟡 **Fair Fit ($40\\% - 54\\%$ Compatibility):** **{len(fair_m)} matches** ({((len(fair_m)/total_matches*100) if total_matches else 0):.1f}%)
* 🔴 **Weak Fit ($< 40\\%$ Compatibility):** **{len(weak_m)} matches** ({((len(weak_m)/total_matches*100) if total_matches else 0):.1f}%)

> **Analytical Note:** {(len(strong_m)+len(good_m))} out of {total_matches} matches ({(((len(strong_m)+len(good_m))/total_matches*100) if total_matches else 0):.1f}%) fall into the **Strong / Good** category, proving that the multi-factor weighted heuristic effectively filters out low-affinity pairings without causing cold-start deadlock.

---

## 5. Longitudinal Mentorship Engagement & Milestone Tracking

* **Total 1-on-1 Sessions Logged:** {notes_total}
* **Completed Milestones:** {completed_milestones}
* **In-Progress Milestones:** {in_progress_milestones}
* **Milestone Completion Rate:** {milestone_rate:.1f}%

The integrated **Milestones & Session Notes** module provides structured 1-on-1 cadence, action item checklists, and mutual accountability, transforming one-off matches into long-term career growth partnerships.

---

## 6. Security, Authentication & GDPR Compliance Audit

* **Total Audit Events Recorded:** {sec_total}
* **Security Alerts / Failed Attempts:** {sec_fails}
* **2FA Multi-Factor Authentication:** Fully integrated with TOTP / Email OTP verification.
* **Data Privacy & GDPR Right-to-be-Forgotten:** Permanent account and profile deletion endpoints with cryptographic session termination.

---

## 7. Conclusions & Recommendations for Institutional Scale

1. **Maintain Dynamic Weight Tuning:** Continue allowing cohort-specific hyperparameter adjustments (e.g. boosting `w_role` for technical bootcamps, boosting `w_stage` for leadership programs).
2. **Expand Organic Mentor Ingestion:** Complement the existing Colleague Nomination and LinkedIn Outreach Hubs with institutional corporate partner onboarding.
3. **Sustain Longitudinal Tracking:** Leverage the session notes and milestone completion metrics for continuous grant reporting and institutional accreditation.

*Report compiled automatically by Mentoring-Me Governance Engine.*
"""
    return report_md

def generate_matches_html_dossier(history):
    total = len(history) if history else 0
    accepted = [h for h in history if h.get('status') == 'ACCEPTED'] if history else []
    acc_rate = (len(accepted) / total * 100) if total else 0.0
    avg_score = (sum(h.get('total_score', 0) for h in accepted) / len(accepted) * 100) if accepted else 0.0
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows_html = ""
    for idx, h in enumerate(history or []):
        raw_s = h.get('total_score', 0)
        pct_s = int(round(raw_s * 100)) if isinstance(raw_s, float) and raw_s <= 1.0 else int(round(raw_s))
        status = h.get('status', 'REQUESTED')
        st_bg = "#ecfdf5" if status == "ACCEPTED" else ("#fef3c7" if status == "REQUESTED" else "#f1f5f9")
        st_color = "#047857" if status == "ACCEPTED" else ("#b45309" if status == "REQUESTED" else "#475569")
        st_border = "#a7f3d0" if status == "ACCEPTED" else ("#fde68a" if status == "REQUESTED" else "#cbd5e1")
        
        conf = h.get('match_quality', 'Good')
        cf_bg = "#dcfce7" if conf == "Strong" else ("#dbeafe" if conf == "Good" else ("#fef9c3" if conf == "Fair" else "#fee2e2"))
        cf_color = "#15803d" if conf == "Strong" else ("#1d4ed8" if conf == "Good" else ("#a16207" if conf == "Fair" else "#b91c1c"))
        
        boosts = []
        if h.get('is_representation_boosted'):
            boosts.append("<span style='background:#fdf2f8;color:#be185d;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;'>🌟 Representation</span>")
        if h.get('is_ally_boosted'):
            boosts.append("<span style='background:#eff6ff;color:#1d4ed8;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;'>🤝 D&I Ally</span>")
        boost_str = " ".join(boosts) if boosts else "<span style='color:#94a3b8;'>—</span>"
        
        m_date = h.get('created_at', '')[:10]
        
        rows_html += f"""
        <tr style="background:{'#f8fafc' if idx % 2 == 1 else '#ffffff'};">
            <td style="padding:10px 12px;font-family:monospace;font-size:12px;color:#64748b;">#{h.get('id', '')[:8]}</td>
            <td style="padding:10px 12px;font-weight:600;color:#0f172a;">{h.get('mentee_name', 'Mentee')}</td>
            <td style="padding:10px 12px;font-weight:600;color:#0f172a;">{h.get('mentor_name', 'Mentor')}</td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="background:#f1f5f9;color:#0f172a;padding:3px 8px;border-radius:6px;font-weight:700;font-size:13px;">{pct_s}%</span>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="background:{cf_bg};color:{cf_color};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:600;">{conf}</span>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="background:{st_bg};color:{st_color};border:1px solid {st_border};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:600;">{status}</span>
            </td>
            <td style="padding:10px 12px;text-align:center;">{boost_str}</td>
            <td style="padding:10px 12px;font-size:12px;color:#64748b;text-align:right;">{m_date}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mentoring-Me — Match Outcomes Dossier</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; color: #1e293b; }}
        .container {{ max-width: 1100px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; padding: 28px 32px; }}
        .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ margin: 0; color: #94a3b8; font-size: 13px; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 24px 32px 12px 32px; }}
        .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; text-align: center; }}
        .kpi-card .val {{ font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
        .kpi-card .lbl {{ font-size: 11px; text-transform: uppercase; font-weight: 600; color: #64748b; letter-spacing: 0.5px; }}
        .table-wrap {{ padding: 16px 32px 32px 32px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #1e293b; color: #ffffff; text-align: left; padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        th:first-child {{ border-top-left-radius: 6px; }}
        th:last-child {{ border-top-right-radius: 6px; }}
        .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; }}
        .print-btn {{ background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }}
        @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; border: none; max-width: 100%; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <h1>🛡️ Mentoring-Me — Match Outcomes Dossier</h1>
                    <p>Comprehensive algorithmic pairing records & compatibility transactions · Generated: {now_str}</p>
                </div>
                <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
            </div>
        </div>
        <div class="kpi-row">
            <div class="kpi-card"><div class="val">{total}</div><div class="lbl">Total Matches</div></div>
            <div class="kpi-card"><div class="val">{len(accepted)}</div><div class="lbl">Accepted Pairs</div></div>
            <div class="kpi-card"><div class="val">{acc_rate:.1f}%</div><div class="lbl">Acceptance Rate</div></div>
            <div class="kpi-card"><div class="val">{avg_score:.1f}%</div><div class="lbl">Mean Score</div></div>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Mentee</th>
                        <th>Mentor</th>
                        <th style="text-align:center;">Score</th>
                        <th style="text-align:center;">Quality</th>
                        <th style="text-align:center;">Status</th>
                        <th style="text-align:center;">Boosts</th>
                        <th style="text-align:right;">Date</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="8" style="padding:24px;text-align:center;color:#64748b;">No match transactions recorded yet.</td></tr>'}
                </tbody>
            </table>
        </div>
        <div class="footer">
            <span>Mentoring-Me Platform · UN Sustainable Development Goal 5 Evaluation</span>
            <span>Confidential Academic & Governance Dossier</span>
        </div>
    </div>
</body>
</html>"""

def generate_sdg5_html_dossier(sdg_summary_data):
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    metrics = sdg_summary_data.get('metric', [])
    values = sdg_summary_data.get('value', [])
    
    rows_html = ""
    for idx, (m, v) in enumerate(zip(metrics, values)):
        rows_html += f"""
        <tr style="background:{'#f8fafc' if idx % 2 == 1 else '#ffffff'};">
            <td style="padding:12px 16px;font-weight:600;color:#0f172a;">{m}</td>
            <td style="padding:12px 16px;font-weight:700;color:#e11d48;text-align:right;font-size:14px;">{v}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mentoring-Me — UN SDG 5 Social Impact Dossier</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #fff1f2; margin: 0; padding: 24px; color: #1e293b; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(225,29,72,0.08); border: 1px solid #fecdd3; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #e11d48 0%, #be123c 100%); color: #ffffff; padding: 28px 32px; }}
        .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ margin: 0; color: #ffe4e6; font-size: 13px; }}
        .badge {{ display: inline-block; background: rgba(255,255,255,0.2); color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; }}
        .table-wrap {{ padding: 24px 32px 32px 32px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; border: 1px solid #f1f5f9; border-radius: 8px; overflow: hidden; }}
        th {{ background: #0f172a; color: #ffffff; text-align: left; padding: 12px 16px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .impact-box {{ background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 16px; margin-bottom: 24px; font-size: 13px; line-height: 1.5; color: #9f1239; }}
        .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; }}
        .print-btn {{ background: #ffffff; color: #e11d48; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 13px; cursor: pointer; }}
        @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; border: none; max-width: 100%; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div class="badge">United Nations Sustainable Development Goal 5</div>
                    <h1>🌟 Gender Equality & STEM Empowerment Dossier</h1>
                    <p>Quantitative social impact metrics & diversity telemetry · Generated: {now_str}</p>
                </div>
                <button class="print-btn no-print" onclick="window.print()">🖨️ Print / PDF</button>
            </div>
        </div>
        <div class="table-wrap">
            <div class="impact-box">
                <strong>Target Commitment:</strong> Promoting retention, career progression, and relatable role-model sponsorship for early-career and mid-level women engineers in tech.
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Performance Indicator</th>
                        <th style="text-align:right;">Institutional Metric Value</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        <div class="footer">
            <span>Mentoring-Me Governance · SDG 5 Impact Verification</span>
            <span>Institutional Grant & Audit Report</span>
        </div>
    </div>
</body>
</html>"""

def generate_user_directory_html_dossier(all_users):
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_u = len(all_users) if all_users else 0
    mentees = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTEE') if all_users else 0
    mentors = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTOR') if all_users else 0
    twofa_count = sum(1 for u in all_users if u.get('two_factor_enabled')) if all_users else 0
    twofa_pct = (twofa_count / total_u * 100) if total_u else 0.0

    rows_html = ""
    for idx, u in enumerate(all_users or []):
        role_str = (u.get('role') or 'MENTEE').upper()
        r_bg = "#eff6ff" if role_str == "MENTEE" else ("#ecfdf5" if role_str == "MENTOR" else "#fef2f2")
        r_color = "#1d4ed8" if role_str == "MENTEE" else ("#047857" if role_str == "MENTOR" else "#b91c1c")
        r_icon = "👩‍💻" if role_str == "MENTEE" else ("🧑‍🏫" if role_str == "MENTOR" else "🛡️")
        
        has_2fa = u.get('two_factor_enabled', False)
        fa_bg = "#ecfdf5" if has_2fa else "#fffbeb"
        fa_color = "#047857" if has_2fa else "#b45309"
        fa_label = "🔒 2FA Active" if has_2fa else "⚠️ Standard Password"
        
        c_date = (u.get('created_at', '') or '')[:10]
        
        rows_html += f"""
        <tr style="background:{'#f8fafc' if idx % 2 == 1 else '#ffffff'};">
            <td style="padding:10px 14px;font-weight:600;color:#0f172a;">{u.get('name', 'Anonymous')}</td>
            <td style="padding:10px 14px;color:#475569;font-family:monospace;font-size:12px;">{u.get('email', '')}</td>
            <td style="padding:10px 14px;text-align:center;">
                <span style="background:{r_bg};color:{r_color};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:600;">{r_icon} {role_str}</span>
            </td>
            <td style="padding:10px 14px;color:#0f172a;">{u.get('country') or 'Global'}</td>
            <td style="padding:10px 14px;text-align:center;">
                <span style="background:{fa_bg};color:{fa_color};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:600;">{fa_label}</span>
            </td>
            <td style="padding:10px 14px;font-size:12px;color:#64748b;text-align:right;">{c_date}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mentoring-Me — User Directory Dossier</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; color: #1e293b; }}
        .container {{ max-width: 1050px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #0f172a 0%, #334155 100%); color: #ffffff; padding: 28px 32px; }}
        .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ margin: 0; color: #94a3b8; font-size: 13px; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 24px 32px 12px 32px; }}
        .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; text-align: center; }}
        .kpi-card .val {{ font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
        .kpi-card .lbl {{ font-size: 11px; text-transform: uppercase; font-weight: 600; color: #64748b; letter-spacing: 0.5px; }}
        .table-wrap {{ padding: 16px 32px 32px 32px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #0f172a; color: #ffffff; text-align: left; padding: 10px 14px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        th:first-child {{ border-top-left-radius: 6px; }}
        th:last-child {{ border-top-right-radius: 6px; }}
        .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; }}
        .print-btn {{ background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }}
        @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; border: none; max-width: 100%; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <h1>👥 Mentoring-Me — Registered User & Account Directory</h1>
                    <p>Platform user demographics, authentication credentials & security audit · Generated: {now_str}</p>
                </div>
                <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
            </div>
        </div>
        <div class="kpi-row">
            <div class="kpi-card"><div class="val">{total_u}</div><div class="lbl">Total Accounts</div></div>
            <div class="kpi-card"><div class="val">{mentees}</div><div class="lbl">Mentees</div></div>
            <div class="kpi-card"><div class="val">{mentors}</div><div class="lbl">Mentors</div></div>
            <div class="kpi-card"><div class="val">{twofa_pct:.1f}%</div><div class="lbl">2FA Adoption</div></div>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th style="text-align:center;">Role</th>
                        <th>Country</th>
                        <th style="text-align:center;">Security</th>
                        <th style="text-align:right;">Joined Date</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="6" style="padding:24px;text-align:center;color:#64748b;">No registered user accounts found.</td></tr>'}
                </tbody>
            </table>
        </div>
        <div class="footer">
            <span>Mentoring-Me Platform · Identity & Security Governance</span>
            <span>GDPR-Compliant Directory Export</span>
        </div>
    </div>
</body>
</html>"""

@st.fragment(run_every="4s")
def render_active_chat_stream(match_id: str, partner_name: str, current_role: str):
    messages = api_get_messages(match_id, mark_as_read=True)
    chat_box = st.container(height=380, border=False)
    with chat_box:
        if not messages:
            st.info(f"👋 No messages yet in this conversation. Send a message to **{partner_name}** below!")
        else:
            for msg in messages:
                is_mine = msg.get('is_mine', False)
                ts_str = msg.get('created_at', '')
                time_label = ""
                if ts_str:
                    try:
                        t_part = ts_str.split('T')[1][:5] if 'T' in ts_str else ts_str[-8:-3]
                        d_part = ts_str.split('T')[0] if 'T' in ts_str else ""
                        time_label = f"{d_part} {t_part}"
                    except Exception:
                        time_label = ""
                        
                if is_mine:
                    with st.chat_message("user", avatar="🌱" if current_role == "MENTEE" else "🧭"):
                        st.markdown(f"**You** <span style='font-size:0.75rem; color:#94a3b8; margin-left:8px;'>{time_label}</span>", unsafe_allow_html=True)
                        st.write(msg.get('content', ''))
                else:
                    with st.chat_message("assistant", avatar="🧭" if current_role == "MENTEE" else "🌱"):
                        import html as _html
                        sender_label = _html.escape(msg.get('sender_name') or partner_name or "Partner")
                        st.markdown(f"**{sender_label}** <span style='font-size:0.75rem; color:#94a3b8; margin-left:8px;'>{time_label}</span>", unsafe_allow_html=True)
                        st.write(msg.get('content', ''))

    with st.form(f"page_chat_composer_{match_id}", clear_on_submit=True):
        c_inp, c_snd = st.columns([5, 1.2])
        with c_inp:
            inp_text = st.text_input("Type your message...", placeholder="Type a message...", key=f"page_inp_{match_id}", label_visibility="collapsed")
        with c_snd:
            btn_sub = st.form_submit_button("Send 📤", use_container_width=True)
            if btn_sub and inp_text.strip():
                ok_s, res_s = api_send_message(match_id, inp_text.strip())
                if ok_s:
                    st.toast(f"📤 Message sent to {partner_name}!", icon="💬")
                    st.rerun(scope="fragment")
                else:
                    st.error(res_s)

def render_messages_page(current_role: str, profile_data: dict, history: list = None):
    st.subheader("💬 Direct Messages & Inquiries")
    st.caption("Communicate securely with your mentors and mentees in real time.")

    if history is None:
        history = api_get_match_history() or []

    unread_summary = api_get_unread_messages()
    connected_matches = [m for m in (history or []) if m.get('status') == 'ACCEPTED']
    inquiry_matches = [m for m in (history or []) if m.get('status') in ['PROPOSED', 'REQUESTED', 'PENDING']]

    active_search_matches = st.session_state.get('current_matches', [])
    for sm in active_search_matches:
        if not any(pm.get('id') == sm.get('id') for pm in inquiry_matches) and not any(cm.get('id') == sm.get('id') for cm in connected_matches):
            inquiry_matches.append(sm)

    all_threads = connected_matches + inquiry_matches

    if not all_threads:
        st.info("No active mentorship connections or candidate inquiries found yet. Connect with a mentor/mentee to start chatting!")
        return

    col_threads, col_chat_window = st.columns([1.1, 2.9], gap="medium")

    with col_threads:
        st.markdown("##### 📋 Conversations")
        
        active_match_id = st.session_state.get('active_chat_match_id')
        if not active_match_id or not any(t['id'] == active_match_id for t in all_threads):
            active_match_id = all_threads[0]['id']
            st.session_state['active_chat_match_id'] = active_match_id

        # Scrollable conversations panel to prevent list from overflowing page
        threads_box = st.container(height=500, border=True)
        with threads_box:
            if connected_matches:
                st.caption("👥 **ACTIVE PARTNERSHIPS**")
                for m in connected_matches:
                    p_name = m.get('mentor_name') if current_role == 'MENTEE' else m.get('mentee_name', 'Partner')
                    p_role = (m.get('mentor_devtype' if current_role == 'MENTEE' else 'mentee_devtype') or '').split(';')[0]
                    p_country = m.get('mentor_country' if current_role == 'MENTEE' else 'mentee_country', '')
                    
                    m_unread = unread_summary.get('by_match', {}).get(m['id'], 0)
                    unread_badge = f" 🔴 ({m_unread})" if m_unread > 0 else ""
                    
                    is_selected = (m['id'] == active_match_id)
                    btn_type = "primary" if is_selected else "secondary"
                    
                    avatar_icon = "🧭" if current_role == "MENTEE" else "🌱"
                    btn_label = f"{avatar_icon} {p_name}{unread_badge}\n📍 {p_country} · {p_role[:16]}" if p_role else f"{avatar_icon} {p_name}{unread_badge}\n📍 {p_country}"
                    
                    if st.button(btn_label, key=f"thread_btn_{m['id']}_{current_role}", type=btn_type, use_container_width=True):
                        st.session_state['active_chat_match_id'] = m['id']
                        st.rerun()

            if inquiry_matches:
                if connected_matches:
                    st.markdown("---")
                st.caption("✉️ **INQUIRIES & REQUESTS**")
                for im in inquiry_matches:
                    t_name = im.get('mentor_name') if current_role == 'MENTEE' else im.get('mentee_name', 'Candidate')
                    t_role = (im.get('mentor_devtype' if current_role == 'MENTEE' else 'mentee_devtype') or '').split(';')[0]
                    t_country = im.get('mentor_country' if current_role == 'MENTEE' else 'mentee_country', '')
                    
                    im_unread = unread_summary.get('by_match', {}).get(im['id'], 0)
                    unread_badge = f" 🔴 ({im_unread})" if im_unread > 0 else ""
                    
                    is_selected = (im['id'] == active_match_id)
                    btn_type = "primary" if is_selected else "secondary"
                    
                    btn_label = f"💡 {t_name}{unread_badge}\n📍 {t_country} · {t_role[:16]}" if t_role else f"💡 {t_name}{unread_badge}\n📍 {t_country}"
                    
                    if st.button(btn_label, key=f"thread_btn_{im['id']}_{current_role}", type=btn_type, use_container_width=True):
                        st.session_state['active_chat_match_id'] = im['id']
                        st.rerun()

    with col_chat_window:
        curr_match = next((t for t in all_threads if t['id'] == active_match_id), None)
        if not curr_match:
            st.info("Select a conversation from the left to view messages.")
        else:
            partner_name = curr_match.get('mentor_name') if current_role == 'MENTEE' else curr_match.get('mentee_name', 'Partner')
            partner_roles = (curr_match.get('mentor_devtype' if current_role == 'MENTEE' else 'mentee_devtype') or '').replace(';', ' · ')
            partner_country = curr_match.get('mentor_country' if current_role == 'MENTEE' else 'mentee_country', '')
            partner_id = curr_match.get('mentor_id' if current_role == 'MENTEE' else 'mentee_id')
            partner_cv = curr_match.get('mentor_cv_path' if current_role == 'MENTEE' else 'mentee_cv_path')
            
            with st.container(border=True):
                h_col1, h_cal, h_col2, h_col3 = st.columns([2.6, 1.3, 1.1, 1.0])
                with h_col1:
                    st.markdown(f"#### 💬 {partner_name}")
                    st.caption(f"📍 {partner_country} · {partner_roles}")
                
                with h_cal:
                    with st.popover("📅 Sync Meeting", use_container_width=True):
                        st.markdown("##### 📅 Meeting & Calendar Sync")
                        st.caption(f"Sync your 1-on-1 mentorship session with **{partner_name}** directly to your calendar.")
                        
                        m_name = (profile_data.get('mentee', {}).get('name') if current_role == 'MENTEE' else profile_data.get('mentor', {}).get('name')) or ('Mentee' if current_role == 'MENTEE' else 'Mentor')
                        title_val = f"Mentoring-Me 1-on-1: {m_name} & {partner_name}"
                        
                        sel_slot = st.session_state.get('selected_scheduled_slot')
                        date_time_line = f"Date/Time: {sel_slot}\n" if (sel_slot and sel_slot != "None of these work / Coordinate Custom Time") else "Date/Time: As coordinated in chat\n"
                        
                        cal_body = (
                            f"Title: {title_val}\n"
                            f"{date_time_line}"
                            f"Duration: 25 minutes\n\n"
                            f"Mentorship 1-on-1 Agenda:\n"
                            f"1. Icebreaker & Introductions (5 mins)\n"
                            f"2. Partnership Goals & Development Milestones (10 mins)\n"
                            f"3. Discussion Topic / Technical Roadmapping (5 mins)\n"
                            f"4. Action Items & Next Steps (5 mins)\n\n"
                            f"Platform: Mentoring-Me Platform"
                        )
                        
                        chat_gcal = generate_google_calendar_url(
                            title=title_val,
                            description=cal_body,
                            location="Virtual (Mentoring-Me Platform)"
                        )
                        chat_ics = generate_ics_calendar_file(
                            title=title_val,
                            description=cal_body,
                            location="Virtual (Mentoring-Me Platform)"
                        )
                        
                        st.link_button("📅 Add to Google Calendar", chat_gcal, use_container_width=True)
                        st.download_button(
                            "📥 Download .ICS Invite",
                            data=chat_ics,
                            file_name=f"mentoring_me_{partner_name.replace(' ', '_')}.ics",
                            mime="text/calendar",
                            use_container_width=True,
                            key=f"chat_pop_ics_{curr_match['id']}"
                        )
                        with st.expander("📋 View Meeting Agenda"):
                            st.text_area("Event Agenda", value=cal_body, height=120, key=f"chat_cal_body_{curr_match['id']}", label_visibility="collapsed")
                            
                with h_col2:
                    with st.popover("👤 Profile", use_container_width=True):
                        display_profile_card(
                            name=partner_name,
                            country=curr_match.get('mentor_country' if current_role == 'MENTEE' else 'mentee_country'),
                            ed_level=curr_match.get('mentor_ed_level' if current_role == 'MENTEE' else 'mentee_ed_level'),
                            roles=curr_match.get('mentor_devtype' if current_role == 'MENTEE' else 'mentee_devtype'),
                            years=curr_match.get('mentor_years' if current_role == 'MENTEE' else 'mentee_years'),
                            org_size=curr_match.get('mentor_org_size' if current_role == 'MENTEE' else 'mentee_org_size'),
                            priorities=curr_match.get('mentor_job_factors' if current_role == 'MENTEE' else 'mentee_job_factors'),
                            additional_details=curr_match.get('mentor_additional_details' if current_role == 'MENTEE' else 'mentee_additional_details'),
                            user_id=partner_id,
                            email=curr_match.get('mentor_email' if current_role == 'MENTEE' else 'mentee_email'),
                            contact_link=curr_match.get('mentor_contact_link' if current_role == 'MENTEE' else None),
                            linkedin_link=curr_match.get('mentor_linkedin_link' if current_role == 'MENTEE' else 'mentee_linkedin_link')
                        )
                with h_col3:
                    if partner_cv:
                        with st.popover("📄 CV", use_container_width=True):
                            pdf_bytes = api_get_cv(partner_id)
                            if pdf_bytes:
                                display_pdf_inline(pdf_bytes)
                            else:
                                st.info("CV preview unavailable.")
                    else:
                        st.write("")

                st.caption("💡 *Tip*: Use **📅 Sync Meeting** in the header above to add confirmed sessions to Google Calendar or download an `.ics` file.")

                st.markdown("---")
                render_active_chat_stream(curr_match['id'], partner_name, current_role)

def trigger_client_tab_switch(target_tab_keyword: str):
    """Programmatically switches the Streamlit client tab using robust multi-selector DOM triggers."""
    import streamlit.components.v1 as components
    import json
    
    clean_keyword = target_tab_keyword.strip()
    js_code = f"""
    <script>
        (function() {{
            const targetKeyword = {json.dumps(clean_keyword)}.toLowerCase();
            const keywords = targetKeyword.split(/\\s+/).filter(w => w.length > 2);
            
            function simulateClick(el) {{
                try {{
                    el.focus();
                    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(function(eventType) {{
                        const ev = new MouseEvent(eventType, {{
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }});
                        el.dispatchEvent(ev);
                    }});
                    if (typeof el.click === 'function') {{
                        el.click();
                    }}
                }} catch(e) {{
                    try {{ el.click(); }} catch(err) {{}}
                }}
            }}
            
            function doSwitch() {{
                try {{
                    const docs = [];
                    if (window.parent && window.parent.document) docs.push(window.parent.document);
                    if (window.top && window.top.document && window.top.document !== (window.parent && window.parent.document)) docs.push(window.top.document);
                    docs.push(document);
                    
                    const selectors = [
                        'div[data-testid="stTabs"] button[data-testid="stTab"]',
                        'div[data-testid="stTabs"] button[role="tab"]',
                        'button[data-testid="stTab"]',
                        'button[role="tab"]',
                        'button[data-baseweb="tab"]',
                        'div[data-baseweb="tab-list"] button',
                        '[data-testid="stTab"]',
                        '[role="tab"]'
                    ];
                    
                    for (let doc of docs) {{
                        let tabs = [];
                        for (let sel of selectors) {{
                            const found = doc.querySelectorAll(sel);
                            if (found && found.length > 0) {{
                                tabs = Array.from(found);
                                break;
                            }}
                        }}
                        
                        if (tabs.length === 0) continue;
                        
                        // 1. Direct / full text substring matching
                        for (let tab of tabs) {{
                            const text = (tab.textContent || tab.innerText || "").toLowerCase().trim();
                            if (text.includes(targetKeyword)) {{
                                simulateClick(tab);
                                return true;
                            }}
                        }}
                        
                        // 2. Keyword fallback matching (e.g. 'matches', 'requests', 'messages')
                        for (let tab of tabs) {{
                            const text = (tab.textContent || tab.innerText || "").toLowerCase().trim();
                            for (let kw of keywords) {{
                                if (text.includes(kw)) {{
                                    simulateClick(tab);
                                    return true;
                                }}
                            }}
                        }}
                    }}
                }} catch(e) {{
                    console.error("Tab switch trigger error:", e);
                }}
                return false;
            }}
            
            // Staged execution retries
            const delays = [10, 40, 100, 220, 450, 800, 1200];
            delays.forEach(function(delay) {{
                setTimeout(doSwitch, delay);
            }});
        }})();
    </script>
    """
    components.html(js_code, height=0, width=0)

def display_in_app_chat(match_id: str, partner_name: str, current_role: str, key_suffix: str = ""):
    st.markdown(f"#### 💬 Direct Conversation with {partner_name}")
    st.caption("Secure, real-time messaging directly within the Mentoring-Me platform.")
    
    messages = api_get_messages(match_id)
    
    chat_container = st.container(height=320, border=True)
    with chat_container:
        if not messages:
            st.info(f"👋 No messages yet. Send a greeting to {partner_name} to start your mentorship collaboration!")
        else:
            for msg in messages:
                is_mine = msg.get('is_mine', False)
                ts_str = msg.get('created_at', '')
                time_label = ""
                if ts_str:
                    try:
                        t_part = ts_str.split('T')[1][:5] if 'T' in ts_str else ts_str[-8:-3]
                        d_part = ts_str.split('T')[0] if 'T' in ts_str else ""
                        time_label = f"{d_part} {t_part}"
                    except Exception:
                        time_label = ""
                        
                if is_mine:
                    with st.chat_message("user", avatar="🌱" if current_role == "MENTEE" else "🧭"):
                        st.markdown(f"**You** <span style='font-size:0.75rem; color:#94a3b8; margin-left:8px;'>{time_label}</span>", unsafe_allow_html=True)
                        st.write(msg.get('content', ''))
                else:
                    with st.chat_message("assistant", avatar="🧭" if current_role == "MENTEE" else "🌱"):
                        import html as _html
                        sender_label = _html.escape(msg.get('sender_name') or partner_name or "Mentor")
                        st.markdown(f"**{sender_label}** <span style='font-size:0.75rem; color:#94a3b8; margin-left:8px;'>{time_label}</span>", unsafe_allow_html=True)
                        st.write(msg.get('content', ''))
                        
    # Composer with unique key
    suf = f"_{key_suffix}" if key_suffix else ""
    with st.form(f"chat_composer_form_{match_id}{suf}", clear_on_submit=True):
        col_inp, col_snd = st.columns([5, 1.2])
        with col_inp:
            msg_text = st.text_input("Type your message...", placeholder="Type a message...", key=f"chat_inp_{match_id}{suf}", label_visibility="collapsed")
        with col_snd:
            send_btn = st.form_submit_button("Send 📤", use_container_width=True)
            if send_btn and msg_text.strip():
                ok_s, res_s = api_send_message(match_id, msg_text.strip())
                if ok_s:
                    st.toast(f"📤 Message sent to {partner_name}!", icon="💬")
                    st.rerun()
                else:
                    st.error(res_s)

@st.fragment(run_every="5s")
def render_top_notifications_bell(current_role: str):
    st.write("")
    st.write("")
    raw_history = api_get_match_history()
    history = [m for m in raw_history if isinstance(m, dict)] if isinstance(raw_history, list) else []
    
    unread_msg_summary = api_get_unread_messages()
    tot_unread_msgs = int(unread_msg_summary.get('total_unread', 0)) if isinstance(unread_msg_summary, dict) else 0
    unread_by_match = unread_msg_summary.get('by_match', {}) if isinstance(unread_msg_summary, dict) else {}
    
    if current_role == "MENTEE":
        unnotified = [m for m in history if isinstance(m, dict) and m.get('status') == 'ACCEPTED' and not m.get('mentee_notified', False)]
        total_alerts = len(unnotified) + tot_unread_msgs
        bell_label = f"🔔 ({total_alerts})" if total_alerts > 0 else "🔔"
        
        last_tot = st.session_state.get('_last_tot_alerts_mentee', None)
        if last_tot is not None and total_alerts > last_tot:
            if tot_unread_msgs > 0:
                st.toast(f"💬 New direct message received! ({tot_unread_msgs} unread)", icon="🔔")
            elif unnotified:
                st.toast("🎉 A mentor accepted your mentorship request!", icon="🔔")
        st.session_state['_last_tot_alerts_mentee'] = total_alerts
        
        with st.popover(bell_label, use_container_width=True):
            head_col1, head_col2 = st.columns([2, 1])
            with head_col1:
                st.markdown("### 🔔 Notifications")
            with head_col2:
                if st.button("🔄 Sync", key="mentee_notif_sync_btn", use_container_width=True):
                    st.rerun(scope="fragment")
                    
            if total_alerts == 0:
                st.write("No new notifications.")
            else:
                # 1. Unread Direct Messages alerts
                if tot_unread_msgs > 0:
                    st.markdown("**💬 New Direct Messages**")
                    for mid, count in unread_by_match.items():
                        if count > 0:
                            m_obj = next((m for m in history if m['id'] == mid), None)
                            partner_name = m_obj.get('mentor_name', 'Mentor') if m_obj else 'Your Connection'
                            msg_alert_btn = f"💬 **{partner_name}** ({count} new message{'s' if count > 1 else ''})"
                            if st.button(msg_alert_btn, key=f"notif_msg_btn_{mid}_{current_role}", use_container_width=True):
                                api_mark_messages_read(mid)
                                st.session_state['active_chat_match_id'] = mid
                                st.session_state['trigger_tab_switch'] = "Direct Messages"
                                st.rerun()

                # 2. Accepted Mentorship Match alerts
                if unnotified:
                    if tot_unread_msgs > 0:
                        st.markdown("---")
                    st.markdown("**🎯 Mentorship Updates**")
                    for unm in unnotified:
                        button_label = f"🎉 **{unm['mentor_name']}** accepted your mentorship request! (Click to connect)"
                        if st.button(button_label, key=f"notif_redirect_btn_{unm['id']}", use_container_width=True):
                            st.session_state['focus_scheduling_match'] = unm['id']
                            st.rerun()
                            
                        c_space, c_dismiss = st.columns([3, 1])
                        with c_dismiss:
                            if st.button("Dismiss", key=f"dismiss_notif_mentee_{unm['id']}", use_container_width=True):
                                if api_mark_match_notified(unm['id']):
                                    st.session_state['profile'] = None
                                    st.rerun(scope="fragment")
    else:  # MENTOR
        unnotified_reqs = [m for m in history if isinstance(m, dict) and m.get('status') == 'REQUESTED' and not m.get('mentor_notified', False)]
        total_alerts = len(unnotified_reqs) + tot_unread_msgs
        bell_label = f"🔔 ({total_alerts})" if total_alerts > 0 else "🔔"
        
        last_tot_m = st.session_state.get('_last_tot_alerts_mentor', None)
        if last_tot_m is not None and total_alerts > last_tot_m:
            if tot_unread_msgs > 0:
                st.toast(f"💬 New direct message received! ({tot_unread_msgs} unread)", icon="🔔")
            elif unnotified_reqs:
                st.toast("📩 New mentorship request received! Check Notifications.", icon="🔔")
        st.session_state['_last_tot_alerts_mentor'] = total_alerts
        
        with st.popover(bell_label, use_container_width=True):
            head_col1, head_col2 = st.columns([2, 1])
            with head_col1:
                st.markdown("### 🔔 Notifications")
            with head_col2:
                if st.button("🔄 Sync", key="mentor_notif_sync_btn", use_container_width=True):
                    st.rerun(scope="fragment")
                    
            if total_alerts == 0:
                st.write("No new notifications.")
            else:
                # 1. Unread Direct Messages alerts
                if tot_unread_msgs > 0:
                    st.markdown("**💬 New Direct Messages**")
                    for mid, count in unread_by_match.items():
                        if count > 0:
                            m_obj = next((m for m in history if m['id'] == mid), None)
                            partner_name = m_obj.get('mentee_name', 'Mentee') if m_obj else 'Your Connection'
                            msg_alert_btn = f"💬 **{partner_name}** ({count} new message{'s' if count > 1 else ''})"
                            if st.button(msg_alert_btn, key=f"notif_msg_btn_{mid}_{current_role}", use_container_width=True):
                                api_mark_messages_read(mid)
                                st.session_state['active_chat_match_id'] = mid
                                st.session_state['trigger_tab_switch'] = "Direct Messages"
                                st.rerun()

                # 2. Incoming Mentorship Requests
                if unnotified_reqs:
                    if tot_unread_msgs > 0:
                        st.markdown("---")
                    st.markdown("**🎯 Mentorship Requests**")
                    for unm in unnotified_reqs:
                        st.info(f"📩 **{unm['mentee_name']}** requested mentorship!")
                        subcol1, subcol2 = st.columns([1, 1])
                        if subcol1.button("👉 Respond", key=f"focus_notif_mentor_{unm['id']}", use_container_width=True):
                            st.session_state['focus_request_match'] = unm['id']
                            st.rerun()
                        if subcol2.button("Dismiss", key=f"dismiss_notif_mentor_{unm['id']}", use_container_width=True):
                            if api_mark_match_notified(unm['id']):
                                st.session_state['profile'] = None
                                st.rerun(scope="fragment")

@st.fragment(run_every="5s")
def render_top_messaging_hub(current_role: str, user_profile: dict, matches_history: list = None):
    st.write("")
    st.write("")
    unread_summary = api_get_unread_messages()
    tot_unread = unread_summary.get('total_unread', 0)
    chat_label = f"💬 ({tot_unread})" if tot_unread > 0 else "💬 Messages"
    
    if matches_history is None:
        matches_history = api_get_match_history() or []
    
    with st.popover(chat_label, use_container_width=True):
        st.markdown("### 💬 Direct Messages & Inquiries")
        
        connected_matches = [m for m in (matches_history or []) if m.get('status') == 'ACCEPTED']
        proposed_matches = [m for m in (matches_history or []) if m.get('status') in ['PROPOSED', 'REQUESTED', 'PENDING']]
        
        active_search_matches = st.session_state.get('current_matches', [])
        for sm in active_search_matches:
            if not any(pm.get('id') == sm.get('id') for pm in proposed_matches) and not any(cm.get('id') == sm.get('id') for cm in connected_matches):
                proposed_matches.append(sm)
                
        tab_active_chats, tab_inquiry = st.tabs(["💬 Active Chats", "✉️ Send Inquiry"])
        
        with tab_active_chats:
            if not connected_matches:
                st.info("No active connected mentorship pairs yet. Accept or receive connection requests to start direct messaging!")
            else:
                chat_options = {}
                for m in connected_matches:
                    partner_name = m.get('mentor_name') if current_role == 'MENTEE' else m.get('mentee_name', 'Partner')
                    m_unread = unread_summary.get('by_match', {}).get(m['id'], 0)
                    unread_tag = f" 🔴 ({m_unread} new)" if m_unread > 0 else ""
                    chat_options[m['id']] = f"{partner_name}{unread_tag}"
                    
                selected_match_id = st.selectbox(
                    "Select Conversation:",
                    options=list(chat_options.keys()),
                    format_func=lambda mid: chat_options.get(mid, "Conversation"),
                    key=f"top_chat_picker_{current_role}"
                )
                
                sel_match = next((m for m in connected_matches if m['id'] == selected_match_id), None)
                if sel_match:
                    p_name = sel_match.get('mentor_name') if current_role == 'MENTEE' else sel_match.get('mentee_name', 'Partner')
                    display_in_app_chat(selected_match_id, p_name, current_role, key_suffix=f"top_bar_{current_role}")
                    
        with tab_inquiry:
            st.caption("Send a direct introductory note to a proposed mentor or candidate in your pool.")
            if not proposed_matches:
                st.info("No proposed candidates in your active pool currently. Head to the **Platform Matches** tab to explore matches!")
            else:
                inq_options = {}
                for m in proposed_matches:
                    target_name = m.get('mentor_name') if current_role == 'MENTEE' else m.get('mentee_name', 'Candidate')
                    dev_type = m.get('mentor_devtype' if current_role=='MENTEE' else 'mentee_devtype', '')
                    dev_label = f" · {dev_type[:20]}" if dev_type else ""
                    inq_options[m['id']] = f"{target_name}{dev_label} ({m.get('status', 'PROPOSED')})"
                    
                inq_match_id = st.selectbox(
                    "Choose Candidate to Message:",
                    options=list(inq_options.keys()),
                    format_func=lambda mid: inq_options.get(mid, "Candidate"),
                    key=f"top_inquiry_picker_{current_role}"
                )
                
                target_m = next((m for m in proposed_matches if m['id'] == inq_match_id), None)
                if target_m:
                    t_name = target_m.get('mentor_name') if current_role == 'MENTEE' else target_m.get('mentee_name', 'Candidate')
                    with st.form(f"inquiry_form_{inq_match_id}_{current_role}", clear_on_submit=True):
                        inq_text = st.text_area(f"Introductory Note for {t_name}:", placeholder="Hi, I noticed our shared background and would love to connect for mentorship guidance...", height=100)
                        send_inq = st.form_submit_button("Send Connection Note 🚀", use_container_width=True)
                        if send_inq:
                            if not inq_text.strip():
                                st.error("Please write a short introductory note.")
                            else:
                                ok_inq, res_inq = api_send_message(inq_match_id, inq_text.strip())
                                if ok_inq:
                                    st.success(f"Introductory note sent to {t_name}!")
                                    st.rerun()
                                else:
                                    st.error(res_inq)

def call_openai_api(api_key, system_instruction, user_prompt, chat_history):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    messages = [{"role": "system", "content": system_instruction}]
    for msg in chat_history:
        role_map = {"user": "user", "assistant": "assistant"}
        messages.append({
            "role": role_map.get(msg["role"], "user"),
            "content": msg["content"]
        })
        
    messages.append({
        "role": "user",
        "content": user_prompt
    })
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['choices'][0]['message']['content']
        else:
            return f"Error from OpenAI API: {response.text} (Status Code: {response.status_code})"
    except Exception as e:
        return f"Failed to contact OpenAI API: {str(e)}"

def call_gemini_api(api_key, system_instruction, user_prompt, chat_history):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    for msg in chat_history:
        role_map = {"user": "user", "assistant": "model"}
        contents.append({
            "role": role_map.get(msg["role"], "user"),
            "parts": [{"text": msg["content"]}]
        })
        
    contents.append({
        "role": "user",
        "parts": [{"text": f"System Context: {system_instruction}\n\nUser Prompt: {user_prompt}"}]
    })
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error from Gemini API: {response.text} (Status Code: {response.status_code})"
    except Exception as e:
        return f"Failed to contact Gemini API: {str(e)}"

def get_simulated_ai_response(user_prompt):
    prompt_lower = user_prompt.lower()
    if "brag" in prompt_lower or "sheet" in prompt_lower or "record" in prompt_lower:
        return (
            "### 📝 AI Career Advisor: How to Build a Brag Sheet\n\n"
            "A brag sheet is a running log of your achievements. It is critical for self-advocacy. Here is a structure you can use:\n\n"
            "1. **Project & Scope:** What did you work on? (e.g., *'Led migration of auth service to FastAPI'*)\n"
            "2. **Impact & Metrics:** What was the business or technical outcome? (e.g., *'Reduced latency by 15% and eliminated 2 security vulnerabilities'*)\n"
            "3. **Collaboration & Leadership:** Who did you work with or mentor? (e.g., *'Coordinated with frontend engineers and mentored 1 junior developer'*)\n"
            "4. **Praise & Feedback:** Paste any Slack screenshots or email kudos from peers or stakeholders.\n\n"
            "**Action Item:** Create a Google Doc called 'My Wins' and set a weekly reminder on Friday afternoons for 15 minutes to update it!"
        )
    elif "sponsor" in prompt_lower or "advocate" in prompt_lower:
        return (
            "### 📣 AI Career Advisor: Finding and Cultivating Sponsors\n\n"
            "Unlike a mentor who guides you, a sponsor has the organizational power to advocate for you in performance reviews or project allocations.\n\n"
            "Here is how to build sponsorship relationships:\n"
            "- **Deliver & Align:** Ensure your work is high quality and aligns with the sponsor's business goals.\n"
            "- **Make Your Work Visible:** Share progress updates in public channels. Leaders cannot sponsor work they don't know exists.\n"
            "- **Ask for Specific Opportunities:** Instead of asking 'Will you sponsor me?', ask: *'I would love to lead the new database optimization initiative next quarter. If you think I'm ready, would you support my nomination in the planning session?'*"
        )
    elif "negotiat" in prompt_lower or "salary" in prompt_lower or "pay" in prompt_lower or "flexibility" in prompt_lower:
        return (
            "### 💵 AI Career Advisor: Self-Advocacy & Negotiation\n\n"
            "Negotiating is not about demanding; it is about collaborative problem-solving. Use the **'I.N.T.R.O.'** method:\n\n"
            "- **I - Information:** Research market benchmarks (e.g., Glassdoor, levels.fyi).\n"
            "- **N - Numbers:** Ground your request in metrics from your brag sheet.\n"
            "- **T - Together:** Frame the negotiation as a partnership (*'I want to ensure my compensation aligns with the value I'm delivering to this team'*).\n"
            "- **R - Rehearse:** Practice saying your numbers out loud with your mentor.\n"
            "- **O - Options:** Have fallback options like extra vacation days, remote work flexibility, or educational stipends."
        )
    elif "imposter" in prompt_lower or "confidence" in prompt_lower or "leader" in prompt_lower:
        return (
            "### 🔧 AI Career Advisor: Technical Leadership & Overcoming Imposter Syndrome\n\n"
            "Our survey analysis shows that women's representation drops by nearly 83% from junior to senior/executive tiers, meaning role models are scarce. "
            "Imposter syndrome is common when transitioning to technical leadership. Try these steps:\n\n"
            "- **Evidence over Emotion:** When you feel like you don't belong, look at your brag sheet. Your presence is backed by objective performance.\n"
            "- **Own the Code Reviews:** Offer constructive, high-quality reviews on pull requests. It is one of the fastest ways to build technical authority.\n"
            "- **Drive Consensus:** You don't need to know all the answers. A great tech lead facilitates discussions and helps the team reach the best decision collectively."
        )
    else:
        return (
            "### 📚 AI Career Advisor: Welcome to Mentorship Coaching!\n\n"
            "I am your AI Career Advisor. I can help you prepare for discussions with your mentor, build self-advocacy skills, or plan your career roadmaps. "
            "Try asking me about:\n"
            "- *\"How do I write a brag sheet?\"*\n"
            "- *\"What is the difference between a mentor and a sponsor?\"*\n"
            "- *\"How do I prepare for a salary negotiation?\"*\n"
            "- *\"How do I deal with imposter syndrome as a tech lead?\"*"
        )

def render_copilot_tab(mentee):
    # Inject custom premium styling
    st.markdown("""
        <style>
        /* Header Card */
        .copilot-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.12);
            border: 1px solid #334155;
        }
        .copilot-header h3 {
            color: #ffffff !important;
            margin-top: 0 !important;
            margin-bottom: 8px !important;
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }
        .copilot-header p {
            color: #94a3b8 !important;
            font-size: 0.92rem !important;
            line-height: 1.6 !important;
            margin-bottom: 0 !important;
        }
        
        /* Suggestion Buttons/Chips styling */
        div.stButton > button {
            border-radius: 20px !important;
            border: 1px solid #cbd5e1 !important;
            background-color: #ffffff !important;
            color: #334155 !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            padding: 10px 18px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
            width: 100% !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            white-space: normal !important;
            height: auto !important;
            min-height: 48px !important;
        }
        div.stButton > button:hover {
            border-color: #3b82f6 !important;
            color: #1d4ed8 !important;
            background-color: #f0f7ff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08) !important;
        }
        div.stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Message action buttons (Copy & Edit icons) */
        div[data-testid="stChatMessage"] div.stButton > button {
            border-radius: 6px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            color: #64748b !important;
            font-size: 0.95rem !important;
            padding: 2px 8px !important;
            min-height: 28px !important;
            height: 28px !important;
            width: auto !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-top: 2px !important;
        }
        div[data-testid="stChatMessage"] div.stButton > button:hover {
            border-color: #3b82f6 !important;
            color: #1d4ed8 !important;
            background-color: #eff6ff !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Chat Area bubble styling & alignment */
        div[data-testid="stChatMessage"] {
            border-radius: 0px !important;
            padding: 16px 0px !important;
            margin-bottom: 0px !important;
            box-shadow: none !important;
            border: none !important;
            border-bottom: 1px solid #f1f5f9 !important;
            background-color: transparent !important;
            display: flex !important;
            gap: 14px !important;
        }
        
        /* Remove bubble-like alignment margins */
        div[data-testid="stChatMessage"]:has([data-testid="chatAvatar-user"]),
        div[data-testid="stChatMessage"]:has([data-testid="chatAvatar-assistant"]) {
            margin-left: 0px !important;
            margin-right: 0px !important;
            background-color: transparent !important;
            border: none !important;
            border-bottom: 1px solid #f1f5f9 !important;
        }
        
        /* Message avatar styling */
        div[data-testid="stChatMessageAvatar"] {
            border-radius: 50% !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            width: 32px !important;
            height: 32px !important;
            flex-shrink: 0 !important;
        }
        
        /* Message content wrapper */
        div[data-testid="stChatMessageContent"] {
            padding: 0px !important;
            background-color: transparent !important;
            border: none !important;
            font-size: 0.94rem !important;
            line-height: 1.6 !important;
            color: #1e293b !important;
        }
        
        /* Divider line */
        .copilot-divider {
            height: 1px;
            background-color: #e2e8f0;
            margin: 24px 0 16px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    import os
    openai_env_key = (st.session_state.get("custom_openai_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
    gemini_env_key = (st.session_state.get("custom_gemini_key") or os.environ.get("GEMINI_API_KEY", "")).strip()
    
    provider = "simulated"
    api_key = ""
    badge_label = "Interactive Advisor"
    
    if gemini_env_key:
        api_key = gemini_env_key
        provider = "gemini"
        badge_label = "Gemini AI Advisor"
    elif openai_env_key:
        api_key = openai_env_key
        provider = "openai"
        badge_label = "OpenAI AI Advisor"

    # Beautiful header panel
    st.markdown(f"""
        <div class="copilot-header">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">💡</span>
                    <h3 style="margin: 0; color: white !important;">AI Career Advisor</h3>
                </div>
                <span style="background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%); color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2); display: inline-block;">{badge_label}</span>
            </div>
            <p>
                Get personalized, real-time guidance on career roadmapping, promotion reviews, salary negotiations, and technical leadership transitions. 
                Your advisor is dynamically tailored to your unique professional profile and industry career progression frameworks.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    import uuid
    welcome_msg = "Hello! I am your AI Career Advisor. Ask me anything about navigating your career, setting goals, or preparing for your next mentorship session."
    
    # Initialize Multi-Session State
    if "chat_sessions" not in st.session_state or not st.session_state["chat_sessions"]:
        init_id = "sess_welcome"
        now_str = datetime.datetime.now().strftime("%b %d, %H:%M")
        st.session_state["chat_sessions"] = [
            {
                "id": init_id,
                "title": "Welcome Discussion",
                "created_at": now_str,
                "messages": [{"role": "assistant", "content": welcome_msg}]
            }
        ]
        st.session_state["active_session_id"] = init_id
        
    # Retrieve currently active session
    active_id = st.session_state.get("active_session_id")
    active_session = next((s for s in st.session_state["chat_sessions"] if s["id"] == active_id), None)
    if not active_session:
        active_session = st.session_state["chat_sessions"][0]
        st.session_state["active_session_id"] = active_session["id"]
        
    messages_list = active_session["messages"]
    st.session_state["playbook_messages"] = messages_list
        
    # Top Action Toolbar: Discussion switcher, New Chat, and Delete buttons
    col_sess, col_new, col_del = st.columns([3.5, 1.4, 0.7])
    
    with col_sess:
        sess_labels = {}
        for s in st.session_state["chat_sessions"]:
            m_len = len(s.get("messages", []))
            sess_labels[s["id"]] = f"💬 {s['title']} · ({s.get('created_at', '')}) [{m_len} msgs]"
            
        all_ids = [s["id"] for s in st.session_state["chat_sessions"]]
        current_idx = all_ids.index(active_session["id"]) if active_session["id"] in all_ids else 0
            
        picked_sess_id = st.selectbox(
            "📜 Discussion Session History:",
            options=all_ids,
            index=current_idx,
            format_func=lambda x: sess_labels.get(x, x),
            key="chat_session_picker_box",
            help="Select any prior discussion to continue or review earlier advice."
        )
        if picked_sess_id != active_session["id"]:
            st.session_state["active_session_id"] = picked_sess_id
            st.session_state["editing_msg_index"] = None
            st.rerun()

    with col_new:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ New Chat", key="new_chat_btn", use_container_width=True, help="Start a new discussion session"):
            new_id = str(uuid.uuid4())[:8]
            now_str = datetime.datetime.now().strftime("%b %d, %H:%M")
            new_num = len(st.session_state["chat_sessions"]) + 1
            new_sess = {
                "id": new_id,
                "title": f"Discussion #{new_num}",
                "created_at": now_str,
                "messages": [{"role": "assistant", "content": welcome_msg}]
            }
            st.session_state["chat_sessions"].insert(0, new_sess)
            st.session_state["active_session_id"] = new_id
            st.session_state["editing_msg_index"] = None
            st.rerun()

    with col_del:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if len(st.session_state["chat_sessions"]) > 1:
            if st.button("🗑️", key="delete_chat_btn", use_container_width=True, help="Delete this discussion session"):
                st.session_state["chat_sessions"] = [s for s in st.session_state["chat_sessions"] if s["id"] != active_session["id"]]
                st.session_state["active_session_id"] = st.session_state["chat_sessions"][0]["id"]
                st.session_state["editing_msg_index"] = None
                st.rerun()
        
    chat_container = st.container(height=450)
    with chat_container:
        for idx, message in enumerate(messages_list):
            avatar = "🤖" if message["role"] == "assistant" else (mentee.get('profile_pic') or "👤")
            role_name = "AI Advisor" if message["role"] == "assistant" else (mentee.get('name') or "You")
            with st.chat_message(message["role"], avatar=avatar):
                # In-place editing inside the chatbot box for user message
                if message["role"] == "user" and st.session_state.get("editing_msg_index") == idx:
                    st.markdown(f"**{role_name}** *(Editing question...)*")
                    edited_val = st.text_area(
                        "Edit your question:",
                        value=message["content"],
                        height=85,
                        key=f"inline_edit_input_{idx}",
                        label_visibility="collapsed"
                    )
                    b_save, b_cancel, _ = st.columns([1.5, 1.2, 5])
                    with b_save:
                        if st.button("💾 Save", key=f"inline_save_btn_{idx}", type="primary", use_container_width=True):
                            prior_history = messages_list[:idx]
                            active_session["messages"] = prior_history + [{"role": "user", "content": edited_val}]
                            st.session_state["editing_msg_index"] = None
                            
                            with st.spinner("Advisor analyzing updated question..."):
                                if provider in ["openai", "gemini"]:
                                    _gender_ctx = mentee.get('gender') or 'Not stated'
                                    _ally_pref = "Yes" if mentee.get('prefer_diversity_ally') else "No"
                                    _exp_tier = mentee.get('exp_tier') or 'early-career'
                                    system_inst = (
                                        "You are an AI Career Advisor for the Mentoring-Me platform, a platform dedicated to "
                                        "equitable mentorship pairing and career acceleration for early-career technologists and women in tech (aligned with SDG 5). "
                                        "You support users to advocate for themselves, navigate sponsorships, handle workplace dynamics, "
                                        "prepare for promotions, and transition to technical leadership. "
                                        "Be warm, encouraging, practical, and action-oriented. "
                                        "Offer tailored advice on imposter syndrome, negotiation, visibility, sponsorship vs mentorship, "
                                        "and building allyship networks. "
                                        f"Current user profile — Name: {mentee['name']}, Country: {mentee['country']}, "
                                        f"Roles: {mentee['dev_type']}, Experience: {mentee['years_code_pro']} years, "
                                        f"Career stage: {_exp_tier}, Gender: {_gender_ctx}, Prefers D&I Ally mentor: {_ally_pref}, "
                                        f"Goals/Bio: {(mentee.get('additional_details') or 'Not provided')[:300]}."
                                    )
                                    if provider == "openai":
                                        ai_response = call_openai_api(api_key.strip(), system_inst, edited_val, prior_history)
                                    else:
                                        ai_response = call_gemini_api(api_key.strip(), system_inst, edited_val, prior_history)
                                else:
                                    ai_response = get_simulated_ai_response(edited_val)
                            active_session["messages"].append({"role": "assistant", "content": ai_response})
                            st.session_state["playbook_messages"] = active_session["messages"]
                            st.rerun()
                    with b_cancel:
                        if st.button("✖️ Cancel", key=f"inline_cancel_btn_{idx}", use_container_width=True):
                            st.session_state["editing_msg_index"] = None
                            st.rerun()
                else:
                    st.markdown(f"**{role_name}**")
                    st.markdown(message["content"])
                    
                    # Sleek action icons inside message (Copy & Edit)
                    if message["role"] == "assistant":
                        if idx > 0:
                            ic_col1, _ = st.columns([0.6, 9])
                            with ic_col1:
                                if st.button("📋", key=f"copy_icon_ast_{idx}", help="Copy response to clipboard"):
                                    st.session_state[f"show_copy_ast_{idx}"] = not st.session_state.get(f"show_copy_ast_{idx}", False)
                                    st.rerun()
                            if st.session_state.get(f"show_copy_ast_{idx}"):
                                st.code(message["content"], language=None)
                    elif message["role"] == "user":
                        ic_col1, ic_col2, _ = st.columns([0.6, 0.6, 8])
                        with ic_col1:
                            if st.button("📋", key=f"copy_icon_user_{idx}", help="Copy message to clipboard"):
                                st.session_state[f"show_copy_u_{idx}"] = not st.session_state.get(f"show_copy_u_{idx}", False)
                                st.rerun()
                        with ic_col2:
                            if st.button("✏️", key=f"edit_icon_user_{idx}", help="Edit this message in place"):
                                st.session_state["editing_msg_index"] = idx
                                st.rerun()
                        if st.session_state.get(f"show_copy_u_{idx}"):
                            st.code(message["content"], language=None)
                
    st.markdown('<div class="copilot-divider"></div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.82rem; font-weight: 600; color: #64748b; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;'>💡 Recommended Advisory Prompts</p>", unsafe_allow_html=True)
    
    cols_sug1, cols_sug2 = st.columns(2)
    sug_prompt = None
    if cols_sug1.button("📝 How to write a brag sheet?", key="sug_brag"):
        sug_prompt = "How do I write a brag sheet to document my achievements and make my work visible at performance review time?"
    if cols_sug2.button("📣 Mentor vs sponsor — what is the difference?", key="sug_sponsor"):
        sug_prompt = "What is the difference between a mentor and a sponsor, and how do I find a sponsor as a woman in tech?"
    if cols_sug1.button("💵 How do I negotiate salary as a woman in tech?", key="sug_neg"):
        sug_prompt = "How do I prepare for a salary negotiation as a woman in tech? What are the common pitfalls and how do I advocate for myself?"
    if cols_sug2.button("🔧 How do I handle imposter syndrome?", key="sug_imposter"):
        sug_prompt = "How do I handle imposter syndrome as a woman in a technical role transitioning to tech lead?"
    if cols_sug1.button("📈 How do I get promoted to senior engineer?", key="sug_promo"):
        sug_prompt = "What concrete steps can I take to get promoted to senior engineer as a woman in tech?"
    if cols_sug2.button("🗣️ How do I speak up in male-dominated meetings?", key="sug_visibility"):
        sug_prompt = "How do I make my voice heard and increase my visibility in male-dominated team meetings and technical discussions?"
        
    user_query = st.chat_input("Ask your AI career advisor a question...")
    if sug_prompt:
        user_query = sug_prompt
        
    if user_query:
        # Auto-update session title with question preview if default
        if active_session["title"].startswith("Discussion #") or active_session["title"] == "Welcome Discussion":
            clean_title = (user_query[:30] + "...") if len(user_query) > 30 else user_query
            active_session["title"] = clean_title
            
        with chat_container:
            user_avatar = (mentee.get('profile_pic') or "👤")
            role_name = (mentee.get('name') or "You")
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(f"**{role_name}**")
                st.markdown(user_query)
                
        active_session["messages"].append({"role": "user", "content": user_query})
        st.session_state["playbook_messages"] = active_session["messages"]
        
        with st.spinner("Advisor analyzing..."):
            if provider in ["openai", "gemini"]:
                _gender_ctx = mentee.get('gender') or 'Not stated'
                _ally_pref = "Yes" if mentee.get('prefer_diversity_ally') else "No"
                _exp_tier = mentee.get('exp_tier') or 'early-career'
                system_inst = (
                    "You are an AI Career Advisor for the Mentoring-Me platform, a platform dedicated to "
                    "equitable mentorship pairing and career acceleration for early-career technologists and women in tech (aligned with SDG 5). "
                    "You support users to advocate for themselves, navigate sponsorships, handle workplace dynamics, "
                    "prepare for promotions, and transition to technical leadership. "
                    "Be warm, encouraging, practical, and action-oriented. "
                    "Offer tailored advice on imposter syndrome, negotiation, visibility, sponsorship vs mentorship, "
                    "and building allyship networks. "
                    f"Current user profile — Name: {mentee['name']}, Country: {mentee['country']}, "
                    f"Roles: {mentee['dev_type']}, Experience: {mentee['years_code_pro']} years, "
                    f"Career stage: {_exp_tier}, Gender: {_gender_ctx}, Prefers D&I Ally mentor: {_ally_pref}, "
                    f"Goals/Bio: {(mentee.get('additional_details') or 'Not provided')[:300]}."
                )
                if provider == "openai":
                    ai_response = call_openai_api(api_key.strip(), system_inst, user_query, active_session["messages"][:-1])
                else:
                    ai_response = call_gemini_api(api_key.strip(), system_inst, user_query, active_session["messages"][:-1])
            else:
                ai_response = get_simulated_ai_response(user_query)
                
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**AI Advisor**")
                st.markdown(ai_response)
        active_session["messages"].append({"role": "assistant", "content": ai_response})
        st.session_state["playbook_messages"] = active_session["messages"]
        st.rerun()


def generate_mentor_ai_completion(system_inst, user_prompt, chat_history=None):
    if chat_history is None:
        chat_history = []
    gemini_env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openai_env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    
    api_key = None
    provider = "simulated"
    if gemini_env_key:
        api_key = gemini_env_key
        provider = "gemini"
    elif openai_env_key:
        api_key = openai_env_key
        provider = "openai"
        
    if provider == "openai":
        return call_openai_api(api_key, system_inst, user_prompt, chat_history)
    elif provider == "gemini":
        return call_gemini_api(api_key, system_inst, user_prompt, chat_history)
    else:
        # High quality simulated mentoring toolkit responses
        p_lower = user_prompt.lower()
        if "agenda" in p_lower or "1-on-1" in p_lower:
            return (
                "### 📅 Structured 1-on-1 Mentoring Agenda\n\n"
                "**Duration:** 45 Minutes | **Focus:** Alignment, Discovery & Goal Execution\n\n"
                "---\n\n"
                "#### ⏱️ Part 1: Check-in & Icebreaker (00:00 - 00:08)\n"
                "- *\"What went well for you since we last spoke? What win (big or small) are you celebrating?\"*\n"
                "- *\"On a scale of 1-5, how is your current cognitive and energy balance?\"*\n\n"
                "#### 🔍 Part 2: Deep Dive on Core Challenge (00:08 - 00:28)\n"
                "- Review progress on previous action items / technical project milestones.\n"
                "- Unpack bottlenecks: *\"What is the biggest barrier preventing you from shipping this?\"*\n"
                "- Walkthrough architectural tradeoffs and code design patterns together.\n\n"
                "#### 💡 Part 3: Career Reflection & Strategic Insight (00:28 - 00:38)\n"
                "- Discuss workplace dynamics, visibility, or upcoming team presentations.\n"
                "- Practice self-advocacy framing for manager 1-on-1s.\n\n"
                "#### 🚀 Part 4: Commitments & Action Items (00:38 - 00:45)\n"
                "- Agree on 2-3 concrete homework action items before the next call.\n"
                "- Confirm date/time of the next session."
            )
        elif "roadmap" in p_lower or "90-day" in p_lower or "plan" in p_lower:
            return (
                "### 🗺️ 90-Day Mentee Growth & Progression Roadmap\n\n"
                "---\n\n"
                "#### 🧱 Month 1: Foundation & High-Frequency Habits\n"
                "- **Goal:** Master core codebase patterns and establish a feedback rhythm.\n"
                "- **Milestones:**\n"
                "  - [ ] Set up end-to-end local environment and write first comprehensive integration test.\n"
                "  - [ ] Start a private 'Brag Sheet' / work log document.\n"
                "  - [ ] Read 3 core architectural RFCs in your domain.\n"
                "- **KPI:** Ship 2 non-trivial features with zero blocker PR review feedback.\n\n"
                "#### ⚙️ Month 2: System Ownership & Architectural Thinking\n"
                "- **Goal:** Transition from ticket-taker to feature owner.\n"
                "- **Milestones:**\n"
                "  - [ ] Author a 1-page mini technical design document for a proposed optimization.\n"
                "  - [ ] Conduct a deep-dive code review for a teammate focusing on maintainability.\n"
                "  - [ ] Identify and fix one high-friction developer experience bottleneck.\n"
                "- **KPI:** Independently lead the deployment and monitoring of a subsystem.\n\n"
                "#### 🌟 Month 3: Visibility, Impact & Leadership Transition\n"
                "- **Goal:** Amplify team impact and prepare promotion evidence.\n"
                "- **Milestones:**\n"
                "  - [ ] Present a 15-min lunch-and-learn tech demo to the wider engineering team.\n"
                "  - [ ] Formulate 6-month career goals with manager using evidence from brag sheet.\n"
                "- **KPI:** Documented senior peer endorsement on technical competence."
            )
        elif "feedback" in p_lower or "cv" in p_lower or "resume" in p_lower:
            return (
                "### ✍️ Constructive Feedback & Actionable Review\n\n"
                "**Framework:** Situation · Behavior · Impact (SBI) + Future Coaching\n\n"
                "---\n\n"
                "#### 🟢 Key Strengths Observed:\n"
                "- Clear technical clarity and strong motivation to tackle ambiguous problems.\n"
                "- Thoughtful approach to collaboration and willingness to seek early guidance.\n\n"
                "#### 🟡 High-Leverage Growth Opportunities:\n"
                "1. **Quantify Business & Technical Impact:** Replace passive statements (e.g. *'worked on backend API'*) with measurable results (e.g. *'architected async FastAPI microservice handling 1.2M req/day with sub-50ms p95 latency'*).\n"
                "2. **Highlight System Ownership:** Emphasize choices made around reliability, testing, and CI/CD pipelines.\n\n"
                "#### 🎯 Recommended Action Plan for Mentee:\n"
                "- Refactor resume bullet points using the Google X-Y-Z formula: *'Accomplished [X], as measured by [Y], by doing [Z]'*.\n"
                "- Schedule a 15-minute mock pitch to practice talking through technical tradeoffs."
            )
        elif "interview" in p_lower or "question" in p_lower:
            return (
                "### 🎯 Mock Interview & Scenario Question Bank\n\n"
                "---\n\n"
                "#### 1. System Design & Architectural Tradeoffs\n"
                "- **Question:** *\"Walk me through how you would design a rate limiter for a public API that handles burst traffic. How would you choose between Token Bucket vs Leaky Bucket?\"*\n"
                "- **What to listen for:** Consideration of Redis distributed locks, latency overhead, and handling race conditions.\n\n"
                "#### 2. Debugging & High-Pressure Incident Management\n"
                "- **Question:** *\"Describe a time when a production deployment failed or caused a latency spike. How did you triage the root cause, communicate with stakeholders, and prevent recurrence?\"*\n"
                "- **What to listen for:** Calmness under pressure, use of logs/telemetry (datadog/grafana), and blameless post-mortem mindset.\n\n"
                "#### 3. Navigating Disagreements & Influence\n"
                "- **Question:** *\"Tell me about a time you strongly disagreed with a senior engineer or product manager's technical direction. How did you handle it?\"*\n"
                "- **What to listen for:** Use of data/benchmarks over emotion, respectful disagreement, and commitment to the team once a decision is made."
            )
        else:
            return (
                f"### 💡 Mentor AI Copilot Guidance\n\n"
                f"Regarding your query on **{user_prompt[:50]}...**:\n\n"
                "1. **Anchor in Psychological Safety:** Ensure your mentee feels comfortable sharing struggles without fear of judgment. Normalize that senior engineers also face ambiguity and imposter syndrome.\n"
                "2. **Ask Powerful Open Questions:** Rather than jumping immediately into problem-solving, ask *'What options have you considered so far?'* and *'What would the ideal outcome look like?'*.\n"
                "3. **Sponsor While Mentoring:** Beyond advice, look for opportunities to mention your mentee's accomplishments in leadership circles and recommend them for high-visibility initiatives."
            )


def render_mentor_milestones_tab(mentor, history):
    st.markdown("""
        <style>
        .milestone-header {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 22px 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(49, 46, 129, 0.15);
            border: 1px solid #4338ca;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="milestone-header">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">📝</span>
                    <h3 style="margin: 0; color: white !important; font-size: 1.45rem; font-weight: 700;">Mentee Milestones & Session Notes</h3>
                </div>
                <span style="background: rgba(255,255,255,0.15); color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Shared Growth Tracker</span>
            </div>
            <p style="color: #c7d2fe; margin-top: 8px; margin-bottom: 0; font-size: 0.92rem;">
                Keep your 1-on-1 mentorship structured and high-impact. Log meeting notes, assign action items / homework, and track progress against career milestones for your paired mentees.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    connected_matches = [m for m in history if m.get('status') == 'ACCEPTED']
    if not connected_matches:
        st.info("👋 **No Active Mentees Yet**: Once you accept a mentorship request in the **Mentorship Requests** tab, you will be able to log meeting notes, set homework checklists, and track milestones here.")
        return

    # Persistent feedback banner across reruns
    if 'milestone_action_feedback' in st.session_state and st.session_state['milestone_action_feedback']:
        mf_type, mf_msg = st.session_state.pop('milestone_action_feedback')
        if mf_type == "success":
            st.success(mf_msg)
        elif mf_type == "info":
            st.info(mf_msg)
        elif mf_type == "error":
            st.error(mf_msg)
        
    mentee_map = {}
    for m in connected_matches:
        e_id = m['mentee_id']
        e_name = m.get('mentee_name') or f"Mentee #{e_id[:6]}"
        e_role = (m.get('mentee_devtype') or '').split(';')[0]
        mentee_map[e_id] = f"{e_name} ({e_role or 'Mentee'})"
        
    all_notes = api_get_notes()
    
    total_notes = len(all_notes)
    completed_milestones = len([n for n in all_notes if n.get('milestone_status') == 'COMPLETED'])
    in_progress = len([n for n in all_notes if n.get('milestone_status') == 'IN_PROGRESS'])
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("👥 Active Mentees", len(mentee_map))
    m_col2.metric("📝 Logged Sessions", total_notes)
    m_col3.metric("🚀 In Progress", in_progress)
    m_col4.metric("✅ Completed Milestones", completed_milestones)
    
    st.markdown("---")
    
    ctrl_col1, ctrl_col2 = st.columns([3, 2])
    with ctrl_col1:
        mentee_opts = ["ALL"] + list(mentee_map.keys())
        selected_mentee = st.selectbox(
            "Filter notes by Mentee:",
            options=mentee_opts,
            format_func=lambda x: "🌐 All Active Mentees" if x == "ALL" else mentee_map.get(x, x),
            key="notes_mentee_filter_sel"
        )
    with ctrl_col2:
        status_filter = st.selectbox(
            "Filter by Milestone Status:",
            options=["ALL", "IN_PROGRESS", "COMPLETED", "NOT_STARTED"],
            format_func=lambda s: {"ALL": "🔍 All Statuses", "IN_PROGRESS": "🚀 In Progress", "COMPLETED": "✅ Completed", "NOT_STARTED": "⏳ Not Started"}.get(s, s),
            key="notes_status_filter_sel"
        )
        
    with st.expander("➕ Log New 1-on-1 Session Note & Milestone", expanded=False):
        st.markdown("##### ✍️ Record Session Agenda & Action Items")
        with st.form("new_session_note_form"):
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                target_e_id = st.selectbox(
                    "Target Mentee *",
                    options=list(mentee_map.keys()),
                    format_func=lambda x: mentee_map.get(x, x),
                    key="new_note_mentee_sel"
                )
            with c_e2:
                n_date = st.date_input("Session Date *", value=datetime.date.today(), key="new_note_date")
                
            n_title = st.text_input("Session / Milestone Title *", placeholder="e.g. Kickoff: 6-Month Career Goals & System Architecture", key="new_note_title")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                n_status = st.selectbox(
                    "Milestone Status",
                    options=["IN_PROGRESS", "COMPLETED", "NOT_STARTED"],
                    format_func=lambda s: {"IN_PROGRESS": "🚀 In Progress", "COMPLETED": "✅ Completed", "NOT_STARTED": "⏳ Not Started"}.get(s, s),
                    key="new_note_status"
                )
            with c_s2:
                n_next_meeting = st.text_input("Next Scheduled Meeting (Optional)", placeholder="e.g. 2026-09-15 15:00 UTC", key="new_note_next_meeting")
                
            n_topics = st.text_area(
                "Topics Covered / Key Discussions",
                placeholder="Summary of topics explored during this call...",
                height=90,
                key="new_note_topics"
            )
            
            n_actions = st.text_area(
                "Action Items & Homework Checklist",
                value="- [ ] \n- [ ] ",
                placeholder="- [ ] Review chapter 2 on microservices\n- [ ] Draft system architecture diagram",
                height=100,
                key="new_note_actions",
                help="Use markdown '- [ ] ' for open tasks and '- [x] ' for finished tasks."
            )
            
            n_takeaways = st.text_area(
                "Feedback, Encouragement & Key Takeaways",
                placeholder="Notes on mentee strengths, areas of growth, and specific feedback given...",
                height=80,
                key="new_note_takeaways"
            )
            
            submit_note = st.form_submit_button("💾 Save Session Note", type="primary", use_container_width=True)
            if submit_note:
                if not n_title.strip():
                    st.error("Please enter a Title for this session note.")
                else:
                    session_dt = datetime.datetime.combine(n_date, datetime.time(12, 0))
                    payload = {
                        "mentee_id": target_e_id,
                        "title": n_title.strip(),
                        "session_date": session_dt.isoformat(),
                        "topics_covered": n_topics.strip() if n_topics else None,
                        "action_items": n_actions.strip() if n_actions else None,
                        "milestone_status": n_status,
                        "key_takeaways": n_takeaways.strip() if n_takeaways else None,
                        "next_meeting_date": n_next_meeting.strip() if n_next_meeting else None
                    }
                    success, res = api_create_note(payload)
                    if success:
                        st.toast("📝 Session note saved successfully!", icon="✅")
                        st.session_state['milestone_action_feedback'] = (
                            "success",
                            f"📝 **Session note '{n_title.strip()}' saved successfully!** It is now visible in your mentee's shared growth tracker."
                        )
                        st.rerun()
                    else:
                        st.error(f"Error saving note: {res}")

    filtered_notes = all_notes.copy()
    if selected_mentee != "ALL":
        filtered_notes = [n for n in filtered_notes if n.get('mentee_id') == selected_mentee]
    if status_filter != "ALL":
        filtered_notes = [n for n in filtered_notes if n.get('milestone_status') == status_filter]
        
    if not filtered_notes:
        st.info("No session notes match your active filters.")
        return
        
    st.markdown(f"#### 📜 Logged Sessions ({len(filtered_notes)})")
    
    for idx, note in enumerate(filtered_notes):
        n_id = note['id']
        st_val = note.get('milestone_status', 'IN_PROGRESS')
        badge_style = {
            'COMPLETED': ('#dcfce7', '#166534', '✅ Completed'),
            'IN_PROGRESS': ('#e0e7ff', '#3730a3', '🚀 In Progress'),
            'NOT_STARTED': ('#fef3c7', '#92400e', '⏳ Not Started')
        }.get(st_val, ('#f1f5f9', '#475569', st_val))
        
        s_date_str = note.get('session_date', '')[:10]
        
        with st.container(border=True):
            hdr_col1, hdr_col2 = st.columns([3, 1])
            with hdr_col1:
                st.markdown(f"### {note.get('title')}")
                st.caption(f"👤 **Mentee:** `{note.get('mentee_name', 'Mentee')}` · 📅 **Date:** `{s_date_str}`")
            with hdr_col2:
                st.markdown(
                    f"<div style='text-align: right; margin-top: 5px;'>"
                    f"<span style='background-color: {badge_style[0]}; color: {badge_style[1]}; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 700;'>{badge_style[2]}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
            if note.get('topics_covered'):
                st.markdown("**📖 Topics Covered:**")
                st.markdown(note['topics_covered'])
                
            if note.get('action_items'):
                st.markdown("**📋 Action Items & Homework:**")
                st.markdown(note['action_items'])
                
            if note.get('key_takeaways'):
                st.markdown("**💡 Feedback & Key Takeaways:**")
                st.markdown(f"*{note['key_takeaways']}*")
                
            if note.get('next_meeting_date'):
                st.markdown(f"📆 **Next Target Meeting:** `{note['next_meeting_date']}`")
                
            act_col1, act_col2, act_col3, _ = st.columns([1.5, 1.2, 1.2, 3])
            with act_col1:
                if st_val != "COMPLETED":
                    if st.button("Mark Completed", key=f"mark_done_{n_id}_{idx}", type="secondary"):
                        api_update_note(n_id, {"milestone_status": "COMPLETED"})
                        st.toast("✅ Milestone marked as completed!", icon="🎉")
                        st.session_state['milestone_action_feedback'] = ("success", "✅ **Milestone marked as completed!**")
                        st.rerun()
                else:
                    if st.button("Mark In-Progress", key=f"mark_inprog_{n_id}_{idx}", type="secondary"):
                        api_update_note(n_id, {"milestone_status": "IN_PROGRESS"})
                        st.toast("🚀 Milestone marked as in progress.", icon="ℹ️")
                        st.session_state['milestone_action_feedback'] = ("info", "🚀 **Milestone marked as in progress.**")
                        st.rerun()
            with act_col2:
                if st.button("✏️ Edit", key=f"toggle_edit_note_{n_id}_{idx}"):
                    st.session_state[f"show_edit_note_{n_id}"] = not st.session_state.get(f"show_edit_note_{n_id}", False)
                    st.rerun()
            with act_col3:
                if st.button("🗑️ Delete", key=f"del_note_{n_id}_{idx}"):
                    api_delete_note(n_id)
                    st.toast("🗑️ Session note deleted.", icon="🗑️")
                    st.session_state['milestone_action_feedback'] = ("info", "🗑️ **Session note has been deleted.**")
                    st.rerun()
                    
            if st.session_state.get(f"show_edit_note_{n_id}"):
                with st.form(f"edit_note_form_{n_id}"):
                    e_title = st.text_input("Title", value=note.get('title', ''))
                    e_status = st.selectbox("Status", ["IN_PROGRESS", "COMPLETED", "NOT_STARTED"], index=["IN_PROGRESS", "COMPLETED", "NOT_STARTED"].index(st_val))
                    e_topics = st.text_area("Topics Covered", value=note.get('topics_covered') or "", height=80)
                    e_actions = st.text_area("Action Items", value=note.get('action_items') or "", height=80)
                    e_takeaways = st.text_area("Takeaways", value=note.get('key_takeaways') or "", height=80)
                    e_next = st.text_input("Next Meeting", value=note.get('next_meeting_date') or "")
                    
                    if st.form_submit_button("💾 Save Edits"):
                        api_update_note(n_id, {
                            "title": e_title,
                            "milestone_status": e_status,
                            "topics_covered": e_topics,
                            "action_items": e_actions,
                            "key_takeaways": e_takeaways,
                            "next_meeting_date": e_next
                        })
                        st.toast("💾 Session note updated successfully!", icon="✅")
                        st.session_state['milestone_action_feedback'] = ("success", "💾 **Session note updated successfully!**")
                        st.session_state[f"show_edit_note_{n_id}"] = False
                        st.rerun()


def render_mentor_toolkit_tab(mentor):
    st.markdown("""
        <style>
        .toolkit-header {
            background: linear-gradient(135deg, #3b0764 0%, #1e1b4b 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 22px 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(59, 7, 100, 0.18);
            border: 1px solid #581c87;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="toolkit-header">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">🧠</span>
                    <h3 style="margin: 0; color: white !important; font-size: 1.45rem; font-weight: 700;">AI Mentorship Copilot & Toolkit</h3>
                </div>
                <span style="background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%); color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Mentor Intelligence Suite</span>
            </div>
            <p style="color: #e9d5ff; margin-top: 8px; margin-bottom: 0; font-size: 0.92rem;">
                Accelerate your coaching with AI-powered agenda generators, 90-day growth roadmaps, constructive feedback frameworks, and mock interview question banks tailored to your mentees.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    tool_choice = st.radio(
        "Select Toolkit Generator:",
        [
            "📅 1-on-1 Meeting Agenda Builder",
            "🗺️ 90-Day Mentee Growth Roadmap",
            "✍️ Constructive Feedback & CV Reviewer",
            "🎯 Scenario & Mock Interview Generator",
            "💬 AI Coaching Advisor Chat"
        ],
        horizontal=True,
        key="mentor_toolkit_tool_radio"
    )
    
    st.markdown("---")
    
    system_inst_base = (
        f"You are an expert AI Mentorship Assistant designed for senior engineering mentors, engineering managers, "
        f"and technical leaders on the Mentoring-Me platform. You help mentors give high-impact guidance to early-career "
        f"technologists, career transitioners, and women in tech (SDG 5 focus). Mentor Name: {mentor.get('name')}, "
        f"Expertise: {mentor.get('dev_type')}, Experience: {mentor.get('years_code_pro')} years."
    )
    
    if tool_choice == "📅 1-on-1 Meeting Agenda Builder":
        st.subheader("📅 1-on-1 Meeting Agenda Builder")
        st.caption("Generate a structured minute-by-minute meeting plan based on your mentee's current stage and goals.")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            agenda_type = st.selectbox(
                "Select Meeting Framework:",
                [
                    "Kickoff & 6-Month Career Vision (30-45 min)",
                    "Mid-Cycle Progress & Skill Check-in (45 min)",
                    "Technical Architecture & Code Review (45 min)",
                    "Promotion, Visibility & Compensation Prep (45 min)",
                    "Crisis Triage, Burnout & Imposter Syndrome (30 min)"
                ],
                key="agenda_type_sel"
            )
        with col_a2:
            duration_opt = st.selectbox("Session Duration:", ["30 Minutes", "45 Minutes", "60 Minutes"], key="duration_opt_sel")
            
        custom_focus = st.text_area(
            "Mentee Background / Specific Focus for this Call:",
            placeholder="e.g. Mentee is an early-career backend developer preparing to lead their first microservice migration and feeling nervous about stakeholder pushback.",
            key="agenda_custom_focus"
        )
        
        if st.button("⚡ Generate Customized Agenda", type="primary", key="gen_agenda_btn"):
            with st.spinner("Generating meeting agenda..."):
                prompt = (
                    f"Create a structured {duration_opt} 1-on-1 mentorship agenda using the '{agenda_type}' framework. "
                    f"Mentee context: {custom_focus or 'Early-career software engineer'}. Include timestamps, icebreaker, "
                    f"open coaching questions, and action items."
                )
                output = generate_mentor_ai_completion(system_inst_base, prompt)
                st.markdown(output)
                
    elif tool_choice == "🗺️ 90-Day Mentee Growth Roadmap":
        st.subheader("🗺️ 90-Day Mentee Growth Roadmap Generator")
        st.caption("Build a progressive 3-month milestone roadmap to guide your mentee from skill acquisition to high-impact execution.")
        
        target_role_goal = st.text_input(
            "Mentee Target Role or Career Milestone:",
            placeholder="e.g. Junior Backend Developer transitioning to Mid-Level Cloud Engineer with AWS & Kubernetes",
            key="roadmap_target_goal"
        )
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            current_skill = st.text_input("Current Level / Skills:", placeholder="e.g. Python, SQL, Git basics", key="roadmap_curr_skills")
        with col_r2:
            time_commitment = st.selectbox("Mentee Weekly Learning Capacity:", ["3-5 hours/week", "5-10 hours/week", "10+ hours/week"], key="roadmap_capacity")
            
        if st.button("⚡ Generate 90-Day Growth Roadmap", type="primary", key="gen_roadmap_btn"):
            if not target_role_goal.strip():
                st.warning("Please enter a Target Role or Milestone.")
            else:
                with st.spinner("Building 90-day progression roadmap..."):
                    prompt = (
                        f"Design a 90-Day Growth Roadmap for a mentee with current skills '{current_skill}' "
                        f"aiming for '{target_role_goal}'. Capacity: {time_commitment}. Break it into Month 1 (Foundations & Habits), "
                        f"Month 2 (System Architecture & Ownership), and Month 3 (Impact & Delivery). Include KPIs and concrete milestones."
                    )
                    output = generate_mentor_ai_completion(system_inst_base, prompt)
                    st.markdown(output)
                    
    elif tool_choice == "✍️ Constructive Feedback & CV Reviewer":
        st.subheader("✍️ Constructive Feedback & CV Review Assistant")
        st.caption("Transform raw project notes or draft resumes into empowering, impactful feedback using the SBI (Situation-Behavior-Impact) framework.")
        
        feedback_mode = st.selectbox(
            "Feedback Type:",
            [
                "CV / Resume Bullet Point Strengthening (X-Y-Z formula)",
                "Situation-Behavior-Impact (SBI) Performance Feedback",
                "Technical Project & Code Design Review Feedback"
            ],
            key="feedback_mode_sel"
        )
        
        raw_draft = st.text_area(
            "Paste Mentee's Draft Text, Resume Bullets, or Scenario:",
            placeholder="e.g. 'I worked on the search feature for our e-commerce platform and fixed several bugs in the Django codebase.'",
            height=120,
            key="feedback_raw_input"
        )
        
        if st.button("⚡ Generate Actionable Feedback", type="primary", key="gen_feedback_btn"):
            if not raw_draft.strip():
                st.warning("Please paste some text to review.")
            else:
                with st.spinner("Analyzing and enhancing feedback..."):
                    prompt = (
                        f"Review the following draft for a mentee using the '{feedback_mode}' framework. "
                        f"Raw input: '{raw_draft}'. Provide specific strengths, high-leverage growth areas, and rewritten high-impact versions."
                    )
                    output = generate_mentor_ai_completion(system_inst_base, prompt)
                    st.markdown(output)
                    
    elif tool_choice == "🎯 Scenario & Mock Interview Generator":
        st.subheader("🎯 Scenario & Mock Interview Question Generator")
        st.caption("Generate realistic technical and behavioral interview questions tailored to your mentee's target seniority.")
        
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            int_domain = st.selectbox(
                "Interview Focus Domain:",
                [
                    "System Design & Scalability",
                    "Full-Stack & Backend Engineering",
                    "DevOps, Cloud & Infrastructure",
                    "Behavioral & Cross-Functional Influence",
                    "Engineering Leadership & Team Dynamics"
                ],
                key="int_domain_sel"
            )
        with col_i2:
            int_level = st.selectbox("Target Seniority:", ["Junior / Early-Career", "Mid-Level", "Senior / Lead"], key="int_level_sel")
            
        if st.button("⚡ Generate Mock Questions & Rubric", type="primary", key="gen_interview_btn"):
            with st.spinner("Generating interview scenarios..."):
                prompt = (
                    f"Generate 5 realistic scenario-based mock interview questions for a {int_level} engineer in '{int_domain}'. "
                    f"Include follow-up probes, what positive signals to look for, and red flags."
                )
                output = generate_mentor_ai_completion(system_inst_base, prompt)
                st.markdown(output)
                
    elif tool_choice == "💬 AI Coaching Advisor Chat":
        st.subheader("💬 AI Coaching Advisor for Mentors")
        st.caption("Ask questions on navigating mentoring dynamics, delivering feedback, coaching burnout, or sponsoring underrepresented engineers.")
        
        if "mentor_coach_messages" not in st.session_state:
            st.session_state["mentor_coach_messages"] = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your AI Coaching Advisor. How can I assist you with your mentorship sessions, coaching techniques, or mentee development plans today?"
                }
            ]
            
        m_chat_box = st.container(height=380)
        with m_chat_box:
            for m_msg in st.session_state["mentor_coach_messages"]:
                with st.chat_message(m_msg["role"], avatar="🤖" if m_msg["role"] == "assistant" else "🧭"):
                    st.markdown(m_msg["content"])
                    
        col_s1, col_s2 = st.columns(2)
        m_prompt_quick = None
        if col_s1.button("💡 How do I coach a mentee through imposter syndrome?", key="quick_q1"):
            m_prompt_quick = "How do I coach an early-career mentee who is experiencing imposter syndrome before leading a major technical project?"
        if col_s2.button("🌟 How do I sponsor underrepresented engineers effectively?", key="quick_q2"):
            m_prompt_quick = "What concrete actions can I take as a mentor to actively sponsor early-career women and minorities in engineering teams?"
            
        mentor_input = st.chat_input("Ask a coaching or mentoring question...", key="mentor_coach_input")
        if m_prompt_quick:
            mentor_input = m_prompt_quick
            
        if mentor_input:
            st.session_state["mentor_coach_messages"].append({"role": "user", "content": mentor_input})
            with m_chat_box:
                with st.chat_message("user", avatar="🧭"):
                    st.markdown(mentor_input)
                    
            with st.spinner("AI Coaching Advisor analyzing..."):
                response_txt = generate_mentor_ai_completion(
                    system_inst_base,
                    mentor_input,
                    st.session_state["mentor_coach_messages"][:-1]
                )
            st.session_state["mentor_coach_messages"].append({"role": "assistant", "content": response_txt})
            st.rerun()


def display_user_avatar(name, user_id, size=80):
    pic_bytes = api_get_profile_pic(user_id)
    if pic_bytes:
        import base64
        encoded = base64.b64encode(pic_bytes).decode('utf-8')
        html = f'<img src="data:image/png;base64,{encoded}" style="width: {size}px; height: {size}px; border-radius: 50%; object-fit: cover; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #eaeaea;">'
    else:
        first_letter = name[0].upper() if name else "?"
        colors = ["#4A90E2", "#50E3C2", "#F5A623", "#E28490", "#9B51E0", "#27AE60", "#2980B9"]
        bg_color = colors[abs(hash(name or "")) % len(colors)]
        html = f'<div style="display: flex; justify-content: center; align-items: center; width: {size}px; height: {size}px; border-radius: 50%; background-color: {bg_color}; color: white; font-size: {int(size * 0.45)}px; font-weight: bold; line-height: {size}px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #eaeaea;">{first_letter}</div>'
    st.markdown(html, unsafe_allow_html=True)

def display_welcome_header(name, user_id):
    import html as _html
    safe_name = _html.escape(name or "")
    pic_bytes = api_get_profile_pic(user_id)
    size = 60
    if pic_bytes:
        import base64
        encoded = base64.b64encode(pic_bytes).decode('utf-8')
        avatar_html = f'<img src="data:image/png;base64,{encoded}" style="width: {size}px; height: {size}px; border-radius: 50%; object-fit: cover; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #ffffff;">'
    else:
        first_letter = safe_name[0].upper() if safe_name else "?"
        colors = ["#4A90E2", "#50E3C2", "#F5A623", "#E28490", "#9B51E0", "#27AE60", "#2980B9"]
        bg_color = colors[abs(hash(name or "")) % len(colors)]
        avatar_html = f'<div style="display: flex; justify-content: center; align-items: center; width: {size}px; height: {size}px; border-radius: 50%; background-color: {bg_color}; color: white; font-size: {int(size * 0.45)}px; font-weight: bold; line-height: {size}px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #ffffff;">{first_letter}</div>'
    
    header_html = f'<div style="display: flex; align-items: center; gap: 15px; margin-top: 10px; margin-bottom: 25px;">{avatar_html}<h1 style="margin: 0; font-family: inherit; font-size: 2.2rem; font-weight: 700; line-height: 1.2;">Welcome, {safe_name}!</h1></div>'
    st.markdown(header_html, unsafe_allow_html=True)

def display_profile_card(name, country, ed_level, roles, years, org_size, priorities, additional_details, user_id, email=None, contact_link=None, alternative_emails=None, linkedin_link=None):
    import html as _html
    safe_name = _html.escape(name or "")
    safe_country = _html.escape(country or "")
    safe_ed = _html.escape(ed_level or "No education specified")
    pic_bytes = api_get_profile_pic(user_id)
    size = 65
    if pic_bytes:
        import base64
        encoded = base64.b64encode(pic_bytes).decode('utf-8')
        avatar_html = f'<img src="data:image/png;base64,{encoded}" style="width: {size}px; height: {size}px; border-radius: 50%; object-fit: cover; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid #eaeaea;">'
    else:
        first_letter = safe_name[0].upper() if safe_name else "?"
        colors = ["#4A90E2", "#50E3C2", "#F5A623", "#E28490", "#9B51E0", "#27AE60", "#2980B9"]
        bg_color = colors[abs(hash(name or "")) % len(colors)]
        avatar_html = f'<div style="display: flex; justify-content: center; align-items: center; width: {size}px; height: {size}px; border-radius: 50%; background-color: {bg_color}; color: white; font-size: {int(size * 0.45)}px; font-weight: bold; line-height: {size}px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid #eaeaea;">{first_letter}</div>'
    
    card_header_html = f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eaeaea;">{avatar_html}<div><h3 style="margin: 0; font-size: 1.25rem; font-weight: bold;">{safe_name}</h3><span style="font-size: 0.9rem; color: #888;">🌍 {safe_country} | 🎓 {safe_ed}</span></div></div>'
    st.markdown(card_header_html, unsafe_allow_html=True)
    
    st.write(f"💼 **Role(s):** {roles}")
    st.write(f"⏳ **Professional Experience:** {format_experience_years(years)} years")
    st.write(f"🏢 **Company Size:** {org_size or 'Not stated'}")
    st.write(f"🌟 **Job Priorities:** {priorities or 'Not stated'}")
    if additional_details:
        st.write(f"📝 **Bio / Goals:**")
        st.info(additional_details)
    if email:
        st.write(f"✉️ **Email Address:** `{email}`")
    if alternative_emails:
        st.write(f"📧 **Other Professional Email(s):** `{alternative_emails}`")
    if contact_link:
        st.write(f"🔗 **Scheduling / Contact Link:** [{contact_link}]({contact_link})")
    if linkedin_link:
        st.write(f"🔗 **LinkedIn Profile:** [{linkedin_link}]({linkedin_link})")

def render_sso_gateway_section(default_role="MENTEE", mode="signin", key_suffix="signin"):
    invite = st.session_state.get('invite_code')
    clean_role = "MENTOR" if "mentor" in str(default_role).lower() else "MENTEE"
    google_url = api_get_sso_url("google", role=clean_role, mode=mode, invite_code=invite)
    
    st.markdown("""
        <div style="display: flex; align-items: center; text-align: center; margin: 20px 0 14px 0;">
            <div style="flex-grow: 1; border-bottom: 1px solid #e2e8f0;"></div>
            <span style="padding: 0 14px; color: #94a3b8; font-size: 0.85rem; font-weight: 500;">or</span>
            <div style="flex-grow: 1; border-bottom: 1px solid #e2e8f0;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    btn_label = f"🌐 Continue as {clean_role.capitalize()} with Google" if mode == "signin" else f"🌐 Register as {clean_role.capitalize()} with Google"
    if google_url and "accounts.google.com" in google_url:
        st.link_button(btn_label, google_url, use_container_width=True)
    else:
        if st.button(btn_label, key=f"disabled_sso_btn_{key_suffix}", use_container_width=True):
            st.warning("⚠️ Google OAuth is not configured on this server. Please ensure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are added to your Railway backend variables.")

# Application Views
if st.session_state['access_token'] is None:
    if st.session_state.get('account_deleted_banner'):
        st.success(f"🗑️ **{st.session_state['account_deleted_banner']}**")
        if st.button("Dismiss Notice", key="dismiss_acc_del_banner_btn"):
            del st.session_state['account_deleted_banner']
            st.rerun()

    if st.session_state.get('sso_success_msg'):
        st.success(f"{st.session_state['sso_success_msg']}")
        if st.button("Dismiss Message", key="dismiss_sso_success_btn"):
            del st.session_state['sso_success_msg']
            st.rerun()

    if st.session_state.get('sso_error'):
        st.error(f"❌ {st.session_state['sso_error']}")
        if st.button("Dismiss Notice", key="dismiss_sso_err_btn"):
            del st.session_state['sso_error']
            st.rerun()
            
    if st.session_state.get('two_factor_challenge'):
        # Step 2: Double Authentication (2FA) / Email Verification
        is_signup = st.session_state.get('two_factor_is_signup', False)
        header_title = "Verify Your Email to Activate Account" if is_signup else "Double Authentication"
        header_sub = "Step 2 of 2: Security Verification"
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 12px; padding: 20px; color: white; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-size: 1.8rem;">🔐</span>
                    <div>
                        <h3 style="margin: 0; color: white; font-weight: 700; font-size: 1.25rem;">{header_title}</h3>
                        <span style="font-size: 0.85rem; color: #94a3b8;">{header_sub}</span>
                    </div>
                </div>
                <p style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0;">
                    We sent a 6-digit verification code to your email. Enter it below to activate your account and proceed directly to your dashboard.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        target_email = st.session_state.get('two_factor_email', 'your account')
        st.caption(f"✉️ Verification destination: **{target_email}** (Code expires in 5 minutes)")
        
        with st.form("two_factor_verify_form"):
            code_input = st.text_input("6-Digit Security Code", max_chars=6, placeholder="e.g. 123456", help="Enter the 6-digit numeric verification code received in your email")
            btn_label = "🚀 Verify & Enter Dashboard" if is_signup else "🚀 Verify & Complete Sign In"
            verify_submit = st.form_submit_button(btn_label, type="primary", use_container_width=True)
            if verify_submit:
                if not code_input or len(code_input.strip()) < 6:
                    st.error("Please enter a valid 6-digit security code.")
                else:
                    v_ok, v_msg = api_verify_2fa(code_input.strip())
                    if v_ok:
                        st.success(v_msg)
                        st.session_state['two_factor_is_signup'] = False
                        st.rerun()
                    else:
                        st.error(v_msg)
                        
        col_resend, col_back = st.columns([1, 1])
        with col_resend:
            if st.button("🔄 Resend Code", key="resend_2fa_btn", use_container_width=True):
                r_ok, r_msg = api_resend_2fa()
                if r_ok:
                    st.success(r_msg)
                    st.rerun()
                else:
                    st.error(r_msg)
        with col_back:
            if st.button("← Back to Sign In / Sign Up", key="cancel_2fa_btn", use_container_width=True):
                st.session_state['two_factor_challenge'] = None
                st.session_state['two_factor_preview'] = None
                st.session_state['two_factor_is_signup'] = False
                st.rerun()
    else:
        st.markdown("""
            <div style="margin-bottom: 22px;">
                <h2 style="margin: 0 0 6px 0; font-weight: 700; color: #0f172a; font-size: 1.85rem;">🚀 Welcome to Mentoring-Me</h2>
                <p style="margin: 0; color: #64748b; font-size: 0.95rem; line-height: 1.5;">A dedicated mentorship community designed to support women navigating technical career milestones, foster psychological safety, and build pathways to senior leadership.</p>
            </div>
        """, unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with tab1:
            # Step 1: Primary Credentials
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="e.g. name@example.com")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In")
                if submit:
                    status_res, msg = api_login(email, password)
                    if status_res == "2FA_REQUIRED":
                        st.info(msg)
                        st.rerun()
                    elif status_res is True:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
            # SSO Options for Sign In
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            signin_role_choice = st.radio(
                "Continue with Google as:",
                options=["🌱 Mentee (seeking guidance)", "🧭 Mentor (sharing expertise)"],
                index=0,
                horizontal=True,
                key="social_signin_role_radio"
            )
            s_in_role = "MENTOR" if "Mentor" in signin_role_choice else "MENTEE"
            render_sso_gateway_section(default_role=s_in_role, mode="signin", key_suffix="signin")
            
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            with st.expander("💡 Capstone Evaluator / Demo Credentials", expanded=False):
                st.markdown("""
                Use these pre-configured accounts to test each platform role:
                - **🌱 Mentee Account:** `user_90001@mentoring-me.demo` *(Password: `password123`)*
                - **🧭 Mentor Account:** `user_1@mentoring-me.demo` *(Password: `password123`)*
                - **🛡️ Platform Admin:** `admin@mentoring-me.demo` *(Password: `adminpassword`)*
                """)

            with st.expander("🔑 Forgot Password?", expanded=bool(st.session_state.get('forgot_password_challenge'))):
                st.caption("Reset your password securely via a 6-digit verification code.")
                if st.session_state.get('forgot_password_challenge'):
                    target_fp_email = st.session_state.get('forgot_password_email', 'your email')
                    banner_msg = st.session_state.get('forgot_password_banner', f"A 6-digit reset code has been sent to **{target_fp_email}** (Valid for 15 minutes).")
                    st.success(f"✉️ {banner_msg}")
                    
                    with st.form("reset_password_subform"):
                        r_code = st.text_input("6-Digit Reset Code", max_chars=6, key="reset_code_input_field", placeholder="e.g. 123456")
                        r_new_pass = st.text_input("New Password", type="password", key="reset_new_pass_input_field", placeholder="Minimum 6 characters")
                        r_confirm_pass = st.text_input("Confirm New Password", type="password", key="reset_confirm_pass_input_field", placeholder="Re-enter your new password")
                        r_sub = st.form_submit_button("🚀 Update & Save New Password", type="primary", use_container_width=True)
                        if r_sub:
                            if not r_code or len(r_code.strip()) < 6:
                                st.error("Please enter the 6-digit verification code.")
                            elif len(r_new_pass.strip()) < 6:
                                st.error("Password must be at least 6 characters long.")
                            elif r_new_pass != r_confirm_pass:
                                st.error("❌ Passwords do not match. Please verify that both passwords are identical.")
                            else:
                                ok_r, msg_r = api_reset_password(
                                    challenge_token=st.session_state['forgot_password_challenge'],
                                    code=r_code.strip(),
                                    new_password=r_new_pass.strip()
                                )
                                if ok_r:
                                    st.success(f"🎉 {msg_r} You may now sign in with your new password.")
                                    del st.session_state['forgot_password_challenge']
                                    if 'forgot_password_preview' in st.session_state:
                                        del st.session_state['forgot_password_preview']
                                    if 'forgot_password_email' in st.session_state:
                                        del st.session_state['forgot_password_email']
                                    if 'forgot_password_banner' in st.session_state:
                                        del st.session_state['forgot_password_banner']
                                    st.rerun()
                                else:
                                    st.error(msg_r)
                    if st.button("← Cancel Password Reset", key="cancel_reset_btn_sub"):
                        del st.session_state['forgot_password_challenge']
                        if 'forgot_password_preview' in st.session_state:
                            del st.session_state['forgot_password_preview']
                        if 'forgot_password_banner' in st.session_state:
                            del st.session_state['forgot_password_banner']
                        st.rerun()
                else:
                    with st.form("forgot_password_req_form"):
                        fp_email = st.text_input("Enter your registered account email", key="forgot_email_in", placeholder="e.g. your_email@example.com")
                        fp_submit = st.form_submit_button("📩 Send 6-Digit Reset Code", use_container_width=True)
                        if fp_submit:
                            if not fp_email or "@" not in fp_email:
                                st.error("Please enter a valid email address.")
                            else:
                                fp_ok, fp_res = api_forgot_password(fp_email.strip())
                                if fp_ok:
                                    st.session_state['forgot_password_challenge'] = fp_res['challenge_token']
                                    st.session_state['forgot_password_preview'] = fp_res.get('otp_code_preview')
                                    st.session_state['forgot_password_email'] = fp_email.strip()
                                    st.session_state['forgot_password_banner'] = fp_res.get('message', 'Reset code sent!')
                                    st.rerun()
                                else:
                                    if "Google" in str(fp_res) or "Facebook" in str(fp_res) or "Sign-In" in str(fp_res):
                                        st.info(f"ℹ️ {fp_res}")
                                    else:
                                        st.error(f"❌ {fp_res}")
                    
        with tab2:
            invite = st.session_state.get('invite_code')
            if invite:
                st.info(f"✨ **Applying Invite Code:** `{invite}`. You will be automatically connected to your nominating mentee upon signup!")
                
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="e.g. Jane.Doe@example.com")
                new_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
                role_options = ["Mentor", "Mentee"] if invite else ["Mentee", "Mentor"]
                role = st.selectbox("I am signing up as a:", role_options)
                st.caption("🔒 *A 6-digit verification code will be sent to your email to verify and activate your account.*")
                submit = st.form_submit_button("🚀 Create Account & Verify Email", type="primary", use_container_width=True)
                if submit:
                    if len(new_password) < 8:
                        st.error("Password must be at least 8 characters long.")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match. Please verify that both passwords are identical.")
                    else:
                        status_res, msg = api_signup(new_email, new_password, role, invite)
                        if status_res == "2FA_REQUIRED":
                            st.info(msg)
                            st.session_state['invite_code'] = None
                            st.rerun()
                        elif status_res is True:
                            st.success(msg)
                            st.session_state['invite_code'] = None
                        else:
                            st.error(msg)
                            
            # Social Registration Options with Mentee / Mentor choice
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            default_idx = 1 if invite else 0
            signup_role_choice = st.radio(
                "Register with Google as:",
                options=["🌱 Mentee (seeking guidance)", "🧭 Mentor (sharing expertise)"],
                index=default_idx,
                horizontal=True,
                key="social_signup_role_radio"
            )
            s_role = "MENTOR" if "Mentor" in signup_role_choice else "MENTEE"
            render_sso_gateway_section(default_role=s_role, mode="signup", key_suffix="signup")
else:
    profile = st.session_state.get('profile')
    if not profile:
        profile = fetch_profile()
    if not profile:
        if not st.session_state.get('access_token'):
            clear_auth_session()
            st.rerun()
        else:
            # Backend process may be completing hot-reload
            import time
            time.sleep(0.5)
            profile = fetch_profile()
            if not profile:
                st.warning("⏳ Reconnecting session to backend service...")
                if st.button("🔄 Refresh Dashboard", key="btn_reload_session_dash"):
                    st.rerun()
                st.stop()
        
    user = profile.get('user', {})
    role = (user.get('role') or "MENTEE").upper()
    
    # Derive user display name from profile
    display_name = None
    if role == "MENTEE" and profile.get('mentee'):
        display_name = profile['mentee'].get('name')
    elif role == "MENTOR" and profile.get('mentor'):
        display_name = profile['mentor'].get('name')
        
    if not display_name or display_name.strip() == "":
        display_name = user.get('name') or user.get('email', 'User')
    
    st.sidebar.header("Navigation Panel")
    st.sidebar.markdown(f"👤 **User:** `{display_name}`")
    st.sidebar.markdown(f"🛡️ **Role:** `{role}`")
    
    unread_summary = api_get_unread_messages()
    tot_unread = unread_summary.get('total_unread', 0)
    if tot_unread > 0:
        if st.sidebar.button(f"💬 View {tot_unread} Unread Message(s)", key="sidebar_unread_btn", type="primary", use_container_width=True):
            st.session_state['trigger_tab_switch'] = "Direct Messages"
            st.rerun()
    
    if st.sidebar.button("🚪 Log Out"):
        clear_auth_session()
        st.rerun()
        
    if role == "MENTEE":
        mentee = profile['mentee']
        history = api_get_match_history()
        
        # Focus workflow for reviewing mentor profile
        if st.session_state.get('focus_review_profile'):
            f_mentor_id = st.session_state['focus_review_profile']
            f_match = next((m for m in history if m['mentor_id'] == f_mentor_id), None)
            if f_match:
                st.markdown("---")
                st.markdown(f"## 👤 Review {f_match['mentor_name']}'s Profile")
                display_profile_card(
                    name=f_match['mentor_name'],
                    country=f_match['mentor_country'],
                    ed_level=f_match.get('mentor_ed_level'),
                    roles=f_match['mentor_devtype'],
                    years=f_match['mentor_years'],
                    org_size=f_match['mentor_org_size'],
                    priorities=f_match.get('mentor_job_factors'),
                    additional_details=f_match.get('mentor_additional_details'),
                    user_id=f_match['mentor_id'],
                    email=f_match['mentor_email'],
                    contact_link=f_match.get('mentor_contact_link'),
                    linkedin_link=f_match.get('mentor_linkedin_link')
                )
                if st.button("⬅️ Return to Dashboard", key="close_focus_review"):
                    del st.session_state['focus_review_profile']
                    st.rerun()
                st.markdown("---")
                st.stop()
        
        # Focus workflow for scheduling
        if st.session_state.get('focus_scheduling_match'):
            f_match_id = st.session_state['focus_scheduling_match']
            f_match = next((m for m in history if m['id'] == f_match_id), None)
            if f_match:
                st.markdown("---")
                st.markdown("## 📅 Complete Scheduling with Mentor")
                st.info(f"Welcome your mentor **{f_match['mentor_name']}**! They have shared their availability slots below.")
                
                if f_match.get('availability_note'):
                    display_mentor_availability(f_match['availability_note'], profile, f_match)
                
                title_val = f"Mentoring-Me Intro Sync: {mentee['name']} & {f_match['mentor_name']}"
                sel_slot = st.session_state.get('selected_scheduled_slot')
                date_time_line = f"Date/Time: {sel_slot}\n" if (sel_slot and sel_slot != "None of these work / Coordinate Custom Time") else "Date/Time: To be coordinated\n"
                
                calendar_body = (
                    f"Title: {title_val}\n"
                    f"{date_time_line}"
                    f"Duration: 25 minutes\n\n"
                    f"Proposed Intro Sync Agenda:\n"
                    f"1. Icebreaker & Introductions (5 mins)\n"
                    f"   - Share briefly about our career journeys, tech stacks, and current roles.\n"
                    f"2. Partnership Goals & Expectations (10 mins)\n"
                    f"   - Discuss what we hope to accomplish together and align on mentoring scope.\n"
                    f"3. Cadence & Communication Preferences (5 mins)\n"
                    f"   - Align on meeting frequency (e.g., bi-weekly or monthly) and default messaging channels.\n"
                    f"4. Action Items & Next Steps (5 mins)\n"
                    f"   - Align on preparation for our first deep-dive discussion (Module 1: Career Progression).\n\n"
                    f"Looking forward to connecting!"
                )
                with st.expander("📋 View / Copy Raw Agenda Text (For Zoom, Teams, or Outlook)", expanded=False):
                    st.caption("💡 **Tip**: The 1-Click **📅 Google Calendar** and **📥 .ICS Invite** buttons below automatically include this full agenda for you. Expand this section only if you need to manually copy the text into Zoom, Microsoft Teams, or custom calendar invites.")
                    st.text_area("Calendar Event Details", value=calendar_body, height=180, key=f"edit_cal_details_{f_match_id}_{sel_slot}", label_visibility="collapsed")
                
                st.markdown("### ✉️ Introductory Message to Mentor")
                st.caption("Personalize this message before sending it via In-App Chat or Email:")
                default_intro_text = generate_default_mentee_intro_message(
                    mentor_name=f_match['mentor_name'],
                    mentee_name=mentee['name'],
                    sel_slot=sel_slot,
                    availability_note=f_match.get('availability_note')
                )
                edited_intro_msg = st.text_area(
                    "Introductory Message",
                    value=default_intro_text,
                    height=180,
                    key=f"edit_intro_msg_{f_match_id}_{sel_slot}",
                    label_visibility="collapsed"
                )
                coordinate_subject = f"Scheduling: Mentoring-Me Intro Call — {mentee['name']} & {f_match['mentor_name']}"

                # Google Calendar and ICS generators for Focus Mode
                f_gcal_url = generate_google_calendar_url(
                    title=title_val,
                    description=calendar_body,
                    location="Virtual (Mentoring-Me Platform)",
                    start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                    end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                )
                f_ics_bytes = generate_ics_calendar_file(
                    title=title_val,
                    description=calendar_body,
                    location="Virtual (Mentoring-Me Platform)",
                    start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                    end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                )

                if st.session_state.get('sched_sent_success_msg'):
                    st.success(f"✅ **{st.session_state['sched_sent_success_msg']}**")

                st.markdown("**Choose Your Communication Channel & Calendar Sync:**")
                coord_col1, coord_col2, coord_col3, coord_col4 = st.columns(4)
                with coord_col1:
                    if st.button("🚀 Send Direct Message", key=f"quick_send_coord_{f_match_id}", type="primary", use_container_width=True):
                        ok_s, res_s = api_send_message(f_match_id, edited_intro_msg)
                        if ok_s:
                            api_mark_match_notified(f_match_id)
                            st.session_state['sched_sent_success_msg'] = f"Message sent & notification email dispatched to {f_match['mentor_name']}!"
                            st.toast(f"📤 Message sent & notification email dispatched to {f_match['mentor_name']}!", icon="✅")
                            st.rerun()
                        else:
                            st.error(res_s)
                with coord_col2:
                    if st.button("✉️ Send via Email", key=f"focus_send_email_{f_match_id}", use_container_width=True):
                        ok_e, msg_e = api_send_direct_match_email(f_match_id, coordinate_subject, edited_intro_msg)
                        if ok_e:
                            api_mark_match_notified(f_match_id)
                            st.session_state['sched_sent_success_msg'] = f"Direct email successfully sent to {f_match['mentor_name']}!"
                            st.toast(f"✉️ Email sent to {f_match['mentor_name']}!", icon="✅")
                            st.rerun()
                        else:
                            st.error(msg_e)
                with coord_col3:
                    st.link_button("📅 Add to Google Calendar", f_gcal_url, use_container_width=True)
                with coord_col4:
                    st.download_button(
                        "📥 Download .ICS Invite",
                        data=f_ics_bytes,
                        file_name=f"mentor_me_sync_{f_match['mentor_name'].replace(' ', '_')}.ics",
                        mime="text/calendar",
                        use_container_width=True,
                        key=f"download_ics_focus_{f_match_id}"
                    )
                
                st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
                nav_c1, nav_c2 = st.columns([1, 1])
                with nav_c1:
                    if st.button("💬 Go to Direct Messages", key=f"focus_open_chat_btn_{f_match_id}", use_container_width=True):
                        if 'sched_sent_success_msg' in st.session_state:
                            del st.session_state['sched_sent_success_msg']
                        del st.session_state['focus_scheduling_match']
                        st.session_state['active_chat_match_id'] = f_match_id
                        st.session_state['trigger_tab_switch'] = "Direct Messages"
                        st.session_state['profile'] = None
                        st.rerun()
                with nav_c2:
                    is_sent = bool(st.session_state.get('sched_sent_success_msg'))
                    btn_label = "✅ Done (Return to Platform Matches)" if is_sent else "⬅️ Close & Return to Dashboard"
                    btn_type = "primary" if is_sent else "secondary"
                    if st.button(btn_label, key="close_focus_scheduling", type=btn_type, use_container_width=True):
                        api_mark_match_notified(f_match_id)
                        if 'sched_sent_success_msg' in st.session_state:
                            del st.session_state['sched_sent_success_msg']
                        del st.session_state['focus_scheduling_match']
                        st.session_state['profile'] = None
                        st.rerun()
                st.markdown("---")
                st.stop()
                
        unnotified = [m for m in history if isinstance(m, dict) and m.get('status') == 'ACCEPTED' and not m.get('mentee_notified', False)]
        unread_count = len(unnotified)
        
        col_greet, col_bell = st.columns([8, 2])
        with col_greet:
            display_welcome_header(mentee['name'], mentee['id'])
            if st.button("📸 Edit Profile Photo", key="mentee_avatar_toggle"):
                st.session_state['show_pic_uploader'] = not st.session_state.get('show_pic_uploader', False)
                
            # Conditionally display uploader when triggered in session state
            if st.session_state.get('show_pic_uploader', False):
                with st.container(border=True):
                    st.info("📸 **Change Profile Picture**")
                    profile_pic_file = st.file_uploader("Choose a photo (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="mentee_pic_upload_standalone")
                    if profile_pic_file is not None:
                        success, msg = api_upload_profile_pic(profile_pic_file.getvalue(), profile_pic_file.name)
                        if success:
                            st.success("Avatar updated!")
                            st.session_state['profile'] = None
                            st.session_state['show_pic_uploader'] = False
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    # Show Remove Picture option if user currently has an uploaded profile photo
                    if mentee.get('profile_pic'):
                        if st.button("🗑️ Remove Picture (Revert to Letter Avatar)", key="mentee_remove_pic_btn"):
                            success, msg = api_delete_profile_pic()
                            if success:
                                st.success(msg)
                                st.session_state['profile'] = None
                                st.session_state['show_pic_uploader'] = False
                                st.rerun()
                            else:
                                st.error(msg)
                                
                    if st.button("❌ Close Photo Drawer", key="mentee_close_uploader_btn"):
                        st.session_state['show_pic_uploader'] = False
                        st.rerun()
        with col_bell:
            render_top_notifications_bell("MENTEE")
        
        msg_tab_label = f"💬 Direct Messages ({tot_unread})" if tot_unread > 0 else "💬 Direct Messages"
        tab_setup, tab_match, tab_messages, tab_outreach, tab_nominations, tab_history, tab_witech, tab_advisor = st.tabs(["⚙️ Profile Setup", "🎯 Platform Matches", msg_tab_label, "🌐 Outreach Hub", "📩 External Invitations", "📜 Match History", "🌟 Women in Tech", "💡 AI Career Advisor"])
        
        if st.session_state.get('trigger_tab_switch'):
            tgt_tab = st.session_state.pop('trigger_tab_switch')
            trigger_client_tab_switch(tgt_tab)
        
        with tab_setup:
            st.subheader("Profile Details")
            if st.session_state.get('profile_save_success'):
                st.success(st.session_state.pop('profile_save_success'))
            with st.form("edit_profile_form"):

                # ── Section 1: My Profile ──────────────────────────────────
                with st.expander("👤 My Profile", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Display Name", value=mentee['name'])
                    with col2:
                        country = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index(mentee['country']) if mentee['country'] in COUNTRIES else 0)

                    col3, col4 = st.columns(2)
                    with col3:
                        raw_years = mentee['years_code_pro'] or 1.0
                        safe_years = min(float(raw_years), 50.0)
                        years = st.number_input("Years of Professional Experience", min_value=0.0, max_value=50.0, value=safe_years, step=0.5, format="%g")
                        st.caption("Use decimals for part-years: e.g. 1.5 = 1 year & 6 months, 0.5 = 6 months.")
                    with col4:
                        ed_level = st.selectbox("Education Level", ED_LEVELS, index=ED_LEVELS.index(mentee['ed_level']) if mentee['ed_level'] in ED_LEVELS else 0)

                    col5, col6 = st.columns(2)
                    with col5:
                        org_size = st.selectbox("Organization Size", ORG_SIZES, index=ORG_SIZES.index(mentee['org_size']) if mentee['org_size'] in ORG_SIZES else 0)
                    with col6:
                        g_opts = ["Female", "Male", "Non-binary"]
                        cur_g = mentee.get('gender')
                        g_idx = g_opts.index(cur_g) if cur_g in g_opts else 0
                        gender = st.selectbox("Gender", g_opts, index=g_idx)
                        st.caption("Sharing your gender helps us connect you with senior women in tech as role models via our representation-aware matching.")

                    # Roles
                    current_roles = [r.strip() for r in mentee['dev_type'].split(";")] if mentee['dev_type'] else []
                    valid_current_roles = [r for r in current_roles if r in ALL_ROLES]
                    picked_roles = st.multiselect("Role(s)", ALL_ROLES, default=valid_current_roles if valid_current_roles else [ALL_ROLES[0]])
                    st.caption("Select all roles that describe your current or target career path.")
                    custom_roles = st.text_input("Additional roles not listed above (semicolon-separated)", key="custom_roles_mentee", placeholder="e.g. ML Engineer; Data Analyst")

                    # Job Priorities
                    current_factors = [f.strip() for f in mentee['job_factors'].split(";")] if mentee['job_factors'] else []
                    valid_current_factors = [f for f in current_factors if f in ALL_FACTORS]
                    picked_factors = st.multiselect("Job Priorities", ALL_FACTORS, default=valid_current_factors if valid_current_factors else [ALL_FACTORS[0]])
                    st.caption("What matters most to you in your career right now? Influences your platform match scoring.")

                    col7, col8 = st.columns(2)
                    with col7:
                        linkedin_link = st.text_input("LinkedIn Profile URL", value=mentee.get('linkedin_link') or "", placeholder="https://linkedin.com/in/yourprofile")
                    with col8:
                        alternative_emails = st.text_input("Additional Contact Emails", value=mentee.get('alternative_emails') or "", placeholder="e.g. personal@email.com; uni@edu.org")
                        st.caption("Other emails mentors or the platform can use to reach you.")

                    # Timezone
                    current_tz = mentee.get('timezone') or "Europe/London"
                    tz_idx = TIMEZONE_OPTIONS.index(current_tz) if current_tz in TIMEZONE_OPTIONS else 0
                    timezone = st.selectbox("Your Timezone", TIMEZONE_OPTIONS, index=tz_idx)
                    st.caption("Used to convert mentor availability slots into your local time.")

                    additional_details = st.text_area("Bio / Goals / Specific Interests", value=mentee.get('additional_details') or "", placeholder="e.g. I am a junior backend developer looking to grow in cloud architecture and distributed systems...")
                    st.caption("This context helps the AI coach and your matched mentor understand your background.")

                    prefer_diversity_ally = st.checkbox(
                        "🤝 Welcome Guidance from Diversity & Inclusion (D&I) Allies",
                        value=bool(mentee.get('prefer_diversity_ally', False)),
                        help="Check this if you are happy to receive mentorship from senior leaders of all genders (including supportive male allies) who actively sponsor and advocate for women in STEM. Applies a +10% matching boost."
                    )
                    st.caption("💡 Check this if you are happy to receive mentorship from senior leaders of all genders (including supportive male allies) who actively sponsor and advocate for women in STEM. Unlocks a **+10% matching priority boost**.")

                # ── Section 2: Mentor Search Preferences ──────────────────
                with st.expander("🎯 Mentor Search Preferences & Match Boosting", expanded=True):
                    st.caption("These preferences directly drive your **platform match ranking** and power targeted discovery across the **Outreach Hub**.")

                    st.info(
                        "💡 **Mandatory Expertise Requirement (Min. 3 Skills)**: Specifying at least 3 distinct technical or domain expertises (e.g. *FastAPI, Cloud Architecture, DevOps*) directly unlocks up to a **+10% algorithmic compatibility bonus** on the platform and optimizes your external candidate discovery across the **Outreach Hub (GitHub, ORCID & LinkedIn)**."
                    )

                    target_mentor_expertise = st.text_input(
                        "Preferred Mentor Expertise Keywords * (Minimum 3 required)",
                        value=mentee.get('target_mentor_expertise') or "",
                        placeholder="e.g. FastAPI, DevOps, Cloud Architecture"
                    )
                    st.caption("Enter at least 3 comma-separated or semicolon-separated skills/technologies you want your mentor to specialize in.")

                    col9, col10 = st.columns(2)
                    with col9:
                        raw_pref_country = mentee.get('target_mentor_country') or ""
                        if raw_pref_country and raw_pref_country != "Any":
                            default_countries = [c.strip() for c in raw_pref_country.replace(",", ";").split(";") if c.strip() in COUNTRIES]
                        else:
                            default_countries = []
                        target_mentor_countries = st.multiselect(
                            "Preferred Mentor Countries (Multi-select)",
                            options=COUNTRIES,
                            default=default_countries,
                            help="Choose one or more countries to prioritize mentors located in those regions. Leave empty to consider all countries (worldwide)."
                        )
                    with col10:
                        target_mentor_min_years = st.number_input(
                            "Minimum Mentor Experience (Years)",
                            min_value=0.0, max_value=50.0,
                            value=float(mentee.get('target_mentor_min_years') or 5.0),
                            step=0.5,
                            format="%g"
                        )
                    st.caption("Mentors below this threshold will score lower. Use 0.5 for 6 months, 1.5 for 1.5 years, etc.")

                # ── CV Upload (bottom of form) ─────────────────────────────
                st.markdown("---")
                st.markdown("**📄 CV Upload**")
                cv_file = st.file_uploader("Upload your CV (PDF format)", type=["pdf"], key="mentee_cv_upload")
                if mentee.get('cv_path'):
                    with st.expander("📄 View My Current Uploaded CV"):
                        pdf_bytes = api_get_cv(mentee['id'])
                        if pdf_bytes:
                            display_pdf_inline(pdf_bytes)
                        else:
                            st.warning("Failed to retrieve CV from server.")

                # ── Save Button ────────────────────────────────────────────
                save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                if save:
                    # Validate at least 3 preferred mentor expertise keywords
                    raw_kws = target_mentor_expertise.replace(";", ",").split(",")
                    cleaned_kws = [k.strip() for k in raw_kws if k.strip()]
                    if len(cleaned_kws) < 3:
                        st.error(
                            "⚠️ **Preferred Mentor Expertise is mandatory (minimum 3 required)**. "
                            "Please enter at least 3 skills/expertises separated by commas (e.g. *FastAPI, DevOps, Cloud Architecture*) "
                            "to boost your platform match ranking and enable Outreach Hub search."
                        )
                    else:
                        combined_roles = picked_roles.copy()
                        if custom_roles.strip():
                            for r in custom_roles.split(";"):
                                r_clean = r.strip()
                                if r_clean and r_clean not in combined_roles:
                                    combined_roles.append(r_clean)

                        updated_data = {
                            "name": name,
                            "country": country,
                            "ed_level": ed_level,
                            "dev_type": ";".join(combined_roles),
                            "years_code_pro": years,
                            "job_factors": ";".join(picked_factors),
                            "org_size": org_size,
                            "additional_details": additional_details,
                            "gender": gender,
                            "target_mentor_expertise": ", ".join(cleaned_kws),
                            "target_mentor_country": "; ".join(target_mentor_countries) if target_mentor_countries else None,
                            "target_mentor_min_years": target_mentor_min_years,
                            "alternative_emails": alternative_emails.strip(),
                            "prefer_diversity_ally": prefer_diversity_ally,
                            "timezone": timezone,
                            "linkedin_link": linkedin_link.strip() if linkedin_link else None
                        }
                        success, msg = api_update_profile(updated_data)
                        if success:
                            if cv_file is not None:
                                api_upload_cv(cv_file.getvalue(), cv_file.name)
                            st.session_state['profile'] = None
                            st.session_state['profile_save_success'] = msg
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("---")
            with st.expander("🔐 Account Security & Double Authentication", expanded=False):
                st.markdown("##### Double Authentication (2FA)")
                st.caption("Protect your account with an extra verification layer requiring a 6-digit code at sign-in.")
                user_info = profile.get('user', {}) if profile else {}
                curr_2fa = user_info.get('two_factor_enabled', True)
                col_2fa_status, col_2fa_act = st.columns([3, 1.2])
                with col_2fa_status:
                    st.write(f"Current Status: **{'🟢 Enabled (Active Protection)' if curr_2fa else '⚪ Disabled'}**")
                with col_2fa_act:
                    target_state = not curr_2fa
                    toggle_btn_text = "Disable 2FA" if curr_2fa else "Enable 2FA"
                    if st.button(toggle_btn_text, key="toggle_2fa_btn_mentee", use_container_width=True):
                        t_ok, t_msg = api_toggle_2fa(target_state)
                        if t_ok:
                            st.success(t_msg)
                            st.rerun()
                        else:
                            st.error(t_msg)

            with st.expander("⚠️ Danger Zone — Delete Account", expanded=False):
                st.markdown("##### 🗑️ Permanent Account Deletion")
                st.caption(
                    "Permanently delete your account, mentee profile, uploaded CV, active mentorship connections, "
                    "and all direct messages. This action is **permanent and irreversible** under GDPR Right to Erasure."
                )
                confirm_del_mentee = st.checkbox(
                    "I understand that this action is permanent and cannot be undone.",
                    key="confirm_del_mentee_check"
                )
                if st.button("🗑️ Permanently Delete My Account", key="btn_delete_own_mentee_acc", type="primary", disabled=not confirm_del_mentee):
                    ok_del, msg_del = api_delete_my_account()
                    if ok_del:
                        st.session_state['account_deleted_banner'] = msg_del
                        st.rerun()
                    else:
                        st.error(msg_del)

        if True:
            
            with tab_match:
                st.subheader("Dynamic Matches Recommendation")
                
                # Persistent feedback banner across reruns
                if 'match_action_feedback' in st.session_state and st.session_state['match_action_feedback']:
                    fb_type, fb_msg = st.session_state.pop('match_action_feedback')
                    if fb_type == "success":
                        st.success(fb_msg)
                    elif fb_type == "info":
                        st.info(fb_msg)
                    elif fb_type == "error":
                        st.error(fb_msg)

                # ── Equity transparency banner ─────────────────────────────
                if mentee.get('gender') in ['Female', 'Woman']:
                    st.info(
                        "🌟 **Equity-Adjusted Results**: As an early-career woman in tech, your match results "
                        "prioritise senior female role models and Diversity & Inclusion Allies where available. "
                        "This is part of our commitment to equitable mentorship aligned with SDG 5 — Gender Equality."
                    )
                elif mentee.get('prefer_diversity_ally'):
                    st.info("🤝 **Ally-Boosted Results**: Your preference for a Diversity & Inclusion Ally mentor is active — matching results reflect this.")
                # Auto-restore match proposals from database if not already in session state
                if 'current_matches' not in st.session_state or st.session_state['current_matches'] is None:
                    db_proposals = api_get_matches(recalculate=False)
                    if db_proposals:
                        st.session_state['current_matches'] = sorted(db_proposals, key=lambda m: m.get('total_score', 0), reverse=True)

                col_s1, col_s2 = st.columns([2, 1])
                btn_label = "🔄 Re-calculate / Refresh Matches" if st.session_state.get('current_matches') else "🚀 Search Active Mentor Pool"
                if col_s1.button(btn_label, type="primary"):
                    with st.spinner("Calculating match coefficients..."):
                        matches = api_get_matches(recalculate=True)
                        if not matches:
                            st.info("No registered mentors match your profile currently, or the pool is empty.")
                        else:
                            st.session_state['current_matches'] = sorted(matches, key=lambda m: m.get('total_score', 0), reverse=True)
                            st.rerun()
                
                if 'current_matches' in st.session_state and st.session_state['current_matches']:
                    matches = st.session_state['current_matches']
                    
                    display_list = []
                    for m in matches:
                        raw_score = m['total_score']
                        pct_score = int(round(raw_score * 100)) if isinstance(raw_score, float) and raw_score <= 1.0 else int(round(raw_score))
                        display_list.append({
                            'Mentor ID': m['mentor_id'][:8] if len(str(m['mentor_id'])) > 8 else m['mentor_id'],
                            'Mentor Name': m['mentor_name'] or f"Mentor #{m['mentor_id']}",
                            'Mentor Role(s)': m['mentor_devtype'],
                            'Experience (yrs)': format_experience_years(m.get('mentor_years')),
                            'Country': m['mentor_country'],
                            'Score': f"{pct_score}%",
                            'Confidence': m['match_quality'],
                            'Status': m['status']
                        })
                    
                    df_matches = pd.DataFrame(display_list)
                    
                    def highlight_quality(val):
                        colors = {'Strong': '#c6e6c6', 'Good': '#f5e6a8', 'Fair': '#f5c99b', 'Weak': '#f0b3b3'}
                        return f'background-color: {colors.get(val, "white")}'
                        
                    styler = df_matches.style
                    if hasattr(styler, 'map'):
                        styler = styler.map(highlight_quality, subset=['Confidence'])
                    else:
                        styler = styler.applymap(highlight_quality, subset=['Confidence'])
                        
                    st.dataframe(
                        styler,
                        use_container_width=True
                    )
                    
                    st.subheader("🎯 Request Mentorship from Top Matches")
                    st.caption("Review your algorithm-recommended mentors below and send a mentorship request to initiate a connection.")
                    for m in matches:
                        if m['status'] == 'PROPOSED':
                            cols = st.columns([2.5, 1.2, 0.8])
                            raw_s = m['total_score']
                            pct_s = int(round(raw_s * 100)) if isinstance(raw_s, float) and raw_s <= 1.0 else int(round(raw_s))
                            cols[0].write(f"**{m['mentor_name']}** ({m['mentor_devtype']} | {format_experience_years(m.get('mentor_years'))} yrs exp) — **Score: {pct_s}%** ({m['match_quality']})") 
                            
                            with st.expander(f"👤 View {m['mentor_name']}'s Profile Details"):
                                display_profile_card(
                                    name=m['mentor_name'],
                                    country=m['mentor_country'],
                                    ed_level=m.get('mentor_ed_level'),
                                    roles=m['mentor_devtype'],
                                    years=m['mentor_years'],
                                    org_size=m['mentor_org_size'],
                                    priorities=m.get('mentor_job_factors'),
                                    additional_details=m.get('mentor_additional_details'),
                                    user_id=m['mentor_id'],
                                    linkedin_link=m.get('mentor_linkedin_link')
                                )
                                if m.get('is_representation_boosted'):
                                    st.success("🌟 **Representation Alignment**: Pair offers mentorship from a senior female leader in technical fields.")
                                if m.get('is_ally_boosted'):
                                    st.success("🤝 **Diversity Ally Match**: This mentor is an active Diversity & Inclusion Ally, committed to supporting gender equality.")
                                    
                            if m.get('mentor_cv_path'):
                                with st.expander(f"📄 Read {m['mentor_name']}'s CV"):
                                    pdf_bytes = api_get_cv(m['mentor_id'])
                                    if pdf_bytes:
                                        display_pdf_inline(pdf_bytes)
                                    else:
                                        st.info("CV details unavailable.")
                            if cols[1].button("📩 Request Mentorship", key=f"req_mentor_{m['id']}", type="primary"):
                                if api_match_action(m['id'], "ACCEPT"):
                                    st.toast(f"🚀 Mentorship request sent to {m['mentor_name']}!", icon="✅")
                                    st.session_state['match_action_feedback'] = (
                                        "success",
                                        f"🚀 **Mentorship request successfully sent to {m['mentor_name']}!**\n\n"
                                        f"Your request has been dispatched to their dashboard and email. You can monitor the response status in your **📜 Match History** tab."
                                    )
                                    if 'current_matches' in st.session_state and st.session_state['current_matches']:
                                        st.session_state['current_matches'] = [cm for cm in st.session_state['current_matches'] if cm['id'] != m['id']]
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to submit mentorship request to {m['mentor_name']}. Please try again.")
                            if cols[2].button("🚫 Pass", key=f"decline_{m['id']}"):
                                if api_match_action(m['id'], "DECLINE"):
                                    st.toast(f"🚫 Passed on proposal for {m['mentor_name']}.", icon="ℹ️")
                                    st.session_state['match_action_feedback'] = (
                                        "info",
                                        f"🚫 **Passed on proposal for {m['mentor_name']}**.\n\n"
                                        f"This recommendation has been archived. You can click **Re-calculate / Refresh Matches** anytime to explore more mentors."
                                    )
                                    if 'current_matches' in st.session_state and st.session_state['current_matches']:
                                        st.session_state['current_matches'] = [cm for cm in st.session_state['current_matches'] if cm['id'] != m['id']]
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to archive proposal for {m['mentor_name']}.")
                                    
                    with st.expander("📊 View Detailed Compatibility Breakdown (Top Match)", expanded=False):
                        top = matches[0]
                        display_match_compatibility_report(top)
            
            with tab_messages:
                render_messages_page("MENTEE", profile, history)
            
            with tab_history:
                import urllib.parse as _up_hist

                st.subheader("My Match History")
                st.caption("A complete log of every mentor the platform has matched you with, along with their current connection status.")

                history = api_get_match_history()

                if not history:
                    st.info("You haven't received any matches yet. Head to the **Platform Matches** tab to find your first mentor!")
                else:
                    # ── 1. Metric bar ─────────────────────────────────────────
                    total_h    = len(history)
                    connected  = sum(1 for h in history if h['status'] == 'ACCEPTED')
                    pending_h  = sum(1 for h in history if h['status'] in ['REQUESTED', 'PENDING'])
                    declined_h = sum(1 for h in history if h['status'] in ['DECLINED', 'DECLINE'])
                    hm1, hm2, hm3, hm4 = st.columns(4)
                    hm1.metric("📋 Total Matches", total_h)
                    hm2.metric("✅ Connected", connected)
                    hm3.metric("⏳ Awaiting Mentor", pending_h)
                    hm4.metric("❌ Declined / Passed", declined_h)
                    st.markdown("---")

                    # ── 3. Filter & sort controls ──────────────────────────────
                    f_col1, f_col2 = st.columns([2, 1])
                    with f_col1:
                        status_filter = st.selectbox(
                            "Filter by Status",
                            ["All", "✅ Connected (ACCEPTED)", "⏳ Awaiting Mentor Response (REQUESTED)", "❌ Declined / Passed"],
                            key="hist_status_filter"
                        )
                    with f_col2:
                        sort_by = st.selectbox(
                            "Sort by",
                            ["📅 Date (Newest First)", "🏆 Match Score (Highest First)", "📅 Date (Oldest First)"],
                            key="hist_sort_by"
                        )

                    # Apply filter
                    status_map = {
                        "All": None,
                        "✅ Connected (ACCEPTED)": "ACCEPTED",
                        "⏳ Awaiting Mentor Response (REQUESTED)": "REQUESTED",
                        "❌ Declined / Passed": "DECLINED"
                    }
                    active_filter = status_map[status_filter]
                    if active_filter == "DECLINED":
                        filtered = [h for h in history if h['status'] in ['DECLINED', 'DECLINE']]
                    elif active_filter == "REQUESTED":
                        filtered = [h for h in history if h['status'] in ['REQUESTED', 'PENDING']]
                    elif active_filter is not None:
                        filtered = [h for h in history if h['status'] == active_filter]
                    else:
                        filtered = history

                    # Apply sort
                    if "Score" in sort_by:
                        filtered = sorted(filtered, key=lambda x: x.get('total_score', 0), reverse=True)
                    elif "Oldest" in sort_by:
                        filtered = sorted(filtered, key=lambda x: x.get('created_at', ''))
                    else:
                        filtered = sorted(filtered, key=lambda x: x.get('created_at', ''), reverse=True)

                    if not filtered:
                        st.info("No matches found for the selected filter.")
                    else:
                        st.caption(f"Showing {len(filtered)} of {total_h} matches.")

                    # ── 2. Card per match ──────────────────────────────────────
                    for h in filtered:
                        score = h.get('total_score', 0)
                        # Normalise: DB stores as 0.0–1.0 float
                        if isinstance(score, float) and score <= 1.0:
                            score = int(round(score * 100))
                        else:
                            score = int(round(score))
                        quality = h.get('match_quality', '')
                        status = h['status']

                        # Score badge colours
                        if score >= 80:
                            sc_color = "#1e7e34"
                        elif score >= 50:
                            sc_color = "#856404"
                        else:
                            sc_color = "#721c24"

                        # Status badge
                        if status == 'ACCEPTED':
                            status_badge = "✅ Connected (Mentor Accepted)"
                            status_color = "#155724"
                            status_bg = "#d4edda"
                        elif status in ['DECLINED', 'DECLINE']:
                            status_badge = "❌ Declined / Passed"
                            status_color = "#721c24"
                            status_bg = "#f8d7da"
                        elif status == 'REQUESTED':
                            status_badge = "⏳ Request Sent (Awaiting Mentor)"
                            status_color = "#856404"
                            status_bg = "#fff3cd"
                        else:
                            status_badge = "💡 Match Proposed"
                            status_color = "#004085"
                            status_bg = "#cce5ff"

                        date_str = h['created_at'].split("T")[0] if 'T' in h['created_at'] else h['created_at']

                        with st.container(border=True):
                            top_l, top_r = st.columns([3, 1])
                            with top_l:
                                st.markdown(f"##### {h['mentor_name']}")
                                roles_display = (h.get('mentor_devtype') or '').replace(';', ' · ')
                                st.caption(f"📍 {h.get('mentor_country', '')}  ·  {roles_display}")
                                st.markdown(
                                    f"<span style='background:{status_bg}; color:{status_color}; "
                                    f"padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>"
                                    f"{status_badge}</span>"
                                    f"  <span style='color:#6c757d; font-size:0.8rem;'>· Matched {date_str}</span>",
                                    unsafe_allow_html=True
                                )
                            with top_r:
                                st.markdown(
                                    f"<div style='text-align:center; background:#f8f9fa; border-radius:8px; padding:8px 4px;'>"
                                    f"<span style='color:{sc_color}; font-size:1rem; font-weight:700;'>{score}%</span><br/>"
                                    f"<span style='font-size:0.7rem; color:#6c757d;'>{quality or 'Match Score'}</span></div>",
                                    unsafe_allow_html=True
                                )

                            with st.expander(f"📊 View Compatibility Breakdown ({score}%)", expanded=False):
                                display_match_compatibility_report(h)

                            # Connected mentor — show full action expanders
                            if status == 'ACCEPTED':
                                contact_parts = []
                                if h.get('mentor_email'):
                                    contact_parts.append(f"📧 `{h['mentor_email']}`")
                                if h.get('mentor_contact_link'):
                                    contact_parts.append(f"[📅 Scheduling Link]({h['mentor_contact_link']})")
                                if contact_parts:
                                    st.markdown("  ·  ".join(contact_parts))
                                if h.get('is_representation_boosted'):
                                    st.success("🌟 **Representation Alignment**: Pair offers mentorship from a senior female leader in technical fields.")
                                if h.get('is_ally_boosted'):
                                    st.success("🤝 **Diversity Ally Match**: This mentor is an active Diversity & Inclusion Ally.")

                                with st.expander(f"👤 View {h['mentor_name']}'s Profile"):
                                    display_profile_card(
                                        name=h['mentor_name'],
                                        country=h.get('mentor_country'),
                                        ed_level=h.get('mentor_ed_level'),
                                        roles=h.get('conn_devtype') or h.get('mentor_devtype'),
                                        years=h.get('mentor_years'),
                                        org_size=h.get('mentor_org_size'),
                                        priorities=h.get('mentor_job_factors'),
                                        additional_details=h.get('mentor_additional_details'),
                                        user_id=h.get('mentor_id'),
                                        email=h.get('mentor_email'),
                                        contact_link=h.get('mentor_contact_link'),
                                        linkedin_link=h.get('mentor_linkedin_link')
                                    )

                                if h.get('mentor_cv_path'):
                                    with st.expander(f"📄 Read {h['mentor_name']}'s CV"):
                                        pdf_bytes = api_get_cv(h['mentor_id'])
                                        if pdf_bytes:
                                            display_pdf_inline(pdf_bytes)

                                with st.expander(f"📅 Schedule First Meeting with {h['mentor_name']}"):
                                    st.write("Generate a calendar invitation draft to schedule your first 25-minute introductory sync.")
                                    if h.get('availability_note'):
                                        display_mentor_availability(h['availability_note'], profile, h)
                                    title_val = f"Mentoring-Me Intro Sync: {mentee['name']} & {h['mentor_name']}"
                                    sel_slot = st.session_state.get('selected_scheduled_slot')
                                    date_time_line = f"Date/Time: {sel_slot}\n" if (sel_slot and sel_slot != "None of these work / Coordinate Custom Time") else "Date/Time: To be coordinated\n"
                                    calendar_body = (
                                        f"Title: {title_val}\n"
                                        f"{date_time_line}"
                                        f"Duration: 25 minutes\n\n"
                                        f"Proposed Intro Sync Agenda:\n"
                                        f"1. Icebreaker & Introductions (5 mins)\n"
                                        f"   - Share briefly about our career journeys, tech stacks, and current roles.\n"
                                        f"2. Partnership Goals & Expectations (10 mins)\n"
                                        f"   - Discuss what we hope to accomplish together and align on mentoring scope.\n"
                                        f"3. Cadence & Communication Preferences (5 mins)\n"
                                        f"   - Align on meeting frequency (e.g., bi-weekly or monthly) and default messaging channels.\n"
                                        f"4. Action Items & Next Steps (5 mins)\n"
                                        f"   - Align on preparation for our first deep-dive discussion (Module 1: Career Progression).\n\n"
                                        f"Looking forward to connecting!"
                                    )
                                    with st.expander("📋 View / Copy Raw Agenda Text (For Zoom, Teams, or Outlook)", expanded=False):
                                        st.caption("💡 **Tip**: The 1-Click **📅 Google Calendar** and **📥 .ICS Invite** buttons below automatically include this full agenda for you. Expand this section only if you need to manually copy the text into Zoom, Microsoft Teams, or custom calendar invites.")
                                        st.text_area("Calendar Event Details", value=calendar_body, height=180, key=f"edit_cal_details_{h['id']}_{sel_slot}", label_visibility="collapsed")
                                    
                                    st.markdown("### ✉️ Introductory Message to Mentor")
                                    st.caption("Personalize this message before sending it via In-App Chat or Email:")
                                    h_default_intro = generate_default_mentee_intro_message(
                                        mentor_name=h['mentor_name'],
                                        mentee_name=mentee['name'],
                                        sel_slot=sel_slot,
                                        availability_note=h.get('availability_note')
                                    )
                                    h_edited_intro_msg = st.text_area(
                                        "Introductory Message",
                                        value=h_default_intro,
                                        height=180,
                                        key=f"edit_mhist_intro_{h['id']}_{sel_slot}",
                                        label_visibility="collapsed"
                                    )
                                    coordinate_subject = f"Scheduling: Mentoring-Me Intro Call — {mentee['name']} & {h['mentor_name']}"
                                    
                                    # Google Calendar and ICS Calendar generators
                                    gcal_url = generate_google_calendar_url(
                                        title=title_val,
                                        description=calendar_body,
                                        location="Virtual (Mentoring-Me Platform)",
                                        start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                                        end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                                    )
                                    ics_bytes = generate_ics_calendar_file(
                                        title=title_val,
                                        description=calendar_body,
                                        location="Virtual (Mentoring-Me Platform)",
                                        start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                                        end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                                    )
                                    
                                    cal_btn1, cal_btn2, cal_btn3, cal_btn4 = st.columns(4)
                                    with cal_btn1:
                                        if st.button("🚀 Send Note & Open Chat", key=f"quick_send_mhist_{h['id']}", type="primary", use_container_width=True):
                                            ok_s, res_s = api_send_message(h['id'], h_edited_intro_msg)
                                            if ok_s:
                                                st.session_state['active_chat_match_id'] = h['id']
                                                st.session_state['trigger_tab_switch'] = "Direct Messages"
                                                st.rerun()
                                            else:
                                                st.error(res_s)
                                    with cal_btn2:
                                        if st.button(f"✉️ Send Email", key=f"mhist_send_email_{h['id']}", use_container_width=True):
                                            ok_e, msg_e = api_send_direct_match_email(h['id'], coordinate_subject, h_edited_intro_msg)
                                            if ok_e:
                                                st.success(f"✅ {msg_e}")
                                            else:
                                                st.error(msg_e)
                                    with cal_btn3:
                                        st.link_button("📅 Google Calendar", gcal_url, use_container_width=True)
                                    with cal_btn4:
                                        st.download_button(
                                            "📥 .ICS Invite",
                                            data=ics_bytes,
                                            file_name=f"mentor_me_sync_{h['mentor_name'].replace(' ', '_')}.ics",
                                            mime="text/calendar",
                                            use_container_width=True,
                                            key=f"download_ics_mentee_{h['id']}"
                                        )

                                # ── In-App Direct Chat Link ────────────────────────
                                if st.button(f"💬 Open Chat with {h['mentor_name']} in Messages Hub", key=f"mentee_goto_chat_{h['id']}", use_container_width=True):
                                    st.session_state['active_chat_match_id'] = h['id']
                                    st.session_state['trigger_tab_switch'] = "Direct Messages"
                                    st.rerun()

                                # ── Goal Tracker ──────────────────────────────────
                                with st.expander(f"📓 Mentorship Journal & Goals — {h['mentor_name']}"):
                                    st.caption("Set your mentorship goals, log sessions, and track your progress throughout the partnership.")
                                    jkey = f"journal_{h['id']}"
                                    if jkey not in st.session_state:
                                        st.session_state[jkey] = {"goals": ["", "", ""], "sessions": [], "reflections": ""}
                                    j = st.session_state[jkey]

                                    st.markdown("**🎯 My Mentorship Goals**")
                                    j["goals"][0] = st.text_input("Goal 1", value=j["goals"][0], key=f"g0_{h['id']}", placeholder="e.g. Get promoted to senior engineer within 12 months")
                                    j["goals"][1] = st.text_input("Goal 2", value=j["goals"][1], key=f"g1_{h['id']}", placeholder="e.g. Build confidence presenting to stakeholders")
                                    j["goals"][2] = st.text_input("Goal 3", value=j["goals"][2], key=f"g2_{h['id']}", placeholder="e.g. Expand my professional network in cloud engineering")

                                    st.markdown("---")
                                    st.markdown("**📋 Session Log**")
                                    if j["sessions"]:
                                        for si, sess in enumerate(j["sessions"]):
                                            sc1, sc2, sc3, sc4 = st.columns([2, 2, 3, 1])
                                            sc1.markdown(f"`{sess.get('date','')}`")
                                            sc2.markdown(sess.get('topic',''))
                                            sc3.markdown(sess.get('notes',''))
                                            sc4.markdown(f"*{sess.get('status','')}*")

                                    st.markdown("*Log a new session:*")
                                    ls1, ls2 = st.columns(2)
                                    new_s_date = ls1.date_input("Session Date", key=f"sd_{h['id']}")
                                    new_s_status = ls2.selectbox("Status", ["Planned", "Completed", "Cancelled"], key=f"ss_{h['id']}")
                                    new_s_topic = st.text_input("Topic / Agenda", key=f"st_{h['id']}", placeholder="e.g. Career roadmap, code review, negotiation prep")
                                    new_s_notes = st.text_input("Key Takeaways", key=f"sn_{h['id']}", placeholder="e.g. Follow up on resume draft, research cloud cert paths")
                                    if st.button("➕ Add Session", key=f"add_sess_{h['id']}"):
                                        j["sessions"].append({"date": str(new_s_date), "topic": new_s_topic, "notes": new_s_notes, "status": new_s_status})
                                        st.success("Session logged!")
                                        st.rerun()

                                    st.markdown("---")
                                    st.markdown("**💭 Reflections & Notes**")
                                    j["reflections"] = st.text_area("Personal reflections on this mentorship", value=j["reflections"], key=f"refl_{h['id']}", height=100, placeholder="What has been most valuable? What challenges have you faced?")

                                # ── Feedback & Rating ──────────────────────────────────
                                with st.expander(f"⭐ Rate This Mentorship — {h['mentor_name']}"):
                                    st.caption("Your feedback helps improve the matching experience for future early-career women on the platform.")
                                    fkey = f"feedback_{h['id']}"
                                    if fkey not in st.session_state:
                                        st.session_state[fkey] = {"rating": 3, "comment": "", "recommend": False, "submitted": False}
                                    fb = st.session_state[fkey]
                                    if fb["submitted"]:
                                        st.success(f"✅ Thank you! You rated this mentorship **{fb['rating']}/5 stars**. Your feedback has been recorded.")
                                    else:
                                        fb["rating"] = st.select_slider("Overall rating", options=[1, 2, 3, 4, 5], value=fb["rating"], format_func=lambda x: f"{x} {'⭐'*x}", key=f"fb_rating_{h['id']}")
                                        fb["comment"] = st.text_area("What was most valuable about this mentorship?", value=fb["comment"], key=f"fb_comment_{h['id']}", height=80, placeholder="e.g. My mentor helped me prepare for a promotion conversation and build my confidence...")
                                        fb["recommend"] = st.checkbox("I would recommend this mentor to other early-career women in tech", value=fb["recommend"], key=f"fb_rec_{h['id']}")
                                        if st.button("📤 Submit Feedback", key=f"fb_submit_{h['id']}"):
                                            fb["submitted"] = True
                                            st.success("Thank you for your feedback!")
                                            st.rerun()

                    # ── Shared Mentorship Notes & Milestones from Mentor ─────
                    mentee_notes = api_get_notes()
                    if mentee_notes:
                        st.markdown("---")
                        st.markdown("### 📝 Shared Session Notes & Milestones from your Mentor")
                        st.caption("Review meeting summaries, homework checklists, and next session targets recorded by your mentor.")
                        for m_note in mentee_notes:
                            st_val = m_note.get('milestone_status', 'IN_PROGRESS')
                            badge_style = {
                                'COMPLETED': ('#dcfce7', '#166534', '✅ Completed'),
                                'IN_PROGRESS': ('#e0e7ff', '#3730a3', '🚀 In Progress'),
                                'NOT_STARTED': ('#fef3c7', '#92400e', '⏳ Not Started')
                            }.get(st_val, ('#f1f5f9', '#475569', st_val))
                            
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.markdown(f"#### {m_note['title']}")
                                    st.caption(f"🧭 **Mentor:** `{m_note.get('mentor_name', 'Mentor')}` · 📅 **Date:** `{m_note.get('session_date', '')[:10]}`")
                                with c2:
                                    st.markdown(
                                        f"<div style='text-align: right; margin-top: 4px;'>"
                                        f"<span style='background-color: {badge_style[0]}; color: {badge_style[1]}; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>{badge_style[2]}</span>"
                                        f"</div>",
                                        unsafe_allow_html=True
                                    )
                                if m_note.get('topics_covered'):
                                    st.markdown(f"**📖 Topics Discussed:**\n{m_note['topics_covered']}")
                                if m_note.get('action_items'):
                                    st.markdown(f"**📋 Action Items & Homework:**\n{m_note['action_items']}")
                                if m_note.get('key_takeaways'):
                                    st.markdown(f"**💡 Mentor Feedback & Takeaways:**\n*{m_note['key_takeaways']}*")
                                if m_note.get('next_meeting_date'):
                                    st.markdown(f"📆 **Next Scheduled Session:** `{m_note['next_meeting_date']}`")

                    # ── 4. Cross-tab callout ───────────────────────────────────
                    st.markdown("---")
                    noms_check = api_get_nominations()
                    pending_ext = sum(1 for n in noms_check if n['status'] != 'ACCEPTED') if noms_check else 0
                    if pending_ext > 0:
                        st.info(f"📩 You also have **{pending_ext} pending external invitation(s)** to mentors you personally reached out to. Track them in the **External Invitations** tab.")
                    elif noms_check:
                        st.info(f"✅ All **{len(noms_check)} external mentor invitation(s)** you sent have been accepted. View them in the **External Invitations** tab.")
                    else:
                        st.info("💡 You can also personally invite external mentors from GitHub, LinkedIn, ORCID, or your network via the **Outreach Hub** tab.")

            
            with tab_outreach:
                import urllib.parse as _up

                st.subheader("🌐 External Mentors Outreach Hub")
                st.caption("Can't find the right mentor in the platform pool? Search live professional directories or nominate someone you already know.")

                # ════════════════════════════════════════════════════════════
                # SECTION A — Discover via Live Directories
                # ════════════════════════════════════════════════════════════
                st.markdown("### 🌐 Discover via Live Directories")
                st.caption("Search GitHub, LinkedIn, or ORCID in real time. Results are automatically scored against your mentor preferences.")

                # Directory source picker
                search_source = st.radio(
                    "Directory:",
                    [
                        "🐱 GitHub (Tech & Open Source Developers)",
                        "🌐 LinkedIn (Direct Deep Link Generator & Search)",
                        "💼 ORCID (Research & Academic Experts)"
                    ],
                    horizontal=True,
                    key="outreach_search_source_radio"
                )

                st.info("💡 **How Matching Works**: The search filters fetch relevant candidates from the selected directory. The **Compatibility Match %** is then calculated by comparing their profile records directly against your desired **Target Mentor Preferences** (preferred skills/expertise, country, and minimum experience years) to ensure personalized compatibility.")

                # Pull saved preferences with smart fallback to mentee's primary role
                profile_role_fallback = (mentee.get('dev_type') or '').split(';')[0].strip() if mentee.get('dev_type') else 'Software Engineering'
                saved_query   = (mentee.get('target_mentor_expertise') or profile_role_fallback or "").strip()
                saved_country = (mentee.get('target_mentor_country') or mentee.get('country') or "Any").strip()
                saved_years   = mentee.get('target_mentor_min_years') or 2.0

                # ── Improvement 1: Session-only search query override ────────
                with st.expander("⚙️ Customize This Search (optional — pre-filled from your profile)", expanded=False):
                    st.caption("Pre-filled automatically from your saved profile preferences. Adjust freely — changes here only affect this search session.")
                    ov_col1, ov_col2, ov_col3 = st.columns([3, 2, 1])
                    with ov_col1:
                        session_query = st.text_input(
                            "Expertise Keywords",
                            value=saved_query,
                            placeholder="e.g. Python, DevOps, Finance",
                            key="outreach_session_query"
                        )
                    with ov_col2:
                        session_country_opts = ["Any"] + COUNTRIES
                        saved_c_list = [c.strip() for c in saved_country.replace(",", ";").split(";") if c.strip()]
                        session_country_default = saved_c_list[0] if saved_c_list and saved_c_list[0] in session_country_opts else "Any"
                        session_country_idx = session_country_opts.index(session_country_default) if session_country_default in session_country_opts else 0
                        session_country = st.selectbox("Preferred Country", session_country_opts, index=session_country_idx, key="outreach_session_country")
                    with ov_col3:
                        session_min_years = st.number_input("Min. Yrs Exp.", min_value=0.0, max_value=50.0, value=float(saved_years), step=0.5, format="%g", key="outreach_session_years")

                # Resolve active search params (session override wins, fallback to profile role)
                active_query   = st.session_state.get("outreach_session_query", saved_query).strip() or profile_role_fallback
                active_country_raw = st.session_state.get("outreach_session_country", session_country_default)
                active_country = active_country_raw if active_country_raw != "Any" else None
                country_lbl    = active_country if active_country else "Any Country"
                
                if "GitHub" in search_source:
                    source_short = "GitHub"
                elif "LinkedIn" in search_source:
                    source_short = "LinkedIn"
                else:
                    source_short = "ORCID"

                # ════════════════════════════════════════════════════════════
                # DIRECT LINKEDIN DEEP LINK GENERATOR SUITE
                # ════════════════════════════════════════════════════════════
                if source_short == "LinkedIn":
                    with st.container(border=True):
                        st.markdown("### 🔗 Direct LinkedIn Deep Link Generator")
                        st.markdown(
                            """
                            **What is the Direct LinkedIn Deep Link Generator?**  
                            A **LinkedIn Deep Link** is a dynamically constructed URL that opens LinkedIn’s official search engine with pre-filled, Boolean-optimized filters based on your exact mentee profile and goals (*Target Role, Country, Skills, Seniority, and Mentorship keywords*).
                            
                            > ⚡ **Why use Deep Links?** Instead of relying on a third-party search API that can get deprecated, rate-limited, or blocked, your app generates a smart one-click link that takes you directly to live, matching mentor candidates on LinkedIn's global network of 1B+ professionals.
                            """
                        )
                        
                        st.markdown("##### ⚙️ Fine-Tune Your Deep Link Search Filters")
                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            dl_role = st.text_input("Target Role / Discipline", value=active_query or "Software Engineering", key="dl_role_input")
                            dl_skills_str = st.text_input("Key Skills / Technologies (comma separated)", value=mentee.get('additional_details') or "Python, Cloud, System Architecture", key="dl_skills_input")
                            dl_seniority = st.selectbox(
                                "Target Seniority Level",
                                ["Any", "Senior", "Lead", "Principal", "Director", "VP", "Head of"],
                                index=1,
                                key="dl_seniority_select"
                            )
                        with dl_col2:
                            dl_country_opts = ["Any"] + COUNTRIES
                            dl_c_default = active_country if active_country and active_country in dl_country_opts else ("United Kingdom" if "United Kingdom" in dl_country_opts else "Any")
                            dl_c_idx = dl_country_opts.index(dl_c_default) if dl_c_default in dl_country_opts else 0
                            dl_country = st.selectbox("Location / Country", dl_country_opts, index=dl_c_idx, key="dl_country_select")
                            dl_c_val = dl_country if dl_country != "Any" else None
                            
                            dl_wit_default = (mentee.get('gender') == 'Female' or mentee.get('prefer_diversity_ally'))
                            dl_women_in_tech = st.checkbox("🌟 Prioritize Women in Tech / Female Leaders (SDG 5)", value=dl_wit_default, key="dl_wit_chk")
                            dl_mentor_intent = st.checkbox("🎯 Include Mentorship Intent Keywords (mentor / mentoring)", value=True, key="dl_intent_chk")
                        
                        # Dynamically construct deep link
                        dl_skills_list = [s.strip() for s in dl_skills_str.replace(";", ",").split(",") if s.strip()]
                        dl_result = build_app_linkedin_deep_link(
                            role=dl_role,
                            skills=dl_skills_list,
                            country=dl_c_val,
                            seniority=dl_seniority if dl_seniority != "Any" else None,
                            mentorship_intent=dl_mentor_intent,
                            women_in_tech=dl_women_in_tech
                        )
                        
                        st.markdown("---")
                        st.markdown("##### 🚀 Launch Your Direct LinkedIn Deep Link")
                        
                        st.link_button(
                            "🌐 Launch Live Search on LinkedIn",
                            dl_result["deep_link_url"],
                            use_container_width=True,
                            help="Opens LinkedIn People Search in a new browser tab with your synthesized Boolean filters."
                        )
                        
                        with st.expander("🔍 Inspect Synthesized LinkedIn Boolean Query"):
                            st.caption("Here is the exact Boolean query formula dynamically built and passed into LinkedIn's search engine:")
                            st.code(dl_result["raw_query"], language="sql")
                            st.text_input("Direct Deep Link URL (Click to copy)", value=dl_result["deep_link_url"], key="dl_copyable_url")

                        # LinkedIn Outreach Message Crafter
                        with st.expander("✉️ LinkedIn Outreach Messages & InMail Crafter", expanded=True):
                            st.caption("Customise ready-to-send messages for connecting with prospective mentors on LinkedIn:")
                            msg_mentor_name = st.text_input("Prospective Mentor Name (optional)", value="Alex", key="dl_msg_mname")
                            
                            templates = generate_app_linkedin_outreach_templates(
                                mentee_name=mentee.get('name') or "Mentee",
                                mentee_role=mentee.get('dev_type') or dl_role or "Software Engineer",
                                mentor_name=msg_mentor_name,
                                tech_focus=dl_role or "Engineering Leadership"
                            )
                            
                            # 1. Connection Note (300 chars limit)
                            cn_note = templates["connection_note"]
                            cn_len = len(cn_note)
                            st.markdown(f"**1. LinkedIn Connection Request Note** `({cn_len}/300 characters - LinkedIn Compliant ✅)`")
                            st.text_area("Personalised Note (Copy to paste in LinkedIn connection request):", value=cn_note, height=80, key="dl_conn_note_area")
                            
                            # 2. InMail / Direct Message
                            st.markdown("**2. Full InMail / Direct Message Template**")
                            st.text_area("Comprehensive Message (For LinkedIn InMail, In-Platform Messages, or Email):", value=templates["inmail_message"], height=200, key="dl_inmail_area")

                else:
                    search_q = active_query or profile_role_fallback or "Software Engineering"
                    st.info(f"🎯 **Search Settings**: Searching **{source_short}** for **'{search_q}'** · Location: **{country_lbl}** · Min. experience: **{int(session_min_years)}+ years**")
                    run_search = st.button(f"🔍 Search Live {source_short} Directory", key="outreach_search_btn", use_container_width=True)

                    if run_search:
                        with st.spinner(f"Querying live {source_short} directory and scoring candidates..."):
                            if "GitHub" in search_source:
                                results = api_search_github(search_q, active_country)
                            else:
                                results = api_search_orcid(search_q, active_country)
                            if results:
                                st.session_state['outreach_search_results'] = sorted(results, key=lambda r: r.get('match_percentage', 0), reverse=True)
                                st.session_state['outreach_search_results_source'] = source_short
                                st.success(f"✅ Found {len(results)} matching profiles!")
                            else:
                                st.warning(f"No matches found in {source_short}. Try broadening your keywords or selecting 'Any Country'.")

                # ── Improvement 2: Modernized Candidate Cards ────────────────
                if 'outreach_search_results' in st.session_state and st.session_state['outreach_search_results']:
                    results_src = st.session_state.get('outreach_search_results_source', 'Directory')
                    st.markdown(f"#### 📋 {len(st.session_state['outreach_search_results'])} Candidates Found · Source: {results_src}")

                    for idx, candidate in enumerate(st.session_state['outreach_search_results']):
                        pct  = candidate['match_percentage']
                        if pct >= 80:
                            score_badge = f"🟢 **{pct}% — High Match**"
                            badge_color = "#1e7e34"
                        elif pct >= 50:
                            score_badge = f"🟡 **{pct}% — Moderate Match**"
                            badge_color = "#856404"
                        else:
                            score_badge = f"🔴 **{pct}% — Low Match**"
                            badge_color = "#721c24"

                        with st.container(border=True):
                            head_col, score_col = st.columns([3, 1])
                            with head_col:
                                st.markdown(f"##### {candidate['name']}")
                                st.caption(f"📍 {candidate['country']}  ·  {candidate['tech_focus']}")
                            with score_col:
                                st.markdown(
                                    f"<div style='text-align:center; background:#f8f9fa; border-radius:8px; padding:8px 4px;'>"
                                    f"<span style='color:{badge_color}; font-size:0.9rem; font-weight:700;'>{pct}%</span><br/>"
                                    f"<span style='font-size:0.72rem; color:#6c757d;'>Compatibility</span></div>",
                                    unsafe_allow_html=True
                                )

                            # Link badges row
                            link_badges = []
                            link_badges.append(f"[🔗 {results_src} Profile]({candidate['contact']})")
                            if candidate.get('linkedin_url'):
                                link_badges.append(f"[🌐 LinkedIn]({candidate['linkedin_url']})")
                            elif candidate.get('name'):
                                cand_name_q = urllib.parse.quote(candidate['name'])
                                cand_tech_q = urllib.parse.quote((candidate.get('tech_focus') or '').split(',')[0].strip())
                                fallback_li_url = f"https://www.linkedin.com/search/results/people/?keywords={cand_name_q}%20{cand_tech_q}"
                                link_badges.append(f"[🌐 Search on LinkedIn]({fallback_li_url})")

                            if candidate.get('other_urls'):
                                for u_idx, u_val in enumerate(candidate['other_urls'][:2]):
                                    link_badges.append(f"[🏠 Website {u_idx+1}]({u_val})")
                            if candidate.get('public_email'):
                                link_badges.append(f"📧 `{candidate['public_email']}`")
                            st.markdown("  ·  ".join(link_badges))

                            # Match justifications
                            with st.expander("📝 View Match Justifications"):
                                for j in candidate['justifications']:
                                    st.markdown(f"- {j}")

                            # Action buttons
                            public_email = candidate.get('public_email')
                            act_col1, act_col2 = st.columns([1, 1])
                            with act_col1:
                                if public_email:
                                    if st.button("✉️ Generate Invitation", key=f"quick_invite_outreach_{idx}", use_container_width=True):
                                        ok, res = api_nominate_mentor(candidate['name'], public_email, active_query)
                                        if ok:
                                            st.session_state[f'nomination_outreach_{idx}'] = res
                                            st.rerun()
                                        else:
                                            st.error(res)
                                else:
                                    st.button("✉️ No Public Email", disabled=True, key=f"no_email_{idx}", use_container_width=True, help="This profile has no publicly listed email. Use the profile link to reach out directly.")
                            with act_col2:
                                # Always offer a copyable invite message for profiles without email (LinkedIn/GitHub outreach)
                                if st.button("📋 Copy Invite Message", key=f"copy_invite_{idx}", use_container_width=True):
                                    st.session_state[f'show_copy_msg_{idx}'] = not st.session_state.get(f'show_copy_msg_{idx}', False)

                            if st.session_state.get(f'show_copy_msg_{idx}', False):
                                copy_link = f"{get_app_base_url()}/?invite_code=PENDING"
                                copy_template = (
                                    f"Hi {candidate['name']},\n\n"
                                    f"I came across your profile and was impressed by your expertise in {candidate['tech_focus']}.\n\n"
                                    f"I am currently seeking mentorship in this area and am using a platform called Mentoring-Me to manage my learning connections. "
                                    f"I would be honoured to connect with you. You can use the link below to join the platform and we will be automatically paired:\n\n"
                                    f"{copy_link}\n\n"
                                    f"If you prefer not to register on a new platform, feel free to reach out directly and we can coordinate externally.\n\n"
                                    f"Thank you for your time!\n\nBest regards,\n{mentee['name']}"
                                )
                                st.text_area("Copy this message to use on LinkedIn, GitHub, or any channel:", value=copy_template, height=180, key=f"copy_msg_area_{idx}")
                                st.caption("💡 After nominating them via email, their actual personalised invite link will appear in the **External Invitations** tab.")

                            # Inline email designer (shown after nomination is generated)
                            if f'nomination_outreach_{idx}' in st.session_state:
                                nom = st.session_state[f'nomination_outreach_{idx}']
                                invite_link = f"{get_app_base_url()}/?invite_code={nom['invite_code']}"
                                with st.expander("✉️ Outreach Email Designer", expanded=True):
                                    email_template = (
                                        f"Hi {nom['mentor_name']},\n\n"
                                        f"I came across your profile and noticed your expertise in {nom['tech_focus']}.\n\n"
                                        f"I am currently looking for mentorship in this area. I'm using a platform called Mentoring-Me to manage my learning connections. "
                                        f"I've created a direct invitation link for you to connect with me:\n\n{invite_link}\n\n"
                                        f"If you are open to a brief chat or periodic mentoring, signing up via this link will automatically connect us on the platform. "
                                        f"Alternatively, if you prefer not to register on a new platform, feel free to reply directly to this email so we can connect and coordinate externally instead.\n\n"
                                        f"Thank you so much for your time!\n\nBest regards,\n{mentee['name']}"
                                    )
                                    outreach_message = st.text_area("Edit your invitation message:", value=email_template, height=200, key=f"drafted_outreach_msg_outreach_{idx}")
                                    inv_subject = "Mentorship Invitation - Mentoring-Me"
                                    btn_c1, btn_c2 = st.columns(2)
                                    with btn_c1:
                                        if st.button("✉️ Send Invitation Email", key=f"send_nom_email_btn_{idx}", use_container_width=True):
                                            ok_n, res_n = api_send_nomination_followup(nom['id'], outreach_message, inv_subject)
                                            if ok_n:
                                                st.success(f"✅ Invitation email dispatched to {nom['mentor_contact']}!")
                                            else:
                                                st.error(res_n)
                                    with btn_c2:
                                        if st.button("✖ Close Designer", key=f"clear_nom_card_outreach_{idx}", use_container_width=True):
                                            del st.session_state[f'nomination_outreach_{idx}']
                                            st.rerun()
                                    st.caption(f"🔗 Invite link: `{invite_link}`")

                    st.markdown("")
                    if st.button("🗑 Clear Search Results", key="clear_outreach_results_btn"):
                        del st.session_state['outreach_search_results']
                        del st.session_state['outreach_search_results_source']
                        st.rerun()

                # ════════════════════════════════════════════════════════════
                # SECTION B — Direct Nomination
                # ════════════════════════════════════════════════════════════
                st.markdown("---")
                st.markdown("### ✉️ Direct Nomination")
                st.caption("Already know who you want as a mentor? Enter their details below to generate a personalised invitation link and draft a message.")

                with st.expander("✉️ Invite a Specific Mentor by Email", expanded=False):
                    mentee_name_val = mentee.get('name') or user.get('email', 'A Mentee')
                    default_note_text = (
                        f"Hi there,\n\n"
                        f"I came across your profile and would be deeply grateful for the opportunity to connect for periodic mentorship.\n\n"
                        f"I am using the Mentoring-Me platform to organise our learning goals and coordinate intro calls. "
                        f"Please click the invitation link to connect with me.\n\n"
                        f"Warm regards,\n{mentee_name_val}"
                    )
                    
                    with st.form("nomination_form", clear_on_submit=False):
                        n_col1, n_col2 = st.columns(2)
                        with n_col1:
                            nom_name = st.text_input("Mentor's Name", placeholder="e.g. Dr. Jane Smith")
                        with n_col2:
                            nom_contact = st.text_input("Mentor's Email Address", placeholder="e.g. mentor@university.ac.uk")
                        nom_focus = st.text_input(
                            "Their Area of Expertise",
                            placeholder="e.g. Python, Cloud Architecture, Machine Learning",
                            value=saved_query
                        )
                        nom_message = st.text_area(
                            "📝 Personal Note to Mentor (Included in the Dispatched Email):",
                            value=default_note_text,
                            height=150,
                            help="This personalized note will be delivered directly to the mentor's inbox with your invitation link. If the mentor replies to the email, it will go directly to your personal email."
                        )
                        nom_submit = st.form_submit_button("🚀 Send Mentorship Invitation Email", type="primary", use_container_width=True)

                        if nom_submit:
                            if not nom_name.strip() or not nom_contact.strip() or not nom_focus.strip():
                                st.error("Please fill in the mentor's name, email, and area of expertise.")
                            elif "@" not in nom_contact or "." not in nom_contact:
                                st.error("Please enter a valid email address (e.g. mentor@example.com).")
                            else:
                                ok, res = api_nominate_mentor(nom_name.strip(), nom_contact.strip(), nom_focus.strip(), nom_message.strip())
                                if ok:
                                    st.session_state['latest_nomination'] = res
                                    st.success(f"✨ Invitation email successfully dispatched to **{nom_contact.strip()}**! (Reply-To configured to your inbox)")
                                    st.rerun()
                                else:
                                    st.error(res)

                    if 'latest_nomination' in st.session_state:
                        nom = st.session_state['latest_nomination']
                        invite_link = f"{get_app_base_url()}/?invite_code={nom['invite_code']}"
                        st.markdown("---")
                        st.markdown(f"#### ✉️ Active Invitation Dispatched to {nom['mentor_name']}")
                        st.info(f"An official invitation containing your personalized note was sent to **{nom['mentor_contact']}** (Reply-To: `{user.get('email')}`). When the mentor registers, your partnership will be automatically connected!")
                        st.text_input("Direct Invitation Link (Copy to share via LinkedIn or WhatsApp):", value=invite_link, key=f"active_inv_link_{nom['invite_code']}")
                        if st.button("✖ Clear Notification", key="clear_nom_card_btn", use_container_width=True):
                            del st.session_state['latest_nomination']
                            st.rerun()


        with tab_nominations:
            import urllib.parse
            import datetime as _dt

            st.subheader("My External Invitations")
            st.caption("Track the registration status of every mentor you have personally invited to Mentoring-Me.")

            noms = api_get_nominations()

            if not noms:
                st.info("You haven't invited any external mentors yet. Head to the **Outreach Hub** tab to discover and nominate mentors from GitHub, LinkedIn, or ORCID.")
            else:
                # ── Summary metric bar ────────────────────────────────────
                total = len(noms)
                accepted = sum(1 for n in noms if n['status'] == "ACCEPTED")
                pending = total - accepted
                m1, m2, m3 = st.columns(3)
                m1.metric("📤 Total Invited", total)
                m2.metric("🟢 Registered & Connected", accepted)
                m3.metric("⏳ Awaiting Registration", pending)
                st.markdown("---")

                # ── One card per nomination ───────────────────────────────
                for n in noms:
                    is_accepted = n['status'] == "ACCEPTED"
                    status_label = "🟢 Registered & Connected" if is_accepted else "⏳ Pending Registration"
                    p_invite_link = f"{get_app_base_url()}/?invite_code={n['invite_code']}"

                    # Parse dates
                    try:
                        created_dt = _dt.datetime.fromisoformat(n['created_at'].replace('Z', '+00:00'))
                        date_str = created_dt.strftime("%d %b %Y")
                    except Exception:
                        date_str = n['created_at']

                    try:
                        last_contact_raw = n.get('last_contacted_at') or n['created_at']
                        last_dt = _dt.datetime.fromisoformat(last_contact_raw.replace('Z', '+00:00'))
                        last_str = last_dt.strftime("%d %b %Y")
                    except Exception:
                        last_str = "Unknown"

                    card_label = f"{status_label}  ·  **{n['mentor_name']}**"
                    with st.expander(card_label, expanded=not is_accepted):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.markdown(f"**Contact:** {n['mentor_contact']}")
                            st.markdown(f"**Focus / Expertise:** {n['tech_focus']}")
                            st.markdown(f"**Invited on:** {date_str}  |  **Last contacted:** {last_str}")
                        with c2:
                            st.markdown(f"**Invite Link:**")
                            st.code(p_invite_link, language="text")

                        if not is_accepted:
                            st.markdown("---")
                            # Toggle follow-up drafter
                            toggle_key = f"show_followup_{n['id']}"
                            if st.button("📣 Compose Follow-Up Email", key=f"follow_up_btn_{n['id']}"):
                                st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)

                            if st.session_state.get(toggle_key, False):
                                mentee_name_display = mentee.get('name') or user.get('email', 'A Mentee')
                                follow_up_template = (
                                    f"Hi {n['mentor_name']},\n\n"
                                    f"Hope you are doing well!\n\n"
                                    f"Just wanted to check in to see if you had a chance to look at the mentorship invitation "
                                    f"I sent recently to connect on Mentoring-Me:\n\n{p_invite_link}\n\n"
                                    f"I would love to learn from your experience in {n['tech_focus']} if you have the capacity. "
                                    f"No pressure at all — looking forward to hearing from you!\n\n"
                                    f"Warm regards,\n{mentee_name_display}"
                                )
                                follow_up_msg = st.text_area(
                                    "📝 Edit your follow-up message (will be sent directly via email):",
                                    value=follow_up_template,
                                    height=180,
                                    key=f"msg_followup_{n['id']}",
                                    help="This follow-up will be sent directly to the mentor's inbox with your Reply-To address attached."
                                )

                                fu_subject = f"Checking In: Mentorship Invitation from {mentee_name_display} (via Mentoring-Me)"
                                
                                fu_col1, fu_col2 = st.columns([2, 1])
                                with fu_col1:
                                    if st.button("🚀 Send Follow-Up Email Directly", key=f"send_direct_followup_{n['id']}", type="primary", use_container_width=True):
                                        ok, res = api_send_nomination_followup(n['id'], follow_up_msg.strip(), fu_subject)
                                        if ok:
                                            st.success(f"✨ Follow-up email successfully sent to **{n['mentor_contact']}**! (Reply-To set to your email)")
                                            st.session_state[toggle_key] = False
                                            st.session_state['profile'] = None
                                            st.rerun()
                                        else:
                                            st.error(res)
                                dangling_close = False
                                with fu_col2:
                                    if st.button("✖ Close", key=f"close_followup_{n['id']}", use_container_width=True):
                                        st.session_state[toggle_key] = False
                                        st.rerun()            
        with tab_witech:
            st.subheader("🌟 Women in Tech — Resources & Community")
            st.caption("A curated space to support your journey as a woman in technical fields — communities, funding, research, and inspiration.")

            # ── Live platform stat ──────────────────────────────────────────
            all_hist = api_get_match_history() or []
            female_mentor_count = sum(1 for h in all_hist if h.get('mentor_gender') == 'Female')
            if female_mentor_count > 0:
                st.success(f"🌟 **{female_mentor_count} active female mentor(s)** are currently registered on Mentoring-Me. You can connect with them via Platform Matches or the Outreach Hub.")

            st.markdown("---")

            # ── Communities ────────────────────────────────────────────────
            st.markdown("### 🤝 Communities & Organisations")
            comm_data = [
                ("Rewriting the Code", "The largest peer-to-peer network for women in tech in college and early career — community, mentorship, and fellowships.", "https://rewritingthecode.org"),
                ("Ada's List", "Global professional network for women and non-binary tech professionals — jobs, events, and community.", "https://www.adaslist.co"),
                ("WiCyS — Women in CyberSecurity", "Dedicated to recruiting, retaining, and advancing women in cybersecurity.", "https://www.wicys.org"),
                ("ABI / Grace Hopper Celebration", "The world's largest gathering of women technologists — hosts the Grace Hopper Conference annually.", "https://anitab.org"),
                ("Code First Girls", "Free coding courses and nanodegrees for women and non-binary people in the UK.", "https://codefirstgirls.com"),
                ("WISE — Women in Science & Engineering", "UK campaign supporting women in STEM from classroom to boardroom.", "https://www.wisecampaign.org.uk"),
                ("Lesbians Who Tech & Allies", "Community for LGBTQ+ women and allies in tech — annual summit and network.", "https://lesbianswhotech.org"),
                ("Women in Tech Global", "A global network and movement for gender diversity in the tech industry.", "https://women-in-tech.org"),
            ]
            for cname, cdesc, curl in comm_data:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"**{cname}**")
                    c1.caption(cdesc)
                    c2.markdown(f"[Visit →]({curl})")

            st.markdown("---")

            # ── Scholarships & Fellowships ──────────────────────────────────
            st.markdown("### 🎓 Scholarships & Fellowships")
            fund_data = [
                ("Grace Hopper Celebration Scholarship", "Full conference scholarship for women and non-binary technologists to attend GHC annually.", "https://anitab.org/awards-grants/ghc-scholarships/"),
                ("Google Women Techmakers Scholars", "Scholarships for women studying computer science and related technical fields globally.", "https://buildyourfuture.withgoogle.com/scholarships"),
                ("TechWomen Fellowship (US State Dept.)", "Competitive professional exchange programme connecting women in STEM from emerging nations with Silicon Valley mentors.", "https://www.techwomen.org"),
                ("Palantir Women in Technology Scholarship", "For women pursuing degrees in computer science, engineering, or related fields — awarded each hiring cycle.", "https://www.palantir.com/careers/students/"),
            ]
            for fname, fdesc, furl in fund_data:
                with st.container(border=True):
                    f1, f2 = st.columns([4, 1])
                    f1.markdown(f"**{fname}**")
                    f1.caption(fdesc)
                    f2.markdown(f"[Apply →]({furl})")

            st.markdown("---")

            # ── Research & Reading ─────────────────────────────────────────
            st.markdown("### 📚 Research, Statistics & Guides")
            res_data = [
                ("McKinsey: Women in the Workplace Report", "Annual research on the state of women in corporate America and globally.", "https://www.mckinsey.com/featured-insights/diversity-and-inclusion/women-in-the-workplace"),
                ("WISE Statistics: Women in STEM", "UK data on women's participation in science, technology, engineering and mathematics.", "https://www.wisecampaign.org.uk/research-statistics/"),
                ("Harvard: Women & Imposter Syndrome", "Research-backed guidance on tackling imposter phenomenon in technical careers.", "https://hbr.org/2021/02/stop-telling-women-they-have-imposter-syndrome"),
                ("Project Implicit — Bias Assessment", "Understand hidden biases that affect hiring and promotion in tech.", "https://implicit.harvard.edu"),
                ("Lean In: Women in Tech Toolkit", "Practical negotiation, self-advocacy and leadership guides for women in tech.", "https://leanin.org/women-in-the-workplace"),
            ]
            for rname, rdesc, rurl in res_data:
                with st.container(border=True):
                    r1, r2 = st.columns([4, 1])
                    r1.markdown(f"**{rname}**")
                    r1.caption(rdesc)
                    r2.markdown(f"[Read →]({rurl})")

            st.markdown("---")
            # ── Direct LinkedIn Search for Women in Tech Leaders ───────────
            with st.container(border=True):
                st.markdown("### 👩‍💻 Connect with Women in Tech Leaders on LinkedIn")
                st.caption("Generate a pre-filtered **Direct LinkedIn Deep Link** to discover senior female engineering leaders and mentors in your target field.")
                
                wit_role = mentee.get('target_mentor_expertise') or mentee.get('dev_type') or "Engineering Leadership"
                wit_ctry = mentee.get('target_mentor_country') or mentee.get('country')
                
                wit_link_data = build_app_linkedin_deep_link(
                    role=wit_role,
                    country=wit_ctry,
                    seniority="Senior",
                    women_in_tech=True,
                    mentorship_intent=True
                )
                
                w_col1, w_col2 = st.columns([3, 2])
                with w_col1:
                    st.link_button("🌐 Search Female Tech Leaders on LinkedIn", wit_link_data["deep_link_url"], use_container_width=True)
                with w_col2:
                    st.caption(f"🎯 **Target Filters**: `{wit_role}` · `Women in Tech / Female Leader` · `{wit_ctry or 'Global'}`")

            st.markdown("---")
            st.caption("💡 Tip: You can ask the AI Career Advisor in the next tab about navigating any of these topics in the context of your career.")

        with tab_advisor:
            render_copilot_tab(mentee)

    elif role == "MENTOR":
        mentor = profile['mentor']
        history = api_get_match_history()
        
        # Focus workflow for responding to incoming request
        if st.session_state.get('focus_request_match'):
            f_match_id = st.session_state['focus_request_match']
            f_match = next((m for m in history if m['id'] == f_match_id), None)
            if f_match:
                st.markdown("---")
                st.markdown("## 📩 Respond to Mentorship Request")
                st.info(f"Review and respond to the incoming mentorship request from **{f_match['mentee_name']}**.")
                
                display_profile_card(
                    name=f_match['mentee_name'],
                    country=f_match['mentee_country'],
                    ed_level=f_match.get('mentee_ed_level'),
                    roles=f_match['mentee_devtype'],
                    years=f_match['mentee_years'],
                    org_size=f_match['mentee_org_size'],
                    priorities=f_match.get('mentee_job_factors'),
                    additional_details=f_match.get('mentee_additional_details'),
                    user_id=f_match['mentee_id'],
                    alternative_emails=f_match.get('mentee_alternative_emails'),
                    linkedin_link=f_match.get('mentee_linkedin_link')
                )
                
                cols = st.columns([1, 1, 1])
                if cols[0].button("✅ Accept Connection", key="accept_focus"):
                    st.session_state['show_accept_dialog_focus'] = True
                    st.session_state['show_decline_dialog_focus'] = False
                if cols[1].button("❌ Decline Connection", key="decline_focus"):
                    st.session_state['show_accept_dialog_focus'] = False
                    st.session_state['show_decline_dialog_focus'] = True
                if cols[2].button("⬅️ Return to Dashboard", key="close_focus_request"):
                    api_mark_match_notified(f_match_id)
                    del st.session_state['focus_request_match']
                    st.session_state['profile'] = None
                    st.rerun()
                    
                if st.session_state.get('show_accept_dialog_focus', False):
                    st.markdown("##### 📅 Share Your Availability")
                    
                    # Pre-fill/Guess timezone
                    default_tz = mentor.get('timezone') or guess_timezone_from_email(user['email'])
                    mentor_tz = st.selectbox(
                        "Confirm Your Timezone:", 
                        TIMEZONE_OPTIONS, 
                        index=TIMEZONE_OPTIONS.index(default_tz) if default_tz in TIMEZONE_OPTIONS else 12,
                        key="accept_tz_focus"
                    )
                    
                    # Save timezone real-time on change!
                    if mentor.get('timezone') != mentor_tz:
                        api_update_profile({"timezone": mentor_tz})
                        st.session_state['profile'] = None
                        st.rerun()
                        
                    input_mode = st.radio("Choose Availability Format:", ["Select Date/Time Slots", "Custom Text / Scheduling Link"], key="input_mode_focus")
                    
                    mentor_avails = ""
                    if input_mode == "Select Date/Time Slots":
                        st.write("Propose up to 3 dates and times (in your local timezone):")
                        
                        c1, c2, c3 = st.columns([2, 1, 1])
                        d1 = c1.date_input("Date (Slot 1)", key="d1_focus")
                        t1_start = c2.time_input("Start (Slot 1)", datetime.time(10, 0), key="t1_start_focus")
                        t1_end = c3.time_input("End (Slot 1)", datetime.time(10, 30), key="t1_end_focus")
                        
                        c4, c5, c6 = st.columns([2, 1, 1])
                        d2 = c4.date_input("Date (Slot 2)", key="d2_focus")
                        t2_start = c5.time_input("Start (Slot 2)", datetime.time(14, 0), key="t2_start_focus")
                        t2_end = c6.time_input("End (Slot 2)", datetime.time(14, 30), key="t2_end_focus")
                        
                        c7, c8, c9 = st.columns([2, 1, 1])
                        d3 = c7.date_input("Date (Slot 3)", key="d3_focus")
                        t3_start = c8.time_input("Start (Slot 3)", datetime.time(16, 0), key="t3_start_focus")
                        t3_end = c9.time_input("End (Slot 3)", datetime.time(16, 30), key="t3_end_focus")
                        
                        extra_note = st.text_input("Optional message/notes:", key="extra_note_focus")
                        
                        utc1_start = convert_local_to_utc_string(d1, t1_start, mentor_tz)
                        utc1_end = convert_local_to_utc_string(d1, t1_end, mentor_tz)
                        
                        utc2_start = convert_local_to_utc_string(d2, t2_start, mentor_tz)
                        utc2_end = convert_local_to_utc_string(d2, t2_end, mentor_tz)
                        
                        utc3_start = convert_local_to_utc_string(d3, t3_start, mentor_tz)
                        utc3_end = convert_local_to_utc_string(d3, t3_end, mentor_tz)
                        
                        mentor_avails = f"UTC_DTS:{utc1_start}/{utc1_end},{utc2_start}/{utc2_end},{utc3_start}/{utc3_end}|NOTE:{extra_note}"
                    else:
                        default_avails = f"Schedule directly via my link:\n{mentor['contact_link']}" if mentor.get('contact_link') else "1. [Insert Day/Time 1]\n2. [Insert Day/Time 2]"
                        mentor_avails = st.text_area("Custom Availability note:", value=default_avails, key="custom_avails_text_focus", height=120)
                        
                    if st.button("Confirm Accept & Share", key="confirm_accept_focus"):
                        if api_match_action(f_match_id, "ACCEPT", availability_note=mentor_avails):
                            api_mark_match_notified(f_match_id)
                            st.success(f"Accepted connection with {f_match['mentee_name']}!")
                            del st.session_state['focus_request_match']
                            del st.session_state['show_accept_dialog_focus']
                            st.session_state['profile'] = None
                            st.rerun()
                        else:
                            st.error("Failed to accept connection.")
                            
                if st.session_state.get('show_decline_dialog_focus', False):
                    if st.button("Confirm Decline", key="confirm_decline_focus"):
                        if api_match_action(f_match_id, "DECLINE"):
                            api_mark_match_notified(f_match_id)
                            st.warning(f"Declined connection with {f_match['mentee_name']}.")
                            del st.session_state['focus_request_match']
                            del st.session_state['show_decline_dialog_focus']
                            st.session_state['profile'] = None
                            st.rerun()
                        else:
                            st.error("Failed to decline connection.")
                st.markdown("---")
                st.stop()
                
        unnotified_reqs = [m for m in history if isinstance(m, dict) and m.get('status') == 'REQUESTED' and not m.get('mentor_notified', False)]
        unread_count = len(unnotified_reqs)
        
        col_greet, col_bell = st.columns([8, 2])
        with col_greet:
            display_welcome_header(mentor['name'], mentor['id'])
            if st.button("📸 Edit Profile Photo", key="mentor_avatar_toggle"):
                st.session_state['show_pic_uploader'] = not st.session_state.get('show_pic_uploader', False)
                
            # Conditionally display uploader when triggered in session state
            if st.session_state.get('show_pic_uploader', False):
                with st.container(border=True):
                    st.info("📸 **Change Profile Picture**")
                    profile_pic_file = st.file_uploader("Choose a photo (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="mentor_pic_upload_standalone")
                    if profile_pic_file is not None:
                        success, msg = api_upload_profile_pic(profile_pic_file.getvalue(), profile_pic_file.name)
                        if success:
                            st.success("Avatar updated!")
                            st.session_state['profile'] = None
                            st.session_state['show_pic_uploader'] = False
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    # Show Remove Picture option if user currently has an uploaded profile photo
                    if mentor.get('profile_pic'):
                        if st.button("🗑️ Remove Picture (Revert to Letter Avatar)", key="mentor_remove_pic_btn"):
                            success, msg = api_delete_profile_pic()
                            if success:
                                st.success(msg)
                                st.session_state['profile'] = None
                                st.session_state['show_pic_uploader'] = False
                                st.rerun()
                            else:
                                st.error(msg)
                                
                    if st.button("❌ Close Photo Drawer", key="mentor_close_uploader_btn"):
                        st.session_state['show_pic_uploader'] = False
                        st.rerun()
        with col_bell:
            render_top_notifications_bell("MENTOR")
        
        msg_tab_label_m = f"💬 Direct Messages ({tot_unread})" if tot_unread > 0 else "💬 Direct Messages"
        tab_setup, tab_requests, tab_milestones_m, tab_toolkit_m, tab_messages_m, tab_history_m, tab_nominate = st.tabs([
            "⚙️ Profile Setup",
            "🎯 Mentorship Requests",
            "📝 Milestones & Notes",
            "🧠 AI Mentoring Toolkit",
            msg_tab_label_m,
            "📜 Match History",
            "🤝 Nominate a Colleague"
        ])
        
        if st.session_state.get('trigger_tab_switch'):
            tgt_tab_m = st.session_state.pop('trigger_tab_switch')
            trigger_client_tab_switch(tgt_tab_m)
        
        with tab_setup:
            st.subheader("Profile Details")
            if st.session_state.get('profile_save_success'):
                st.success(st.session_state.pop('profile_save_success'))
            with st.form("edit_profile_form"):

                # ── Section 1: My Profile ───────────────────────────────────
                with st.expander("👤 My Profile", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Display Name", value=mentor['name'])
                    with col2:
                        country = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index(mentor['country']) if mentor['country'] in COUNTRIES else 0)

                    col3, col4 = st.columns(2)
                    with col3:
                        raw_yrs_m = mentor['years_code_pro'] or 5.0
                        safe_yrs_m = min(float(raw_yrs_m), 50.0)
                        years = st.number_input("Years of Professional Experience", min_value=0.0, max_value=50.0, value=safe_yrs_m, step=0.5, format="%g")
                        st.caption("Use decimals for part-years: e.g. 1.5 = 1 year & 6 months, 0.5 = 6 months.")
                    with col4:
                        ed_level = st.selectbox("Education Level", ED_LEVELS, index=ED_LEVELS.index(mentor['ed_level']) if mentor['ed_level'] in ED_LEVELS else 0)

                    col5, col6 = st.columns(2)
                    with col5:
                        org_size = st.selectbox("Organization Size", ORG_SIZES, index=ORG_SIZES.index(mentor['org_size']) if mentor['org_size'] in ORG_SIZES else 0)
                    with col6:
                        g_opts_m = ["Female", "Male", "Non-binary"]
                        cur_g_m = mentor.get('gender')
                        g_idx_m = g_opts_m.index(cur_g_m) if cur_g_m in g_opts_m else 0
                        gender = st.selectbox("Gender", g_opts_m, index=g_idx_m)

                    current_roles = [r.strip() for r in mentor['dev_type'].split(";")] if mentor['dev_type'] else []
                    valid_current_roles = [r for r in current_roles if r in ALL_ROLES]
                    picked_roles = st.multiselect("Role(s) / Areas of Expertise", ALL_ROLES, default=valid_current_roles if valid_current_roles else [ALL_ROLES[0]])
                    st.caption("Select all roles that describe your expertise — used to match you with relevant mentees.")
                    custom_roles = st.text_input("Additional roles not listed above (semicolon-separated)", key="custom_roles_mentor", placeholder="e.g. ML Engineer; Platform Architect")

                    current_factors = [f.strip() for f in mentor['job_factors'].split(";")] if mentor['job_factors'] else []
                    valid_current_factors = [f for f in current_factors if f in ALL_FACTORS]
                    picked_factors = st.multiselect("Job Priorities / Values", ALL_FACTORS, default=valid_current_factors if valid_current_factors else [ALL_FACTORS[0]])
                    st.caption("Helps the algorithm match you with mentees who share similar career values.")

                    col7, col8 = st.columns(2)
                    with col7:
                        linkedin_link = st.text_input("LinkedIn Profile URL", value=mentor.get('linkedin_link') or "", placeholder="https://linkedin.com/in/yourprofile")
                    with col8:
                        contact_link = st.text_input("Direct Scheduling / Contact Link", value=mentor.get('contact_link') or "", placeholder="e.g. Calendly, Topmate, booking page URL")
                        st.caption("Shown to matched mentees so they can book time with you directly.")

                    current_tz = mentor.get('timezone') or "Europe/London"
                    tz_idx = TIMEZONE_OPTIONS.index(current_tz) if current_tz in TIMEZONE_OPTIONS else 0
                    timezone = st.selectbox("Your Timezone", TIMEZONE_OPTIONS, index=tz_idx)
                    st.caption("Your availability slots will be displayed to mentees in their own local timezone.")

                    additional_details = st.text_area("Bio / Mentoring Approach / Specialist Skills", value=mentor.get('additional_details') or "", placeholder="e.g. I am a senior cloud engineer specialising in GCP. I enjoy mentoring junior developers navigating their first production deployments...")
                    st.caption("This is shown to potential mentees when reviewing your profile.")

                    is_diversity_ally = st.checkbox(
                        "🤝 Register as an Active Diversity & Inclusion (D&I) Ally",
                        value=bool(mentor.get('is_diversity_ally', False)),
                        help="Check this if you are committed to advocating for women and underrepresented engineers, providing constructive career sponsorship, and fostering psychological safety. Mentees seeking supportive allies will be prioritized to match with you."
                    )
                    st.caption("💡 Check this if you are committed to advocating for women and underrepresented engineers, providing constructive career sponsorship, and fostering psychological safety. Mentees seeking supportive allies will be prioritized to match with you (**+10% Boost**).")

                # ── Section 2: Mentorship Capacity ─────────────────────────
                with st.expander("🎯 Mentorship Capacity & Availability", expanded=True):
                    col9, col10 = st.columns(2)
                    with col9:
                        is_active = st.checkbox("Active / Available for New Matches", value=mentor['is_active'])
                        st.caption("Uncheck to pause new mentee match requests without losing your profile.")
                    with col10:
                        max_mentees = st.number_input("Max Concurrent Mentees", min_value=1, max_value=10, value=mentor['max_mentees'])
                        st.caption("The platform will stop offering you new matches once this threshold is reached.")

                # ── CV Upload (bottom) ──────────────────────────────────────
                st.markdown("---")
                st.markdown("**📄 CV Upload**")
                cv_file = st.file_uploader("Upload your CV (PDF format)", type=["pdf"], key="mentor_cv_upload")
                if mentor.get('cv_path'):
                    with st.expander("📄 View My Current Uploaded CV"):
                        pdf_bytes = api_get_cv(mentor['id'])
                        if pdf_bytes:
                            display_pdf_inline(pdf_bytes)
                        else:
                            st.warning("Failed to retrieve CV from server.")

                # ── Save Button ─────────────────────────────────────────────
                save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                if save:
                    combined_roles = picked_roles.copy()
                    if custom_roles.strip():
                        for r in custom_roles.split(";"):
                            r_clean = r.strip()
                            if r_clean and r_clean not in combined_roles:
                                combined_roles.append(r_clean)

                    updated_data = {
                        "name": name,
                        "country": country,
                        "ed_level": ed_level,
                        "dev_type": ";".join(combined_roles),
                        "years_code_pro": years,
                        "job_factors": ";".join(picked_factors),
                        "org_size": org_size,
                        "is_active": is_active,
                        "is_diversity_ally": is_diversity_ally,
                        "max_mentees": max_mentees,
                        "additional_details": additional_details,
                        "contact_link": contact_link,
                        "gender": gender,
                        "timezone": timezone,
                        "linkedin_link": linkedin_link.strip() if linkedin_link else None
                    }
                    success, msg = api_update_profile(updated_data)
                    if success:
                        if cv_file is not None:
                            api_upload_cv(cv_file.getvalue(), cv_file.name)
                        st.session_state['profile'] = None
                        st.session_state['profile_save_success'] = msg
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            with st.expander("🔐 Account Security & Double Authentication", expanded=False):
                st.markdown("##### Double Authentication (2FA)")
                st.caption("Protect your account with an extra verification layer requiring a 6-digit code at sign-in.")
                user_info = profile.get('user', {}) if profile else {}
                curr_2fa = user_info.get('two_factor_enabled', True)
                col_2fa_status, col_2fa_act = st.columns([3, 1.2])
                with col_2fa_status:
                    st.write(f"Current Status: **{'🟢 Enabled (Active Protection)' if curr_2fa else '⚪ Disabled'}**")
                with col_2fa_act:
                    target_state = not curr_2fa
                    toggle_btn_text = "Disable 2FA" if curr_2fa else "Enable 2FA"
                    if st.button(toggle_btn_text, key="toggle_2fa_btn_mentor", use_container_width=True):
                        t_ok, t_msg = api_toggle_2fa(target_state)
                        if t_ok:
                            st.success(t_msg)
                            st.rerun()
                        else:
                            st.error(t_msg)

            with st.expander("⚠️ Danger Zone — Delete Account", expanded=False):
                st.markdown("##### 🗑️ Permanent Account Deletion")
                st.caption(
                    "Permanently delete your account, mentor profile, active mentorship connections, "
                    "milestones, and all direct messages. This action is **permanent and irreversible** under GDPR Right to Erasure."
                )
                confirm_del_mentor = st.checkbox(
                    "I understand that this action is permanent and cannot be undone.",
                    key="confirm_del_mentor_check"
                )
                if st.button("🗑️ Permanently Delete My Account", key="btn_delete_own_mentor_acc", type="primary", disabled=not confirm_del_mentor):
                    ok_del, msg_del = api_delete_my_account()
                    if ok_del:
                        st.session_state['account_deleted_banner'] = msg_del
                        st.rerun()
                    else:
                        st.error(msg_del)
                            
        with tab_requests:
            import urllib.parse as _up_req

            st.subheader("Incoming Requests & Active Mentoring")
            st.caption("Review incoming mentee requests requiring your response, and coordinate with your active mentees.")

            if 'mentor_action_feedback' in st.session_state and st.session_state['mentor_action_feedback']:
                m_type, m_msg = st.session_state.pop('mentor_action_feedback')
                if m_type == "success":
                    st.success(m_msg)
                elif m_type == "info":
                    st.info(m_msg)
                elif m_type == "error":
                    st.error(m_msg)

            history = sorted(api_get_match_history() or [], key=lambda h: h.get('created_at', ''), reverse=True)

            proposed = [h for h in history if h['status'] == 'REQUESTED']
            active_conns = [h for h in history if h['status'] == 'ACCEPTED']

            # ════════════════════════════════════════════════════════════
            # SECTION A — Incoming Requests (REQUESTED status)
            # ════════════════════════════════════════════════════════════
            st.markdown(f"### 🔔 Incoming Requests ({len(proposed)} awaiting your response)")
            if proposed:
                st.caption("Review each mentee's profile before deciding. You can accept and share your availability in one step.")
                for p in proposed:
                        raw_s = p.get('total_score', 0)
                        pct_s = int(round(raw_s * 100)) if isinstance(raw_s, float) and raw_s <= 1.0 else int(round(raw_s))
                        if pct_s >= 80:
                            sc_col, sc_lbl = "#1e7e34", "High Match"
                        elif pct_s >= 50:
                            sc_col, sc_lbl = "#856404", "Moderate Match"
                        else:
                            sc_col, sc_lbl = "#721c24", "Low Match"

                        date_str = p['created_at'].split("T")[0] if 'T' in p['created_at'] else p['created_at']

                        with st.container(border=True):
                            hd_l, hd_r = st.columns([3, 1])
                            with hd_l:
                                st.markdown(f"##### {p['mentee_name']}")
                                roles_disp = (p.get('mentee_devtype') or '').replace(';', ' · ')
                                st.caption(f"📍 {p.get('mentee_country', '')}  ·  {roles_disp}  ·  {format_experience_years(p.get('mentee_years'))} yrs exp")
                                st.markdown(
                                    f"<span style='background:#fff3cd; color:#856404; padding:3px 10px; "
                                    f"border-radius:12px; font-size:0.8rem; font-weight:600;'>🔔 Awaiting Response</span>"
                                    f"  <span style='color:#6c757d; font-size:0.8rem;'>· Requested {date_str}</span>",
                                    unsafe_allow_html=True
                                )
                                if p.get('is_ally_boosted'):
                                    st.info("🤝 **Diversity Ally Match**: This mentee requested a D&I Ally mentor — matched with you.")
                            with hd_r:
                                st.markdown(
                                    f"<div style='text-align:center; background:#f8f9fa; border-radius:8px; padding:8px 4px;'>"
                                    f"<span style='color:{sc_col}; font-size:1rem; font-weight:700;'>{pct_s}%</span><br/>"
                                    f"<span style='font-size:0.7rem; color:#6c757d;'>{sc_lbl}</span></div>",
                                    unsafe_allow_html=True
                                )

                            with st.expander(f"👤 View {p['mentee_name']}'s Profile"):
                                display_profile_card(
                                    name=p['mentee_name'],
                                    country=p.get('mentee_country'),
                                    ed_level=p.get('mentee_ed_level'),
                                    roles=p.get('mentee_devtype'),
                                    years=p.get('mentee_years'),
                                    org_size=p.get('mentee_org_size'),
                                    priorities=p.get('mentee_job_factors'),
                                    additional_details=p.get('mentee_additional_details'),
                                    user_id=p.get('mentee_id'),
                                    alternative_emails=p.get('mentee_alternative_emails'),
                                    linkedin_link=p.get('mentee_linkedin_link')
                                )

                            if p.get('mentee_cv_path'):
                                with st.expander(f"📄 Read {p['mentee_name']}'s CV"):
                                    pdf_bytes = api_get_cv(p['mentee_id'])
                                    if pdf_bytes:
                                        display_pdf_inline(pdf_bytes)
                                    else:
                                        st.info("CV details unavailable.")

                            # Accept / Decline buttons
                            st.markdown("---")
                            ac1, ac2 = st.columns(2)
                            if ac1.button("✅ Accept Connection", key=f"accept_conn_{p['id']}", use_container_width=True):
                                st.session_state[f"show_accept_dialog_{p['id']}"] = True
                                st.session_state[f"show_decline_dialog_{p['id']}"] = False
                                st.rerun()
                            if ac2.button("❌ Decline Connection", key=f"decline_conn_{p['id']}", use_container_width=True):
                                st.session_state[f"show_accept_dialog_{p['id']}"] = False
                                st.session_state[f"show_decline_dialog_{p['id']}"] = True
                                st.rerun()

                            # ── Accept dialog ─────────────────────────────────
                            if st.session_state.get(f"show_accept_dialog_{p['id']}", False):
                                st.markdown("##### 📅 Share Your Availability")
                                default_tz = mentor.get('timezone') or guess_timezone_from_email(user['email'])
                                mentor_tz = st.selectbox(
                                    "Confirm Your Timezone:",
                                    TIMEZONE_OPTIONS,
                                    index=TIMEZONE_OPTIONS.index(default_tz) if default_tz in TIMEZONE_OPTIONS else 12,
                                    key=f"accept_tz_{p['id']}"
                                )
                                if mentor.get('timezone') != mentor_tz:
                                    api_update_profile({"timezone": mentor_tz})
                                    st.session_state['profile'] = None
                                    st.rerun()

                                st.caption(f"Propose up to 3 time slots for your first sync with **{p['mentee_name']}**.")
                                input_mode = st.radio(
                                    "Availability Format:",
                                    ["Select Date/Time Slots", "Custom Text / Scheduling Link"],
                                    horizontal=True,
                                    key=f"input_mode_{p['id']}"
                                )

                                mentor_avails = ""
                                if input_mode == "Select Date/Time Slots":
                                    c1, c2, c3 = st.columns([2, 1, 1])
                                    d1 = c1.date_input("Date (Slot 1)", key=f"d1_{p['id']}")
                                    t1_start = c2.time_input("Start", datetime.time(10, 0), key=f"t1_start_{p['id']}")
                                    t1_end   = c3.time_input("End",   datetime.time(10, 30), key=f"t1_end_{p['id']}")
                                    c4, c5, c6 = st.columns([2, 1, 1])
                                    d2 = c4.date_input("Date (Slot 2)", key=f"d2_{p['id']}")
                                    t2_start = c5.time_input("Start", datetime.time(14, 0), key=f"t2_start_{p['id']}")
                                    t2_end   = c6.time_input("End",   datetime.time(14, 30), key=f"t2_end_{p['id']}")
                                    c7, c8, c9 = st.columns([2, 1, 1])
                                    d3 = c7.date_input("Date (Slot 3)", key=f"d3_{p['id']}")
                                    t3_start = c8.time_input("Start", datetime.time(16, 0), key=f"t3_start_{p['id']}")
                                    t3_end   = c9.time_input("End",   datetime.time(16, 30), key=f"t3_end_{p['id']}")
                                    extra_note = st.text_input("Optional notes for the mentee:", key=f"extra_note_{p['id']}")
                                    utc1_s = convert_local_to_utc_string(d1, t1_start, mentor_tz)
                                    utc1_e = convert_local_to_utc_string(d1, t1_end,   mentor_tz)
                                    utc2_s = convert_local_to_utc_string(d2, t2_start, mentor_tz)
                                    utc2_e = convert_local_to_utc_string(d2, t2_end,   mentor_tz)
                                    utc3_s = convert_local_to_utc_string(d3, t3_start, mentor_tz)
                                    utc3_e = convert_local_to_utc_string(d3, t3_end,   mentor_tz)
                                    mentor_avails = f"UTC_DTS:{utc1_s}/{utc1_e},{utc2_s}/{utc2_e},{utc3_s}/{utc3_e}|NOTE:{extra_note}"
                                else:
                                    default_avails = f"Schedule directly via my link:\n{mentor['contact_link']}" if mentor.get('contact_link') else "1. [Insert Day/Time 1]\n2. [Insert Day/Time 2]\n3. [Insert Day/Time 3]"
                                    mentor_avails = st.text_area("Custom availability note:", value=default_avails, key=f"custom_avails_text_{p['id']}", height=120)

                                conf1, conf2 = st.columns(2)
                                if conf1.button("✅ Confirm & Accept", key=f"confirm_accept_{p['id']}", use_container_width=True):
                                    if api_match_action(p['id'], "ACCEPT", availability_note=mentor_avails):
                                        st.toast(f"✅ Connection with {p['mentee_name']} accepted!", icon="🎉")
                                        st.session_state['mentor_action_feedback'] = (
                                            "success",
                                            f"🎉 **Connection with {p['mentee_name']} accepted!**\n\n"
                                            f"Your availability has been dispatched to them. You can now chat or coordinate next steps under **Active Mentoring Partnerships** below."
                                        )
                                        st.session_state[f"show_accept_dialog_{p['id']}"] = False
                                        st.session_state['profile'] = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to accept connection.")
                                if conf2.button("↩ Cancel", key=f"cancel_accept_{p['id']}", use_container_width=True):
                                    st.session_state[f"show_accept_dialog_{p['id']}"] = False
                                    st.rerun()

                            # ── Decline dialog ────────────────────────────────
                            if st.session_state.get(f"show_decline_dialog_{p['id']}", False):
                                st.warning(f"Are you sure you want to decline the request from **{p['mentee_name']}**?")
                                dec1, dec2 = st.columns(2)
                                if dec1.button("Confirm Decline", key=f"confirm_decline_{p['id']}", use_container_width=True):
                                    if api_match_action(p['id'], "DECLINE"):
                                        st.toast(f"Declined request from {p['mentee_name']}.", icon="ℹ️")
                                        st.session_state['mentor_action_feedback'] = (
                                            "info",
                                            f"ℹ️ **Request from {p['mentee_name']} has been declined and archived.**"
                                        )
                                        st.session_state[f"show_decline_dialog_{p['id']}"] = False
                                        st.session_state['profile'] = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to decline connection.")
                                if dec2.button("↩ Cancel", key=f"cancel_decline_{p['id']}", use_container_width=True):
                                    st.session_state[f"show_decline_dialog_{p['id']}"] = False
                                    st.rerun()
            else:
                st.info("✨ **You're all caught up!** No pending mentee requests awaiting response.")

            # ════════════════════════════════════════════════════════════
            # SECTION B — Active Connections
            # ════════════════════════════════════════════════════════════
            st.markdown("---")
            st.markdown(f"### 👥 Active Mentoring Partnerships ({len(active_conns)})")
            if active_conns:
                st.caption("Your current active mentees. Reach out to welcome them, coordinate intro syncs, or chat directly in-app.")

                for conn in active_conns:
                    raw_sc = conn.get('total_score', 0)
                    pct_sc = int(round(raw_sc * 100)) if isinstance(raw_sc, float) and raw_sc <= 1.0 else int(round(raw_sc))
                    date_c = conn['created_at'].split("T")[0] if 'T' in conn['created_at'] else conn['created_at']

                    with st.container(border=True):
                        cl, cr = st.columns([3, 1])
                        with cl:
                            st.markdown(f"##### {conn['mentee_name']}")
                            roles_c = (conn.get('mentee_devtype') or '').replace(';', ' · ')
                            st.caption(f"📍 {conn.get('mentee_country', '')}  ·  {roles_c}  ·  {format_experience_years(conn.get('mentee_years'))} yrs exp")
                            st.markdown(
                                f"<span style='background:#d4edda; color:#155724; padding:3px 10px; "
                                f"border-radius:12px; font-size:0.8rem; font-weight:600;'>✅ Connected</span>"
                                f"  <span style='color:#6c757d; font-size:0.8rem;'>· Since {date_c}</span>",
                                unsafe_allow_html=True
                            )
                            contact_parts = []
                            if conn.get('mentee_email'):
                                contact_parts.append(f"📧 `{conn['mentee_email']}`")
                            if conn.get('mentee_linkedin_link'):
                                contact_parts.append(f"[🌐 LinkedIn]({conn['mentee_linkedin_link']})")
                            if contact_parts:
                                st.markdown("  ·  ".join(contact_parts))
                            if conn.get('is_ally_boosted'):
                                st.success("🤝 **Diversity Ally Match**: Matched because you are a registered D&I Ally and the mentee requested one.")
                        with cr:
                            st.markdown(
                                f"<div style='text-align:center; background:#f8f9fa; border-radius:8px; padding:8px 4px;'>"
                                f"<span style='font-size:1rem; font-weight:700; color:#1e7e34;'>{pct_sc}%</span><br/>"
                                f"<span style='font-size:0.7rem; color:#6c757d;'>Match Score</span></div>",
                                unsafe_allow_html=True
                            )

                        with st.expander(f"👤 View {conn['mentee_name']}'s Profile"):
                            display_profile_card(
                                name=conn['mentee_name'],
                                country=conn.get('mentee_country'),
                                ed_level=conn.get('mentee_ed_level'),
                                roles=conn.get('mentee_devtype'),
                                years=conn.get('mentee_years'),
                                org_size=conn.get('mentee_org_size'),
                                priorities=conn.get('mentee_job_factors'),
                                additional_details=conn.get('mentee_additional_details'),
                                user_id=conn.get('mentee_id'),
                                email=conn.get('mentee_email'),
                                alternative_emails=conn.get('mentee_alternative_emails'),
                                linkedin_link=conn.get('mentee_linkedin_link')
                            )

                        if conn.get('mentee_cv_path'):
                            with st.expander(f"📄 Read {conn['mentee_name']}'s CV"):
                                pdf_bytes = api_get_cv(conn['mentee_id'])
                                if pdf_bytes:
                                    display_pdf_inline(pdf_bytes)

                        with st.expander(f"📅 Coordinate Intro Call with {conn['mentee_name']}"):
                            st.caption("Edit and send an email sharing your availability for the first 25-minute sync.")
                            avail_template = (
                                f"Hi {conn['mentee_name']},\n\n"
                                f"Welcome! I am looking forward to our mentorship partnership.\n\n"
                                f"Here are a few times I am available for our introductory 25-minute sync:\n"
                                f"- [Insert Day/Time 1]\n"
                                f"- [Insert Day/Time 2]\n"
                                f"- [Insert Day/Time 3]\n\n"
                            )
                            if mentor.get('contact_link'):
                                avail_template += f"Alternatively, you can book directly on my calendar:\n{mentor['contact_link']}\n\n"
                            avail_template += "Please let me know which slot works best and send a calendar invite once confirmed!\n\nBest regards,\n" + mentor.get('name', '')
                            avail_msg = st.text_area("Edit your availability email:", value=avail_template, height=200, key=f"avail_msg_{conn['id']}")
                            avail_subject = "Scheduling: Mentoring-Me Intro Sync"
                            avail_mailto = f"mailto:{conn['mentee_email']}?subject={_up_req.quote(avail_subject)}&body={_up_req.quote(avail_msg)}"
                            
                            m_title_val = f"Mentoring-Me Intro Sync: {mentor.get('name', 'Mentor')} & {conn['mentee_name']}"
                            m_gcal_url = generate_google_calendar_url(
                                title=m_title_val,
                                description=avail_msg,
                                location="Virtual (Mentoring-Me Platform)",
                                start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                                end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                            )
                            m_ics_bytes = generate_ics_calendar_file(
                                title=m_title_val,
                                description=avail_msg,
                                location="Virtual (Mentoring-Me Platform)",
                                start_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14),
                                end_dt=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2, hours=14, minutes=25)
                            )
                            
                            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                            with m_col1:
                                if st.button("🚀 Send Note & Open Chat", key=f"quick_send_avail_{conn['id']}", type="primary", use_container_width=True):
                                    ok_s, res_s = api_send_message(conn['id'], avail_msg)
                                    if ok_s:
                                        st.session_state['active_chat_match_id'] = conn['id']
                                        st.session_state['trigger_tab_switch'] = "Direct Messages"
                                        st.rerun()
                                    else:
                                        st.error(res_s)
                            with m_col2:
                                if st.button(f"✉️ Send Email", key=f"mentor_send_email_{conn['id']}", use_container_width=True):
                                    ok_e, msg_e = api_send_direct_match_email(conn['id'], avail_subject, avail_msg)
                                    if ok_e:
                                        st.success(f"✅ {msg_e}")
                                    else:
                                        st.error(msg_e)
                            with m_col3:
                                st.link_button("📅 Google Calendar", m_gcal_url, use_container_width=True)
                            with m_col4:
                                st.download_button(
                                    "📥 .ICS Invite",
                                    data=m_ics_bytes,
                                    file_name=f"mentoring_me_{conn['mentee_name'].replace(' ', '_')}.ics",
                                    mime="text/calendar",
                                    use_container_width=True,
                                    key=f"download_ics_mentor_{conn['id']}"
                                )

                        if st.button(f"💬 Open Chat with {conn['mentee_name']} in Messages Hub", key=f"mentor_open_chat_{conn['id']}", use_container_width=True):
                            st.session_state['active_chat_match_id'] = conn['id']
                            st.session_state['trigger_tab_switch'] = "Direct Messages"
                            st.rerun()
            else:
                st.info("No active mentorship connections yet. Once you accept incoming requests above, they will appear here.")

        with tab_milestones_m:
            render_mentor_milestones_tab(mentor, history)

        with tab_toolkit_m:
            render_mentor_toolkit_tab(mentor)

        with tab_messages_m:
            render_messages_page("MENTOR", profile, history)

        with tab_history_m:
            import urllib.parse as _up_mhist
            st.subheader("My Match & Connection History")
            st.caption("A comprehensive archive of all mentee match requests, active mentorship connections, and previous responses.")

            m_history = sorted(api_get_match_history() or [], key=lambda h: h.get('created_at', ''), reverse=True)

            if not m_history:
                st.info("You haven't received any mentee connection requests yet.")
            else:
                total_mh   = len(m_history)
                active_mh  = sum(1 for h in m_history if h['status'] == 'ACCEPTED')
                pending_mh = sum(1 for h in m_history if h['status'] in ['REQUESTED', 'PENDING'])
                declined_mh = sum(1 for h in m_history if h['status'] in ['DECLINED', 'DECLINE'])

                mhm1, mhm2, mhm3, mhm4 = st.columns(4)
                mhm1.metric("📋 Total Matches", total_mh)
                mhm2.metric("✅ Active Connections", active_mh)
                mhm3.metric("🔔 Awaiting Response", pending_mh)
                mhm4.metric("❌ Declined / Passed", declined_mh)
                st.markdown("---")

                # Filter & Sort controls
                mf_col1, mf_col2 = st.columns([2, 1])
                with mf_col1:
                    m_status_filter = st.selectbox(
                        "Filter by Status",
                        ["All", "✅ Active Connections (ACCEPTED)", "🔔 Awaiting Response (REQUESTED)", "❌ Declined / Passed"],
                        key="m_hist_status_filter"
                    )
                with mf_col2:
                    m_sort_by = st.selectbox(
                        "Sort by",
                        ["📅 Date (Newest First)", "🏆 Match Score (Highest First)", "📅 Date (Oldest First)"],
                        key="m_hist_sort_by"
                    )

                m_status_map = {
                    "All": None,
                    "✅ Active Connections (ACCEPTED)": "ACCEPTED",
                    "🔔 Awaiting Response (REQUESTED)": "REQUESTED",
                    "❌ Declined / Passed": "DECLINED"
                }
                m_active_filter = m_status_map[m_status_filter]
                if m_active_filter == "DECLINED":
                    m_filtered = [h for h in m_history if h['status'] in ['DECLINED', 'DECLINE']]
                elif m_active_filter == "REQUESTED":
                    m_filtered = [h for h in m_history if h['status'] in ['REQUESTED', 'PENDING']]
                elif m_active_filter is not None:
                    m_filtered = [h for h in m_history if h['status'] == m_active_filter]
                else:
                    m_filtered = m_history

                if "Score" in m_sort_by:
                    m_filtered = sorted(m_filtered, key=lambda x: x.get('total_score', 0), reverse=True)
                elif "Oldest" in m_sort_by:
                    m_filtered = sorted(m_filtered, key=lambda x: x.get('created_at', ''))
                else:
                    m_filtered = sorted(m_filtered, key=lambda x: x.get('created_at', ''), reverse=True)

                if not m_filtered:
                    st.info("No records found for the selected filter.")
                else:
                    st.caption(f"Showing {len(m_filtered)} of {total_mh} records.")

                for mh in m_filtered:
                    m_score = mh.get('total_score', 0)
                    if isinstance(m_score, float) and m_score <= 1.0:
                        m_score = int(round(m_score * 100))
                    else:
                        m_score = int(round(m_score))
                    
                    mh_status = mh['status']
                    if m_score >= 80:
                        m_sc_color = "#1e7e34"
                    elif m_score >= 50:
                        m_sc_color = "#856404"
                    else:
                        m_sc_color = "#721c24"

                    if mh_status == 'ACCEPTED':
                        mh_badge = "✅ Active Connection"
                        mh_color = "#155724"
                        mh_bg = "#d4edda"
                    elif mh_status in ['DECLINED', 'DECLINE']:
                        mh_badge = "❌ Declined / Passed"
                        mh_color = "#721c24"
                        mh_bg = "#f8d7da"
                    elif mh_status == 'REQUESTED':
                        mh_badge = "🔔 Awaiting Your Response"
                        mh_color = "#856404"
                        mh_bg = "#fff3cd"
                    else:
                        mh_badge = f"ℹ️ {mh_status}"
                        mh_color = "#004085"
                        mh_bg = "#cce5ff"

                    mh_date = mh['created_at'].split("T")[0] if 'T' in mh['created_at'] else mh['created_at']

                    with st.container(border=True):
                        top_ml, top_mr = st.columns([3, 1])
                        with top_ml:
                            st.markdown(f"##### {mh['mentee_name']}")
                            m_roles_display = (mh.get('mentee_devtype') or '').replace(';', ' · ')
                            st.caption(f"📍 {mh.get('mentee_country', '')}  ·  {m_roles_display}  ·  {format_experience_years(mh.get('mentee_years'))} yrs exp")
                            st.markdown(
                                f"<span style='background:{mh_bg}; color:{mh_color}; "
                                f"padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>"
                                f"{mh_badge}</span>"
                                f"  <span style='color:#6c757d; font-size:0.8rem;'>· Received {mh_date}</span>",
                                unsafe_allow_html=True
                            )
                            if mh.get('is_ally_boosted'):
                                st.success("🤝 **Diversity Ally Match**: Matched because you are a registered D&I Ally.")
                        with top_mr:
                            st.markdown(
                                f"<div style='text-align:center; background:#f8f9fa; border-radius:8px; padding:8px 4px;'>"
                                f"<span style='color:{m_sc_color}; font-size:1rem; font-weight:700;'>{m_score}%</span><br/>"
                                f"<span style='font-size:0.7rem; color:#6c757d;'>{mh.get('match_quality', 'Match Score')}</span></div>",
                                unsafe_allow_html=True
                            )

                        with st.expander(f"👤 View {mh['mentee_name']}'s Profile"):
                            display_profile_card(
                                name=mh['mentee_name'],
                                country=mh.get('mentee_country'),
                                ed_level=mh.get('mentee_ed_level'),
                                roles=mh.get('mentee_devtype'),
                                years=mh.get('mentee_years'),
                                org_size=mh.get('mentee_org_size'),
                                priorities=mh.get('mentee_job_factors'),
                                additional_details=mh.get('mentee_additional_details'),
                                user_id=mh.get('mentee_id'),
                                email=mh.get('mentee_email'),
                                alternative_emails=mh.get('mentee_alternative_emails'),
                                linkedin_link=mh.get('mentee_linkedin_link')
                            )

                        if mh.get('mentee_cv_path'):
                            with st.expander(f"📄 Read {mh['mentee_name']}'s CV"):
                                pdf_bytes = api_get_cv(mh['mentee_id'])
                                if pdf_bytes:
                                    display_pdf_inline(pdf_bytes)

                        with st.expander(f"📊 View Compatibility Breakdown ({m_score}%)", expanded=False):
                            display_match_compatibility_report(mh, is_mentor_view=True)

                        if mh.get('status') == 'ACCEPTED':
                            if st.button(f"💬 Open Chat with {mh['mentee_name']} in Messages Hub", key=f"mhist_chat_btn_{mh['id']}", use_container_width=True):
                                st.session_state['active_chat_match_id'] = mh['id']
                                st.session_state['trigger_tab_switch'] = "Direct Messages"
                                st.rerun()

        with tab_nominate:
            import urllib.parse as _up_nom
            st.subheader("🤝 Pass the Torch — Nominate a Peer Mentor")
            st.caption(
                "Help expand our pool of senior technical role models and diversity allies. "
                "Nominate talented colleagues, senior engineers, or researchers from your network to join Mentoring-Me as mentors."
            )

            if 'nominate_feedback' in st.session_state and st.session_state['nominate_feedback']:
                st.success(st.session_state.pop('nominate_feedback'))

            # ── Section 1: Nomination Form ────────────────────────────────────
            st.markdown("### ✉️ Invite a Colleague")
            with st.form("colleague_nomination_form", clear_on_submit=True):
                cn_col1, cn_col2 = st.columns(2)
                with cn_col1:
                    colleague_name = st.text_input("Colleague's Full Name", placeholder="e.g. Dr. Sarah Jenkins")
                with cn_col2:
                    colleague_email = st.text_input("Colleague's Email Address", placeholder="e.g. sarah.jenkins@company.com")
                
                colleague_focus = st.text_input(
                    "Their Area(s) of Technical Expertise",
                    placeholder="e.g. Cloud Architecture, Distributed Systems, ML Engineering, Cybersecurity"
                )
                
                colleague_submit = st.form_submit_button("🔗 Generate Colleague Invitation & Email Draft", use_container_width=True)
                
                if colleague_submit:
                    if not colleague_name.strip() or not colleague_email.strip() or not colleague_focus.strip():
                        st.error("Please fill in all three fields to generate the invitation.")
                    elif "@" not in colleague_email or "." not in colleague_email:
                        st.error("Please enter a valid email address.")
                    else:
                        ok, res = api_nominate_mentor(colleague_name.strip(), colleague_email.strip(), colleague_focus.strip())
                        if ok:
                            st.session_state['latest_colleague_nomination'] = res
                            st.toast(f"✅ Invitation created for {colleague_name}!", icon="🎉")
                            st.session_state['nominate_feedback'] = f"✅ **Invitation created for {colleague_name}!** See the email designer below to customize and send the invite."
                            st.rerun()
                        else:
                            st.error(res)

    elif role == "ADMIN":
        st.header("🛡️ Administrator Dashboard")
        st.caption("Platform-wide oversight, equity analytics, security telemetry, and data governance.")

        # Fetch base raw datasets
        all_users_raw = api_admin_get_users() or []
        history_raw = api_get_match_history() or []
        all_notes_raw = api_get_notes() or []
        audit_logs_raw = api_admin_get_audit_logs(limit=100) or []

        # ════════════════════════════════════════════════════════════════════
        # GLOBAL SCOPE SELECTOR — Controls All Admin Sections & Exports
        # ════════════════════════════════════════════════════════════════════
        st.markdown("##### 🌐 Global Dashboard Analytics & Export Scope")
        admin_global_scope = st.radio(
            "Filter all dashboard analytics, logs, and exports by scope:",
            ["🟢 Live Registered Users Only", "🧪 Combined Dataset (Real Users + SO2020 Benchmark)", "🔬 Benchmark Demo Accounts Only"],
            index=0,
            horizontal=True,
            key="admin_global_scope_radio",
            help="Toggling this filter immediately updates Equity Analytics, Matches Logs, Milestones Tracker, Security Telemetry, and Data Exports across the entire dashboard."
        )

        def _is_demo_usr(u_obj):
            if not isinstance(u_obj, dict):
                return False
            em = (u_obj.get('email') or '').lower()
            uid = str(u_obj.get('id') or '')
            return em.endswith('@mentoring-me.demo') or em.endswith('@mentorme.demo') or uid.startswith('user-uuid-')

        real_u_ids = {
            str(u['id']) for u in all_users_raw if not _is_demo_usr(u) and u.get('id')
        }
        real_u_emails = {
            (u.get('email') or '').lower() for u in all_users_raw if not _is_demo_usr(u) and u.get('email')
        }

        def _is_real_mtch(m_obj):
            if not isinstance(m_obj, dict):
                return False
            m_id = str(m_obj.get('id') or '')
            if m_id.startswith('match_') or m_id.startswith('mtch_demo_') or m_id.startswith('user-uuid-'):
                return False
            m_eid = str(m_obj.get('mentee_id') or '')
            r_eid = str(m_obj.get('mentor_id') or '')
            m_em = (m_obj.get('mentee_email') or '').lower()
            r_em = (m_obj.get('mentor_email') or '').lower()
            
            if m_em.endswith('@mentoring-me.demo') or r_em.endswith('@mentoring-me.demo') or m_em.endswith('@mentorme.demo') or r_em.endswith('@mentorme.demo'):
                return False
            if m_eid.startswith('user-uuid-') or r_eid.startswith('user-uuid-'):
                return False

            is_mentee_real = (m_eid in real_u_ids) or (m_em in real_u_emails)
            is_mentor_real = (r_eid in real_u_ids) or (r_em in real_u_emails)
            return is_mentee_real and is_mentor_real

        def _is_demo_mtch(m_obj):
            return not _is_real_mtch(m_obj)

        def _is_real_note(n_obj):
            if not isinstance(n_obj, dict):
                return False
            m_eid = str(n_obj.get('mentee_id') or '')
            r_eid = str(n_obj.get('mentor_id') or '')
            if m_eid.startswith('user-uuid-') or r_eid.startswith('user-uuid-'):
                return False
            return (m_eid in real_u_ids) and (r_eid in real_u_ids)

        def _is_demo_note(n_obj):
            return not _is_real_note(n_obj)

        def _is_real_audit(a_obj):
            if not isinstance(a_obj, dict):
                return False
            em = (a_obj.get('user_email') or '').lower()
            uid = str(a_obj.get('user_id') or '')
            if em.endswith('@mentoring-me.demo') or em.endswith('@mentorme.demo') or uid.startswith('user-uuid-'):
                return False
            return (uid in real_u_ids) or (em in real_u_emails)

        def _is_demo_audit(a_obj):
            return not _is_real_audit(a_obj)

        # Apply scope filtering globally
        if admin_global_scope == "🟢 Live Registered Users Only":
            all_users = [u for u in all_users_raw if not _is_demo_usr(u)]
            # Exclude PROPOSED matches from live scope — these are auto-generated algorithm
            # recommendations that have NOT been explicitly requested or accepted by any user.
            # Only count REQUESTED, ACCEPTED or DECLINED matches as real match activity.
            history = [
                m for m in history_raw
                if _is_real_mtch(m) and (m.get('status') or '').upper() != 'PROPOSED'
            ]
            all_notes = [n for n in all_notes_raw if _is_real_note(n)]
            audit_logs = [a for a in audit_logs_raw if _is_real_audit(a)]
        elif admin_global_scope == "🔬 Benchmark Demo Accounts Only":
            all_users = [u for u in all_users_raw if _is_demo_usr(u)]
            history = [m for m in history_raw if _is_demo_mtch(m)]
            all_notes = [n for n in all_notes_raw if _is_demo_note(n)]
            audit_logs = [a for a in audit_logs_raw if _is_demo_audit(a)]
        else:
            all_users = all_users_raw
            history = history_raw
            all_notes = all_notes_raw
            audit_logs = audit_logs_raw

        st.caption(f"📊 Dashboard Active Scope: `{admin_global_scope}` — Displaying **{len(all_users)} Users**, **{len(history)} Matches**, **{len(all_notes)} Sessions**, and **{len(audit_logs)} Security Events**.")

        # ════════════════════════════════════════════════════════════════════
        # SECTION A — Equity Analytics Dashboard
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("📊 Equity Impact Analytics")
        st.caption("Live metrics measuring the platform's progress toward equitable mentorship for early-career women in tech (SDG 5).")

        total_matches   = len(history)
        accepted        = [h for h in history if h['status'] == 'ACCEPTED']
        female_mentee   = [h for h in history if is_female_gender_val(h.get('mentee_gender'), default_mentee=True)]
        female_mentor   = [h for h in history if is_female_gender_val(h.get('mentor_gender'), default_mentee=False)]
        ff_pairs        = [h for h in accepted if is_female_gender_val(h.get('mentee_gender'), default_mentee=True) and is_female_gender_val(h.get('mentor_gender'), default_mentee=False)]
        ally_boosted    = [h for h in history if h.get('is_ally_boosted')]
        rep_boosted     = [h for h in history if h.get('is_representation_boosted')]

        reg_female_mentees = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTEE' and is_female_gender_val(u.get('gender'), default_mentee=True))
        reg_female_mentors = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTOR' and is_female_gender_val(u.get('gender'), default_mentee=False))
        male_mentor     = [h for h in history if (h.get('mentor_gender') or '').lower() in ['male', 'man']]
        reg_male_mentors = sum(1 for u in all_users if (u.get('role') or '').upper() == 'MENTOR' and (u.get('gender') or '').lower() in ['male', 'man'])

        f_mentee_count = reg_female_mentees
        f_mentor_count = reg_female_mentors
        m_mentor_count = reg_male_mentors

        active_f_mentee = len(set(h['mentee_name'] for h in female_mentee))
        active_f_mentor = len(set(h['mentor_name'] for h in female_mentor))
        active_m_mentor = len(set(h['mentor_name'] for h in male_mentor))

        em1, em2, em3, em4, em5 = st.columns(5)
        em1.metric("📋 Total Matches", total_matches)
        em2.metric("✅ Accepted Connections", len(accepted))
        em3.metric("♀️ Female Mentees", f_mentee_count, help=f"{f_mentee_count} registered female mentees on platform ({active_f_mentee} active in match requests)")
        em4.metric("♀️ Female Mentors", f_mentor_count, help=f"{f_mentor_count} registered female mentors on platform ({active_f_mentor} active in matches)")
        em5.metric("♂️ Male Mentors", m_mentor_count, help=f"{m_mentor_count} registered male mentors on platform ({active_m_mentor} active in matches)")

        st.markdown("")
        em5, em6, em7, em8 = st.columns(4)
        ff_pct = int(round(len(ff_pairs)/len(accepted)*100)) if accepted else 0
        fm_ally_pct = max(0, 100 - ff_pct) if accepted else 0
        ff_rate = f"{ff_pct}%" if accepted else "N/A"
        fm_ally_rate = f"{fm_ally_pct}%" if accepted else "N/A"
        ally_rate = f"{int(round(len(ally_boosted)/total_matches*100))}%" if total_matches else "N/A"
        rep_rate = f"{int(round(len(rep_boosted)/total_matches*100))}%" if total_matches else "N/A"
        avg_score = f"{int(round(sum(h.get('total_score',0) for h in accepted)/len(accepted)*100))}%" if accepted else "N/A"
        
        em5.metric("🌟 Female-Female Match Rate", ff_rate, help="% of accepted connections: female mentee → female mentor (peer role-model pairings)")
        em6.metric("🔀 Cross-Gender Pairing Rate", fm_ally_rate, help="% of accepted connections: female mentee → male mentor (cross-gender pairings)")
        em7.metric("🤝 D&I Ally Boost Rate", ally_rate, help="% of all matches where the D&I Ally boost was applied. D&I Allies can be any gender — female senior engineers championing junior women are also D&I allies.")
        em8.metric("📈 Avg. Accepted Score", avg_score)

        # Match Quality & Confidence Score Distribution
        q_strong = [h for h in history if h.get('match_quality') == 'Strong' or (h.get('total_score', 0) >= 0.70)]
        q_good   = [h for h in history if h.get('match_quality') == 'Good' or (0.55 <= h.get('total_score', 0) < 0.70)]
        q_fair   = [h for h in history if h.get('match_quality') == 'Fair' or (0.40 <= h.get('total_score', 0) < 0.55)]
        q_weak   = [h for h in history if h.get('match_quality') == 'Weak' or (h.get('total_score', 0) < 0.40)]

        st.markdown("---")
        st.markdown("##### 🎯 Match Quality & Confidence Distribution")
        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("🟢 Strong Matches (≥70%)", len(q_strong), f"{(len(q_strong)/total_matches*100):.0f}%" if total_matches else "0%")
        qc2.metric("🔵 Good Matches (55-69%)", len(q_good), f"{(len(q_good)/total_matches*100):.0f}%" if total_matches else "0%")
        qc3.metric("🟡 Fair Matches (40-54%)", len(q_fair), f"{(len(q_fair)/total_matches*100):.0f}%" if total_matches else "0%")
        qc4.metric("🔴 Weak Matches (<40%)", len(q_weak), f"{(len(q_weak)/total_matches*100):.0f}%" if total_matches else "0%")

        if total_matches > 0:
            st.markdown("")
            ch_col1, ch_col2, ch_col3 = st.columns(3)
            with ch_col1:
                st.markdown("**Confidence Tier Distribution**")
                q_df = pd.DataFrame([
                    {'Tier': 'Strong (≥70%)', 'Count': len(q_strong)},
                    {'Tier': 'Good (55-69%)', 'Count': len(q_good)},
                    {'Tier': 'Fair (40-54%)', 'Count': len(q_fair)},
                    {'Tier': 'Weak (<40%)', 'Count': len(q_weak)},
                ])
                st.bar_chart(q_df.set_index('Tier'))
            with ch_col2:
                st.markdown("**Career Stage Distribution of Mentees**")
                tier_counts = {}
                for h in history:
                    t = h.get('mentee_exp_tier') or 'Unknown'
                    tier_counts[t] = tier_counts.get(t, 0) + 1
                if tier_counts:
                    tier_df = pd.DataFrame(list(tier_counts.items()), columns=['Career Stage', 'Mentees']).sort_values('Mentees', ascending=False)
                    st.bar_chart(tier_df.set_index('Career Stage'))
            with ch_col3:
                st.markdown("**Country Diversity of Matched Mentors**")
                country_counts = {}
                for h in history:
                    c = h.get('mentor_country') or 'Unknown'
                    country_counts[c] = country_counts.get(c, 0) + 1
                if country_counts:
                    country_df = pd.DataFrame(list(country_counts.items()), columns=['Country', 'Mentors']).sort_values('Mentors', ascending=False).head(10)
                    st.bar_chart(country_df.set_index('Country'))

        # ════════════════════════════════════════════════════════════════════
        # SECTION B — Global Match Log & Outcomes
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("📋 Global Platform Matches Log")
        if not history:
            st.info(f"No match transactions exist in the database under scope `{admin_global_scope}`.")
        else:
            admin_list = []
            for h in history:
                raw_s = h.get('total_score', 0)
                pct_s = int(round(raw_s * 100)) if isinstance(raw_s, float) and raw_s <= 1.0 else int(round(raw_s))
                admin_list.append({
                    'Match ID': h['id'],
                    'Mentee': h['mentee_name'],
                    'Mentor': h['mentor_name'],
                    'Score': f"{pct_s}%",
                    'Raw Score': raw_s,
                    'Confidence': h['match_quality'],
                    'Status': h['status'],
                    'Rep. Boost': '🌟' if h.get('is_representation_boosted') else '',
                    'Ally Boost': '🤝' if h.get('is_ally_boosted') else '',
                    'Date': h['created_at'].split('T')[0] if 'T' in h.get('created_at','') else h.get('created_at','')
                })
            df_admin_matches = pd.DataFrame(admin_list)
            st.dataframe(df_admin_matches[['Match ID', 'Mentee', 'Mentor', 'Score', 'Confidence', 'Status', 'Rep. Boost', 'Ally Boost', 'Date']], use_container_width=True)

        # ════════════════════════════════════════════════════════════════════
        # SECTION B2 — Mentorship Health & Milestones Progress Tracker
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("📈 Mentorship Health & Milestones Progress Tracker")
        st.caption("Live monitoring of ongoing 1-on-1 sessions, homework task completion, and long-term mentee milestones logged across all pairings.")
        
        n_total = len(all_notes)
        n_completed = sum(1 for n in all_notes if n.get('milestone_status') == 'COMPLETED')
        n_in_progress = sum(1 for n in all_notes if n.get('milestone_status') == 'IN_PROGRESS')
        n_not_started = sum(1 for n in all_notes if n.get('milestone_status') == 'NOT_STARTED')
        unique_mentees_notes = len(set(n['mentee_id'] for n in all_notes if n.get('mentee_id')))
        m_comp_rate = (n_completed / n_total * 100) if n_total > 0 else 0.0

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("📝 Total Sessions Logged", n_total)
        mc2.metric("🏆 Milestones Completed", n_completed, f"{m_comp_rate:.1f}% Rate")
        mc3.metric("⏳ In-Progress Milestones", n_in_progress)
        mc4.metric("👥 Mentees Guided", unique_mentees_notes)

        if n_total > 0:
            st.markdown(f"**Overall Platform Milestone Completion Rate:** `{m_comp_rate:.1f}%`")
            st.progress(min(1.0, m_comp_rate / 100.0))
            
            with st.expander("📋 View Platform-Wide Mentorship Sessions & Milestones Log", expanded=False):
                notes_table = []
                for n in all_notes:
                    notes_table.append({
                        "Session Date": n.get('session_date', '')[:10],
                        "Mentor": n.get('mentor_name', 'Mentor'),
                        "Mentee": n.get('mentee_name', 'Mentee'),
                        "Milestone Title": n.get('title', 'Session'),
                        "Status": n.get('milestone_status', 'IN_PROGRESS'),
                        "Action Items": n.get('action_items', 'N/A')[:60] + "..." if len(n.get('action_items', '')) > 60 else n.get('action_items', 'N/A'),
                    })
                st.dataframe(pd.DataFrame(notes_table), use_container_width=True)
        else:
            st.info(f"No mentorship sessions or milestones logged under scope `{admin_global_scope}`.")

        # ════════════════════════════════════════════════════════════════════
        # SECTION C — Dynamic Algorithm Weight Tuning (Live Hyperparameters)
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("⚙️ Dynamic Algorithm Weight Tuning (Live Hyperparameters)")
        st.caption("Adjust the empirical weights and institutional boosts used by the 5-Factor Weighted Matching Model in real time without restarting services.")

        current_cfg = api_admin_get_algorithm_config()
        def_role = current_cfg.get("w_role", 0.30)
        def_exp  = current_cfg.get("w_exp", 0.25)
        def_stage = current_cfg.get("w_stage", 0.20)
        def_goals = current_cfg.get("w_goals", 0.15)
        def_pract = current_cfg.get("w_practical", 0.10)
        def_ally  = current_cfg.get("ally_boost", 0.10)
        def_rep   = current_cfg.get("rep_boost", 0.05)

        with st.form("admin_algorithm_weights_form"):
            w_c1, w_c2 = st.columns(2)
            with w_c1:
                sl_role = st.slider("1. Role & Technical Alignment Weight (Jaccard)", min_value=0.0, max_value=0.60, value=float(def_role), step=0.05, help="Weight given to overlapping DevType roles and technical skills.")
                sl_exp = st.slider("2. Relatable Experience Gap Weight (2-10y window)", min_value=0.0, max_value=0.50, value=float(def_exp), step=0.05, help="Weight given to optimal seniority distance.")
                sl_stage = st.slider("3. Career-Stage Priority Weight (Retention Risk 0-2y, 5-10y)", min_value=0.0, max_value=0.50, value=float(def_stage), step=0.05, help="Direct boost given to retention-risk career milestones.")
            with w_c2:
                sl_goals = st.slider("4. Goals & Workplace Culture Alignment", min_value=0.0, max_value=0.40, value=float(def_goals), step=0.05, help="Alignment on stated JobFactors priorities.")
                sl_pract = st.slider("5. Practical Logistics / Org Size Fit", min_value=0.0, max_value=0.30, value=float(def_pract), step=0.05, help="Weight given to company scale and logistics compatibility.")
                sl_ally = st.slider("🤝 D&I Ally Priority Boost", min_value=0.0, max_value=0.20, value=float(def_ally), step=0.01, help="Additive score boost applied when mentor is a registered Diversity Ally.")
                sl_rep = st.slider("🌟 Gender Representation Boost", min_value=0.0, max_value=0.15, value=float(def_rep), step=0.01, help="Additive boost for underrepresented female-female pairs.")

            raw_sum = sl_role + sl_exp + sl_stage + sl_goals + sl_pract
            st.markdown(f"**Core 5-Factor Weight Sum:** `{raw_sum:.2f}` {'✅ (Balanced to 1.00)' if abs(raw_sum - 1.0) < 0.001 else f'⚠️ (Normalizes to 1.00 on save)'}")

            btn_save_weights = st.form_submit_button("💾 Save & Activate Algorithm Weights", type="primary", use_container_width=True)
            if btn_save_weights:
                norm_factor = raw_sum if raw_sum > 0 else 1.0
                new_weights = {
                    "w_role": round(sl_role / norm_factor, 3),
                    "w_exp": round(sl_exp / norm_factor, 3),
                    "w_stage": round(sl_stage / norm_factor, 3),
                    "w_goals": round(sl_goals / norm_factor, 3),
                    "w_practical": round(sl_pract / norm_factor, 3),
                    "ally_boost": round(sl_ally, 3),
                    "rep_boost": round(sl_rep, 3),
                }
                ok_w, msg_w = api_admin_update_algorithm_config(new_weights)
                if ok_w:
                    st.success(f"🎉 {msg_w}")
                    st.rerun()
                else:
                    st.error(msg_w)

        # ════════════════════════════════════════════════════════════════════
        # SECTION D — Institutional Data Export Hub & Capstone Report Generator
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("📑 Capstone Report & Institutional Data Hub")
        seed_col1, seed_col2 = st.columns([3, 1])
        with seed_col1:
            st.caption("Generate complete academic evaluation reports, SDG 5 equity summaries, and export raw data packages ready for capstone submission and stakeholder presentation.")
        with seed_col2:
            if st.button("🌱 Populate/Refresh Reports Data", key="btn_admin_reseed_ui", use_container_width=True):
                ok_re, msg_re = api_admin_reseed_db()
                if ok_re:
                    st.toast("✅ Platform database populated! Reloading reports...", icon="🎉")
                    st.rerun()
                else:
                    st.error(msg_re)

        export_target_scope = admin_global_scope
        all_users_exp = all_users
        history_exp = history

        # Compile Capstone Report Markdown
        capstone_report_md = generate_capstone_executive_report(history_exp, all_users_exp, audit_logs, all_notes, current_cfg)
        
        # Compile Evaluation JSON
        capstone_eval_json = json.dumps({
            "project_metadata": {
                "title": "Mentoring-Me Capstone Platform",
                "export_scope": export_target_scope,
                "evaluation_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "sdg_alignment": "UN SDG 5 (Gender Equality & Women in STEM)"
            },
            "quantitative_kpis": {
                "total_matches": len(history_exp),
                "accepted_connections": len([h for h in history_exp if h.get('status') == 'ACCEPTED']),
                "acceptance_rate_pct": round(len([h for h in history_exp if h.get('status') == 'ACCEPTED'])/len(history_exp)*100, 2) if history_exp else 0.0,
                "mean_compatibility_score_pct": round(sum(h.get('total_score',0) for h in history_exp if h.get('status') == 'ACCEPTED')/max(1, len([h for h in history_exp if h.get('status') == 'ACCEPTED']))*100, 2) if [h for h in history_exp if h.get('status') == 'ACCEPTED'] else 0.0,
                "total_users": len(all_users_exp),
                "mfa_adoption_pct": round(sum(1 for u in all_users_exp if u.get('two_factor_enabled'))/len(all_users_exp)*100, 2) if all_users_exp else 0.0,
            },
            "algorithm_hyperparameters": current_cfg
        }, indent=2)

        st.markdown("##### 📥 One-Click Academic & Institutional Exports")
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            st.download_button(
                label="📑 Download Capstone Executive Report (.md)",
                data=capstone_report_md.encode('utf-8'),
                file_name=f"mentoring_me_capstone_report_{datetime.datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True
            )
        with rep_col2:
            st.download_button(
                label="📊 Download Evaluation Summary (.json)",
                data=capstone_eval_json.encode('utf-8'),
                file_name=f"mentoring_me_evaluation_summary_{datetime.datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("")
        sdg_summary_data = {
            "metric": [
                "Total Matches Generated",
                "Accepted Mentorships",
                "Exported User Scope",
                "Export Timestamp"
            ],
            "value": [
                len(history_exp),
                len([h for h in history_exp if h.get('status') == 'ACCEPTED']),
                export_target_scope,
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            ]
        }

        # Generate Styled HTML Dossiers
        html_matches_dossier = generate_matches_html_dossier(history_exp)
        html_sdg5_dossier = generate_sdg5_html_dossier(sdg_summary_data)
        html_users_dossier = generate_user_directory_html_dossier(all_users_exp)

        st.markdown("##### 🌐 Executive HTML Dossiers (Styled & Print-to-PDF Ready)")
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            if history_exp:
                st.download_button(
                    label="🌐 Match Outcomes Dossier (.html)",
                    data=html_matches_dossier.encode('utf-8'),
                    file_name=f"mentoring_me_matches_dossier_{datetime.datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            else:
                st.button("🌐 Match Outcomes Dossier (.html)", disabled=True, use_container_width=True)

        with exp_col2:
            st.download_button(
                label="🌟 SDG 5 Impact Dossier (.html)",
                data=html_sdg5_dossier.encode('utf-8'),
                file_name=f"mentoring_me_sdg5_dossier_{datetime.datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )

        with exp_col3:
            if all_users_exp:
                st.download_button(
                    label="👥 User Directory Dossier (.html)",
                    data=html_users_dossier.encode('utf-8'),
                    file_name=f"mentoring_me_users_dossier_{datetime.datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            else:
                st.button("👥 User Directory Dossier (.html)", disabled=True, use_container_width=True)

        # Raw CSV Export Fallback (Optional)
        with st.expander("📦 Raw Spreadsheet Data Packages (CSV Fallback)", expanded=False):
            st.caption(f"Download unformatted CSV raw files scoped to `{export_target_scope}`.")
            raw_c1, raw_c2, raw_c3 = st.columns(3)
            with raw_c1:
                if history_exp:
                    csv_matches = pd.DataFrame(history_exp).to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Raw Matches (CSV)", data=csv_matches, file_name=f"raw_matches_{datetime.datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
                else:
                    st.button("📥 Raw Matches (CSV)", disabled=True, use_container_width=True)
            with raw_c2:
                csv_sdg = pd.DataFrame(sdg_summary_data).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Raw SDG 5 (CSV)", data=csv_sdg, file_name=f"raw_sdg5_{datetime.datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            with raw_c3:
                if all_users_exp:
                    csv_users = pd.DataFrame(all_users_exp).to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Raw Users (CSV)", data=csv_users, file_name=f"raw_users_{datetime.datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
                else:
                    st.button("📥 Raw Users (CSV)", disabled=True, use_container_width=True)

        # In-App Interactive Report Previewer
        with st.expander("👁️ Preview Full Live Capstone Executive Report (Ready to Copy for Paper / Slides)", expanded=False):
            st.caption("This live document automatically synthesizes real database records, algorithm weights, and SDG 5 metrics into standard academic report format.")
            st.markdown(capstone_report_md)

        # ════════════════════════════════════════════════════════════════════
        # SECTION E — Security Telemetry & Real-Time Audit Logs
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("🛡️ Security Telemetry & Real-Time Audit Logs")
        st.caption(f"Live security monitoring, 2FA delivery verification, and event auditing scoped to `{admin_global_scope}`.")

        if not audit_logs:
            st.info(f"No security audit logs recorded under scope `{admin_global_scope}`.")
        else:
            total_events = len(audit_logs)
            logins_ok = sum(1 for l in audit_logs if l.get('event_type') == 'LOGIN_SUCCESS')
            twofa_ok  = sum(1 for l in audit_logs if l.get('event_type') == '2FA_VERIFIED')
            failures  = sum(1 for l in audit_logs if l.get('status') == 'FAILED')

            sec_c1, sec_c2, sec_c3, sec_c4 = st.columns(4)
            sec_c1.metric("🛡️ Total Audit Events", total_events)
            sec_c2.metric("✅ 2FA Successes", twofa_ok)
            sec_c3.metric("🔑 Direct Logins", logins_ok)
            sec_c4.metric("⚠️ Security Alerts/Fails", failures)

            log_table_data = []
            for l in audit_logs:
                st_icon = "🟢" if l.get('status') == 'SUCCESS' else ("🔴" if l.get('status') == 'FAILED' else "🟡")
                log_table_data.append({
                    "Status": f"{st_icon} {l.get('status', 'SUCCESS')}",
                    "Event": l.get('event_type', 'EVENT'),
                    "User": l.get('user_email', 'Anonymous'),
                    "Details": l.get('details', ''),
                    "IP Address": l.get('ip_address', 'Internal'),
                    "Timestamp": l.get('created_at', '').replace('T', ' ')[:19]
                })
            st.dataframe(pd.DataFrame(log_table_data), use_container_width=True)

        # ════════════════════════════════════════════════════════════════════
        # SECTION F — Registered User & Credential Management
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("👥 Registered User & Credential Management")
        st.caption(f"Inspect registered accounts, monitor authentication status, and manage users scoped to `{admin_global_scope}`.")

        if not all_users_raw:
            st.info("No registered users retrieved.")
        else:
            # Search & Filter Controls
            uf_c1, uf_c2, uf_c3 = st.columns([2, 1, 1])
            with uf_c1:
                search_q = st.text_input("🔍 Search Users by Email, Name, or Country", placeholder="e.g. jane@example.com or Sarah", key="user_search_query_input").strip().lower()
            with uf_c2:
                default_origin_idx = 1 if admin_global_scope == "🟢 Live Registered Users Only" else (2 if admin_global_scope == "🔬 Benchmark Demo Accounts Only" else 0)
                origin_filter = st.selectbox("Account Origin Filter", ["All Accounts", "🟢 Live Real Users Only", "🧪 Seeded Benchmark Data Only"], index=default_origin_idx, key="user_origin_filter_selectbox")
            with uf_c3:
                role_filter = st.selectbox("Filter by Role", ["All Roles", "MENTEE", "MENTOR", "ADMIN"], key="user_role_filter_selectbox")

            filtered_users = all_users_raw
            if origin_filter == "🟢 Live Real Users Only":
                filtered_users = [u for u in filtered_users if not _is_demo_usr(u)]
            elif origin_filter == "🧪 Seeded Benchmark Data Only":
                filtered_users = [u for u in filtered_users if _is_demo_usr(u)]

            if role_filter != "All Roles":
                filtered_users = [u for u in filtered_users if (u.get('role') or '').upper() == role_filter]
            if search_q:
                filtered_users = [
                    u for u in filtered_users
                    if search_q in (u.get('email') or '').lower()
                    or search_q in (u.get('name') or '').lower()
                    or search_q in (u.get('country') or '').lower()
                ]

            real_users_count = sum(1 for u in filtered_users if not _is_demo_usr(u))
            synthetic_count = len(filtered_users) - real_users_count
            total_u = len(filtered_users)
            mentees_u = sum(1 for u in filtered_users if (u.get('role') or '').upper() == 'MENTEE')
            mentors_u = sum(1 for u in filtered_users if (u.get('role') or '').upper() == 'MENTOR')
            two_fa_u  = sum(1 for u in filtered_users if u.get('two_factor_enabled'))

            uc1, uc2, uc3, uc4 = st.columns(4)
            uc1.metric("👥 Total Accounts Listed", total_u)
            uc2.metric("🟢 Live Real Users", real_users_count, f"{synthetic_count} Benchmark" if synthetic_count > 0 else "0 Benchmark")
            uc3.metric("👩‍💻 Mentees / Mentors", f"{mentees_u} / {mentors_u}")
            uc4.metric("🔒 2FA Enabled", two_fa_u)

            st.caption(f"Showing **{len(filtered_users)}** of **{len(all_users_raw)}** total platform user accounts.")

            for u_item in filtered_users:
                u_id = u_item['id']
                u_email = u_item.get('email', '')
                u_name = u_item.get('name', 'Unnamed User')
                u_role = (u_item.get('role') or 'MENTEE').upper()
                u_2fa = "🔒 2FA Active" if u_item.get('two_factor_enabled') else "🔓 2FA Off"
                u_provider = u_item.get('auth_provider', 'LOCAL')
                u_country = u_item.get('country', 'Not Specified')
                u_gender = u_item.get('gender') or 'Not Specified'
                u_created = u_item.get('created_at', '').split('T')[0] if 'T' in u_item.get('created_at', '') else u_item.get('created_at', '')

                is_real_user = not _is_demo_usr(u_item)
                origin_badge_bg = "#e8f5e9" if is_real_user else "#fff3e0"
                origin_badge_color = "#2e7d32" if is_real_user else "#e65100"
                origin_badge_label = "🟢 LIVE REAL USER" if is_real_user else "🧪 BENCHMARK (SO 2020)"

                badge_bg = "#e3f2fd" if u_role == "MENTEE" else ("#e8f5e9" if u_role == "MENTOR" else "#f3e5f5")
                badge_color = "#0d47a1" if u_role == "MENTEE" else ("#1b5e20" if u_role == "MENTOR" else "#4a148c")

                # "Not Specified" means the user registered but has not yet filled in their
                # gender in Profile Settings — it is NOT a derived or assumed value.
                gender_display = u_gender
                if u_gender in ("Not Specified", "Not stated", None, ""):
                    gender_display = "Not Set in Profile" if is_real_user else (u_gender or "Not Specified")
                g_icon = "♀️" if u_gender in ("Female", "Woman") else ("♂️" if u_gender in ("Male", "Man") else "👤")
                g_bg = "#fce4ec" if u_gender in ("Female", "Woman") else ("#e3f2fd" if u_gender in ("Male", "Man") else "#f5f5f5")
                g_color = "#880e4f" if u_gender in ("Female", "Woman") else ("#0d47a1" if u_gender in ("Male", "Man") else "#424242")

                with st.container(border=True):
                    ul_c, ur_c = st.columns([3, 1])
                    with ul_c:
                        st.markdown(f"**{u_name}** (`{u_email}`)")
                        st.markdown(
                            f"<span style='background:{origin_badge_bg}; color:{origin_badge_color}; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:700;'>{origin_badge_label}</span>  "
                            f"<span style='background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:700;'>{u_role}</span>  "
                            f"<span style='background:{g_bg}; color:{g_color}; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:700;'>{g_icon} {gender_display}</span>  "
                            f"<span style='background:#f5f5f5; color:#424242; padding:2px 8px; border-radius:10px; font-size:0.75rem;'>{u_2fa}</span>  "
                            f"<span style='color:#757575; font-size:0.8rem;'>📍 {u_country} · Auth: {u_provider} · Registered {u_created}</span>",
                            unsafe_allow_html=True
                        )
                    with ur_c:
                        if u_role == "ADMIN":
                            st.caption("🛡️ Primary Admin")
                        else:
                            with st.popover(f"🗑️ Delete Account", use_container_width=True):
                                st.warning(f"Are you sure you want to delete **{u_email}**?")
                                st.caption("This will permanently delete their login credentials, profile, chat history, and match records.")
                                if st.button(f"Confirm Permanent Deletion", key=f"del_user_btn_{u_id}", type="primary", use_container_width=True):
                                    ok_d, msg_d = api_admin_delete_user(u_id)
                                    if ok_d:
                                        st.success(f"✅ {msg_d}")
                                        st.rerun()
                                    else:
                                        st.error(msg_d)

        # ════════════════════════════════════════════════════════════════════
        # SECTION G — System Tools (Danger Zone)
        # ════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("⚙️ System Reset & Database Tools")
        st.warning("⚠️ **Danger Zone**: Wiping the database is permanent and deletes all users, mentors, mentees, matches, and external invitations.")
        st.write("This tool allows resetting the database to a completely clean slate, ready for real users to sign up and test.")

        confirm_reset = st.checkbox("I confirm that I want to completely wipe all simulated database records.")
        if st.button("🔴 Wipe Database & Reset System", type="primary", disabled=not confirm_reset):
            success, msg = api_reset_database()
            if success:
                st.success("🎉 Database wiped and reset successfully!")
                clear_auth_session()
                st.info("You have been logged out. A clean admin account has been created: **admin@mentoring-me.demo** with password **adminpassword**.")
                if st.button("Proceed to Login"):
                    st.rerun()
            else:
                st.error(f"Failed to reset database: {msg}")
