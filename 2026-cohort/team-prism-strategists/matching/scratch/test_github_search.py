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

# Query github search
print("Querying /github/search with keyword 'python' and country 'Nigeria'...")
params = {"q": "python", "country": "Nigeria"}
search_res = requests.get(f"{API_URL}/github/search", params=params, headers=headers)
print("Response Status:", search_res.status_code)
if search_res.status_code == 200:
    results = search_res.json()
    print("Found profiles count:", len(results))
    for idx, r in enumerate(results):
        print(f"\nProfile {idx+1}:")
        print("  Name:", r["name"])
        print("  Contact:", r["contact"])
        print("  Tech Focus:", r["tech_focus"])
        print("  Compatibility Match:", r["match_percentage"], "%")
else:
    print("Error:", search_res.text)
