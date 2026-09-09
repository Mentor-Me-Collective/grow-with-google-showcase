import requests

base = 'http://127.0.0.1:8000/api/v1'

# 1. Sign up a fresh mentee
email = 'diag_test_user_400@example.com'
pwd = 'Password123!'
signup_payload = {
    'email': email,
    'password': pwd,
    'role': 'MENTEE'
}
r_signup = requests.post(f'{base}/auth/signup', json=signup_payload)
print('Signup status:', r_signup.status_code)

# 2. Login
r_login = requests.post(f'{base}/auth/token', data={'username': email, 'password': pwd})
login_data = r_login.json()

if login_data.get('two_factor_required'):
    # Complete 2FA
    challenge_token = login_data['challenge_token']
    otp_code = login_data['otp_code_preview']
    r_2fa = requests.post(f'{base}/auth/2fa/verify', json={'challenge_token': challenge_token, 'code': otp_code})
    token = r_2fa.json().get('access_token')
else:
    token = login_data.get('access_token')

print('Access Token acquired:', bool(token))
headers = {'Authorization': f'Bearer {token}'}

# 3. Create mentee profile
prof_data = {
    'name': 'Diagnostic Ada',
    'country': 'United Kingdom',
    'dev_type': 'Developer, full-stack;Developer, back-end',
    'years_code_pro': 3,
    'job_factors': 'Diversity of the company;Opportunities for development'
}
requests.put(f'{base}/users/profile/mentee', json=prof_data, headers=headers)

print('\n======================================================')
print('=== 1. TESTING GITHUB OUTREACH API ===')
print('======================================================')
r_gh = requests.get(f'{base}/github/search', params={'q': 'python cloud', 'country': 'United Kingdom'}, headers=headers, timeout=15)
print('GitHub Status:', r_gh.status_code)
gh_data = r_gh.json()
print(f'GitHub Candidates Found: {len(gh_data)}')
for i, c in enumerate(gh_data[:3], 1):
    print(f"  {i}. {c.get('name')} ({c.get('company', 'Independent')}) - Country: {c.get('country')} - Tech: {c.get('tech_focus')} - Match: {c.get('match_score')}%")

print('\n======================================================')
print('=== 2. TESTING ORCID ACADEMIC OUTREACH API ===')
print('======================================================')
r_or = requests.get(f'{base}/orcid/search', params={'q': 'machine learning', 'country': 'United Kingdom'}, headers=headers, timeout=15)
print('ORCID Status:', r_or.status_code)
or_data = r_or.json()
print(f'ORCID Researchers Found: {len(or_data)}')
for i, c in enumerate(or_data[:3], 1):
    print(f"  {i}. {c.get('name')} - Org: {c.get('institution')} - Focus: {c.get('tech_focus')} - Match: {c.get('match_score')}%")

print('\n======================================================')
print('=== 3. TESTING LINKEDIN SEARCH & DEEP LINK API ===')
print('======================================================')
r_li = requests.get(f'{base}/linkedin/search', params={'q': 'data science', 'country': 'United Kingdom'}, headers=headers, timeout=15)
print('LinkedIn Directory Status:', r_li.status_code)
li_data = r_li.json()
print(f'LinkedIn Candidates Found: {len(li_data)}')
for i, c in enumerate(li_data[:3], 1):
    print(f"  {i}. {c.get('name')} ({c.get('current_company')}) - Headline: {c.get('headline')} - Match: {c.get('match_score')}%")

r_dl = requests.get(f'{base}/linkedin/deep-link', headers=headers, timeout=15)
print('\nLinkedIn Deep Link Status:', r_dl.status_code)
dl_data = r_dl.json()
print('Generated 1-Click Search URL:', dl_data.get('deep_link_url'))
print(f"Connection Note Template (Length: {len(dl_data.get('outreach_templates', {}).get('connection_note', ''))} chars):")
print(f"  \"{dl_data.get('outreach_templates', {}).get('connection_note')}\"")
