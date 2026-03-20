import requests
import json

res = requests.get('http://localhost:8088/status')
data = res.json()
types = set(d['type'] for d in data['details'])
print(f"Full status details types: {types}")
print(f"Summary keys: {data['summary'].keys()}")
