import requests, json, os

headers = {
  'x-rapidapi-host': 'twitter-v24.p.rapidapi.com',
  'x-rapidapi-key': os.environ.get('RAPIDAPI_KEY')
}
r = requests.get('https://twitter-v24.p.rapidapi.com/search/', headers=headers, params={'query': 'ai', 'section': 'top', 'limit': 5})
print('STATUS:', r.status_code)
d = r.json()
print('TOP KEYS:', list(d.keys()))
print(json.dumps(d, indent=2)[:3000])
