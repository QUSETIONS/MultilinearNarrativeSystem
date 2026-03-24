from typing import Dict, List, Optional, Any
from .relationships import RelationshipManager
from .nar import NarrativeAttentionResidual
from .critic import NarrativeCritic, apply_critic
from .memory import get_shared_memory

class PromptRefiner:
    """
    Intelligently refines and expands raw asset descriptions into high-quality AI prompts.
    Incorporates NAR (Narrative Attention Residuals) for selective depth-wise aggregation.
    """
    
    STYLE_PRESETS = {
        "背景图": "High-fidelity digital painting, 8k resolution, cinematic lighting, detailed environment, oil on canvas style, concept art.",
        "人物立绘": "Character portrait, high detail, sharp focus, vibrant colors, anime style, clean lines, white background.",
        "bgm": "High-quality orchestral soundtrack, cinematic atmosphere, 44.1kHz, professional mixing."
    }

    def get_spatial_hint(self, asset_type: str) -> str:
        """Determines the composition layout based on asset type."""
        layouts = {
            "人物立绘": "Composition: Full body portrait, centered, high-key lighting, blank background.",
            "背景图": "Composition: Wide angle, deep depth of field, environmental storytelling, rule of thirds.",
            "bgm": "Atmosphere: Surround sound, immersive, high dynamic range."
        }
        return layouts.get(asset_type, "Standard centered composition.")

    def refine(self, asset_type: str, raw_description: str, 
                asset_id: Optional[str] = None,
                attention: Optional[Dict[str, List[str]]] = None, 
                entropy: float = 0.5,
                relationships: Optional[Dict[str, Any]] = None,
                refinement_passes: int = 1,
                rejected_reasons: Optional[List[str]] = None,
                nar_context: str = "") -> Dict[str, str]:
        """
        Enhances the raw description with attention, spatial hints, social context, and NAR integration.
        """
        # 1. Inject Social Context if available
        social_context = ""
        if relationships and "speaker" in relationships and "listener" in relationships:
            mgr = RelationshipManager(relationships.get("graph", {}))
            social_context = f" [SOCIAL: {mgr.get_prompt_context(relationships['speaker'], relationships['listener'])}]"

        # Phase 19: World-State NAR Implementation
        nar = NarrativeAttentionResidual(temperature=0.3)
        snmb = get_shared_memory()
        
        # 1. Fetch World-State context instead of just config
        # Phase 20: Entangled Fetch
        if asset_id:
            world_context = snmb.fetch_entangled(asset_id)
        else:
            world_context = snmb.fetch_all()
            
        for item in world_context:
            nar.push(item["content"], metadata={**item["metadata"], "stage": "world-state"})
            
        # 2. Push current asset spotlight
        nar.push(f"Attention Spotlight: {raw_description}", metadata={"stage": "spotlight"})
        
        # 3. Dynamic Entropy Scaling (Phase 18 legacy maintained)
        saliency = nar.get_saliency_score()
        effective_entropy = entropy * saliency
        
        # 4. Base Refinement
        base_result = self._base_refine(asset_type, raw_description, attention, effective_entropy, social_context, rejected_reasons, nar_context)
        
        # 5. Recursive Refinement (Multi-pass) with ILC
        if refinement_passes > 1:
            res = self._recursive_loop(asset_type, base_result, refinement_passes, nar=nar, asset_id=asset_id)
            # Push the final result to SNMB for World-State continuity
            snmb.push(res["prompt"], metadata={"stage": "asset_nar_final", "type": asset_type, "asset_id": asset_id})
            return res
        
        # Final audit and world-state injection for single pass
        base_result["prompt"] = nar.aggregate_prompts(base_result["prompt"])
        base_result["prompt"] = apply_critic(base_result["prompt"], nar.stack)
        snmb.push(base_result["prompt"], metadata={"stage": "asset_nar_final", "type": asset_type, "asset_id": asset_id})
        return base_result

    def _base_refine(self, asset_type: str, raw_description: str, attention: Optional[Dict[str, List[str]]], 
                     entropy: float, social_context: str, rejected_reasons: Optional[List[str]] = None,
                     nar_context: str = "") -> Dict[str, str]:
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
        
        # Pipeline NAR Integration: Inject context from prior stages
        pipe_context = f" [PIPE-NAR: {nar_context}]" if nar_context else ""
        
        refined_prompt = f"{spatial} {raw_description}{decorations}. {preset}{social_context}{anti_patterns}{pipe_context} [FOCUS: {focus}]"
        
        return {
            "prompt": refined_prompt,
            "negative_prompt": negative
        }

    def _recursive_loop(self, asset_type: str, initial_result: Dict[str, str], passes: int, 
                        nar: Optional[NarrativeAttentionResidual] = None,
                        asset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Recursive NAR (Level 2): Aggregates previous refinement passes using softmax attention.
        """
        if nar is None:
            nar = NarrativeAttentionResidual(temperature=0.3)
        
        snapshots: List[Dict[str, Any]] = [{
            "pass": 0,
            "prompt": initial_result["prompt"],
            "critique": "Initial Draft"
        }]
        
        current_prompt = initial_result["prompt"]
        nar.push(current_prompt, metadata={"stage": "refine_pass_0"})
        
        # Dynamic Cooling Schedule: start high (0.8) for exploration, end low (0.2) for convergence
        temp_start = 0.8
        temp_end = 0.2
        
        for i in range(passes - 1):
            # Calculate current temperature for this pass
            cooling_temp = temp_start - (temp_start - temp_end) * (i / max(passes - 2, 1))
            
            critique = f"Pass {i+1}: Enhance mood and specific texture details."
            
            # Phase 19: In-Loop Critic (ILC) and Distillation
            # Audit the pass BEFORE pushing to stack or moving to next pass
            current_prompt = nar.aggregate_prompts(current_prompt, cooling_temp=cooling_temp)
            raw_pass_prompt = f"{current_prompt} (Refined Pass {i+1}: {critique})"
            
            # Run audit inside the loop
            current_prompt = apply_critic(raw_pass_prompt, nar.stack)
            
            nar.push(current_prompt, metadata={"stage": f"refine_pass_{i+1}", "asset_id": asset_id})
            
            # Distillation every 3 passes to prevent bloat
            if (i + 1) % 3 == 0:
                nar.distill(target_size=5)
            
            snapshots.append({
                "pass": i + 1,
                "prompt": current_prompt,
                "critique": critique,
                "cooling_temp": cooling_temp
            })
            
        return {
            "prompt": current_prompt,
            "negative_prompt": initial_result["negative_prompt"],
            "snapshots": snapshots
        }


class MockRefiner(PromptRefiner):
    def refine(self, asset_type: str, raw_description: str, attention: Optional[Dict[str, List[str]]] = None, 
               entropy: float = 0.5, relationships: Optional[Dict[str, Any]] = None, refinement_passes: int = 1,
               rejected_reasons: Optional[List[str]] = None, nar_context: str = "") -> Dict[str, str]:
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
