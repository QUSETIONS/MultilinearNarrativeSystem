import os
import json
from fastapi import APIRouter
from foundation_platform.core.generator import GeneratorRegistry

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "models.json")
    model_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            model_config = json.load(f)
    
    return {
        "status": "online",
        "version": "v32.0",
        "providers": GeneratorRegistry.list_providers(),
        "llm_available": bool(model_config.get("deepseek", {}).get("api_key")),
        "image_gen_available": bool(model_config.get("siliconflow", {}).get("api_key")),
        "image_model": model_config.get("siliconflow", {}).get("model", "N/A")
    }
