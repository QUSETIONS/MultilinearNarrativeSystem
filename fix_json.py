import json

def fix_json():
    with open("东方快车谋杀案合并版.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    node_ids = {n["id"] for n in nodes if "id" in n}

    for i, node in enumerate(nodes):
        if "next" in node and isinstance(node["next"], str) and node["next"] not in node_ids:
            missing = node["next"]
            if i + 1 < len(nodes):
                next_id = nodes[i+1]["id"]
                node["next"] = next_id
                print(f"Fixed {missing} -> {next_id} at node {node['id']}")
                
        if "choices" in node and isinstance(node["choices"], list):
            for choice in node["choices"]:
                if "next" in choice and choice["next"] not in node_ids:
                    missing = choice["next"]
                    if i + 1 < len(nodes):
                        next_id = nodes[i+1]["id"]
                        choice["next"] = next_id
                        print(f"Fixed {missing} -> {next_id} in choice of node {node['id']}")

        if "conditions" in node and isinstance(node["conditions"], list):
            for condition in node["conditions"]:
                if "next" in condition and condition["next"] not in node_ids:
                    missing = condition["next"]
                    if i + 1 < len(nodes):
                        next_id = nodes[i+1]["id"]
                        condition["next"] = next_id
                        print(f"Fixed {missing} -> {next_id} in condition of node {node['id']}")

        if "default" in node and isinstance(node["default"], str) and node["default"] not in node_ids:
            missing = node["default"]
            if i + 1 < len(nodes):
                next_id = nodes[i+1]["id"]
                node["default"] = next_id
                print(f"Fixed branch default {missing} -> {next_id} at node {node['id']}")

    with open("东方快车谋杀案合并版.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fix_json()
