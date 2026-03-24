import sqlite3
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "assets.db")

def init_db():
    """初始化数据库并创建表"""
    # 确保 data 目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asset_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT NOT NULL,
        prompt TEXT,
        negative_prompt TEXT,
        seed INTEGER,
        guidance_scale REAL,
        image_url TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 添加 node_id 索引提高查询速度
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_node_id ON asset_variants(node_id)')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

def insert_asset_variant(
    node_id: str,
    image_url: str,
    status: str,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    guidance_scale: Optional[float] = None
) -> Optional[int]:
    """插入一条资产生图记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO asset_variants (node_id, prompt, negative_prompt, seed, guidance_scale, image_url, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (node_id, prompt, negative_prompt, seed, guidance_scale, image_url, status))
    
    last_row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_row_id

def get_variants_by_node(node_id: str) -> List[Dict[str, Any]]:
    """获取某个节点的所有生成历史版本（按时间倒序）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM asset_variants 
    WHERE node_id = ? 
    ORDER BY created_at DESC
    ''', (node_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为 dict 列表
    return [dict(row) for row in rows]


# ──────────── Phase 42: Registry Persistence ────────────

def _ensure_registry_table():
    """Create the asset_registry_items table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asset_registry_items (
        path TEXT PRIMARY KEY,
        asset_type TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        task_status TEXT NOT NULL DEFAULT 'QUEUED',
        last_prompt TEXT NOT NULL DEFAULT ''
    )
    ''')
    conn.commit()
    conn.close()


def save_registry(registry: Dict[str, Dict]) -> None:
    """
    Persist the entire in-memory asset_registry to SQLite.
    Called after extraction/registration to ensure data survives restarts.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _ensure_registry_table()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear and rewrite (simple full-sync strategy)
    cursor.execute('DELETE FROM asset_registry_items')
    
    for asset_type, items in registry.items():
        for path, status_obj in items.items():
            if hasattr(status_obj, 'description'):
                # It's an AssetStatus pydantic model
                desc = status_obj.description
                t_status = status_obj.task_status
                prompt = status_obj.last_prompt
            else:
                # Legacy string format
                desc = str(status_obj)
                t_status = "QUEUED"
                prompt = ""
            
            cursor.execute(
                'INSERT OR REPLACE INTO asset_registry_items (path, asset_type, description, task_status, last_prompt) VALUES (?, ?, ?, ?, ?)',
                (path, asset_type, desc, t_status, prompt)
            )
    
    conn.commit()
    conn.close()
    logger.info(f"Registry persisted: {sum(len(v) for v in registry.values())} items saved.")


def load_registry() -> Dict[str, Dict]:
    """
    Restore asset_registry from SQLite on server startup.
    Returns the reconstructed registry dict: {type: {path: AssetStatus}}.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _ensure_registry_table()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM asset_registry_items')
    rows = cursor.fetchall()
    conn.close()
    
    # Late import to avoid circular dependency
    from foundation_platform.api.models import AssetStatus
    
    registry: Dict[str, Dict] = {}
    for row in rows:
        atype = row['asset_type']
        if atype not in registry:
            registry[atype] = {}
        registry[atype][row['path']] = AssetStatus(
            path=row['path'],
            description=row['description'],
            task_status=row['task_status'],
            last_prompt=row['last_prompt']
        )
    
    logger.info(f"Registry restored: {len(rows)} items loaded from disk.")
    return registry
