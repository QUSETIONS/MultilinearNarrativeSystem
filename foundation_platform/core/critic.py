import re
from typing import List, Dict, Any

class NarrativeCritic:
    """
    Phase 18: Proactive Critique Layer.
    Audits prompts for 'OOC' (Out of Character) or logical contradictions
    by comparing them against the NAR stack.
    """
    
    def __init__(self, sensitivity: float = 0.5):
        self.sensitivity = sensitivity

    def audit(self, prompt: str, nar_stack: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 21: Logical Invariance Audit.
        Checks for violations of domain rules based on NAR predicates.
        """
        issues = []
        
        # 1. Gather all logic predicates from stack
        # This includes [PROP:] and [IF: THEN:]
        active_logic = []
        for item in nar_stack:
            content = item["content"]
            # Extract from aggregated tags
            if "Logical Entanglement:" in content:
                try:
                    tags = content.split("Logical Entanglement:")[1].split(")")[0].split(",")
                    active_logic.extend([t.strip() for t in tags])
                except Exception:
                    pass
            # Extract directly from raw PROP tags (Phase 21 Robustness)
            if "[PROP:" in content:
                prop = content.split("[PROP:")[1].split("]")[0].strip()
                active_logic.append(prop)
            if "[IF:" in content:
                logic = content.split("[IF:")[1].split("]")[0].strip()
                active_logic.append(f"CONDITIONAL: {logic}")
        
        # 2. Rule Enforcement: Inverse Conflict
        # e.g. If LOGIC: Status=Broken, then AVOID 'Active', 'Working', 'Efficient'
        rules = {
            "Status=Broken": ["Active", "Working", "Functional", "Efficient"],
            "Status=Rust": ["Clean", "Shiny", "Polished"],
            "Environment=Gloom": ["Bright", "Sunny", "Radiant", "Glow"]
        }
        
        for logic_tag in set(active_logic):
            # Clean 'LOGIC: ' prefix if present
            clean_tag = logic_tag.replace("LOGIC: ", "")
            if clean_tag in rules:
                forbidden_traits = rules[clean_tag]
                for trait in forbidden_traits:
                    if trait.lower() in prompt.lower():
                        issues.append(f"Invariant Violation: '{trait}' contradicts state '{clean_tag}'")
                        
        # 3. Conditional Enforcement: [IF: A THEN: B]
        # Example: CONDITIONAL: Status=Broken THEN: AVOID Shining
        for logic_tag in set(active_logic):
            if "CONDITIONAL:" in logic_tag and "THEN:" in logic_tag:
                try:
                    parts = logic_tag.replace("CONDITIONAL: ", "").split("THEN:")
                    cond = parts[0].strip()
                    effect = parts[1].strip()
                    if cond.lower() in prompt.lower():
                        if "AVOID" in effect:
                            forbidden = effect.replace("AVOID ", "").strip()
                            if forbidden.lower() in prompt.lower():
                                issues.append(f"Conditional Fault: Condition '{cond}' triggered avoidance of '{forbidden}'")
                except Exception:
                    pass

        # 4. Standard Heuristic (Phase 18)
        for item in nar_stack:
            content = item["content"].lower()
            if "avoid" in content:
                forbidden = re.findall(r"avoid\s+(\w+)", content)
                for f in forbidden:
                    if f in prompt.lower():
                        issues.append(f"Consistency Leak: Found forbidden term '{f}' from NAR lineage.")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "audit_depth": len(nar_stack)
        }

def apply_critic(prompt: str, nar_stack: List[Dict[str, Any]]) -> str:
    critic = NarrativeCritic()
    report = critic.audit(prompt, nar_stack)
    
    if not report["is_valid"]:
        issue_text = " | ".join(report["issues"])
        return f"{prompt}\n[CRITIC AUDIT: {issue_text}]"
    
    return prompt
