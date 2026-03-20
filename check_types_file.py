import requests
import json

res = requests.get('http://localhost:8088/status')
data = res.json()
types = list(set(d['type'] for d in data['details']))
with open('d:/Desktop/workk/types_out.json', 'w', encoding='utf-8') as f:
    json.dump(types, f, ensure_ascii=False)
