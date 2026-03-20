import requests
import json
import time

API_URL = "http://localhost:8088"

def test_social_recursive_gen():
    payload = {
        "asset_path": "assets/portraits/poirot.png",
        "description": "Hercule Poirot looks suspiciously at the countess.",
        "asset_type": "人物立绘",
        "provider": "mock",
        "entropy": 0.8,
        "relationships": {
            "speaker": "Poirot",
            "listener": "Countess",
            "graph": {
                "Poirot": {
                    "Countess": {"trust": -0.8, "tension": 0.9, "hierarchy": 0.6}
                }
            }
        },
        "refinement_passes": 3
    }

    print("--- Sending Social+Recursive Generation Request ---")
    res = requests.post(f"{API_URL}/generate", json=payload)
    print(res.json())

    # Poll for status
    path = payload["asset_path"]
    for _ in range(10):
        time.sleep(2)
        status_res = requests.get(f"{API_URL}/status")
        data = status_res.json()
        
        target = next((d for d in data["details"] if d["path"] == path), None)
        if target:
            print(f"Status: {target['task_status']}")
            for log in target["logs"]:
                print(f" LOG: {log}")
            if target["task_status"] == "COMPLETED":
                print("SUCCESS!")
                break
        else:
            print("Asset not found in status yet...")

if __name__ == "__main__":
    test_social_recursive_gen()
