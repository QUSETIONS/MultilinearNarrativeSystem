import json
from collections import Counter

def fix_json():
    with open("东方快车谋杀案修复版.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    
    # First pass: Identify duplicates
    ids = [n["id"] for n in nodes if "id" in n]
    id_counts = Counter(ids)
    duplicates = {id for id, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"Detecting {len(duplicates)} duplicate IDs: {list(duplicates)[:5]}...")
    
    # Second pass: Rename duplicates and track mappings
    id_map = {}
    seen_ids = set()
    
    for node in nodes:
        orig_id = node.get("id")
        if not orig_id: continue
        
        if orig_id in seen_ids:
            # Generate a new unique ID
            counter = 1
            new_id = f"{orig_id}_dup{counter}"
            while new_id in seen_ids or new_id in duplicates:
                counter += 1
                new_id = f"{orig_id}_dup{counter}"
            
            node["id"] = new_id
            seen_ids.add(new_id)
            print(f"Renamed duplicate node {orig_id} -> {new_id}")
        else:
            seen_ids.add(orig_id)

    # Third pass: Fix broken references (existing logic + updated IDs if needed)
    # Note: In this project, duplicates are often redundant blocks, so we don't necessarily 
    # need to update all parents to point to the new ID, but we MUST ensure 'next' pointers 
    # aren't pointing to nothing.
    
    node_ids = seen_ids
    for i, node in enumerate(nodes):
        for field in ["next", "default"]:
            if field in node and isinstance(node[field], str) and node[field] not in node_ids:
                if i + 1 < len(nodes):
                    node[field] = nodes[i+1]["id"]
        
        if "choices" in node and isinstance(node["choices"], list):
            for choice in node["choices"]:
                if "next" in choice and choice["next"] not in node_ids:
                    if i + 1 < len(nodes):
                        choice["next"] = nodes[i+1]["id"]

    with open("东方快车谋杀案修复版.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fix_json()
