import argparse
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import import_orient_express as parser


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark chapter parser pipeline in-memory.")
    p.add_argument("--input", required=True, help="Source JSON file")
    p.add_argument("--multipliers", nargs="+", type=int, default=[1, 10, 50])
    return p.parse_args()


def scale_story(data: dict, multiplier: int) -> dict:
    if multiplier == 1:
        return copy.deepcopy(data)

    base_nodes = data["nodes"]
    scaled_nodes = []

    for m in range(multiplier):
        suffix = f"__m{m}"
        id_map = {str(n["id"]): f"{n['id']}{suffix}" for n in base_nodes}

        for node in base_nodes:
            new_node = copy.deepcopy(node)
            old_id = str(new_node["id"])
            new_node["id"] = id_map[old_id]

            if "next" in new_node and new_node["next"]:
                next_old = str(new_node["next"])
                new_node["next"] = id_map.get(next_old, next_old)

            if new_node.get("type") == "choice":
                choices = new_node.get("choices", [])
                for choice in choices:
                    if "next" in choice and choice["next"]:
                        next_old = str(choice["next"])
                        choice["next"] = id_map.get(next_old, next_old)

            scaled_nodes.append(new_node)

    result = copy.deepcopy(data)
    result["nodes"] = scaled_nodes
    return result


def run_benchmark(data: dict, multiplier: int) -> dict:
    scaled = scale_story(data, multiplier)

    t0 = time.perf_counter()
    parser.validate_schema(scaled, strict=True)
    t1 = time.perf_counter()

    nodes = scaled["nodes"]
    chapters = parser.split_segments(nodes)
    index_map, node_to_chapter, chapter_start_node = parser.build_node_index(nodes, chapters)
    jump_targets = parser.collect_jump_targets(nodes)

    render_chars = 0
    for chapter in chapters:
        text = parser.render_chapter_timeline(
            chapter,
            nodes,
            index_map,
            node_to_chapter,
            chapter_start_node,
            jump_targets,
            text_policy="preserve",
        )
        render_chars += len(text)
    t2 = time.perf_counter()

    total_nodes = len(nodes)
    total_seconds = t2 - t0
    sec_per_1k = total_seconds / max(total_nodes, 1) * 1000.0

    return {
        "multiplier": multiplier,
        "nodes": total_nodes,
        "chapters": len(chapters),
        "validate_seconds": round(t1 - t0, 6),
        "render_seconds": round(t2 - t1, 6),
        "total_seconds": round(total_seconds, 6),
        "sec_per_1k_nodes": round(sec_per_1k, 6),
        "render_chars": render_chars,
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))

    results = []
    for m in args.multipliers:
        results.append(run_benchmark(data, m))

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))

    # Soft threshold: >2s per 1k nodes indicates potential performance work.
    over_threshold = [r for r in results if r["sec_per_1k_nodes"] > 2.0]
    if over_threshold:
        print("[WARN] Performance threshold exceeded for:")
        for r in over_threshold:
            print(f"  multiplier={r['multiplier']} sec_per_1k_nodes={r['sec_per_1k_nodes']}")
    else:
        print("[OK] Performance is within threshold (<=2s per 1k nodes).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

