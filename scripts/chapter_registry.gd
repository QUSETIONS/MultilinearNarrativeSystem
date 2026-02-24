extends Node

const CHAPTER_PREFIX := "chapter_"
const CHAPTER_HEADER := "# --- Chapter:"
const CHAPTER_ID_HEADER := "# --- ChapterId:"
const CHAPTER_ORDER_HEADER := "# --- ChapterOrder:"
const CHAPTER_GRAPH_PATH := "res://dialogic/timelines/chapter_graph.json"
const CHAPTER_ENTRIES_PATH := "res://dialogic/timelines/chapter_entries.json"
const VARIABLE_DEFAULTS_PATH := "res://dialogic/timelines/variable_defaults.json"

var chapters: Dictionary = {}
var chapter_graph: Dictionary = {}
var chapter_entries: Dictionary = {}
var variable_defaults: Dictionary = {}
var last_error: String = ""

func _chapter_progress() -> Node:
	return get_node_or_null("/root/ChapterProgress")


func _ready() -> void:
	DialogicResourceUtil.update_directory(".dtl")
	rebuild_variable_defaults()
	rebuild_registry()
	rebuild_graph()
	rebuild_entries()


func rebuild_registry() -> bool:
	chapters.clear()
	last_error = ""

	var timeline_dir: Dictionary = DialogicResourceUtil.get_timeline_directory()
	if timeline_dir.is_empty():
		last_error = "Dialogic timeline directory is empty."
		push_warning("[ChapterRegistry] " + last_error)
		return false

	for timeline_id_variant in timeline_dir.keys():
		var timeline_id := str(timeline_id_variant)
		if not timeline_id.begins_with(CHAPTER_PREFIX):
			continue

		var timeline_path := str(timeline_dir[timeline_id_variant])
		if timeline_path.is_empty():
			push_warning("[ChapterRegistry] Empty timeline path for id: %s" % timeline_id)
			continue

		var meta := _read_chapter_meta(timeline_path)
		var chapter_id := str(meta.get("id", timeline_id.trim_prefix(CHAPTER_PREFIX)))
		var title := str(meta.get("title", chapter_id))
		var order := _normalize_order(meta.get("order", 999999))

		chapters[chapter_id] = {
			"id": chapter_id,
			"title": title,
			"order": order,
			"timeline_id": timeline_id,
			"timeline_path": timeline_path,
		}

	if chapters.is_empty():
		last_error = "No chapter timelines found. Ensure chapter_*.dtl files exist."
		push_warning("[ChapterRegistry] " + last_error)
		return false

	rebuild_graph()
	return true


func get_chapter_list() -> Array[Dictionary]:
	var list: Array[Dictionary] = []
	for chapter in chapters.values():
		list.append(chapter)

	list.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var a_order := _normalize_order(a.get("order", 999999))
		var b_order := _normalize_order(b.get("order", 999999))
		if a_order == b_order:
			return str(a.get("id", "")) < str(b.get("id", ""))
		return a_order < b_order
	)

	return list


func start_chapter(chapter_id: String, label_name: String = "", reset_variables: bool = true) -> bool:
	if not chapters.has(chapter_id):
		push_error("[ChapterRegistry] Chapter not found: %s" % chapter_id)
		return false

	var chapter: Dictionary = chapters[chapter_id]
	var timeline_id := str(chapter.get("timeline_id", ""))
	if timeline_id.is_empty():
		push_error("[ChapterRegistry] timeline_id is empty for chapter: %s" % chapter_id)
		return false

	if reset_variables:
		rebuild_variable_defaults()
		_apply_variable_defaults(true)

	if label_name.is_empty():
		Dialogic.start(timeline_id)
	else:
		Dialogic.start(timeline_id, label_name)

	var progress := _chapter_progress()
	if is_instance_valid(progress):
		progress.mark_visited(chapter_id)
		progress.unlock_from_graph(chapter_graph, chapter_id)

	return true


func start_entry(entry_key: String, label_name: String = "", reset_variables: bool = true) -> bool:
	if chapter_entries.is_empty():
		rebuild_entries()
	if chapter_entries.is_empty():
		push_error("[ChapterRegistry] chapter_entries is empty; cannot start entry: %s" % entry_key)
		return false

	var entries: Dictionary = chapter_entries.get("entries", {})
	if not entries.has(entry_key):
		push_error("[ChapterRegistry] Entry key not found: %s" % entry_key)
		return false

	var entry: Dictionary = entries[entry_key]
	var chapter_id := str(entry.get("chapter_id", ""))
	if chapter_id.is_empty():
		push_error("[ChapterRegistry] Entry '%s' has empty chapter_id." % entry_key)
		return false
	if label_name.is_empty():
		label_name = str(entry.get("label", ""))
	return start_chapter(chapter_id, label_name, reset_variables)


func rebuild_entries() -> bool:
	chapter_entries = {
		"version": "1.0",
		"chapters": [],
		"entries": {},
	}
	if not FileAccess.file_exists(CHAPTER_ENTRIES_PATH):
		push_warning("[ChapterRegistry] chapter entries file not found: %s" % CHAPTER_ENTRIES_PATH)
		return false

	var text := FileAccess.get_file_as_string(CHAPTER_ENTRIES_PATH)
	if text.strip_edges().is_empty():
		push_warning("[ChapterRegistry] chapter entries file is empty: %s" % CHAPTER_ENTRIES_PATH)
		return false

	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("[ChapterRegistry] chapter entries parse failed: %s" % CHAPTER_ENTRIES_PATH)
		return false

	chapter_entries = parsed as Dictionary
	return true


func get_chapter_entries() -> Dictionary:
	return chapter_entries.duplicate(true)


func get_entry_list() -> Array[Dictionary]:
	if chapter_entries.is_empty():
		rebuild_entries()

	var chapter_by_id: Dictionary = {}
	var chapters_array: Array = chapter_entries.get("chapters", [])
	for item_variant in chapters_array:
		if item_variant is Dictionary:
			var item: Dictionary = item_variant
			var cid := str(item.get("chapter_id", ""))
			if not cid.is_empty():
				chapter_by_id[cid] = item

	var list: Array[Dictionary] = []
	var entries: Dictionary = chapter_entries.get("entries", {})
	for key_variant in entries.keys():
		var entry_key := str(key_variant)
		var entry_variant: Variant = entries[key_variant]
		if not (entry_variant is Dictionary):
			continue
		var entry: Dictionary = entry_variant
		var chapter_id := str(entry.get("chapter_id", ""))
		var chapter_meta: Dictionary = chapter_by_id.get(chapter_id, {})
		list.append(
			{
				"entry_key": entry_key,
				"chapter_id": chapter_id,
				"timeline_id": str(entry.get("timeline_id", "")),
				"label": str(entry.get("label", "")),
				"title": str(entry.get("title", chapter_meta.get("title", chapter_id))),
				"order": _normalize_order(chapter_meta.get("order", 999999)),
			}
		)

	list.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var ao := _normalize_order(a.get("order", 999999))
		var bo := _normalize_order(b.get("order", 999999))
		if ao == bo:
			return str(a.get("entry_key", "")) < str(b.get("entry_key", ""))
		return ao < bo
	)
	return list


func reset_variables_to_defaults() -> bool:
	var loaded := rebuild_variable_defaults()
	_apply_variable_defaults(true)
	return loaded


func rebuild_variable_defaults() -> bool:
	variable_defaults = {}
	if not FileAccess.file_exists(VARIABLE_DEFAULTS_PATH):
		return false

	var raw_text := FileAccess.get_file_as_string(VARIABLE_DEFAULTS_PATH)
	if raw_text.strip_edges().is_empty():
		return false

	var parsed: Variant = JSON.parse_string(raw_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("[ChapterRegistry] variable_defaults parse failed: %s" % VARIABLE_DEFAULTS_PATH)
		return false

	variable_defaults = parsed as Dictionary
	return true


func _apply_variable_defaults(reset_existing: bool) -> void:
	if not (Dialogic and Dialogic.VAR):
		return
	if variable_defaults.is_empty():
		return

	for key_variant in variable_defaults.keys():
		var key := str(key_variant)
		if key.is_empty():
			continue
		if reset_existing or Dialogic.VAR.get_variable(key, null) == null:
			var target_value: Variant = variable_defaults[key_variant]
			if target_value == null:
				target_value = ""
			if Dialogic.VAR.has(key):
				Dialogic.VAR.set_variable(key, target_value)
			else:
				Dialogic.VAR.var_storage[key] = target_value


func rebuild_graph() -> bool:
	chapter_graph = {
		"version": "1.0",
		"entry_chapter_id": "",
		"entry_timeline_id": "",
		"nodes": [],
		"edges": [],
	}

	if not FileAccess.file_exists(CHAPTER_GRAPH_PATH):
		last_error = "Chapter graph file not found: %s" % CHAPTER_GRAPH_PATH
		push_warning("[ChapterRegistry] " + last_error)
		return false

	var graph_text := FileAccess.get_file_as_string(CHAPTER_GRAPH_PATH)
	if graph_text.strip_edges().is_empty():
		last_error = "Chapter graph file is empty: %s" % CHAPTER_GRAPH_PATH
		push_warning("[ChapterRegistry] " + last_error)
		return false

	var parsed: Variant = JSON.parse_string(graph_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		last_error = "Chapter graph parse failed: %s" % CHAPTER_GRAPH_PATH
		push_warning("[ChapterRegistry] " + last_error)
		return false

	chapter_graph = parsed as Dictionary
	return true


func get_chapter_graph() -> Dictionary:
	return chapter_graph.duplicate(true)


func get_outgoing_chapters(chapter_id: String) -> Array[String]:
	var out: Array[String] = []
	var edges: Array = chapter_graph.get("edges", [])
	for edge_variant in edges:
		if not (edge_variant is Dictionary):
			continue
		var edge: Dictionary = edge_variant
		if str(edge.get("from_chapter_id", "")) != chapter_id:
			continue
		var target := str(edge.get("to_chapter_id", ""))
		if target.is_empty() or out.has(target):
			continue
		out.append(target)
	return out


func _read_chapter_meta(timeline_path: String) -> Dictionary:
	var meta := {
		"title": "",
		"id": "",
		"order": 999999,
	}

	if not FileAccess.file_exists(timeline_path):
		return meta

	var file := FileAccess.open(timeline_path, FileAccess.READ)
	if file == null:
		return meta

	for _i in range(6):
		if file.eof_reached():
			break
		var line := file.get_line().strip_edges()
		if line.begins_with(CHAPTER_HEADER):
			meta["title"] = _extract_header_value(line, CHAPTER_HEADER)
		elif line.begins_with(CHAPTER_ID_HEADER):
			meta["id"] = _extract_header_value(line, CHAPTER_ID_HEADER)
		elif line.begins_with(CHAPTER_ORDER_HEADER):
			meta["order"] = _normalize_order(_extract_header_value(line, CHAPTER_ORDER_HEADER))

	return meta


func _extract_header_value(line: String, prefix: String) -> String:
	var value := line.trim_prefix(prefix).strip_edges()
	if value.ends_with("---"):
		value = value.trim_suffix("---").strip_edges()
	return value


func _normalize_order(raw_order: Variant) -> int:
	if raw_order is int:
		return raw_order
	var text := str(raw_order).strip_edges()
	if text.is_empty() or not text.is_valid_int():
		return 999999
	return int(text)
