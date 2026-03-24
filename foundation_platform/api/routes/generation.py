import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import shutil
from foundation_platform.api.models import GenerationRequest, VariantGenerateRequest, AssetStatus
from foundation_platform.core.generator import GeneratorRegistry
from foundation_platform.api.state import asset_registry, tasks_kv, task_logs
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation_platform.api.services.generation_service import run_generation_v5
from foundation_platform.api.services.db_service import get_variants_by_node

router = APIRouter(tags=["Generation"])

@router.get("/status")
async def get_status():
    summary = {"total": 0, "found": 0, "missing": 0}
    details = []
    
    for asset_type, items in asset_registry.items():
        for path, target_status in items.items():
            full_path = os.path.join(PROJECT_ROOT, path.replace('/', os.sep))
            exists = os.path.exists(full_path)
            
            if isinstance(target_status, AssetStatus):
                desc = target_status.description
                t_status = target_status.task_status
                prompt = target_status.last_prompt
            else:
                desc = target_status
                t_status = "QUEUED"
                prompt = ""
                
            summary["total"] += 1
            if exists:
                summary["found"] += 1
            else:
                summary["missing"] += 1
                
            details.append({
                "type": asset_type,
                "path": path,
                "description": desc,
                "status": "FOUND" if exists else ("GENERATING" if t_status == "IN_PROGRESS" else "MISSING"),
                "task_status": t_status,
                "last_prompt": prompt
            })
            
    return {"summary": summary, "details": details}

@router.get("/tasks")
async def get_tasks():
    merged_tasks = {}
    for path, data in tasks_kv.items():
        logs = task_logs.get(path, [])
        merged_tasks[path] = {
            "status": data["status"],
            "provider": data.get("provider", "mock"),
            "prompt": data.get("prompt"),
            "logs": logs,
            "snapshots": data.get("snapshots")
        }
    return merged_tasks

class RollbackRequest(BaseModel):
    variant_url: str

@router.post("/assets/{node_id:path}/rollback")
async def rollback_node_variant(node_id: str, req: RollbackRequest):
    """Restore a specific variant as the active asset"""
    canonical_path = os.path.join(PROJECT_ROOT, node_id.replace('/', os.sep))
    v_url = req.variant_url.replace('/static/', '').lstrip('/')
    variant_path = os.path.join(PROJECT_ROOT, v_url.replace('/', os.sep))
    
    if os.path.exists(variant_path):
        shutil.copy(variant_path, canonical_path)
        # Sync simple status
        tasks_kv[node_id] = {"status": "COMPLETED", "provider": "rollback"}
        return {"message": "Rollback successful"}
    raise HTTPException(status_code=404, detail="Variant file not found on disk")

@router.get("/assets/{node_id:path}/variants")
async def get_node_variants(node_id: str):
    """Retrieve history of asset generations for a specific node"""
    variants = get_variants_by_node(node_id)
    return {"node_id": node_id, "variants": variants}

@router.post("/generate-variants")
async def generate_variants(req: VariantGenerateRequest, background_tasks: BackgroundTasks):
    if req.provider not in GeneratorRegistry.list_providers():
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    base_path = req.asset_path
    variant_paths = []
    for i in range(req.count):
        name, ext = os.path.splitext(base_path)
        variant_path = f"{name}_v{i+1}{ext}"
        variant_paths.append(variant_path)
        
        tasks_kv[variant_path] = {"status": "QUEUED", "provider": req.provider}
        task_logs[variant_path] = [f"Variant {i+1}/{req.count} queued"]
        
        background_tasks.add_task(
            run_generation_v5, req.provider, variant_path, 
            req.description, req.asset_type, 
            req.base_entropy + (i * 0.2),
            None, 1, 
            req.seed, 7.5, req.negative_prompt
        )
    
    return {
        "message": f"已启动 {req.count} 个变体生成",
        "variants": variant_paths
    }

@router.post("/generate")
async def generate_asset(req: GenerationRequest, background_tasks: BackgroundTasks):
    if req.provider not in GeneratorRegistry.list_providers():
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    tasks_kv[req.asset_path] = {"status": "PROCESSING", "provider": req.provider}
    task_logs[req.asset_path] = [f"Initial request (Entropy: {req.entropy}, Seed: {req.seed}, Guidance: {req.guidance_scale}) received for {req.asset_path}"]
    background_tasks.add_task(
        run_generation_v5, req.provider, req.asset_path, req.description, req.asset_type, 
        req.entropy, req.relationships, req.refinement_passes, req.seed, req.guidance_scale, req.negative_prompt
    )
    return {"message": "Task started", "asset": req.asset_path}
