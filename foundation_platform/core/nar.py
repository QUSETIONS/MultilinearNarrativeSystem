import math
import re
from typing import List, Dict, Any, Optional
import numpy as np

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def normalize(v):
    """L2 normalization (analogous to RMSNorm in paper)."""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

class NarrativeAttentionResidual:
    """
    NAR: Narrative Attention Residuals.
    Integrates Kimi Team's AttnRes logic into the narrative pipeline.
    
    Replaces fixed residual accumulation with content-dependent softmax attention over 'depth'
    (stages, passes, or historical sessions).
    """
    
    def __init__(self, temperature: float = 0.5):
        self.stack: List[Dict[str, Any]] = []
        self.temperature = temperature
        
    def push(self, representation: str, weight: float = 1.0, metadata: Optional[Dict[str, Any]] = None):
        """
        Push a 'layer' output into the stack.
        Since we are in a text-based pipeline, representations are strings.
        We use a simple embedding-like proxy for similarity.
        """
        self.stack.append({
            "content": representation,
            "weight": weight,
            "metadata": metadata or {}
        })
        
    def clear(self):
        self.stack = []

    # Phase 19: Narrative Concept Map (Semantic Proximity Heuristic)
    CONCEPT_MAP = {
        "dark": ["gloom", "shadow", "obscurity", "night", "grim"],
        "light": ["bright", "radiance", "sun", "glow", "luminous"],
        "knight": ["warrior", "paladin", "soldier", "fighter", "squire", "armor"],
        "magic": ["arcane", "spell", "wizardry", "sorcery", "power"]
    }

    def _fuzzy_similarity(self, s1: str, s2: str) -> float:
        """Heuristic semantic similarity with Concept Mapping (Phase 19)."""
        s1, s2 = s1.lower(), s2.lower()
        if not s1 or not s2: return 0.0
        
        # 1. Direct Concept Match Expansion
        bonus = 0.0
        for concept, synonyms in self.CONCEPT_MAP.items():
            if concept in s1:
                if any(syn in s2 for syn in synonyms) or concept in s2:
                    bonus = 0.2  # Semantic proximity boost
        
        # 2. 3-gram overlap using list comprehension for lint compatibility
        n = 3
        q1 = {s1[i:i+n] for i in range(len(s1)-n+1)}
        q2 = {s2[i:i+n] for i in range(len(s2)-n+1)}
        
        if not q1 or not q2: return bonus
        intersection = q1.intersection(q2)
        base_sim = len(intersection) / max(len(q1), len(q2), 1)
        
        return min(base_sim + bonus, 1.0)

    def distill(self, target_size: int = 5):
        """
        Phase 19: Narrative Distillation.
        Compresses the stack by merging oldest items into a 'Narrative Premise'.
        """
        if len(self.stack) <= target_size:
            return
            
        to_distill = self.stack[:-target_size]
        keeping = self.stack[-target_size:]
        
        # Distillation: Summarize high-level 'Anchors' from distilled items
        anchors = []
        for item in to_distill:
            if "[FOCUS:" in item["content"]:
                anchor = item["content"].split("[FOCUS:")[1].split("]")[0].strip()
                anchors.append(anchor)
        
        premise = f"Established World-State: {', '.join(set(anchors))}"
        new_distilled = {
            "content": premise,
            "metadata": {"stage": "distilled_premise", "count": len(to_distill)}
        }
        
        self.stack = [new_distilled] + keeping

    def get_context_hint(self, query: str, decay: float = 0.9) -> str:
        """
        Computes softmax attention weights with fuzzy similarity and temporal decay.
        Returns a string summary of the most relevant NAR context items.
        """
        if not self.stack:
            return ""
            
        scores = []
        n_items = len(self.stack)
        for i, item in enumerate(self.stack):
            similarity = self._fuzzy_similarity(query, item["content"])
            
            # Temporal Decay: 0.9^(distance from end)
            time_factor = math.pow(decay, n_items - 1 - i)
            
            # Combine similarity with recency
            score = (similarity * 0.7 + time_factor * 0.3) / self.temperature
            scores.append(score)
            
        # Softmax normalization
        weights = softmax(np.array(scores))
        
        # Select items with significant attention weight
        selected = []
        for i, weight in enumerate(weights):
            if weight > 0.1:  # Lower threshold for deep retrieval
                stage = self.stack[i]['metadata'].get('stage', 'prev')
                content = self.stack[i]['content']
                # If too long, take the most relevant snippet
                snippet = content[:60] if len(content) <= 60 else content[:60] + "..."
                selected.append(f"[{stage}: {snippet}]")
        
        return " | ".join(selected)

    def get_saliency_score(self) -> float:
        """
        Computes the 'Narrative Saliency' of the current stack.
        Higher scores imply high-impact nodes with significant historical residuals.
        """
        if not self.stack:
            return 1.0
            
        # Saliency = log(number of high-attention items + 1) * mean_similarity
        # (This is a heuristic for 'Narrative Density')
        n_items = len(self.stack)
        if n_items == 0: return 1.0
        
        # Calculate mean weight over the stack for a generic 'relevance' query
        # Using the last item as a proxy for the current context
        last_content = self.stack[-1]["content"]
        scores = [self._fuzzy_similarity(last_content, item["content"]) for item in self.stack]
        mean_sim = np.mean(scores) if scores else 0.0
        
        return 1.0 + (math.log(n_items + 1) * mean_sim)

    def get_style_vector(self) -> List[str]:
        """
        Extracts aesthetic keywords (Style Steering) from LIKED feedback history.
        Only keeps high-frequency 'positive' style tokens.
        """
        styles = []
        for item in self.stack:
            if item["metadata"].get("feedback") == "LIKE":
                content = item["content"].lower()
                for trigger in ["style:", "vibe:", "mood:"]:
                    if trigger in content:
                        raw_segment = content.split(trigger)[1].split(",")[0].split(".")[0]
                        # Phase 18: Sanitation - Remove trailing brackets or non-alphanumeric noise
                        clean_segment = re.sub(r"[^a-z0-9\-\s]", "", raw_segment).strip()
                        if clean_segment:
                            styles.append(clean_segment)
        
        # Return unique high-freq styles
        unique_styles = sorted(list(set(styles)))
        return unique_styles[:3]

    def aggregate_prompts(self, current_prompt: str, cooling_temp: Optional[float] = None) -> str:
        """
        Level 2 NAR: Recursive Residual Aggregator. (v18: with Style Steering)
        """
        if not self.stack:
            return current_prompt
            
        temp = cooling_temp or self.temperature
        
        # Phase 20: Relationship-Driven Attention Floors & Predicates
        similarities = []
        for item in self.stack:
            content = item["content"]
            sim = self._fuzzy_similarity(current_prompt, content)
            
            # 1. Global Attention Floor & Phase 20 Relationship Boost
            if item["metadata"].get("stage") in ["distilled_premise", "world-state"]:
                sim = max(sim, 0.45)
                
            # Entanglement Boost: Residuals from direct relatives (dist 1) get higher floor
            if item["metadata"].get("rel_dist") == 1:
                sim = max(sim, 0.55)
            
            # 2. Predicate Weighting: If content contains key from prompt, boost sim
            # e.g. [PROP: Armor=Silver]
            if "[PROP:" in content and any(word.lower() in content.lower() for word in current_prompt.split()):
                sim = min(sim + 0.15, 1.0)
                
            # Phase 21: Conditional Aggregation (IF/THEN Predicates)
            # Example: [IF: Status=Broken THEN: AVOID Active]
            if "[IF:" in content and "THEN:" in content:
                condition = content.split("[IF:")[1].split("THEN:")[0].strip()
                # Check if condition is met by current prompt OR other stack items
                if any(word.lower() in current_prompt.lower() for word in condition.split("=")):
                    sim = min(sim + 0.25, 1.0) # High attention if condition matches
                
            similarities.append(sim / temp)
            
        weights = softmax(np.array(similarities))
        
        anchors = []
        # Phase 20: Anchor/Predicate Conflict Resolution
        # We track source asset to ensure latest state overrides historical ones
        source_anchors = {} # {asset_id_or_generic: {anchor_val: index}}
        
        for i, weight in enumerate(weights):
            if weight > 0.1:
                content = self.stack[i]['content']
                asset_id = self.stack[i]["metadata"].get("asset_id", "generic")
                
                if asset_id not in source_anchors: source_anchors[asset_id] = set()
                
                # FOCUS extraction
                if "[FOCUS:" in content:
                    anchor = content.split("[FOCUS:")[1].split("]")[0].strip()
                    if anchor:
                        # For the same asset, we keep adding but we might want to prioritize.
                        # Actually, better: if asset_id is the same, we only take the LATEST one.
                        # Since we iterate stack in order, we can just replace.
                        source_anchors[asset_id] = {anchor}
                
                # PROP extraction
                if "[PROP:" in content:
                    prop = content.split("[PROP:")[1].split("]")[0].strip()
                    if prop:
                        # If it's a key=value pair, we override by key
                        if "=" in prop:
                            p_key = prop.split("=")[0]
                            # Simple tracking: for now just group by asset
                            source_anchors[asset_id].add(f"LOGIC: {prop}")
                        else:
                            source_anchors[asset_id].add(f"LOGIC: {prop}")
                
                # Phase 21: Conditional Extraction
                if "[IF:" in content and "THEN:" in content:
                    logic = content.split("[IF:")[1].split("]")[0].strip()
                    if logic:
                        if asset_id not in source_anchors: source_anchors[asset_id] = set()
                        source_anchors[asset_id].add(f"CONDITIONAL: {logic}")
                            
        # Flatten source_anchors into final list
        for asset_res in source_anchors.values():
            anchors.extend(list(asset_res))
        
        if anchors:
            # Phase 20: Logical Entanglement tagging
            current_prompt = f"{current_prompt} (Logical Entanglement: {', '.join(set(anchors))})"
        
        # Style Steering: Inject historical 'LIKED' styles if they don't contradict
        style_vec = self.get_style_vector()
        style_injection = f" (Aesthetic Steering: {', '.join(style_vec)})" if style_vec else ""
        
        if anchors:
            anchor_text = ", ".join(set(anchors))
            return f"{current_prompt}{style_injection} (NAR Depth-Reinforcement: {anchor_text})"
            
        return f"{current_prompt}{style_injection}"
