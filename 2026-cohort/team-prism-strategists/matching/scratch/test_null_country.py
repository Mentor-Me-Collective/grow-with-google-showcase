import requests

API_URL = "http://127.0.0.1:8000/api/v1"

# Login as seeded mentee to get access token
login_data = {
    "username": "ally_seeking_mentee@example.com",
    "password": "password123"
}
res = requests.post(f"{API_URL}/auth/token", data=login_data)
if res.status_code != 200:
    print("Login Failed:", res.status_code, res.text)
    exit(1)

token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# First update country to None (which corresponds to 'Any')
print("Updating target_mentor_country to None (Any)...")
update_data = {
    "target_mentor_country": None,
    "target_mentor_expertise": "Python, Go"
}
update_res = requests.put(f"{API_URL}/profile", json=update_data, headers=headers)
print("Update profile status:", update_res.status_code)

# Fetch user profile to verify
me_res = requests.get(f"{API_URL}/users/me", headers=headers)
print("Fetch user status:", me_res.status_code)
if me_res.status_code == 200:
    profile = me_res.json()
    print("Saved target_mentor_country:", profile["target_mentor_country"])
    if profile["target_mentor_country"] is None:
        print("PASS: Null country preference successfully persisted in database!")
    else:
        print("FAIL: target_mentor_country was not updated to None!")
else:
    print("Error:", me_res.text)
