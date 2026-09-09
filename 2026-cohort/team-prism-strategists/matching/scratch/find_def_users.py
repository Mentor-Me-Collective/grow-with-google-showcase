with open(r"c:\Users\seuna\Downloads\mentor_me_capstone (1)\mentor_me_capstone\matching\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def api_admin_get_users" in line or "def api_get_match_history" in line:
        print(f"Line {idx+1}: {line.strip()}")
        for k in range(idx, min(idx+25, len(lines))):
            print(f"  {k+1}: {lines[k].strip()}")
