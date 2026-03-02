extends Node

## Lightweight bridge for external chapter-selection UIs.
## This script intentionally avoids owning any UI logic.


func _registry() -> Node:
	return get_node_or_null("/root/ChapterRegistry")


func get_entries() -> Array[Dictionary]:
	var registry := _registry()
	if not is_instance_valid(registry):
		push_error("[ChapterEntryBridge] ChapterRegistry is unavailable.")
		return []
	return registry.get_entry_list()


func get_entry(entry_key: String) -> Dictionary:
	var registry := _registry()
	if not is_instance_valid(registry):
		push_error("[ChapterEntryBridge] ChapterRegistry is unavailable.")
		return {}

	var entries_data: Dictionary = registry.get_chapter_entries()
	var entries: Dictionary = entries_data.get("entries", {})
	if not entries.has(entry_key):
		return {}
	var result: Variant = entries[entry_key]
	if result is Dictionary:
		return result
	return {}


func start_entry(entry_key: String, label_name: String = "", reset_variables: bool = true) -> bool:
	var registry := _registry()
	if not is_instance_valid(registry):
		push_error("[ChapterEntryBridge] ChapterRegistry is unavailable.")
		return false
	return registry.start_entry(entry_key, label_name, reset_variables)


func start_chapter(chapter_id: String, label_name: String = "", reset_variables: bool = true) -> bool:
	var registry := _registry()
	if not is_instance_valid(registry):
		push_error("[ChapterEntryBridge] ChapterRegistry is unavailable.")
		return false
	return registry.start_chapter(chapter_id, label_name, reset_variables)


func reset_story_variables() -> bool:
	var registry := _registry()
	if not is_instance_valid(registry):
		push_error("[ChapterEntryBridge] ChapterRegistry is unavailable.")
		return false
	return registry.reset_variables_to_defaults()
