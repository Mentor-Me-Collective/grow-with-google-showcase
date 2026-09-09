import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'MentorMe-Capstone-App'}
res = requests.get('https://api.github.com/search/users', params={'q': 'python location:United Kingdom', 'per_page': 3}, headers=headers, verify=False, timeout=5)
print('Direct GitHub Search Status:', res.status_code)
if res.status_code == 200:
    print('Found items:', len(res.json().get('items', [])))
    for item in res.json().get('items', []):
        print(' - User:', item.get('login'))
else:
    print('Error text:', res.text[:200])
