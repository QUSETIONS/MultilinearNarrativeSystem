from typing import Dict, List, Optional, Any
from .relationships import RelationshipManager

class PromptRefiner:
    """
    Intelligently refines and expands raw asset descriptions into high-quality AI prompts.
    In a real-world scenario, this would call an LLM (e.g. GPT-4, Claude).
    """
    
    STYLE_PRESETS = {
        "背景图": "High-fidelity digital painting, 8k resolution, cinematic lighting, detailed environment, oil on canvas style, concept art.",
        "人物立绘": "Character portrait, high detail, sharp focus, vibrant colors, anime style, clean lines, white background.",
        "bgm": "High-quality orchestral soundtrack, cinematic atmosphere, 44.1kHz, professional mixing."
    }

    def get_spatial_hint(self, asset_type: str) -> str:
        """
        Determines the composition layout based on asset type.
        Inspired by 'Masked-Attention Guidance' research.
        """
        layouts = {
            "人物立绘": "Composition: Full body portrait, centered, high-key lighting, blank background.",
            "背景图": "Composition: Wide angle, deep depth of field, environmental storytelling, rule of thirds.",
            "bgm": "Atmosphere: Surround sound, immersive, high dynamic range."
        }
        return layouts.get(asset_type, "Standard centered composition.")

    def refine(self, asset_type: str, raw_description: str, 
               attention: Optional[Dict[str, List[str]]] = None, 
               entropy: float = 0.5,
               relationships: Optional[Dict[str, Any]] = None,
               refinement_passes: int = 1,
               rejected_reasons: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Enhances the raw description with attention, spatial hints, social context, and recursive loops.
        """
        # 1. Inject Social Context if available
        social_context = ""
        if relationships and "speaker" in relationships and "listener" in relationships:
            mgr = RelationshipManager(relationships.get("graph", {}))
            social_context = f" [SOCIAL: {mgr.get_prompt_context(relationships['speaker'], relationships['listener'])}]"

        # 2. Base Refinement
        base_result = self._base_refine(asset_type, raw_description, attention, entropy, social_context, rejected_reasons)
        
        # 3. Recursive Refinement (Multi-pass)
        if refinement_passes > 1:
            return self._recursive_loop(asset_type, base_result, refinement_passes)
        
        return base_result

    def _base_refine(self, asset_type: str, raw_description: str, attention: Optional[Dict[str, List[str]]], entropy: float, social_context: str, rejected_reasons: Optional[List[str]] = None) -> Dict[str, str]:
        preset = self.STYLE_PRESETS.get(asset_type, "High quality asset.")
        spatial = self.get_spatial_hint(asset_type)
        
        pos_tokens = attention.get("positive", []) if attention else []
        neg_tokens = attention.get("negative", []) if attention else []
        
        anti_patterns = ""
        if rejected_reasons:
            reasons_str = "; ".join(set(rejected_reasons))
            anti_patterns = f" [AVOID PREVIOUS MISTAKES: {reasons_str}]"
            neg_tokens.append(reasons_str)
            
        decorations = ""
        if entropy > 0.7:
            decorations = ", ornate art deco patterns, vintage atmosphere, rich textures, smoke from steam engine, luxury materiality"
        elif entropy < 0.3:
            preset = "Clean and precise rendering."
            
        if any("tense" in t.lower() for t in pos_tokens):
            neg_tokens.append("bright colors, cheerful, sunny")
            
        focus = " ".join(pos_tokens)
        negative = ", ".join(neg_tokens)
        
        refined_prompt = f"{spatial} {raw_description}{decorations}. {preset}{social_context}{anti_patterns} [FOCUS: {focus}]"
        
        return {
            "prompt": refined_prompt,
            "negative_prompt": negative
        }

    def _recursive_loop(self, asset_type: str, initial_result: Dict[str, str], passes: int) -> Dict[str, Any]:
        """
        Simulates the AI critiquing and improving its own prompt, returning snapshots.
        """
        snapshots = [{
            "pass": 0,
            "prompt": initial_result["prompt"],
            "critique": "Initial Draft"
        }]
        
        current_prompt = initial_result["prompt"]
        for i in range(passes - 1):
            critique = f"Pass {i+1}: Enhance mood and specific texture details."
            current_prompt += f" (Refined Pass {i+1}: {critique})"
            snapshots.append({
                "pass": i + 1,
                "prompt": current_prompt,
                "critique": critique
            })
            
        return {
            "prompt": current_prompt,
            "negative_prompt": initial_result["negative_prompt"],
            "snapshots": snapshots
        }

class MockRefiner(PromptRefiner):
    def refine(self, asset_type: str, raw_description: str, attention: Optional[Dict[str, List[str]]] = None, 
               entropy: float = 0.5, relationships: Optional[Dict[str, Any]] = None, refinement_passes: int = 1,
               rejected_reasons: Optional[List[str]] = None) -> Dict[str, str]:
        # Simulate LLM thinking
        pos_tokens = attention.get("positive", []) if attention else ["Standard"]
        neg_tokens = attention.get("negative", []) if attention else ["None"]
        
        base_prompt = f"[REFINED] {raw_description} | Style: {self.STYLE_PRESETS.get(asset_type, 'Standard')} | Attention: {' '.join(pos_tokens)}"
        
        if refinement_passes > 1:
            base_prompt += f" | (Recursive: {refinement_passes} passes)"
            
        return {
            "prompt": base_prompt,
            "negative_prompt": ", ".join(neg_tokens)
        }
