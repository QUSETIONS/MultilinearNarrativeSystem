import os
import json
from fastapi import APIRouter, HTTPException
from foundation_platform.api.models import StateUpdateRequest, NarrativeConfigRequest, FeedbackRequest, DescEnhanceRequest
from foundation_platform.api.state import attention_mgr, refiner, feedback_lock
from foundation_platform.core.config import PROJECT_ROOT
from scripts.deep_enhance import enhance_prompt_via_llm

router = APIRouter(tags=["Narrative"])

@router.post("/state")
async def update_state(req: StateUpdateRequest):
    attention_mgr.update_state(req.entity_id, req.trait)
    return {"message": "State updated", "entity": req.entity_id, "trait": req.trait}

@router.get("/narrative/config")
async def get_narrative_config():
    return {
        "global_context": attention_mgr.global_context,
        "social_graph": refiner.relationships if hasattr(refiner, 'relationships') else {}
    }

@router.post("/narrative/config")
async def update_narrative_config(req: NarrativeConfigRequest):
    attention_mgr.update_global_config(theme=req.theme, era=req.era, negative_prompt=req.negative_prompt)
    if req.social_graph:
        pass
    return {"message": "Global configuration updated"}

@router.post("/narrative/feedback")
async def process_feedback(req: FeedbackRequest):
    async with feedback_lock:
        feedback_file = os.path.join(PROJECT_ROOT, "feedback.jsonl")
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(req.dict(), ensure_ascii=False) + "\n")
    
    if req.status == 'DISLIKED':
        print(f"Negative feedback received for {req.asset_path}: {req.reason}")
        
    return {"message": "Feedback collected", "status": "ok"}

@router.post("/enhance-desc")
async def enhance_description(req: DescEnhanceRequest):
    try:
        enhanced = enhance_prompt_via_llm(req.asset_type, req.description, "")
        if enhanced and enhanced != req.description:
            return {"enhanced": enhanced}
        return {"enhanced": req.description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
