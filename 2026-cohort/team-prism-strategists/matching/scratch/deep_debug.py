"""
Deep diagnostic: Dump all users (with match count) and matches from the database
to understand exactly what the admin dashboard would see.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, DATABASE_URL, SessionLocal
from backend import models
from sqlalchemy import text

print(f"Database: {DATABASE_URL}\n")

db = SessionLocal()
conn = engine.connect()

# All users
all_users = conn.execute(text("SELECT id, email, role FROM users")).fetchall()
print(f"Total users in DB: {len(all_users)}")

# Identify demo vs real
demo_users = [u for u in all_users if u[1].endswith('@mentoring-me.demo') or u[1].endswith('@mentorme.demo') or u[0].startswith('user-uuid-')]
real_users  = [u for u in all_users if u not in demo_users]
print(f"  Demo users: {len(demo_users)}")
print(f"  Real users: {len(real_users)}")
if real_users:
    for u in real_users:
        print(f"    {u}")

# Admin users
admin_users = [u for u in all_users if u[2] == 'ADMIN']
print(f"\nAdmin users: {len(admin_users)}")
for u in admin_users:
    print(f"  {u}")
    is_demo = u[1].endswith('@mentoring-me.demo') or u[1].endswith('@mentorme.demo') or u[0].startswith('user-uuid-')
    print(f"    → _is_demo_usr: {is_demo}")
    print(f"    → Would be in real_u_ids: {not is_demo}")

# All matches
matches = conn.execute(text("SELECT id, mentee_id, mentor_id, status FROM matches")).fetchall()
print(f"\nTotal matches in DB: {len(matches)}")
for m in matches:
    print(f"  {m}")

# Check match IDs that could pass _is_real_mtch filters
print("\n--- Simulating _is_real_mtch for each match ---")
real_u_ids_set = {str(u[0]) for u in real_users}
real_u_emails_set = {u[1].lower() for u in real_users}

print(f"real_u_ids: {real_u_ids_set}")
print(f"real_u_emails: {real_u_emails_set}")

for m in matches:
    m_id = str(m[0])
    m_eid = str(m[1])
    r_eid = str(m[2])
    
    # Get emails
    mentee_user = conn.execute(text(f"SELECT email FROM users WHERE id='{m[1]}'")).fetchone()
    mentor_user = conn.execute(text(f"SELECT email FROM users WHERE id='{m[2]}'")).fetchone()
    m_em = (mentee_user[0] if mentee_user else '').lower()
    r_em = (mentor_user[0] if mentor_user else '').lower()
    
    fails = []
    if m_id.startswith('match_') or m_id.startswith('mtch_demo_') or m_id.startswith('user-uuid-'):
        fails.append(f"id starts with demo prefix")
    if m_em.endswith('@mentoring-me.demo') or r_em.endswith('@mentoring-me.demo') or m_em.endswith('@mentorme.demo') or r_em.endswith('@mentorme.demo'):
        fails.append(f"email ends with demo suffix (mentee: {m_em}, mentor: {r_em})")
    if m_eid.startswith('user-uuid-') or r_eid.startswith('user-uuid-'):
        fails.append(f"user_id starts with user-uuid-")
    
    is_mentee_real = (m_eid in real_u_ids_set) or (m_em in real_u_emails_set)
    is_mentor_real = (r_eid in real_u_ids_set) or (r_em in real_u_emails_set)
    passes = not fails and is_mentee_real and is_mentor_real
    
    print(f"\nMatch {m_id}: mentee={m_eid}, mentor={r_eid}")
    print(f"  Mentee email: {m_em}, Mentor email: {r_em}")
    print(f"  is_mentee_real: {is_mentee_real}, is_mentor_real: {is_mentor_real}")
    print(f"  Filter failures: {fails}")
    print(f"  → _is_real_mtch: {passes}")
