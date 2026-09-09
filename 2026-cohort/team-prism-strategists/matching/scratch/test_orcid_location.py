"""
Live E2E test for ORCID search + location matching correctness.
Tests:
  1. Search with a specific country preference → should show country-based score
  2. Search with Any location (no country) → should return results with "Open Location" justification
"""
import requests, time

API = "http://127.0.0.1:8000/api/v1"
time.sleep(1)  # Give server a moment

# Login
res = requests.post(f"{API}/auth/token", data={"username": "ally_seeking_mentee@example.com", "password": "password123"})
assert res.status_code == 200, f"Login failed: {res.text}"
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# --- Test 1: Search with country = Nigeria ---
print("Test 1: Setting country preference to Nigeria...")
requests.put(f"{API}/profile", json={"target_mentor_expertise": "Python", "target_mentor_country": "Nigeria"}, headers=headers)
r = requests.get(f"{API}/orcid/search", params={"q": "Python", "country": "Nigeria"}, headers=headers)
print("  Status:", r.status_code, "| Results count:", len(r.json()))
for c in r.json():
    print(f"  → {c['name']} | Country: {c['country']} | Match: {c['match_percentage']}%")
    for j in c['justifications']:
        if 'Location' in j or 'location' in j:
            print(f"     {j[:100]}")

# --- Test 2: Search with Any country ---
print("\nTest 2: Setting country preference to None (Any)...")
requests.put(f"{API}/profile", json={"target_mentor_expertise": "Python", "target_mentor_country": None}, headers=headers)
r = requests.get(f"{API}/orcid/search", params={"q": "Python"}, headers=headers)
print("  Status:", r.status_code, "| Results count:", len(r.json()))
for c in r.json():
    print(f"  -> {c['name']} | Country: {c['country']} | Match: {c['match_percentage']}%")
    for j in c['justifications']:
        if 'Location' in j or 'location' in j or 'Open' in j:
            print(f"     {j[:110]}")

print("\nDone.")
