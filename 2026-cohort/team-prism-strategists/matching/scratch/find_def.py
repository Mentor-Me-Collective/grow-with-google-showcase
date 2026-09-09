with open(r"c:\Users\seuna\Downloads\mentor_me_capstone (1)\mentor_me_capstone\matching\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def generate_capstone_executive_report" in line:
        print(f"Found at line {idx+1}: {line.strip()}")
        for k in range(idx, min(idx+60, len(lines))):
            print(f"{k+1}: {lines[k].strip()}")
        break
