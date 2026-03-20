import requests
import time
import json

API_BASE = "http://localhost:8088"

def test_observability():
    print("--- 1. Testing Global Config Update ---")
    config_payload = {
        "theme": "Dark Art Deco Mystery",
        "era": "1934 Winter"
    }
    resp = requests.post(f"{API_BASE}/narrative/config", json=config_payload)
    print(f"Update Config: {resp.status_code} - {resp.json()}")

    print("\n--- 2. Triggering Observability-Enabled Generation ---")
    gen_payload = {
        "asset_path": "assets/backgrounds/train_dining_car.png",
        "description": "Dining car with luxurious wooden panels and snow outside",
        "asset_type": "背景图",
        "provider": "mock",
        "entropy": 0.7,
        "relationships": {
            "speaker": "Poirot",
            "listener": "Countess",
            "graph": {}
        },
        "refinement_passes": 3
    }
    resp = requests.post(f"{API_BASE}/generate", json=gen_payload)
    print(f"Generate Request: {resp.status_code} - {resp.json()}")

    print("\n--- 3. Polling Status for Telemetry (Attention & Snapshots) ---")
    for _ in range(5):
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/status")
        data = resp.json()
        
        target = next((d for d in data["details"] if d["path"] == gen_payload["asset_path"]), None)
        if target:
            print(f"Status: {target['task_status']}")
            if "attention" in target:
                print(f"Structured Attention: {json.dumps(target['attention'], indent=2)}")
            if "snapshots" in target and target["snapshots"]:
                print(f"Refinement Snapshots found: {len(target['snapshots'])} passes")
                for snap in target["snapshots"]:
                    print(f"  [Pass {snap['pass']}] {snap['critique'][:50]}...")
            
            if target["task_status"] == "COMPLETED":
                print("\nSUCCESS: Observability data captured successfully!")
                return
    
    print("\nFAILED: Observability data not captured in time.")

if __name__ == "__main__":
    test_observability()
