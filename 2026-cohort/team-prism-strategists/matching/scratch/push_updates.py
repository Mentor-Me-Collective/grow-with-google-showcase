import subprocess
import os

git_bin = r"C:\Users\seuna\AppData\Local\GitHubDesktop\app-3.6.4\resources\app\git\cmd\git.exe"
repo_dir = r"c:\Users\seuna\Downloads\mentor_me_capstone (1)\mentor_me_capstone"

print("Staging files...")
subprocess.run([git_bin, "add", "."], cwd=repo_dir)

print("Committing...")
res_commit = subprocess.run([git_bin, "commit", "-m", "fix: exclude PROPOSED matches from admin Live scope count; clarify gender 'Not Set in Profile' label for real users"], cwd=repo_dir, capture_output=True, text=True)
print(res_commit.stdout or res_commit.stderr)

print("Pushing to origin main...")
res_push = subprocess.run([git_bin, "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
print(res_push.stdout or res_push.stderr)

print("Done!")
