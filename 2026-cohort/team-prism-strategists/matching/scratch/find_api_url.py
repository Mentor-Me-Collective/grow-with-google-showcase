with open(r"c:\Users\seuna\Downloads\mentor_me_capstone (1)\mentor_me_capstone\matching\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines[:300]):
    if "api" in line.lower() or "url" in line.lower() or "backend" in line.lower():
        print(f"{idx+1}: {line.strip()}")
