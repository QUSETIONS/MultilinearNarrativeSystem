import requests
import json
import sys

# Ensure UTF-8 output if possible, but handle GBK safely
API_URL = "http://localhost:8088"
path = "assets/portraits/countess.png"

def get_proof():
    try:
        res = requests.get(f"{API_URL}/status")
        data = res.json()
        target = next((d for d in data["details"] if d["path"] == path), None)
        
        if target:
            print(f"Asset: {path}")
            print(f"Status: {target['task_status']}")
            print("--- Recursive Refining Logs ---")
            for log in target["logs"]:
                # Print only ASCII or hex to avoid GBK issues if necessary
                # But here we just want to see it.
                try:
                    print(log)
                except UnicodeEncodeError:
                    print(log.encode('ascii', 'ignore').decode('ascii'))
        else:
            print(f"Asset {path} not found in status.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_proof()
