import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

OUTPUT_DIR_TIMELINES = Path("dialogic/timelines")
OUTPUT_DIR_CHARACTERS = Path("dialogic/characters")
OUTPUT_FILENAME = "orient_express.dtl"
OUTPUT_GRAPH_FILENAME = "chapter_graph.json"
OUTPUT_VARIABLES_FILENAME = "variable_defaults.json"
OUTPUT_ENTRY_FILENAME = "chapter_entries.json"
ASSETS_DIR_BG = Path("assets/backgrounds")
ASSETS_DIR_PORTRAITS = Path("assets/portraits")
CHAPTER_PREFIX = "chapter_"
ALLOWED_NODE_TYPES = {"segment", "chapter", "dialogue", "choice", "branch"}

BACKGROUND_ALIASES = {
    "Aleppo Station Night": "station_night.png",
    "Taurus Express Inside": "train_compartment.png",
    "Taurus Express Window": "train_window.png",
    "Marmara Hotel Lobby": "hotel_lobby.png",
    "Marmara Hotel Restaurant": "hotel_restaurant.png",
    "Bosphorus View": "hotel_lounge.png",
    "Train Station SNCP": "train_station_night.png",
    "Orient Express Corridor": "train_corridor.png",
    "Orient Express Dining Car": "train_dining_car.png",
    "Orient Express Compartment": "train_compartment_night.png",
    "Snowy Landscape": "mountain_scenery.png",
}


class ParserError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def emit_info(message: str) -> None:
    print(f"[INFO] {message}")


def emit_warn(code: str, message: str) -> None:
    print(f"[WARN][{code}] {message}")


def emit_error(code: str, message: str) -> None:
    print(f"[ERROR][{code}] {message}")


def load_json(filepath: Path) -> dict:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_chars = []
    for ch in value:
        code = ord(ch)
        if code < 32 and ch not in ("\t", "\n"):
            continue
        cleaned_chars.append(ch)
    return "".join(cleaned_chars)


def _clean_inline(value: str) -> str:
    return _clean_text(value).replace("\n", " ")


def sanitize_for_timeline(text: str, text_policy: str, inline: bool = False) -> str:
    cleaned = _clean_text(text)
    if inline or text_policy == "inline-safe":
        return cleaned.replace("\n", " ")
    # preserve newline semantics in single-line DTL by encoding as literal \n
    return cleaned.replace("\n", "\\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate chapterized Dialogic timelines from story JSON."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="",
        help="Path to source JSON. If omitted, auto-discovery is used.",
    )
    parser.add_argument(
        "--input-glob",
        type=str,
        default="*.json",
        help="Glob pattern used for discovery when --input is omitted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on schema/reference issues instead of warning.",
    )
    parser.add_argument(
        "--no-legacy",
        action="store_true",
        help="Do not generate orient_express.dtl legacy output.",
    )
    parser.add_argument(
        "--text-policy",
        choices=["preserve", "inline-safe"],
        default="preserve",
        help="Text sanitization policy for timeline text output.",
    )
    parser.add_argument(
        "--chapter-mode",
        choices=["auto", "segment", "chapter"],
        default="auto",
        help="Chapter split strategy. 'auto' prefers chapter boundaries for chapter/branch schema.",
    )
    return parser.parse_args()


def warn_or_fail(code: str, message: str, strict: bool) -> None:
    if strict:
        raise ParserError(code, message)
    emit_warn(code, message)


def discover_story_json(pattern: str) -> Path:
    candidates: List[Path] = []
    for candidate in Path(".").glob(pattern):
        try:
            data = load_json(candidate)
        except Exception:
            continue
        if isinstance(data, dict) and "characters" in data and "nodes" in data:
            candidates.append(candidate)

    if not candidates:
        raise ParserError("INPUT_NOT_FOUND", f"No JSON file containing 'characters' and 'nodes' matched pattern: {pattern}")
    if len(candidates) > 1:
        names = ", ".join(sorted(str(p.resolve()) for p in candidates))
        raise ParserError(
            "INPUT_AMBIGUOUS",
            "Multiple candidate JSON files found. Please specify --input explicitly. "
            f"Candidates: {names}",
        )
    return candidates[0]


def validate_top_level(data: dict) -> Tuple[List[dict], List[dict]]:
    if not isinstance(data, dict):
        raise ParserError("SCHEMA_TOP_LEVEL", "Top-level JSON must be an object.")

    characters = data.get("characters")
    nodes = data.get("nodes")
    if not isinstance(characters, list):
        raise ParserError("SCHEMA_CHARACTERS", "Top-level 'characters' must be a list.")
    if not isinstance(nodes, list):
        raise ParserError("SCHEMA_NODES", "Top-level 'nodes' must be a list.")
    return characters, nodes


def validate_characters(characters: List[dict], strict: bool) -> None:
    for idx, char in enumerate(characters):
        if not isinstance(char, dict):
            warn_or_fail("SCHEMA_CHAR_OBJECT", f"Character at index {idx} is not an object.", strict)
            continue
        if not char.get("id"):
            warn_or_fail("SCHEMA_CHAR_ID", f"Character at index {idx} missing 'id'.", strict)
        if not char.get("name"):
            warn_or_fail("SCHEMA_CHAR_NAME", f"Character '{char.get('id', idx)}' missing 'name'.", strict)


def collect_and_validate_node_ids(nodes: List[dict], strict: bool) -> Set[str]:
    node_ids: Set[str] = set()

    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            warn_or_fail("SCHEMA_NODE_OBJECT", f"Node at index {idx} is not an object.", strict)
            continue

        node_id = str(node.get("id", "")).strip()
        node_type = str(node.get("type", "")).strip()

        if not node_id:
            warn_or_fail("SCHEMA_NODE_ID", f"Node at index {idx} missing 'id'.", strict)
            continue
        if node_id in node_ids:
            warn_or_fail("SCHEMA_NODE_DUP_ID", f"Duplicate node id detected: {node_id}", strict)
        node_ids.add(node_id)

        if node_type not in ALLOWED_NODE_TYPES:
            warn_or_fail(
                "SCHEMA_NODE_TYPE",
                f"Node '{node_id}' has unsupported type '{node_type}'. Allowed: {sorted(ALLOWED_NODE_TYPES)}",
                strict,
            )
            continue

        if node_type == "dialogue" and "text" not in node:
            warn_or_fail("SCHEMA_DIALOGUE_TEXT", f"Dialogue node '{node_id}' missing 'text'.", strict)

        if node_type == "choice":
            choices = node.get("choices")
            if not isinstance(choices, list):
                warn_or_fail("SCHEMA_CHOICE_LIST", f"Choice node '{node_id}' has invalid 'choices'.", strict)
                continue

            for cidx, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    warn_or_fail(
                        "SCHEMA_CHOICE_ITEM_OBJECT",
                        f"Choice item {cidx} in node '{node_id}' is not an object.",
                        strict,
                    )
                    continue
                if "next" not in choice:
                    warn_or_fail("SCHEMA_CHOICE_NEXT", f"Choice item {cidx} in node '{node_id}' missing 'next'.", strict)
                if "text" not in choice:
                    warn_or_fail("SCHEMA_CHOICE_TEXT", f"Choice item {cidx} in node '{node_id}' missing 'text'.", strict)
                set_variable = choice.get("set_variable")
                if set_variable is not None and not isinstance(set_variable, dict):
                    warn_or_fail(
                        "SCHEMA_CHOICE_SET_VARIABLE",
                        f"Choice item {cidx} in node '{node_id}' has invalid 'set_variable' (expected object).",
                        strict,
                    )

        if node_type == "branch":
            conditions = node.get("conditions")
            if not isinstance(conditions, list):
                warn_or_fail("SCHEMA_BRANCH_CONDITIONS", f"Branch node '{node_id}' has invalid 'conditions'.", strict)
                continue

            for cidx, condition in enumerate(conditions):
                if not isinstance(condition, dict):
                    warn_or_fail(
                        "SCHEMA_BRANCH_CONDITION_OBJECT",
                        f"Condition {cidx} in branch '{node_id}' is not an object.",
                        strict,
                    )
                    continue
                if "next" not in condition:
                    warn_or_fail(
                        "SCHEMA_BRANCH_CONDITION_NEXT",
                        f"Condition {cidx} in branch '{node_id}' missing 'next'.",
                        strict,
                    )

    return node_ids


def validate_references(nodes: List[dict], node_ids: Set[str], strict: bool) -> None:
    for node in nodes:
        if not isinstance(node, dict):
            continue

        node_id = str(node.get("id", "<unknown>"))
        next_id = node.get("next")
        if next_id and str(next_id) not in node_ids:
            warn_or_fail("REF_NEXT_MISSING", f"Node '{node_id}' references missing next node '{next_id}'.", strict)

        if node.get("type") == "choice":
            for choice in node.get("choices", []):
                if not isinstance(choice, dict):
                    continue
                choice_next = choice.get("next")
                if choice_next and str(choice_next) not in node_ids:
                    warn_or_fail(
                        "REF_CHOICE_NEXT_MISSING",
                        f"Choice in node '{node_id}' references missing next node '{choice_next}'.",
                        strict,
                    )

        if node.get("type") == "branch":
            for condition in node.get("conditions", []):
                if not isinstance(condition, dict):
                    continue
                branch_next = condition.get("next")
                if branch_next and str(branch_next) not in node_ids:
                    warn_or_fail(
                        "REF_BRANCH_NEXT_MISSING",
                        f"Condition in branch '{node_id}' references missing next node '{branch_next}'.",
                        strict,
                    )


def validate_schema(data: dict, strict: bool) -> None:
    characters, nodes = validate_top_level(data)
    validate_characters(characters, strict)
    node_ids = collect_and_validate_node_ids(nodes, strict)
    validate_references(nodes, node_ids, strict)


def create_character_files(characters: List[dict], output_dir: Path) -> None:
    ensure_directory(output_dir)
    emit_info(f"Generating {len(characters)} characters...")

    for char in characters:
        char_id = str(char.get("id", "")).strip()
        display_name = _clean_inline(str(char.get("name", char_id)).strip() or char_id)
        if not char_id:
            continue

        file_path = output_dir / f"{char_id}.dch"
        portrait_path = ASSETS_DIR_PORTRAITS / f"{char_id}.png"
        has_portrait = portrait_path.exists()

        default_portrait = char_id if has_portrait else ""
        portraits_str = "{}"

        if has_portrait:
            portraits_str = f"""{{
"{char_id}": {{
"export_overrides": {{
"image": "res://assets/portraits/{char_id}.png"
}},
"mirror": false,
"offset": Vector2(0, 0),
"scale": 1,
"scene": ""
}}
}}"""

        content = f"""{{
"class_name": "DialogicCharacter",
"@path": "res://addons/dialogic/Resources/character.gd",
"@subpath": NodePath(""),
"_translation_id": "",
"color": Color(1, 1, 1, 1),
"custom_info": {{
}},
"default_portrait": "{default_portrait}",
"description": "",
"display_name": "{display_name}",
"mirror": false,
"nicknames": ["{display_name}"],
"offset": Vector2(0, 0),
"portraits": {portraits_str},
"scale": 1.0
}}"""
        file_path.write_text(content, encoding="utf-8")
        emit_info(f"  Created {file_path.as_posix()}")


def _normalize_chapter_id(raw_id: str) -> str:
    for suffix in ("_start", "_end"):
        if raw_id.endswith(suffix):
            return raw_id[: -len(suffix)]
    return raw_id


def _is_chapter_end(node: dict) -> bool:
    if node.get("type") != "chapter":
        return False
    node_id = str(node.get("id", ""))
    title = str(node.get("title", ""))
    return node_id.startswith("end_") or node_id.endswith("_end") or ("结束" in title)


def _is_chapter_start(node: dict, entry_start_ids: Set[str]) -> bool:
    if node.get("type") != "chapter":
        return False
    node_id = str(node.get("id", ""))
    if node_id in entry_start_ids:
        return True
    if node_id.endswith("_start"):
        return True
    if _is_chapter_end(node):
        return False
    return bool(str(node.get("next", "")).strip())


def split_story_chapters(data: dict, nodes: List[dict], chapter_mode: str) -> List[dict]:
    entry_points = data.get("entry_points", {})
    entry_start_ids: Set[str] = set()
    if isinstance(entry_points, dict):
        for value in entry_points.values():
            if value:
                entry_start_ids.add(str(value))

    segment_indices = [i for i, n in enumerate(nodes) if n.get("type") == "segment"]
    chapter_start_indices = [i for i, n in enumerate(nodes) if _is_chapter_start(n, entry_start_ids)]

    has_branch = any(isinstance(n, dict) and n.get("type") == "branch" for n in nodes)
    has_top_variables = isinstance(data.get("variables"), dict) and len(data.get("variables", {})) > 0
    prefers_chapter_mode = bool(chapter_start_indices) and (has_branch or has_top_variables or bool(entry_start_ids))

    if chapter_mode == "segment":
        start_indices = segment_indices
        mode_used = "segment"
    elif chapter_mode == "chapter":
        start_indices = chapter_start_indices
        mode_used = "chapter"
    else:
        if prefers_chapter_mode:
            start_indices = chapter_start_indices
            mode_used = "chapter"
        elif segment_indices:
            start_indices = segment_indices
            mode_used = "segment"
        else:
            start_indices = chapter_start_indices
            mode_used = "chapter"

    if not start_indices:
        raise ParserError("SCHEMA_CHAPTER_MISSING", "No segment/chapter start nodes found in JSON.")

    emit_info(f"Chapter split mode: {mode_used} (starts={len(start_indices)})")
    chapters: List[dict] = []
    is_segment_mode = mode_used == "segment"

    for chapter_order, start_index in enumerate(start_indices, start=1):
        end_index = (
            start_indices[chapter_order] - 1
            if chapter_order < len(start_indices)
            else len(nodes) - 1
        )
        chapter_node = nodes[start_index]
        raw_id = str(chapter_node["id"])
        chapter_id = raw_id if is_segment_mode else _normalize_chapter_id(raw_id)
        chapters.append(
            {
                "id": chapter_id,
                "title": _clean_inline(str(chapter_node.get("title", chapter_id))),
                "order": chapter_order,
                "start_node_id": raw_id,
                "start_index": start_index,
                "end_index": end_index,
                "nodes": nodes[start_index : end_index + 1],
            }
        )
    return chapters


def collect_variable_defaults(data: dict) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {}
    raw = data.get("variables", {})
    if isinstance(raw, dict):
        for key, value in raw.items():
            var_name = str(key).strip()
            if var_name:
                # Dialogic expressions can fail on null defaults; normalize to empty string.
                defaults[var_name] = "" if value is None else value
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            var_name = str(item.get("id", item.get("name", ""))).strip()
            if not var_name:
                continue
            raw_value = item.get("value", item.get("default", ""))
            defaults[var_name] = "" if raw_value is None else raw_value
    return defaults

def build_node_index(nodes: List[dict], chapters: List[dict]) -> Tuple[Dict[str, int], Dict[str, str], Dict[str, str]]:
    index_map = {str(node["id"]): i for i, node in enumerate(nodes)}
    node_to_chapter: Dict[str, str] = {}
    chapter_start_node: Dict[str, str] = {}

    for chapter in chapters:
        chapter_id = chapter["id"]
        chapter_nodes = chapter["nodes"]
        chapter_start_node[chapter_id] = str(chapter_nodes[0]["id"])
        for node in chapter_nodes:
            node_to_chapter[str(node["id"])] = chapter_id

    return index_map, node_to_chapter, chapter_start_node


def _extract_branch_edges(
    nodes: List[dict],
    node_to_chapter: Dict[str, str],
) -> List[Dict[str, Any]]:
    index_by_id = {str(node.get("id", "")): node for node in nodes if isinstance(node, dict)}
    edges: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()

    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("type", "")) != "chapter":
            continue

        source_node_id = str(node.get("id", ""))
        branch_id = str(node.get("next", "")).strip()
        if not branch_id:
            continue
        branch_node = index_by_id.get(branch_id, {})
        if not isinstance(branch_node, dict) or str(branch_node.get("type", "")) != "branch":
            continue

        source_chapter_id = node_to_chapter.get(source_node_id, _normalize_chapter_id(source_node_id))
        conditions = branch_node.get("conditions", [])
        if not isinstance(conditions, list):
            continue
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            next_id = str(condition.get("next", "")).strip()
            if not next_id:
                continue
            target_chapter_id = node_to_chapter.get(next_id, _normalize_chapter_id(next_id))
            if not target_chapter_id or target_chapter_id == source_chapter_id:
                continue
            key = (source_chapter_id, target_chapter_id)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "from_chapter_id": source_chapter_id,
                    "to_chapter_id": target_chapter_id,
                    "via_node_id": branch_id,
                    "choice_text": _clean_inline(
                        f"{condition.get('variable', 'branch')}={condition.get('value', '')}"
                    ),
                }
            )
    return edges


def _append_edge(
    edges: List[Dict[str, Any]],
    seen: Set[Tuple[str, str]],
    from_chapter_id: str,
    to_chapter_id: str,
    via_node_id: str,
    choice_text: str,
) -> None:
    if not from_chapter_id or not to_chapter_id or from_chapter_id == to_chapter_id:
        return
    key = (from_chapter_id, to_chapter_id)
    if key in seen:
        return
    seen.add(key)
    edges.append(
        {
            "from_chapter_id": from_chapter_id,
            "to_chapter_id": to_chapter_id,
            "via_node_id": via_node_id,
            "choice_text": _clean_inline(choice_text),
        }
    )


def _extract_chapter_next_edges(
    nodes: List[dict],
    node_to_chapter: Dict[str, str],
) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for node in nodes:
        if not isinstance(node, dict) or str(node.get("type", "")) != "chapter":
            continue
        from_node_id = str(node.get("id", "")).strip()
        raw_next = node.get("next")
        if raw_next is None:
            continue
        next_id = str(raw_next).strip()
        if not from_node_id or not next_id:
            continue
        from_chapter_id = node_to_chapter.get(from_node_id, "")
        to_chapter_id = node_to_chapter.get(next_id, "")
        if not from_chapter_id or not to_chapter_id:
            continue
        _append_edge(
            edges,
            seen,
            from_chapter_id,
            to_chapter_id,
            via_node_id=from_node_id,
            choice_text="chapter.next",
        )
    return edges


def _extract_next_edges(
    nodes: List[dict],
    node_to_chapter: Dict[str, str],
) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type", ""))
        if node_type in ("choice", "branch", "chapter"):
            continue
        from_node_id = str(node.get("id", "")).strip()
        raw_next = node.get("next")
        if raw_next is None:
            continue
        next_id = str(raw_next).strip()
        if not from_node_id or not next_id:
            continue
        from_chapter_id = node_to_chapter.get(from_node_id, "")
        to_chapter_id = node_to_chapter.get(next_id, "")
        _append_edge(
            edges,
            seen,
            from_chapter_id,
            to_chapter_id,
            via_node_id=from_node_id,
            choice_text="%s.next" % node_type if node_type else "next",
        )
    return edges


def _extract_choice_edges(
    nodes: List[dict],
    node_to_chapter: Dict[str, str],
) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != "choice":
            continue
        from_node_id = str(node.get("id", "")).strip()
        from_chapter_id = node_to_chapter.get(from_node_id, "")
        if not from_node_id or not from_chapter_id:
            continue
        for choice in node.get("choices", []):
            if not isinstance(choice, dict):
                continue
            next_id = str(choice.get("next", "")).strip()
            if not next_id:
                continue
            to_chapter_id = node_to_chapter.get(next_id, "")
            _append_edge(
                edges,
                seen,
                from_chapter_id,
                to_chapter_id,
                via_node_id=from_node_id,
                choice_text=str(choice.get("text", "")),
            )
    return edges


def build_chapter_graph(
    chapters: List[dict],
    nodes: List[dict],
    node_to_chapter: Dict[str, str],
    entry_points: Dict[str, Any],
) -> Dict[str, Any]:
    chapter_nodes: List[Dict[str, Any]] = []
    for chapter in chapters:
        chapter_id = str(chapter["id"])
        chapter_nodes.append(
            {
                "chapter_id": chapter_id,
                "timeline_id": f"{CHAPTER_PREFIX}{chapter_id}",
                "title": str(chapter.get("title", chapter_id)),
                "order": int(chapter.get("order", 0)),
            }
        )

    all_edges: List[Dict[str, Any]] = []
    seen_edges: Set[Tuple[str, str]] = set()
    for group in (
        _extract_branch_edges(nodes, node_to_chapter),
        _extract_chapter_next_edges(nodes, node_to_chapter),
        _extract_next_edges(nodes, node_to_chapter),
        _extract_choice_edges(nodes, node_to_chapter),
    ):
        for edge in group:
            if not isinstance(edge, dict):
                continue
            from_id = str(edge.get("from_chapter_id", "")).strip()
            to_id = str(edge.get("to_chapter_id", "")).strip()
            _append_edge(
                all_edges,
                seen_edges,
                from_id,
                to_id,
                via_node_id=str(edge.get("via_node_id", "")),
                choice_text=str(edge.get("choice_text", "")),
            )

    has_incoming = {str(edge.get("to_chapter_id", "")).strip() for edge in all_edges}
    detected_entries = [str(chapter["id"]) for chapter in chapters if str(chapter["id"]) not in has_incoming]
    
    # Fallback to chapters[0] if somehow everything has incoming edges
    if not detected_entries and chapters:
        detected_entries = [str(chapters[0]["id"])]

    # We keep entry_chapter_id as the first one for backwards compatibility,
    # but introduce "entry_points" array for multiple parallel roots.
    primary_entry = detected_entries[0] if detected_entries else ""

    return {
        "version": "1.1",
        "entry_chapter_id": primary_entry,
        "entry_timeline_id": f"{CHAPTER_PREFIX}{primary_entry}" if primary_entry else "",
        "entry_points": detected_entries,
        "nodes": chapter_nodes,
        "edges": all_edges,
    }


def build_chapter_entries(
    chapters: List[dict],
    data: dict,
    node_to_chapter: Dict[str, str],
) -> Dict[str, Any]:
    chapter_items: List[Dict[str, Any]] = []
    chapter_by_id: Dict[str, Dict[str, Any]] = {}
    for chapter in chapters:
        chapter_id = str(chapter["id"])
        item = {
            "chapter_id": chapter_id,
            "timeline_id": f"{CHAPTER_PREFIX}{chapter_id}",
            "title": str(chapter.get("title", chapter_id)),
            "order": int(chapter.get("order", 0)),
            "start_node_id": str(chapter.get("start_node_id", "")),
        }
        chapter_items.append(item)
        chapter_by_id[chapter_id] = item

    entries: Dict[str, Dict[str, Any]] = {}
    entry_points = data.get("entry_points", {})
    if isinstance(entry_points, dict):
        for entry_key, node_id in entry_points.items():
            key = str(entry_key).strip()
            node = str(node_id).strip()
            if not key or not node:
                continue
            chapter_id = node_to_chapter.get(node, "")
            if chapter_id and chapter_id in chapter_by_id:
                chapter_item = chapter_by_id[chapter_id]
                entries[key] = {
                    "entry_key": key,
                    "chapter_id": chapter_id,
                    "timeline_id": chapter_item["timeline_id"],
                    "label": "",
                    "title": chapter_item["title"],
                }

    return {
        "version": "1.0",
        "chapters": chapter_items,
        "entries": entries,
    }


def collect_jump_targets(nodes: List[dict]) -> Set[str]:
    jump_targets: Set[str] = set()
    for i, node in enumerate(nodes):
        if node.get("type") == "choice":
            for choice in node.get("choices", []):
                next_id = choice.get("next")
                if next_id:
                    jump_targets.add(str(next_id))
            continue
        if node.get("type") == "branch":
            for condition in node.get("conditions", []):
                next_id = condition.get("next") if isinstance(condition, dict) else None
                if next_id:
                    jump_targets.add(str(next_id))
            default_next = node.get("default")
            if default_next:
                jump_targets.add(str(default_next))
            continue

        next_id = node.get("next")
        if not next_id:
            continue
        next_id = str(next_id)
        if i + 1 >= len(nodes) or str(nodes[i + 1]["id"]) != next_id:
            jump_targets.add(next_id)

    return jump_targets


def background_line(bg_ref: str) -> str:
    clean_bg = _clean_inline(str(bg_ref)).strip()
    if not clean_bg:
        return ""

    if clean_bg.startswith("assets/backgrounds/"):
        clean_bg = clean_bg[len("assets/backgrounds/"):]
    elif clean_bg.startswith("res://assets/backgrounds/"):
        clean_bg = clean_bg[len("res://assets/backgrounds/"):]

    # Try common extensions if missing
    exts = ["", ".png", ".PNG", ".jpg", ".JPG", ".jpeg"]
    for ext in exts:
        test_file = clean_bg + ext
        if (Path(".") / "assets" / "backgrounds" / test_file).exists():
            return f'[background arg="res://assets/backgrounds/{test_file}" fade="1.5"]'
    
    # Check aliases for descriptive names
    alias = BACKGROUND_ALIASES.get(clean_bg)
    if alias and (Path(".") / "assets" / "backgrounds" / alias).exists():
        return f'[background arg="res://assets/backgrounds/{alias}" fade="1.5"]'
    
    # Fallback to direct arg if it looks like a path
    if "." in clean_bg:
        return f'[background arg="res://assets/backgrounds/{clean_bg}" fade="1.5"]'
        
    return f'# [background missing="{clean_bg}"]'

def music_line(music_ref: str) -> str:
    clean_music = _clean_inline(str(music_ref)).strip()
    if not clean_music:
        return ""
        
    if clean_music.startswith("assets/bgm/"):
        clean_music = clean_music[len("assets/bgm/"):]
    elif clean_music.startswith("res://assets/bgm/"):
        clean_music = clean_music[len("res://assets/bgm/"):]
        
    # We'll just emit a music command, Godot will handle the path logic
    return f'[music arg="res://assets/bgm/{clean_music}" fade="1.0"]'

def resolve_next_target(
    next_id: str,
    current_node_id: str,
    current_chapter_id: str,
    node_to_chapter: Dict[str, str],
    chapter_start_node: Dict[str, str],
) -> Tuple[bool, str]:
    if next_id not in node_to_chapter:
        raise ParserError(
            "REF_RESOLVE_NEXT",
            "Unable to resolve jump target. "
            f"current_node={current_node_id}, current_chapter={current_chapter_id}, target_node={next_id}",
        )

    target_chapter = node_to_chapter[next_id]
    if target_chapter == current_chapter_id:
        return False, next_id
    if next_id == chapter_start_node[target_chapter]:
        return True, f"{CHAPTER_PREFIX}{target_chapter}"
    return True, f"{CHAPTER_PREFIX}{target_chapter}/{next_id}"


def _to_dialogic_literal(value: Any, text_policy: str) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return '"' + sanitize_for_timeline(str(value), text_policy=text_policy, inline=True).replace('"', '\\"') + '"'


def _choice_set_lines(choice: dict, text_policy: str) -> List[str]:
    lines: List[str] = []
    set_payload = choice.get("set_variable")
    if not isinstance(set_payload, dict):
        return lines
    for key, value in set_payload.items():
        var_name = _clean_inline(str(key)).strip()
        if not var_name:
            continue
        lines.append(f"set {{{var_name}}} = {_to_dialogic_literal(value, text_policy=text_policy)}")
    return lines


def _variable_init_lines(variable_defaults: Dict[str, Any], text_policy: str) -> List[str]:
    lines: List[str] = []
    for key, value in variable_defaults.items():
        var_name = _clean_inline(str(key)).strip()
        if not var_name:
            continue
        lines.append(f"set {{{var_name}}} = {_to_dialogic_literal(value, text_policy=text_policy)}")
    return lines


def render_chapter_timeline(
    chapter: dict,
    nodes: List[dict],
    index_map: Dict[str, int],
    node_to_chapter: Dict[str, str],
    chapter_start_node: Dict[str, str],
    jump_targets: Set[str],
    entry_start_ids: Set[str],
    variable_defaults: Dict[str, Any],
    text_policy: str,
) -> str:
    lines: List[str] = [
        f"# --- Chapter: {chapter['title']} ---",
        f"# --- ChapterId: {chapter['id']} ---",
        f"# --- ChapterOrder: {chapter['order']} ---",
        "",
    ]
    chapter_id = chapter["id"]

    if chapter.get("start_node_id", "") in entry_start_ids and variable_defaults:
        lines.append("# --- Variable Defaults ---")
        lines.extend(_variable_init_lines(variable_defaults, text_policy=text_policy))
        lines.append("")

    for node in chapter["nodes"]:
        node_id = str(node["id"])
        if node_id in jump_targets:
            lines.append(f"label {node_id}")

        node_type = node.get("type")
        if node_type in ("segment", "chapter"):
            lines.append(f"# --- Segment: {_clean_inline(str(node.get('title', chapter_id)))} ---")

        elif node_type == "dialogue":
            bg = node.get("bg")
            if bg:
                lines.append(background_line(str(bg)))
            
            music = node.get("music")
            if music:
                lines.append(music_line(str(music)))

            text = sanitize_for_timeline(str(node.get("text", "")), text_policy=text_policy)
            speaker = _clean_inline(str(node.get("speaker", ""))).strip()
            lines.append("leave --All--")
            if speaker:
                if speaker != "narrator":
                    lines.append(f"join {speaker} 1")
                lines.append(f"{speaker}: {text}")
            else:
                lines.append(f"narrator: {text}")

            next_id = node.get("next")
            if next_id:
                next_id = str(next_id)
                current_index = index_map[node_id]
                is_linear = (
                    node_to_chapter.get(next_id, "") == chapter_id
                    and
                    current_index + 1 < len(nodes)
                    and str(nodes[current_index + 1]["id"]) == next_id
                )
                if not is_linear:
                    is_ext, target = resolve_next_target(
                        next_id, node_id, chapter_id, node_to_chapter, chapter_start_node
                    )
                    if is_ext:
                        lines.append(f'\t[signal arg="next_chapter:{target}"]')
                        lines.append(f'\t[end_timeline]')
                    else:
                        lines.append(f"\tjump {target}")

        elif node_type == "choice":
            bg = node.get("bg")
            if bg:
                lines.append(background_line(str(bg)))
            
            music = node.get("music")
            if music:
                lines.append(music_line(str(music)))

            if str(chapter_id) == "32":
                lines.append('[wait time="1.0"]')

            for choice in node.get("choices", []):
                choice_text = sanitize_for_timeline(str(choice.get("text", "")), text_policy=text_policy)
                next_id = choice.get("next")
                if not next_id:
                    continue
                next_id = str(next_id)
                is_ext, target = resolve_next_target(
                    next_id, node_id, chapter_id, node_to_chapter, chapter_start_node
                )
                lines.append(f"- {choice_text}")
                for set_line in _choice_set_lines(choice, text_policy=text_policy):
                    lines.append(f"\t{set_line}")
                if is_ext:
                    lines.append(f'\t[signal arg="next_chapter:{target}"]')
                    lines.append(f'\t[end_timeline]')
                else:
                    lines.append(f"\tjump {target}")

        elif node_type == "branch":
            emitted_conditions = 0
            for condition in node.get("conditions", []):
                if not isinstance(condition, dict):
                    continue
                next_id = condition.get("next")
                if not next_id:
                    continue
                next_id = str(next_id)
                is_ext, target = resolve_next_target(
                    next_id, node_id, chapter_id, node_to_chapter, chapter_start_node
                )
                var_name = _clean_inline(str(condition.get("variable", ""))).strip()
                cond_value = _to_dialogic_literal(condition.get("value", ""), text_policy=text_policy)
                keyword = "if" if emitted_conditions == 0 else "elif"
                if var_name:
                    lines.append(f"{keyword} {{{var_name}}} == {cond_value}:")
                else:
                    lines.append(f"{keyword} true:")
                if is_ext:
                    lines.append(f'\t[signal arg="next_chapter:{target}"]')
                    lines.append(f'\t[end_timeline]')
                else:
                    lines.append(f"\tjump {target}")
                emitted_conditions += 1

            default_next = node.get("default")
            if default_next:
                is_ext, target = resolve_next_target(
                    str(default_next), node_id, chapter_id, node_to_chapter, chapter_start_node
                )
                lines.append("else:")
                if is_ext:
                    lines.append(f'\t[signal arg="next_chapter:{target}"]')
                    lines.append(f'\t[end_timeline]')
                else:
                    lines.append(f"\tjump {target}")

        lines.append("")

    return "\n".join(lines)


def render_legacy_timeline(
    nodes: List[dict],
    jump_targets: Set[str],
    variable_defaults: Dict[str, Any],
    text_policy: str,
) -> str:
    lines: List[str] = []
    if variable_defaults:
        lines.append("# --- Variable Defaults ---")
        lines.extend(_variable_init_lines(variable_defaults, text_policy=text_policy))
        lines.append("")

    for i, node in enumerate(nodes):
        node_id = str(node["id"])
        if node_id in jump_targets:
            lines.append(f"label {node_id}")

        node_type = node.get("type")
        if node_type in ("segment", "chapter"):
            lines.append(f"# --- Segment: {_clean_inline(str(node.get('title', 'Unknown')))} ---")

        elif node_type == "dialogue":
            bg = node.get("bg")
            if bg:
                lines.append(background_line(str(bg)))
            
            music = node.get("music")
            if music:
                lines.append(music_line(str(music)))

            text = sanitize_for_timeline(str(node.get("text", "")), text_policy=text_policy)
            speaker = _clean_inline(str(node.get("speaker", ""))).strip()
            lines.append("leave --All--")
            if speaker:
                if speaker != "narrator":
                    lines.append(f"join {speaker} 1")
                lines.append(f"{speaker}: {text}")
            else:
                lines.append(f"narrator: {text}")

            next_id = node.get("next")
            if next_id:
                next_id = str(next_id)
                is_linear = i + 1 < len(nodes) and str(nodes[i + 1]["id"]) == next_id
                if not is_linear:
                    lines.append(f"\tjump {next_id}")

        elif node_type == "choice":
            bg = node.get("bg")
            if bg:
                lines.append(background_line(str(bg)))

            for choice in node.get("choices", []):
                next_id = choice.get("next")
                if not next_id:
                    continue
                lines.append(f"- {sanitize_for_timeline(str(choice.get('text', '')), text_policy=text_policy)}")
                for set_line in _choice_set_lines(choice, text_policy=text_policy):
                    lines.append(f"\t{set_line}")
                lines.append(f"\tjump {str(next_id)}")

        elif node_type == "branch":
            emitted_conditions = 0
            for condition in node.get("conditions", []):
                if not isinstance(condition, dict):
                    continue
                next_id = condition.get("next")
                if not next_id:
                    continue
                keyword = "if" if emitted_conditions == 0 else "elif"
                var_name = _clean_inline(str(condition.get("variable", ""))).strip()
                cond_value = _to_dialogic_literal(condition.get("value", ""), text_policy=text_policy)
                if var_name:
                    lines.append(f"{keyword} {{{var_name}}} == {cond_value}:")
                else:
                    lines.append(f"{keyword} true:")
                lines.append(f"\tjump {str(next_id)}")
                emitted_conditions += 1

            default_next = node.get("default")
            if default_next:
                lines.append("else:")
                lines.append(f"\tjump {str(default_next)}")

        lines.append("")

    return "\n".join(lines)


def cleanup_old_chapter_files(output_dir: Path) -> None:
    for path in output_dir.glob(f"{CHAPTER_PREFIX}*.dtl"):
        path.unlink()


def generate_timelines(
    data: dict,
    output_dir: Path,
    generate_legacy: bool,
    text_policy: str,
    chapter_mode: str,
) -> None:
    ensure_directory(output_dir)
    nodes = data["nodes"]
    chapters = split_story_chapters(data, nodes, chapter_mode=chapter_mode)
    index_map, node_to_chapter, chapter_start_node = build_node_index(nodes, chapters)
    jump_targets = collect_jump_targets(nodes)
    variable_defaults = collect_variable_defaults(data)
    entry_points = data.get("entry_points", {})
    entry_start_ids: Set[str] = set()
    if isinstance(entry_points, dict):
        for value in entry_points.values():
            if value:
                entry_start_ids.add(str(value))

    cleanup_old_chapter_files(output_dir)

    for chapter in chapters:
        filename = f"{CHAPTER_PREFIX}{chapter['id']}.dtl"
        chapter_text = render_chapter_timeline(
            chapter,
            nodes,
            index_map,
            node_to_chapter,
            chapter_start_node,
            jump_targets,
            entry_start_ids,
            variable_defaults,
            text_policy=text_policy,
        )
        file_path = output_dir / filename
        file_path.write_text(chapter_text, encoding="utf-8")
        emit_info(f"Generated chapter timeline: {file_path.as_posix()}")

    graph = build_chapter_graph(chapters, nodes, node_to_chapter, entry_points=entry_points if isinstance(entry_points, dict) else {})
    graph_path = output_dir / OUTPUT_GRAPH_FILENAME
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    emit_info(f"Generated chapter graph: {graph_path.as_posix()}")

    chapter_entries = build_chapter_entries(chapters, data, node_to_chapter)
    chapter_entries_path = output_dir / OUTPUT_ENTRY_FILENAME
    chapter_entries_path.write_text(json.dumps(chapter_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    emit_info(f"Generated chapter entries: {chapter_entries_path.as_posix()}")

    variable_defaults_path = output_dir / OUTPUT_VARIABLES_FILENAME
    variable_defaults_path.write_text(
        json.dumps(variable_defaults, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    emit_info(f"Generated variable defaults: {variable_defaults_path.as_posix()}")

    if generate_legacy:
        legacy_text = render_legacy_timeline(
            nodes,
            jump_targets,
            variable_defaults=variable_defaults,
            text_policy=text_policy,
        )
        legacy_path = output_dir / OUTPUT_FILENAME
        legacy_path.write_text(legacy_text, encoding="utf-8")
        emit_info(f"Generated legacy timeline: {legacy_path.as_posix()}")


def main() -> None:
    args = parse_args()
    try:
        if args.input:
            json_file = Path(args.input)
            if not json_file.exists():
                raise ParserError("INPUT_FILE_NOT_FOUND", f"Input file not found: {json_file}")
        else:
            json_file = discover_story_json(args.input_glob)

        emit_info(f"Using source JSON: {json_file.as_posix()}")
        data = load_json(json_file)
        validate_schema(data, strict=args.strict)

        create_character_files(data["characters"], OUTPUT_DIR_CHARACTERS)
        generate_timelines(
            data,
            OUTPUT_DIR_TIMELINES,
            generate_legacy=not args.no_legacy,
            text_policy=args.text_policy,
            chapter_mode=args.chapter_mode,
        )
        emit_info("Done.")
    except ParserError as exc:
        emit_error(exc.code, exc.message)
        sys.exit(2)


if __name__ == "__main__":
    main()

