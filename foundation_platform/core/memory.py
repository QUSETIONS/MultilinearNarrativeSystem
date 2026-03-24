from typing import Dict, List, Any, Optional
import threading

class SharedNarrativeMemory:
    """
    Phase 19: Shared Narrative Memory Buffer (SNMB).
    A persistent, thread-safe store for NAR residuals that spans 
    multiple assets and generation sessions.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SharedNarrativeMemory, cls).__new__(cls)
                cls._instance._storage = []  # Global residuals
                cls._instance._nodes = {}    # Asset-specific residuals: {asset_id: [residuals]}
                cls._instance._edges = {}    # Relationships: {asset_id: {target_id: type}}
                cls._instance._metadata = {"world_state": "Initial"}
            return cls._instance

    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        """Phase 20: Establishes a logical entanglement edge."""
        with self._lock:
            if source_id not in self._edges: self._edges[source_id] = {}
            self._edges[source_id][target_id] = rel_type

    def push(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Adds a new residual, tagging it to an asset node if provided."""
        with self._lock:
            entry = {
                "content": content,
                "metadata": metadata or {}
            }
            asset_id = entry["metadata"].get("asset_id")
            
            # 1. Global storage
            self._storage.append(entry)
            
            # 2. Node-specific storage (Logical Entanglement)
            if asset_id:
                if asset_id not in self._nodes: self._nodes[asset_id] = []
                self._nodes[asset_id].append(entry)
            
            if len(self._storage) > 100:
                self._storage.pop(0)

    def fetch_entangled(self, asset_id: str, max_depth: int = 3, _current_depth: int = 0) -> List[Dict[str, Any]]:
        """Phase 21: Transitive Fetch - recurses through the relationship graph."""
        if _current_depth >= max_depth:
            return []
            
        with self._lock:
            results = list(self._nodes.get(asset_id, []))
            
            # Fetch from neighbors (Transitive Ripple)
            neighbors = self._edges.get(asset_id, {})
            for neighbor_id, rel_type in neighbors.items():
                # Transitive recursion
                neighbor_res = self.fetch_entangled(neighbor_id, max_depth, _current_depth + 1)
                for nr in neighbor_res:
                    # Apply distance-based attention decay metadata
                    enriched_nr = nr.copy()
                    dist = nr["metadata"].get("rel_dist", 0) + 1
                    enriched_nr["metadata"] = {**nr["metadata"], "rel_dist": dist, "rel_type": rel_type}
                    results.append(enriched_nr)
            
            # Deduplicate by content to prevent cycles/redundancy
            unique_results = []
            seen_content = set()
            for r in results:
                if r["content"] not in seen_content:
                    unique_results.append(r)
                    seen_content.add(r["content"])
            return unique_results

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Returns all global residuals."""
        with self._lock:
            return list(self._storage)

    def clear(self):
        """Resets the global narrative clock."""
        with self._lock:
            self._storage = []

def get_shared_memory() -> SharedNarrativeMemory:
    return SharedNarrativeMemory()
