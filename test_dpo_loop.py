import requests
import time
import json

BASE_URL = "http://localhost:8088"
ASSET_PATH = "assets/backgrounds/station_night.png"

print("--- 1. Submitting DPO Feedback (DISLIKED) ---")
fb_payload = {
    "asset_path": ASSET_PATH,
    "status": "DISLIKED",
    "reason": "Too much modern lighting, needs more steam and shadows",
    "prompt": "Initial prompt from yesterday",
    "context": {"type": "背景图", "description": "night station"}
}
res = requests.post(f"{BASE_URL}/narrative/feedback", json=fb_payload)
print(f"Feedback Response: {res.json()}")

print("\n--- 2. Triggering Smart Generation ---")
gen_payload = {
    "asset_path": ASSET_PATH,
    "description": "night station with train arriving",
    "asset_type": "背景图",
    "provider": "mock",
    "entropy": 0.5,
    "refinement_passes": 1
}
res = requests.post(f"{BASE_URL}/generate", json=gen_payload)
print(f"Generate Request Response: {res.json()}")

print("\n--- 3. Polling for Completion and reading /status ---")
time.sleep(4) # wait for generation loop (1s + 2s + 0.5s)

res = requests.get(f"{BASE_URL}/status")
data = res.json()
asset_details = [d for d in data.get('details', []) if d['path'] == ASSET_PATH][0]

print("\n--- 4. Verification Results ---")
print(f"Task Status: {asset_details.get('task_status')}")
print(f"Last Prompt Extracted:\n{asset_details.get('last_prompt')}\n")
print(f"Global Attention Focus (Should have penalty applied! <1.1 Era weight):")
print(asset_details.get('attention', {}).get('global', []))
