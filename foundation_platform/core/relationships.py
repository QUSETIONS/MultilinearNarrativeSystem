import json
from typing import Dict, Any, Optional

class RelationshipManager:
    """
    Manages the social graph between characters in the narrative.
    Weights are floats from -1.0 (strong conflict) to 1.0 (absolute trust).
    Also supports 'hierarchy' (0.0 to 1.0) and 'tension' (0.0 to 1.0).
    """

    def __init__(self, initial_data: Optional[Dict] = None):
        # Format: { "char_a": { "char_b": {"trust": 0.5, "tension": 0.2, "hierarchy": 0.8} } }
        self.graph = initial_data or {}

    def set_relationship(self, char_id: str, target_id: str, 
                         trust: Optional[float] = None, 
                         tension: Optional[float] = None, 
                         hierarchy: Optional[float] = None):
        if char_id not in self.graph:
            self.graph[char_id] = {}
        if target_id not in self.graph[char_id]:
            self.graph[char_id][target_id] = {"trust": 0.0, "tension": 0.0, "hierarchy": 0.5}
        
        rels = self.graph[char_id][target_id]
        if trust is not None: rels["trust"] = max(-1.0, min(1.0, trust))
        if tension is not None: rels["tension"] = max(0.0, min(1.0, tension))
        if hierarchy is not None: rels["hierarchy"] = max(0.0, min(1.0, hierarchy))

    def get_relationship(self, char_id: str, target_id: str) -> Dict[str, float]:
        return self.graph.get(char_id, {}).get(target_id, {"trust": 0.0, "tension": 0.5, "hierarchy": 0.5})

    def get_prompt_context(self, speaker_id: str, listener_id: str) -> str:
        """
        Returns a natural language descriptor of the relationship for prompt injection.
        """
        rels = self.get_relationship(speaker_id, listener_id)
        trust = rels.get("trust", 0.0)
        tension = rels.get("tension", 0.5)
        hierarchy = rels.get("hierarchy", 0.5)

        descriptors = []
        
        # Power dynamic
        if hierarchy > 0.7:
            descriptors.append(f"{speaker_id} holds significant authority over {listener_id}")
        elif hierarchy < 0.3:
            descriptors.append(f"{speaker_id} is subordinate to {listener_id}")
        
        # Emotional quality
        if trust > 0.6:
            descriptors.append(f"The interaction is rooted in deep mutual trust")
        elif trust < -0.4:
            descriptors.append(f"There is a palpable undercurrent of suspicion and animosity between them")
        
        # Current tension
        if tension > 0.8:
            descriptors.append(f"The atmosphere is electric with immediate conflict")
        elif tension < 0.2:
            descriptors.append(f"The conversation is unusually relaxed and candid")

        if not descriptors:
            return f"The relationship between {speaker_id} and {listener_id} is professionally neutral."
        
        return ". ".join(descriptors) + "."
