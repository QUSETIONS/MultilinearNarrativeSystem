import requests
import concurrent.futures
import time
import json
import random
import uuid

BASE_URL = "http://localhost:8095"

def register_bulk_assets(n=50):
    """Scenario 1: Bulk registration from text outline."""
    print(f"[Phase 1] Registering {n} assets...")
    outline = "\n".join([f"角色：测试人_{i} (特征: {uuid.uuid4().hex[:8]})" for i in range(n)])
    resp = requests.post(f"{BASE_URL}/assets/register", json={"outline": outline})
    return resp.status_code

def feedback_flood(n=100):
    """Scenario 2: Concurrent feedback writes."""
    print(f"[Phase 2] Flooding {n} feedback requests...")
    def send_one_feedback():
        data = {
            "asset_path": f"chars/stress/test_{random.randint(0, 50)}.png",
            "status": random.choice(["LIKED", "DISLIKED"]),
            "reason": f"Stress Test Feedback {uuid.uuid4().hex[:8]}",
            "prompt": "Test Prompt",
            "context": {}
        }
        return requests.post(f"{BASE_URL}/narrative/feedback", json=data).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: send_one_feedback(), range(n)))
    
    success_rate = results.count(200) / n
    return success_rate

def generate_parallel(n=20):
    """Scenario 3: Parallel heavy generation with high recursion."""
    print(f"[Phase 3] Running {n} parallel generations (passes=5)...")
    def trigger_gen(i):
        data = {
            "asset_path": f"chars/stress/gen_{i}.png",
            "description": f"Complexity test for NAR Level 2 and 3. ID={i}",
            "asset_type": "人物立绘",
            "provider": "mock",
            "refinement_passes": 5
        }
        start = time.time()
        requests.post(f"{BASE_URL}/generate", json=data)
        return time.time() - start

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        latencies = list(executor.map(trigger_gen, range(n)))
    
    avg_latency = sum(latencies) / n
    return avg_latency

def audit_nar_retrieval():
    """Scenario 4: Verify NAR consistency post-load."""
    print("[Phase 4] Auditing NAR retrieval status...")
    resp = requests.get(f"{BASE_URL}/status")
    data = resp.json()
    
    completed_tasks = [d for d in data['details'] if d.get('task_status') == "COMPLETED"]
    nar_hits = sum(1 for d in completed_tasks if any("NAR" in l for l in d.get('logs', [])))
    
    return len(completed_tasks), nar_hits

def run_deep_audit():
    print("=" * 60)
    print("DEEP PRODUCTION AUDIT: FOUNDATION PLATFORM v6.1 [NAR]")
    print("=" * 60)
    
    start_total = time.time()
    
    # 1. Registration
    reg_status = register_bulk_assets(50)
    print(f"Registration Result: {reg_status}")
    
    # 2. Feedback Flood
    fb_success = feedback_flood(100)
    print(f"Feedback Success Rate: {fb_success * 100:.1f}%")
    
    # 3. Parallel Generation
    avg_gen_lat = generate_parallel(20)
    print(f"Average Generation Start Latency: {avg_gen_lat:.3f}s")
    
    # 5s wait for background tasks
    print("Waiting for background processes to settle...")
    time.sleep(10)
    
    # 4. Audit
    total_comp, nar_hits = audit_nar_retrieval()
    print(f"Audit Summary: {total_comp} tasks completed, {nar_hits} used NAR retrieval.")
    
    total_time = time.time() - start_total
    print("=" * 60)
    print(f"AUDIT COMPLETE in {total_time:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    run_deep_audit()
