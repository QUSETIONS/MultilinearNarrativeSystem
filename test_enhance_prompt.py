import asyncio
from foundation_platform.core.llm_service import enhance_prompt_via_llm

desc_character = "全身，神情恐慌，穿着黑色的哥特式长裙，戴着面纱，站在昏暗的行李车厢中，光线勾勒出隐约的身影。"
desc_bg = "华丽装潢的火车头等车厢，有柔软的沙发，黄铜台灯散发出温暖的光芒。带有明亮的氛围。全局光照，色彩饱和度对比强烈。"

prompt_char = enhance_prompt_via_llm("人物立绘", desc_character)
prompt_bg = enhance_prompt_via_llm("背景图", desc_bg)

print("--- Translated Prompts ---")
print("CHARACTER:")
print(prompt_char)
print("\nBACKGROUND:")
print(prompt_bg)
