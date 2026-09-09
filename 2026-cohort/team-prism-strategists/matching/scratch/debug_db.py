import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, DATABASE_URL
from sqlalchemy import text

print("Database URL:", DATABASE_URL)
conn = engine.connect()

print("\n=== ALL USERS (email, role) ===")
all_u = conn.execute(text("SELECT id, email, role FROM users")).fetchall()
print(f"Total users: {len(all_u)}")
for r in all_u:
    print(f"  {r}")

print("\n=== REAL (non-demo) USERS ===")
real_u = [r for r in all_u if "@mentoring-me.demo" not in r[1]]
print(f"Total real users: {len(real_u)}")
for r in real_u:
    print(f"  {r}")

print("\n=== ALL MATCHES ===")
matches = conn.execute(text("SELECT id, mentee_id, mentor_id, status FROM matches")).fetchall()
print(f"Total matches: {len(matches)}")
for m in matches:
    print(f"  {m}")

print("\n=== MATCH REQUESTS ===")
try:
    reqs = conn.execute(text("SELECT id, mentee_id, mentor_id, status FROM match_requests LIMIT 10")).fetchall()
    print(f"Total match_requests: {len(reqs)}")
    for r in reqs:
        print(f"  {r}")
except Exception as e:
    print(f"No match_requests table: {e}")
