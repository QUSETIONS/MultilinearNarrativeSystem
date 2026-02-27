import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

CHAPTER_PATTERN = "chapter_*.dtl"
HEADER_KEYS = ["# --- Chapter:", "# --- ChapterId:", "# --- ChapterOrder:"]
VALIDATOR_VERSION = "1.2.0"
GRAPH_FILENAME = "chapter_graph.json"
ENTRIES_FILENAME = "chapter_entries.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate chapter timeline outputs.")
    parser.add_argument("--input", required=True, help="Path to source JSON")
    parser.add_argument(
        "--timelines-dir",
        default="dialogic/timelines",
        help="Timeline output directory",
    )
    parser.add_argument(
        "--no-legacy",
        action="store_true",
        help="Skip orient_express.dtl existence check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary to stdout.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional file path to write JSON summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    timelines_dir = Path(args.timelines_dir)

    checks = []
    checks_total = 0
    checks_passed = 0
    checks_failed = 0

    def emit(level: str, message: str) -> None:
        if not args.json:
            print(f"[{level}] {message}")

    def check_ok(rule_id: str, message: str) -> None:
        nonlocal checks_total, checks_passed
        checks_total += 1
        checks_passed += 1
        checks.append({"rule_id": rule_id, "status": "ok", "message": message})
        emit("OK", f"[{rule_id}] {message}")

    def check_fail(rule_id: str, message: str) -> None:
        nonlocal checks_total, checks_failed
        checks_total += 1
        checks_failed += 1
        checks.append({"rule_id": rule_id, "status": "fail", "message": message})
        emit("FAIL", f"[{rule_id}] {message}")

    def build_report(exit_code: int) -> dict:
        rules_executed = []
        for item in checks:
            rid = item["rule_id"]
            if rid not in rules_executed:
                rules_executed.append(rid)

        return {
            "ok": exit_code == 0,
            "exit_code": exit_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": VALIDATOR_VERSION,
            "input": str(input_path),
            "timelines_dir": str(timelines_dir),
            "no_legacy": bool(args.no_legacy),
            "rules_executed": rules_executed,
            "summary": {
                "passed": checks_passed,
                "failed": checks_failed,
                "total": checks_total,
            },
            "checks": checks,
        }

    def finalize(exit_code: int) -> int:
        report = build_report(exit_code)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(
                f"[SUMMARY] passed={checks_passed} failed={checks_failed} total={checks_total}"
            )

        if args.json_out:
            out_path = Path(args.json_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        return exit_code

    if not input_path.exists():
        check_fail("R000", f"Input JSON not found: {input_path}")
        return finalize(2)

    if not timelines_dir.exists():
        check_fail("R000", f"Timelines dir not found: {timelines_dir}")
        return finalize(2)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    entry_points = data.get("entry_points", {})
    entry_start_ids = set()
    if isinstance(entry_points, dict):
        for value in entry_points.values():
            if value:
                entry_start_ids.add(str(value))

    def is_chapter_end(node: dict) -> bool:
        node_id = str(node.get("id", ""))
        title = str(node.get("title", ""))
        return node_id.startswith("end_") or node_id.endswith("_end") or ("结束" in title)

    def is_chapter_start(node: dict) -> bool:
        if node.get("type") != "chapter":
            return False
        node_id = str(node.get("id", ""))
        if node_id in entry_start_ids:
            return True
        if node_id.endswith("_start"):
            return True
        if is_chapter_end(node):
            return False
        return bool(str(node.get("next", "")).strip())

    segment_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("type") == "segment")
    chapter_start_count = sum(1 for n in nodes if isinstance(n, dict) and is_chapter_start(n))
    has_branch = any(isinstance(n, dict) and n.get("type") == "branch" for n in nodes)
    has_top_variables = isinstance(data.get("variables"), dict) and len(data.get("variables", {})) > 0
    prefers_chapter_mode = chapter_start_count > 0 and (has_branch or has_top_variables or bool(entry_start_ids))
    if prefers_chapter_mode:
        expected_chapters = chapter_start_count
    elif segment_count > 0:
        expected_chapters = segment_count
    else:
        expected_chapters = chapter_start_count

    chapter_files = sorted(timelines_dir.glob(CHAPTER_PATTERN))
    if len(chapter_files) != expected_chapters:
        check_fail(
            "R001",
            f"Chapter file count mismatch: expected={expected_chapters}, actual={len(chapter_files)}",
        )
        return finalize(1)
    check_ok("R001", f"Chapter file count matched: {len(chapter_files)}")

    chapter_ids = {f.stem for f in chapter_files}
    jump_target_issues = []

    for chapter_file in chapter_files:
        lines = chapter_file.read_text(encoding="utf-8").splitlines()

        for idx, expected_prefix in enumerate(HEADER_KEYS):
            if idx >= len(lines) or not lines[idx].startswith(expected_prefix):
                check_fail(
                    "R002",
                    f"Missing/invalid header in {chapter_file}: line {idx+1} expected prefix '{expected_prefix}'",
                )
                return finalize(1)

        text = "\n".join(lines)
        for m in re.finditer(r"^\s*jump\s+([^\s]+)", text, flags=re.M):
            target = m.group(1)
            if target.startswith("chapter_"):
                timeline = target.split("/")[0]
                if timeline not in chapter_ids:
                    line_no = text[: m.start()].count("\n") + 1
                    jump_target_issues.append((chapter_file.name, line_no, target))

    check_ok("R002", "Chapter metadata headers are valid")

    if jump_target_issues:
        for file_name, line_no, target in jump_target_issues:
            check_fail("R003", f"Invalid chapter jump target in {file_name}:{line_no} -> {target}")
        return finalize(1)
    check_ok("R003", "All chapter jump targets are valid")

    if not args.no_legacy:
        legacy_path = timelines_dir / "orient_express.dtl"
        if not legacy_path.exists():
            check_fail("R004", f"Legacy file missing: {legacy_path}")
            return finalize(1)
        check_ok("R004", "Legacy timeline exists")

    graph_path = timelines_dir / GRAPH_FILENAME
    if not graph_path.exists():
        check_fail("R005", f"Chapter graph file missing: {graph_path}")
        return finalize(1)

    try:
        graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as exc:
        check_fail("R005", f"Failed to parse chapter graph JSON: {exc}")
        return finalize(1)

    graph_nodes = graph_data.get("nodes", [])
    if not isinstance(graph_nodes, list) or len(graph_nodes) != len(chapter_files):
        check_fail(
            "R005",
            f"Chapter graph node count mismatch: expected={len(chapter_files)}, actual={len(graph_nodes) if isinstance(graph_nodes, list) else 'invalid'}",
        )
        return finalize(1)
    check_ok("R005", f"Chapter graph nodes matched: {len(graph_nodes)}")

    graph_chapter_ids = {
        str(node.get("chapter_id", "")).strip()
        for node in graph_nodes
        if isinstance(node, dict)
    }
    graph_chapter_ids.discard("")
    edges = graph_data.get("edges", [])
    if not isinstance(edges, list):
        check_fail("R006", "Chapter graph 'edges' must be a list.")
        return finalize(1)
    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            check_fail("R006", f"Chapter graph edge at index {idx} is not an object.")
            return finalize(1)
        from_id = str(edge.get("from_chapter_id", "")).strip()
        to_id = str(edge.get("to_chapter_id", "")).strip()
        if from_id not in graph_chapter_ids or to_id not in graph_chapter_ids:
            check_fail(
                "R006",
                f"Invalid graph edge at index {idx}: from='{from_id}' to='{to_id}'",
            )
            return finalize(1)
    check_ok("R006", "Chapter graph edges reference valid chapters")

    entries_path = timelines_dir / ENTRIES_FILENAME
    if not entries_path.exists():
        check_fail("R007", f"Chapter entries file missing: {entries_path}")
        return finalize(1)

    try:
        entries_data = json.loads(entries_path.read_text(encoding="utf-8"))
    except Exception as exc:
        check_fail("R007", f"Failed to parse chapter entries JSON: {exc}")
        return finalize(1)

    entries_chapters = entries_data.get("chapters", [])
    if not isinstance(entries_chapters, list):
        check_fail("R007", "Chapter entries 'chapters' must be a list.")
        return finalize(1)
    for idx, chapter in enumerate(entries_chapters):
        if not isinstance(chapter, dict):
            check_fail("R007", f"Chapter entries chapter at index {idx} is not an object.")
            return finalize(1)
        cid = str(chapter.get("chapter_id", "")).strip()
        tid = str(chapter.get("timeline_id", "")).strip()
        if not cid or not tid:
            check_fail("R007", f"Chapter entries chapter at index {idx} missing chapter_id/timeline_id.")
            return finalize(1)
        if f"chapter_{cid}" != tid:
            check_fail("R007", f"Chapter entries chapter mismatch at index {idx}: chapter_id='{cid}' timeline_id='{tid}'.")
            return finalize(1)
        if cid not in graph_chapter_ids:
            check_fail("R007", f"Chapter entries references unknown chapter_id at index {idx}: '{cid}'.")
            return finalize(1)

    entries_map = entries_data.get("entries", {})
    if not isinstance(entries_map, dict):
        check_fail("R007", "Chapter entries 'entries' must be an object.")
        return finalize(1)
    for entry_key, entry in entries_map.items():
        if not isinstance(entry, dict):
            check_fail("R007", f"Entry '{entry_key}' is not an object.")
            return finalize(1)
        cid = str(entry.get("chapter_id", "")).strip()
        tid = str(entry.get("timeline_id", "")).strip()
        if not cid or not tid:
            check_fail("R007", f"Entry '{entry_key}' missing chapter_id/timeline_id.")
            return finalize(1)
        if cid not in graph_chapter_ids:
            check_fail("R007", f"Entry '{entry_key}' references unknown chapter_id '{cid}'.")
            return finalize(1)
    check_ok("R007", "Chapter entries are valid")

    source_entry_points = data.get("entry_points", {})
    if isinstance(source_entry_points, dict):
        source_keys = {str(k).strip() for k in source_entry_points.keys() if str(k).strip()}
        generated_keys = {str(k).strip() for k in entries_map.keys() if str(k).strip()}
        missing_keys = sorted(source_keys - generated_keys)
        if missing_keys:
            check_fail("R008", f"Missing entry keys in chapter_entries.json: {missing_keys}")
            return finalize(1)
        check_ok("R008", "Source entry_points keys are fully represented")

    check_ok("R999", "Validation passed")
    return finalize(0)


if __name__ == "__main__":
    raise SystemExit(main())

