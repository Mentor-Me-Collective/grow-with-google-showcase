import sqlite3
conn = sqlite3.connect('mentor_me.db')
c = conn.cursor()
c.execute("SELECT email, target_mentor_country FROM users JOIN mentees ON users.id = mentees.id LIMIT 5")
for r in c.fetchall():
    print(f"User: {r[0]}, Target Country: {r[1]}")
conn.close()
