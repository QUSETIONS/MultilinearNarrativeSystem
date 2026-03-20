from typing import Dict, List, Optional, Any


class AttentionManager:
    """
    Manages the 'Narrative Attention' of the platform.
    
    Computes weighted focus tokens for AI generation based on:
    - Global context (theme, era, art style)
    - Scene mood detection
    - Entity canonical IDs
    - Character state memory
    - DPO rejection-based weight decay
    
    Does NOT read from JSON files. All data is registered via API calls or config dicts.
    """
    
    def __init__(self, global_config: Optional[Dict[str, str]] = None):
        self.global_context = global_config or {
            "theme": "1930s Detective Mystery",
            "era": "1930s",
            "setting": "Orient Express, luxury train, snowy mountains",
            "art_style": "High-fidelity cinematic digital painting",
            "negative_prompt": "modern, electronic gadget, messy, low resolution, ugly, blurry"
        }
        self.state_memory: Dict[str, str] = {}    # Tracks character state over scenes
        self.resonance_cache: Dict[str, str] = {}  # Tracks visual vibe for BGM
        self.entities: Dict[str, str] = {}         # asset_path → description
        self.canonical_ids: Dict[str, str] = {}    # character key → consistency tag

    def register_assets(self, assets: List[Dict[str, str]]):
        """
        Register a list of parsed assets into the attention entity store.
        
        Args:
            assets: Output from AssetExtractor.parse_outline()
                    [{"type": "人物立绘", "name": "波洛", "description": "...", "path": "..."}, ...]
        """
        for asset in assets:
            path = asset["path"]
            desc = asset.get("description", asset.get("name", ""))
            self.entities[path] = desc

            # Auto-generate canonical consistency IDs for characters
            if asset["type"] == "人物立绘":
                name = asset["name"]
                safe_key = name.lower()
                self.canonical_ids[safe_key] = f"[CHARACTER-{name}-CONSISTENT]"

    def register_characters(self, characters: Dict[str, str]):
        """
        Register character canonical IDs manually.
        
        Args:
            characters: {"poirot": "[HERO-POIROT-CONSISTENT]", ...}
        """
        self.canonical_ids.update(characters)

    def get_scene_mood(self, description: str) -> str:
        """Simple NLP inference to detect mood from raw description."""
        mood_map = {
            "cold": ["snow", "frost", "night", "winter", "寒冷", "冰", "雪"],
            "tense": ["murder", "blood", "scream", "dark", "crime", "suspense", "紧张", "谋杀", "血"],
            "luxury": ["gold", "silk", "princess", "dining", "elegant", "华丽", "优雅", "丝绸"],
            "mystery": ["shadow", "whisper", "clue", "hidden", "悬疑", "暗影", "线索"]
        }
        
        detected = []
        desc_lower = description.lower()
        for mood, keywords in mood_map.items():
            if any(k in desc_lower for k in keywords):
                detected.append(mood)
                
        return ", ".join(detected) if detected else "standard"

    def get_focus_tokens(self, asset_path: str, description: str = "", rejected_reasons: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns a dictionary of categorized positive and negative tokens."""
        global_weight = 1.2
        era_weight = 1.1
        if rejected_reasons and len(rejected_reasons) > 0:
            penalty = min(0.3, len(rejected_reasons) * 0.1)
            global_weight = max(0.5, global_weight - penalty)
            era_weight = max(0.5, era_weight - penalty)

        categorized = {
            "global": [f"({self.global_context['theme']}:{global_weight:.1f})", f"({self.global_context['era']}:{era_weight:.1f})"],
            "mood": [],
            "entity": [],
            "consistency": []
        }
        
        # 1. Scene Mood Focus
        if description:
            mood = self.get_scene_mood(description)
            if mood != "standard":
                categorized["mood"].append(f"({mood} mood:1.25)")
        
        # 2. Canonical ID Anchoring & Entity hints
        asset_lower = asset_path.lower()
        for key, cid in self.canonical_ids.items():
            if key in asset_lower:
                categorized["entity"].append(f"<{cid}>")
        
        if asset_path in self.entities:
            categorized["entity"].append(f"({self.entities[asset_path]}:1.3)")
        
        # 3. State Memory Recall (Consistency)
        for key in self.state_memory:
            if key in asset_lower:
                categorized["consistency"].append(f"({self.state_memory[key]}:1.1)")
        
        # 4. Multi-Modal Resonance
        if "bgm" in asset_path.lower():
            for key in self.resonance_cache:
                if key.split('.')[0] in asset_path:
                    categorized["consistency"].append(f"(resonant with visual {self.resonance_cache[key]}:1.2)")
            
        positive = []
        for v in categorized.values():
            positive.extend(v)

        return {
            "structured": categorized,
            "positive": list(set(positive)),
            "negative": [self.global_context["negative_prompt"]]
        }

    def update_global_config(self, theme: Optional[str] = None, era: Optional[str] = None, 
                             negative_prompt: Optional[str] = None):
        """Dynamic update for global focus."""
        if theme: self.global_context["theme"] = theme
        if era: self.global_context["era"] = era
        if negative_prompt: self.global_context["negative_prompt"] = negative_prompt

    def update_resonance(self, asset_path: str, visual_vibe: str):
        """Saves the visual mood for later BGM resonance."""
        self.resonance_cache[asset_path] = visual_vibe

    def update_state(self, entity_id: str, trait: str):
        """Updates the character memory (e.g. 'poirot', 'holding a silver glass')."""
        self.state_memory[entity_id] = trait


class MockAttentionManager(AttentionManager):
    def get_focus_tokens(self, asset_path: str, description: str = "", rejected_reasons: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "structured": {"global": [], "mood": [], "entity": [], "consistency": []},
            "positive": ["(Orient Express:1.2)", "(Cinematic Lighting:1.1)"],
            "negative": ["modern, blurry"]
        }
