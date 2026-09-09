import os
import subprocess
import glob

def find_git():
    possible_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ]
    # Check GitHub Desktop embedded git
    gh_desktop_paths = glob.glob(r"C:\Users\seuna\AppData\Local\GitHubDesktop\app-*\resources\app\git\cmd\git.exe")
    possible_paths.extend(gh_desktop_paths)
    
    # Check PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "git.exe")
        if os.path.exists(candidate):
            return candidate
            
    for candidate in possible_paths:
        if os.path.exists(candidate):
            return candidate
            
    return None

git_bin = find_git()
print(f"Git executable found: {git_bin}")

if git_bin:
    repo_dir = r"c:\Users\seuna\Downloads\mentor_me_capstone (1)\mentor_me_capstone"
    
    print("\n--- GIT STATUS ---")
    status_out = subprocess.run([git_bin, "status"], cwd=repo_dir, capture_output=True, text=True)
    print(status_out.stdout or status_out.stderr)
    
    print("\n--- RECENT COMMITS ---")
    log_out = subprocess.run([git_bin, "log", "-n", "5", "--oneline"], cwd=repo_dir, capture_output=True, text=True)
    print(log_out.stdout or log_out.stderr)
    
    print("\n--- UNPUSHED COMMITS (git status -sb) ---")
    branch_out = subprocess.run([git_bin, "status", "-sb"], cwd=repo_dir, capture_output=True, text=True)
    print(branch_out.stdout or branch_out.stderr)
else:
    print("Could not locate git.exe automatically.")
