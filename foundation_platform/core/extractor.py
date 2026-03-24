import os
import re
from typing import List, Dict, Optional


class AssetExtractor:
    """
    素材需求提取器。
    从纯文字大纲中提取结构化的素材需求列表。
    
    输入格式（文字大纲）：
        角色：波洛（灰色胡须的比利时侦探）、公主（高贵的俄国老妇人）
        场景：车站夜景（寒冷，蒸汽弥漫）、餐车（温暖的灯光，华丽装饰）
        BGM：紧张悬疑（弦乐为主）、优雅华尔兹（钢琴）
    
    输出：结构化素材需求列表
    """

    # 类别 → (素材类型, 资产子目录, 文件扩展名)
    CATEGORY_MAP = {
        "角色":  ("人物立绘", "assets/portraits",    ".png"),
        "人物":  ("人物立绘", "assets/portraits",    ".png"),
        "立绘":  ("人物立绘", "assets/portraits",    ".png"),
        "场景":  ("背景图",   "assets/backgrounds",  ".png"),
        "背景":  ("背景图",   "assets/backgrounds",  ".png"),
        "BGM":   ("BGM",     "assets/bgm",          ".mp3"),
        "音乐":  ("BGM",     "assets/bgm",          ".mp3"),
        "音效":  ("音效",     "assets/sfx",          ".wav"),
        "道具":  ("道具图",   "assets/items",        ".png"),
        "CG":    ("剧情CG",   "assets/cgs",          ".png"),
    }

    def parse_outline(self, outline: str) -> List[Dict[str, str]]:
        """
        解析纯文字大纲，返回结构化素材需求列表。

        Returns:
            [
                {"type": "人物立绘", "name": "波洛", "description": "灰色胡须的比利时侦探",
                 "path": "assets/portraits/波洛.png"},
                ...
            ]
        """
        assets = []
        lines = [l.strip() for l in outline.strip().splitlines() if l.strip()]

        for line in lines:
            # 尝试匹配 "类别：条目1（描述1）、条目2（描述2）"
            category, items = self._parse_line(line)
            if category is None:
                continue

            mapping = self.CATEGORY_MAP.get(category)
            if not mapping:
                # 未知类别，用通用映射
                asset_type, sub_dir, ext = ("其他素材", "assets/other", ".png")
            else:
                asset_type, sub_dir, ext = mapping

            for name, description in items:
                safe_name = self._sanitize_filename(name)
                
                # Determine path based on asset_type, with specific overrides
                if asset_type == "BGM":
                    path = f"assets/bgm/{safe_name}.mp3"
                elif asset_type == "音效":
                    path = f"assets/sfx/{safe_name}.wav"
                else:
                    path = f"{sub_dir}/{safe_name}{ext}" # Use generic path for other types

                assets.append({
                    "type": asset_type,
                    "name": name,
                    "description": description or name,
                    "path": path,
                })

        return assets

    def _parse_line(self, line: str):
        """
        解析单行，返回 (类别, [(名称, 描述), ...])。
        
        支持格式：
            角色：波洛（灰色胡须的比利时侦探）、公主（高贵的老妇人）
            角色: 波洛(灰色胡须), 公主(高贵)
            场景：车站夜景, 餐车
        """
        # 分割 "类别：内容" 或 "类别: 内容"
        match = re.match(r'^([^:：]+)[：:]\s*(.+)$', line)
        if not match:
            return None, []
        
        category = match.group(1).strip()
        content = match.group(2).strip()

        # 按 "、" 分割条目（但不分割括号内的内容）
        raw_items = self._split_items(content)

        items = []
        for raw in raw_items:
            raw = raw.strip()
            if not raw:
                continue
            # 提取 "名称（描述）" 或 "名称(描述)" 或 "名称"
            item_match = re.match(r'^([^(（]+)\s*[（(]([^)）]*)[)）]$', raw)
            if item_match:
                name = item_match.group(1).strip()
                desc = item_match.group(2).strip()
            else:
                name = raw
                desc = ""
            items.append((name, desc))

        return category, items

    def _split_items(self, content: str) -> List[str]:
        """
        按 '、' 分割条目，但不分割括号 （） 或 () 内部的内容。
        例如: "波洛（灰色胡须的比利时侦探）、公主（高贵的俄国老妇人）"
        → ["波洛（灰色胡须的比利时侦探）", "公主（高贵的俄国老妇人）"]
        """
        items = []
        current = []
        depth = 0
        for ch in content:
            if ch in '（(':
                depth += 1
                current.append(ch)
            elif ch in '）)':
                depth = max(0, depth - 1)
                current.append(ch)
            elif ch == '、' and depth == 0:
                items.append(''.join(current))
                current = []
            else:
                current.append(ch)
        if current:
            items.append(''.join(current))
        return items

    def _sanitize_filename(self, name: str) -> str:
        """去除文件名中的非法字符。"""
        # 保留中文、字母、数字、下划线、连字符
        return re.sub(r'[^\w\u4e00-\u9fff\-]', '_', name).strip('_')

    def to_registry_dict(self, assets: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """
        将素材列表转换为按类型分组的注册表字典。
        格式：{"人物立绘": {"assets/portraits/波洛.png": "灰色胡须的比利时侦探"}, ...}
        
        兼容原有 /status 端点的遍历格式。
        """
        registry = {}
        for asset in assets:
            atype = asset["type"]
            if atype not in registry:
                registry[atype] = {}
            registry[atype][asset["path"]] = asset["description"]
        return registry
