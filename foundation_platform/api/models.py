from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class AssetRegistrationRequest(BaseModel):
    outline: str

class AssetStatus(BaseModel):
    path: str
    description: str
    task_status: str = "QUEUED"
    last_prompt: str = ""
    logs: List[str] = []

class GenerationRequest(BaseModel):
    asset_path: str
    description: str
    asset_type: str
    provider: str = "mock"
    entropy: float = 0.5
    relationships: Optional[Dict[str, Any]] = None
    refinement_passes: int = 1

class NarrativeConfigRequest(BaseModel):
    theme: Optional[str] = None
    era: Optional[str] = None
    social_graph: Optional[Dict[str, Any]] = None
    negative_prompt: Optional[str] = None

class FeedbackRequest(BaseModel):
    asset_path: str
    status: str
    reason: Optional[str] = None
    prompt: str
    context: Dict[str, Any]

class StateUpdateRequest(BaseModel):
    entity_id: str
    trait: str

class ScriptExtractRequest(BaseModel):
    chapters: List[Dict[str, Any]]
    characters: Optional[List[Dict[str, Any]]] = None
    use_llm: bool = True

class VariantGenerateRequest(BaseModel):
    asset_path: str
    description: str
    asset_type: str
    provider: str = "mock"
    count: int = 3
    base_entropy: float = 0.5

class DescEnhanceRequest(BaseModel):
    asset_type: str
    description: str
