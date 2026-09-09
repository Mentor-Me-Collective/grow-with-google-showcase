import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal
from backend import models
from sqlalchemy import text

db = SessionLocal()
conn = engine.connect()

print("=== ALL MATCHES in DB ===")
matches = db.query(models.Match).all()
print(f"Total matches: {len(matches)}")
for m in matches:
    print(f"  ID={m.id}, mentee_id={m.mentee_id}, mentor_id={m.mentor_id}, status={m.status}")

print()
print("=== REAL (non-demo) USERS ===")
real_users = db.query(models.User).filter(
    ~models.User.email.like('%@mentoring-me.demo%'),
    ~models.User.id.like('user-uuid-%')
).all()
print(f"Total real users: {len(real_users)}")
for u in real_users:
    print(f"  ID={u.id}, email={u.email}, role={u.role}")

print()
print("=== REAL USER IDs (for match cross-check) ===")
real_u_ids = {u.id for u in real_users}
print(f"Real user IDs: {real_u_ids}")

print()
print("=== MATCHES INVOLVING REAL USERS ===")
for m in matches:
    if m.mentee_id in real_u_ids or m.mentor_id in real_u_ids:
        print(f"  Match {m.id}: mentee={m.mentee_id} mentor={m.mentor_id} status={m.status}")
