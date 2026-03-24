import os
import shutil
import tempfile
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from foundation_platform.core.config import PROJECT_ROOT

router = APIRouter(prefix="/export", tags=["Export"])

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

@router.get("/godot")
async def export_to_godot():
    output_dir = os.path.join(PROJECT_ROOT, "output")
    audit_file = os.path.join(output_dir, "narrative_audit.json")
    
    if not os.path.exists(ASSETS_DIR):
        raise HTTPException(status_code=404, detail="No assets found to export.")

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
    
    staging_assets = os.path.join(staging_dir, "assets")
    shutil.copytree(ASSETS_DIR, staging_assets)
    
    with open(os.path.join(staging_dir, "resources.json"), 'w', encoding='utf-8') as f:
        json.dump(resources_map, f, ensure_ascii=False, indent=2)
        
    zip_path = shutil.make_archive(target_zip, 'zip', staging_dir)
    return FileResponse(zip_path, filename="godot_assets.zip", media_type="application/zip")
