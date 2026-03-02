"""
GitHub Actions script — fetches all Strava runs and writes runs.json
Reads credentials from environment variables (set as GitHub secrets)
"""
import os, json, requests, time

CLIENT_ID     = os.environ['STRAVA_CLIENT_ID']
CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']

# Refresh access token
r = requests.post('https://www.strava.com/oauth/token', data={
    'client_id':     CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type':    'refresh_token',
    'refresh_token': REFRESH_TOKEN,
})
token_data = r.json()
access_token = token_data['access_token']

# Also update the refresh token if it changed (Strava rotates them)
# Write new refresh token back to a file so the next run uses it
# (In Actions we use the secret directly — rotation handled via secret update)
print(f"Token refreshed OK, expires in {token_data['expires_in']}s")

headers = {'Authorization': f'Bearer {access_token}'}

# Fetch all running activities (paginate)
all_runs = []
page = 1
while True:
    resp = requests.get(
        'https://www.strava.com/api/v3/athlete/activities',
        headers=headers,
        params={'per_page': 100, 'page': page}
    )
    batch = resp.json()
    if not batch:
        break
    runs = [a for a in batch if a.get('type') == 'Run' or a.get('sport_type') == 'Run']
    all_runs.extend(runs)
    print(f"Page {page}: {len(runs)} runs (total: {len(all_runs)})")
    page += 1
    time.sleep(0.3)

# Extract fields we need for the dashboard
out = []
for a in all_runs:
    out.append({
        'date':        a['start_date_local'][:10],
        'km':          round(a['distance'] / 1000, 2),
        'moving_time': a['moving_time'],
        'name':        a['name'],
        'avg_hr':      a.get('average_heartrate'),
        'max_hr':      a.get('max_heartrate'),
    })

out.sort(key=lambda x: x['date'])
print(f"\nTotal runs: {len(out)}")
print(f"With HR: {sum(1 for r in out if r['avg_hr'])}")

with open('runs.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=True)

print("runs.json written")
