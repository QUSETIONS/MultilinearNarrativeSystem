import asyncio
from foundation_platform.core.llm_service import extract_assets_via_llm
import sys

# Sample story spanning multiple events to ensure tail is not truncated
story = """
第一章 启程
风雪交加的火车站站台，气氛凝重。
福尔摩斯穿着厚重的长款大衣，戴着猎鹿帽，表情严肃地站在月台上。
华生急忙赶来，提着沉重的公文包，看起来十分疲惫。
场景转移到了火车温暖的头等车厢内部。华丽的装饰，柔软的沙发，黄铜台灯散发着光芒。
这里需要一首悠扬轻松的古典音乐。

第二章 惊魂
深夜，走廊门厅一片漆黑。推开沉重的橡木门，里面是一间杂乱的行李车厢。
行李车厢里散落着各种箱包，光线昏暗只有月光透进来。
神秘女子穿着黑色的哥特式长裙，戴着面纱，眼神中透出一丝恐慌。
此时播放一首悬疑紧张的弦乐。

第三章 终局
清晨的雪原上，阳光刺眼。
一望无际的雪地，只留下两串脚印。火车停在远处的风雪中。
大反派穿着白色的军装，冷静地站在雪地中央。
这里播放一首史诗般的交响乐。
"""

# The frontend pseudo-parser wraps it in a single chapter with a node for each line
lines = [line.strip() for line in story.strip().split("\n") if line.strip()]
chapters = [{
    "name": "Imported Chapter",
    "nodes": [{"id": f"node_{i}", "line": line, "text": line} for i, line in enumerate(lines)]
}]

print("Extracting from " + str(len(chapters[0]["nodes"])) + " nodes...")
assets = extract_assets_via_llm(chapters, None)

print("\n--- Extracted Assets ---")
for a in assets:
    print(f"[{a.get('type')}] {a.get('name')}: {a.get('description')}")
