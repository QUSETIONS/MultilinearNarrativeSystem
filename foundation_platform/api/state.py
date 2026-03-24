import asyncio
from typing import Dict, List
from foundation_platform.core.extractor import AssetExtractor
from foundation_platform.core.refiner import PromptRefiner
from foundation_platform.core.attention import AttentionManager
from foundation_platform.api.services.websocket import ConnectionManager

# In-Memory Stores
tasks_kv: Dict[str, Dict] = {}
task_logs: Dict[str, List[str]] = {}
asset_registry: Dict[str, Dict[str, str]] = {}  # {type: {path: AssetStatus}}

manager = ConnectionManager()

# Core engines
extractor = AssetExtractor()
refiner = PromptRefiner()
attention_mgr = AttentionManager()
feedback_lock = asyncio.Lock()
