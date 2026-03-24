import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from foundation_platform.core.config import PROJECT_ROOT

from foundation_platform.api.routes import assets, export, health, ws, narrative, generation

app = FastAPI(title="Foundation Platform API v32.0 [Refactored]")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
app.mount("/static/assets", StaticFiles(directory=ASSETS_DIR), name="static_assets")

app.include_router(health.router)
app.include_router(ws.router)
app.include_router(narrative.router)
app.include_router(assets.router)
app.include_router(generation.router)
app.include_router(export.router)
