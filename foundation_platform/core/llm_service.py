"""
Phase 24: LLM-Driven Script Understanding.
Uses DeepSeek API to intelligently extract asset requirements from script data.
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "models.json")

def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def extract_assets_via_llm(chapters: List[Dict], characters: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    Uses DeepSeek to intelligently parse script chapters and extract
    ALL asset requirements, including implicit ones.
    
    Returns a list of candidate assets with type, name, description.
    """
    config = _load_config().get("deepseek", {})
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://api.deepseek.com/v1")
    model = config.get("model", "deepseek-chat")
    
    if not api_key:
        return []
    
    # Build a compact summary of the script for the LLM
    script_summary = _build_script_summary(chapters, characters)
    
    system_prompt = """你是一个游戏素材需求分析专家。用户会给你一段视觉小说/互动游戏的剧本摘要。

你的任务是从剧本中提取所有需要制作的游戏素材，包括：
1. **人物立绘** — 每个登场角色都需要。要描述外貌、服装、气质。
2. **场景背景图** — 每个独特场景都需要。要描述环境、光线、氛围。
3. **BGM** — 每种独特氛围的场景都需要。要描述风格、情绪、乐器。

特别注意：
- 不要遗漏对话中**隐含提到**的场景（如"推开沉重的橡木门"暗示需要一个走廊/门厅场景）
- 角色描述要包含视觉特征，适合AI绘画使用
- 场景描述要包含具体的视觉元素和氛围

严格按以下JSON格式回复（不要添加其他内容）：
```json
[
  {"type": "人物立绘", "name": "角色名", "description": "详细外貌描述，适合AI绘画"},
  {"type": "背景图", "name": "场景名", "description": "详细场景描述，适合AI绘画"},
  {"type": "BGM", "name": "音乐名", "description": "风格、情绪、乐器描述"}
]
```"""

    user_prompt = f"以下是剧本摘要，请提取所有素材需求：\n\n{script_summary}"
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[LLM Extractor] API Error: {response.status_code} - {response.text[:200]}")
            return []
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        assets = json.loads(content.strip())
        
        # Add default fields
        for asset in assets:
            asset["selected"] = True
            safe_name = asset["name"].replace(" ", "_").replace("/", "_")
            if asset["type"] == "人物立绘":
                asset["path"] = f"assets/portraits/{safe_name}.png"
            elif asset["type"] == "背景图":
                asset["path"] = f"assets/backgrounds/{safe_name}.png"
            elif asset["type"] == "BGM":
                asset["path"] = f"assets/bgm/{safe_name}.mp3"
            else:
                asset["path"] = f"assets/other/{safe_name}.png"
        
        return assets
        
    except Exception as e:
        print(f"[LLM Extractor] Error: {e}")
        return []


def _build_script_summary(chapters: List[Dict], characters: Optional[List[Dict]] = None) -> str:
    """Build a compact text summary from chapter data for LLM consumption."""
    lines = []
    
    # Character info
    if characters:
        lines.append("【已知角色】")
        for c in characters[:20]:  # Cap at 20
            name = c.get("name", c.get("id", "Unknown"))
            desc = c.get("description", "")
            lines.append(f"- {name}: {desc}")
        lines.append("")
    
    # Chapter summaries (compact: only first 5 nodes per chapter)
    for i, ch in enumerate(chapters[:10]):  # Cap at 10 chapters
        title = ch.get("title", f"第{i+1}章")
        lines.append(f"【{title}】")
        nodes = ch.get("nodes", [])
        for node in nodes[:8]:  # First 8 nodes per chapter
            speaker = node.get("speaker", "")
            text = node.get("text", "")
            bg = node.get("bg", "")
            music = node.get("music", "")
            
            parts = []
            if bg:
                parts.append(f"[场景:{bg}]")
            if music:
                parts.append(f"[BGM:{music}]")
            if speaker and text:
                parts.append(f"{speaker}: {text[:80]}")
            elif text:
                parts.append(text[:80])
            
            if parts:
                lines.append("  " + " ".join(parts))
        
        if len(nodes) > 8:
            lines.append(f"  ... ({len(nodes) - 8} more dialogue nodes)")
        lines.append("")
    
    return "\n".join(lines)


def enhance_prompt_via_llm(asset_type: str, description: str, nar_context: str = "") -> str:
    """
    Uses DeepSeek to enhance a raw asset description into a high-quality
    AI generation prompt (for Stable Diffusion / SDXL).
    """
    config = _load_config().get("deepseek", {})
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://api.deepseek.com/v1")
    model = config.get("model", "deepseek-chat")
    
    if not api_key:
        return description
    
    if asset_type in ["人物立绘", "背景图"]:
        system_prompt = """你是一个AI绘画提示词专家。将用户给出的素材描述转化为高质量的英文Stable Diffusion提示词。

要求：
- 输出纯英文提示词，用逗号分隔
- 包含：主体描述、风格(anime/realistic)、光照、构图、品质词(masterpiece, best quality等)
- 对于人物：描述面部特征、服装、姿态、表情
- 对于场景：描述环境细节、光线、氛围、透视

只输出提示词本身，不要有其他文字。"""
    else:
        return description  # BGM doesn't need SD prompts
    
    context_hint = f"\n叙事上下文参考: {nar_context}" if nar_context else ""
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"素材类型: {asset_type}\n描述: {description}{context_hint}"}
                ],
                "temperature": 0.5,
                "max_tokens": 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            return description
            
    except Exception as e:
        print(f"[LLM Enhance] Error: {e}")
        return description
