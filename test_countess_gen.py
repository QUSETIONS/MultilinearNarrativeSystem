import requests
import json
import time

# Current API is active on 8088
API_URL = "http://localhost:8088"

def run_test_case():
    payload = {
        "asset_path": "assets/portraits/countess.png",
        "description": "The Countess looks elegant but visibly nervous as she holds a lace handkerchief.",
        "asset_type": "人物立绘",
        "provider": "mock",
        "entropy": 0.9,
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

    print(f"--- 启动实测：{payload['asset_path']} ---")
    print(f"人物关系：{payload['relationships']['speaker']} -> {payload['relationships']['listener']}")
    
    res = requests.post(f"{API_URL}/generate", json=payload)
    print(f"API 响应: {res.json()}")

    # 轮询状态
    path = payload["asset_path"]
    print("正在等待 AI 递归打磨完成...")
    for _ in range(15):
        time.sleep(2)
        try:
            status_res = requests.get(f"{API_URL}/status")
            data = status_res.json()
            
            target = next((d for d in data["details"] if d["path"] == path), None)
            if target:
                if target['task_status'] == "COMPLETED":
                    print("\n✅ 生成任务成功完成！")
                    print("--- 最终提示词日志 (提示词已注入社交权重与递归修正) ---")
                    for log in target["logs"]:
                        if "Refined Prompt" in log:
                            print(f"\n{log}")
                        else:
                            print(f" LOG: {log}")
                    break
                elif target['task_status'].startswith("ERROR"):
                    print(f"❌ 任务出错: {target['task_status']}")
                    break
                else:
                    print(f"状态: {target['task_status']}...", end="\r")
        except Exception as e:
            print(f"查询失败: {e}")

if __name__ == "__main__":
    run_test_case()
