extends Node

const SAVE_PATH := "user://chapter_progress.json"

var visited: Dictionary = {}
var unlocked: Dictionary = {}


func _ready() -> void:
	_load_state()


func reset_progress(entry_points: Array = []) -> void:
	visited.clear()
	unlocked.clear()
	for entry in entry_points:
		if not str(entry).is_empty():
			unlocked[str(entry)] = true
	_save_state()


func mark_visited(chapter_id: String) -> void:
	if chapter_id.is_empty():
		return
	visited[chapter_id] = true
	unlocked[chapter_id] = true
	_save_state()


func is_visited(chapter_id: String) -> bool:
	return bool(visited.get(chapter_id, false))


func is_unlocked(chapter_id: String) -> bool:
	return bool(unlocked.get(chapter_id, false))


func unlock_from_graph(graph: Dictionary, chapter_id: String) -> void:
	var edges: Array = graph.get("edges", [])
	for edge_variant in edges:
		if not (edge_variant is Dictionary):
			continue
		var edge: Dictionary = edge_variant
		if str(edge.get("from_chapter_id", "")) != chapter_id:
			continue
		var target := str(edge.get("to_chapter_id", ""))
		if target.is_empty():
			continue
		unlocked[target] = true
	_save_state()


func ensure_entries_unlocked(entry_points: Array) -> void:
	var changed = false
	for entry_variant in entry_points:
		var entry = str(entry_variant)
		if entry.is_empty():
			continue
		if not unlocked.has(entry):
			unlocked[entry] = true
			changed = true
	if changed:
		_save_state()

func _save_state() -> void:
	var payload := {
		"visited": visited,
		"unlocked": unlocked,
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		push_warning("[ChapterProgress] Failed to open save file: %s" % SAVE_PATH)
		return
	file.store_string(JSON.stringify(payload))


func _load_state() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var text := FileAccess.get_file_as_string(SAVE_PATH)
	if text.strip_edges().is_empty():
		return
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var parsed_dict: Dictionary = parsed as Dictionary
	visited = parsed_dict.get("visited", {})
	unlocked = parsed_dict.get("unlocked", {})
