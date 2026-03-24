import os
import shutil
import tempfile
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation_platform.api.state import asset_registry
from foundation_platform.api.models import GodotExportRequest

router = APIRouter(prefix="/export", tags=["Export"])

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

@router.post("/godot")
async def export_to_godot(req: GodotExportRequest):
    """
    Phase 40: Bundle assets + script data into a single Godot-ready ZIP.
    Accepts the full editor store JSON from the frontend.
    """
    output_dir = os.path.join(PROJECT_ROOT, "output")
    audit_file = os.path.join(output_dir, "narrative_audit.json")
    
    # Build resource map from audit (backward compat)
    resources_map = {}
    if os.path.exists(audit_file):
        with open(audit_file, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
            for asset in audit_data.get('details', []):
                if asset.get('status') == 'FOUND':
                    key = asset['path'].split('assets/')[-1]
                    resources_map[key] = {
                        "type": asset.get('type'),
                        "description": asset.get('description'),
                        "entropy": asset.get('entropy'),
                        "character": asset.get('speaker') or asset.get('listener')
                    }
    
    temp_dir = tempfile.mkdtemp()
    target_zip = os.path.join(temp_dir, "godot_assets_export")
    staging_dir = os.path.join(temp_dir, "staging")
    os.makedirs(staging_dir)
    
    # 1. Copy assets directory (portraits, backgrounds, bgm, sfx, cgs, etc.)
    if os.path.exists(ASSETS_DIR):
        staging_assets = os.path.join(staging_dir, "assets")
        shutil.copytree(ASSETS_DIR, staging_assets)
    
    # 2. Write resource manifest
    with open(os.path.join(staging_dir, "resources.json"), 'w', encoding='utf-8') as f:
        json.dump(resources_map, f, ensure_ascii=False, indent=2)
    
    # 3. Phase 40: Write the full script/dialogue data
    try:
        script_data = json.loads(req.script_json)
        with open(os.path.join(staging_dir, "script.json"), 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        # If parsing fails, write raw string as-is
        with open(os.path.join(staging_dir, "script.json"), 'w', encoding='utf-8') as f:
            f.write(req.script_json)
        
    zip_path = shutil.make_archive(target_zip, 'zip', staging_dir)
    return FileResponse(zip_path, filename="godot_assets.zip", media_type="application/zip")
