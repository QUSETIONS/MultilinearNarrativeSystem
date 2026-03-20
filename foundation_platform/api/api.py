import os
import asyncio
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# New encapsulated imports
from foundation_platform.core.generator import GeneratorRegistry, BaseGenerator
from foundation_platform.core.extractor import AssetExtractor
from foundation_platform.core.refiner import PromptRefiner
from foundation_platform.core.attention import AttentionManager

app = FastAPI(title="Foundation Platform API v5.0 [RESONANCE ENABLED]")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Narrative Path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NARRATIVE_JSON = os.path.join(PROJECT_ROOT, "东方快车谋杀案修复版.json")

# In-Memory Store
tasks_kv: Dict[str, Dict] = {}
task_logs: Dict[str, List[str]] = {}

refiner = PromptRefiner()
attention_mgr = AttentionManager(NARRATIVE_JSON)

class GenerationRequest(BaseModel):
    asset_path: str
    description: str
    asset_type: str
    provider: str = "mock"
    entropy: float = 0.5 # Creative freedom
    relationships: Optional[Dict[str, Any]] = None # {speaker, listener, graph}
    refinement_passes: int = 1 # Recursive polish

class NarrativeConfigRequest(BaseModel):
    theme: Optional[str] = None
    era: Optional[str] = None
    social_graph: Optional[Dict[str, Any]] = None
    negative_prompt: Optional[str] = None

class FeedbackRequest(BaseModel):
    asset_path: str
    status: str # 'LIKED' or 'DISLIKED'
    reason: Optional[str] = None
    prompt: str
    context: Dict[str, Any]

class StateUpdateRequest(BaseModel):
    entity_id: str
    trait: str

@app.post("/state")
async def update_state(req: StateUpdateRequest):
    attention_mgr.update_state(req.entity_id, req.trait)
    return {"message": "State updated", "entity": req.entity_id, "trait": req.trait}

@app.get("/narrative/config")
async def get_narrative_config():
    return {
        "global_context": attention_mgr.global_context,
        "social_graph": refiner.relationships if hasattr(refiner, 'relationships') else {} # Fallback
    }

@app.post("/narrative/config")
async def update_narrative_config(req: NarrativeConfigRequest):
    attention_mgr.update_global_config(theme=req.theme, era=req.era, negative_prompt=req.negative_prompt)
    if req.social_graph:
        # Assuming RelationshipManager integration or similar
        pass
    return {"message": "Global configuration updated"}

@app.post("/narrative/feedback")
async def process_feedback(req: FeedbackRequest):
    feedback_file = os.path.join(PROJECT_ROOT, "feedback.jsonl")
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(req.dict(), ensure_ascii=False) + "\n")
    
    # Logic for dynamic weight decay or ICL integration would go here
    if req.status == 'DISLIKED':
        print(f"Negative feedback received for {req.asset_path}: {req.reason}")
        
    return {"message": "Feedback collected", "status": "ok"}

@app.get("/status")
async def get_status():
    extractor = AssetExtractor(NARRATIVE_JSON, PROJECT_ROOT)
    data = extractor.extract_all()
    
    summary = {"total": 0, "found": 0, "missing": 0}
    details = []
    
    for asset_type, items in data.items():
        for path, desc in items.items():
            full_path = os.path.join(PROJECT_ROOT, path.replace('/', os.sep))
            exists = os.path.exists(full_path)
            
            summary["total"] += 1
            if exists:
                summary["found"] += 1
            else:
                summary["missing"] += 1
            
            logs_list = task_logs.get(path, [])
            attention_data = attention_mgr.get_focus_tokens(path, desc)
            task_ref = tasks_kv.get(path, {})
            
            details.append({
                "type": asset_type,
                "path": path,
                "description": desc,
                "status": "FOUND" if exists else "MISSING",
                "task_status": task_ref.get("status"),
                "attention": attention_data.get("structured", {}),
                "attention_flat": attention_data.get("positive", []),
                "negative_attention": attention_data.get("negative", []),
                "snapshots": task_ref.get("snapshots", []),
                "last_prompt": task_ref.get("prompt"),
                "logs": logs_list[-5:] if logs_list else []
            })
            
    return {"summary": summary, "details": details, "providers": GeneratorRegistry.list_providers()}

@app.post("/generate")
async def generate_asset(req: GenerationRequest, background_tasks: BackgroundTasks):
    if req.provider not in GeneratorRegistry.list_providers():
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    tasks_kv[req.asset_path] = {"status": "PROCESSING", "provider": req.provider}
    task_logs[req.asset_path] = [f"Initial request (Entropy: {req.entropy}) received for {req.asset_path}"]
    background_tasks.add_task(run_generation_v5, req.provider, req.asset_path, req.description, req.asset_type, req.entropy, req.relationships, req.refinement_passes)
    return {"message": "Task started", "asset": req.asset_path}

async def run_generation_v5(provider_name: str, path: str, description: str, asset_type: str, entropy: float, 
                           relationships: Optional[Dict[str, Any]] = None, refinement_passes: int = 1):
    full_path = os.path.join(PROJECT_ROOT, path.replace('/', os.sep))
    logs = task_logs[path]
    
    # Look up rejected reasons for this asset
    feedback_file = os.path.join(PROJECT_ROOT, "feedback.jsonl")
    rejected_reasons = []
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    fb = json.loads(line.strip())
                    if fb.get('asset_path') == path and fb.get('status') == 'DISLIKED' and fb.get('reason'):
                        rejected_reasons.append(fb['reason'])
                except:
                    pass
    
    try:
        # Stage 1: Attention-driven Refinement with Entropy
        logs.append(f"Stage 1/3: Deep Refinement (Entropy={entropy})...")
        await asyncio.sleep(1)
        
        attention = attention_mgr.get_focus_tokens(path, description, rejected_reasons)
        refinement_result = refiner.refine(asset_type, description, attention, entropy, relationships, refinement_passes, rejected_reasons)
        
        prompt = refinement_result["prompt"]
        neg_prompt = refinement_result["negative_prompt"]
        tasks_kv[path]["prompt"] = prompt
        if "snapshots" in refinement_result:
            tasks_kv[path]["snapshots"] = refinement_result["snapshots"]
        
        # Log visual vibe for future BGM resonance
        if asset_type in ["背景图", "人物立绘"]:
            attention_mgr.update_resonance(path, description)
            logs.append(f"Visual Atmosphere cached for resonance.")
            
        logs.append(f"Attention Spotlight: {', '.join(attention['positive'])}")
        logs.append(f"Refined Prompt: {prompt}")
        if neg_prompt:
            logs.append(f"Negative Attention: {neg_prompt}")
        
        # Stage 2: AI Generation
        logs.append(f"Stage 2/3: Generating via {provider_name}...")
        await asyncio.sleep(2)
        generator = GeneratorRegistry.get_generator(provider_name)
        if not generator:
            raise Exception(f"Provider {provider_name} not found")
            
        success = generator.generate(prompt, full_path)
        
        # Stage 3: Metadata Finalization
        if success:
            logs.append("Stage 3/3: Finalizing production assets...")
            await asyncio.sleep(0.5)
            tasks_kv[path]["status"] = "COMPLETED"
            logs.append("Task successfully completed.")
        else:
            tasks_kv[path]["status"] = "FAILED"
            logs.append("Error: Model generation failed.")
            
    except Exception as e:
        tasks_kv[path]["status"] = "FAILED"
        logs.append(f"Critical System Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import sys
    sys.path.append(PROJECT_ROOT)
    uvicorn.run(app, host="0.0.0.0", port=8088)
