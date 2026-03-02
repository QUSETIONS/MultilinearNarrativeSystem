extends Node
class_name ChapterEntryUIAdapter

signal entries_loaded(entries: Array[Dictionary])
signal chapter_started(entry_key: String)
signal start_failed(entry_key: String, reason: String)

func _bridge() -> Node:
	return get_node_or_null("/root/ChapterEntryBridge")


func _registry() -> Node:
	return get_node_or_null("/root/ChapterRegistry")


func load_entries() -> Array[Dictionary]:
	var bridge := _bridge()
	if not is_instance_valid(bridge):
		var reason := "ChapterEntryBridge is unavailable."
		push_error("[ChapterEntryUIAdapter] " + reason)
		start_failed.emit("", reason)
		return []

	var entries: Array[Dictionary] = bridge.get_entries()
	entries_loaded.emit(entries)
	return entries


func get_entries_map() -> Dictionary:
	var mapping := {}
	for entry in load_entries():
		var key := str(entry.get("entry_key", "")).strip_edges()
		if key.is_empty():
			continue
		mapping[key] = entry
	return mapping


func start_from_entry(entry_key: String, reset_variables: bool = true) -> bool:
	var bridge := _bridge()
	if not is_instance_valid(bridge):
		var reason := "ChapterEntryBridge is unavailable."
		push_error("[ChapterEntryUIAdapter] " + reason)
		start_failed.emit(entry_key, reason)
		return false

	var ok := bridge.start_entry(entry_key, "", reset_variables)
	if ok:
		chapter_started.emit(entry_key)
		return true

	var reason2 := "Start entry failed."
	var registry := _registry()
	if is_instance_valid(registry):
		var last := str(registry.last_error).strip_edges()
		if not last.is_empty():
			reason2 = last
	start_failed.emit(entry_key, reason2)
	return false


func reset_variables() -> bool:
	var bridge := _bridge()
	if not is_instance_valid(bridge):
		push_error("[ChapterEntryUIAdapter] ChapterEntryBridge is unavailable.")
		return false
	return bridge.reset_story_variables()
