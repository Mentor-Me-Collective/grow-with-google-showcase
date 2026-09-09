import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

query = 'biography:"FastAPI, DevOps, Python" OR keyword:"FastAPI, DevOps, Python"'
r = requests.get('https://pub.orcid.org/v3.0/search', params={'q': query}, headers={'Accept': 'application/json'}, verify=False)
print("Status Code:", r.status_code)
if r.status_code == 200:
    results = r.json().get('result', [])
    print("Found count:", len(results))
else:
    print("Error:", r.text)
