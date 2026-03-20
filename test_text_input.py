import requests
import time

BASE_URL = "http://localhost:8089"

print("=" * 60)
print("Phase 13 验证：纯文字输入 → 素材生成")
print("=" * 60)

# 1. 先确认初始状态是空的
print("\n--- 1. 检查初始 /status（应为空） ---")
res = requests.get(f"{BASE_URL}/status")
data = res.json()
print(f"初始素材数量: {data['summary']['total']}")
assert data['summary']['total'] == 0, "初始应该是空的！"
print("✅ 初始状态正确：0 个素材")

# 2. 提交纯文字大纲
print("\n--- 2. 提交文字大纲 POST /assets/register ---")
outline = """角色：波洛（灰色胡须的比利时侦探）、公主（高贵的俄国老妇人）、布克（列车公司经理）
场景：车站夜景（寒冷刺骨，蒸汽弥漫的1930年代）、餐车（温暖的灯光，华丽装饰）、包厢（狭小私密，暗红色调）
BGM：紧张悬疑（弦乐为主，低频不安）、优雅华尔兹（钢琴主旋律）"""

res = requests.post(f"{BASE_URL}/assets/register", json={"outline": outline})
data = res.json()
print(f"注册结果: {data['message']}")
print(f"已注册素材总数: {data['total_registered']}")
for a in data['assets']:
    print(f"  [{a['type']}] {a['name']} → {a['path']}")
assert len(data['assets']) == 8, f"应该提取 8 个素材，实际 {len(data['assets'])}"
print("✅ 大纲解析正确：8 个素材")

# 3. 验证 /status 现在有数据了
print("\n--- 3. 验证 /status 返回已注册素材 ---")
res = requests.get(f"{BASE_URL}/status")
data = res.json()
print(f"素材总数: {data['summary']['total']}")
print(f"已存在: {data['summary']['found']}, 缺失: {data['summary']['missing']}")
assert data['summary']['total'] == 8
print("✅ /status 正确返回 8 个素材")

# 4. 验证 Attention 引擎已注册资产
print("\n--- 4. 测试 Attention 对已注册素材的响应 ---")
# 找到波洛的素材路径
poirot_detail = [d for d in data['details'] if '波洛' in d['path']][0]
print(f"波洛的 attention tokens: {poirot_detail['attention_flat']}")
# 应该包含注册时的描述
has_desc = any('灰色胡须' in t for t in poirot_detail['attention_flat'])
has_canonical = any('CHARACTER' in t for t in poirot_detail['attention_flat'])
print(f"  包含描述权重: {has_desc}")
print(f"  包含角色一致性标签: {has_canonical}")
assert has_desc or has_canonical, "Attention 应该包含注册的实体信息"
print("✅ Attention 引擎正确响应已注册素材")

# 5. 尝试生成一个素材
print("\n--- 5. 触发生成 (Mock) ---")
res = requests.post(f"{BASE_URL}/generate", json={
    "asset_path": poirot_detail['path'],
    "description": poirot_detail['description'],
    "asset_type": poirot_detail['type'],
    "provider": "mock",
    "entropy": 0.7
})
print(f"生成请求: {res.json()}")

time.sleep(5)

res = requests.get(f"{BASE_URL}/status")
data = res.json()
poirot_after = [d for d in data['details'] if '波洛' in d['path']][0]
print(f"生成后状态: {poirot_after['task_status']}")
print(f"生成后 Prompt: {poirot_after['last_prompt'][:80]}...")
assert poirot_after['task_status'] == 'COMPLETED'
print("✅ 生成成功完成")

print("\n" + "=" * 60)
print("Phase 13 验证全部通过 ✅")
print("素材平台已完全脱离 JSON，纯文字输入工作正常。")
print("=" * 60)
