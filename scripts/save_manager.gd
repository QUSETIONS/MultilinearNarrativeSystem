extends Node

signal save_completed(slot_id: int)
signal load_completed(slot_id: int)

const MAX_SLOTS: int = 8
const SAVE_DIR: String = "user://saves/"
const MIGRATION_MARKER_PATH: String = "user://saves/legacy_migrated_v1.json"


func _ready() -> void:
	_ensure_save_dir()


func get_slot_count() -> int:
	return MAX_SLOTS


func has_any_slot() -> bool:
	for slot_id in range(1, MAX_SLOTS + 1):
		var info := get_slot_info(slot_id)
		if not bool(info.get("is_empty", true)):
			return true
	return _has_legacy_quick_slot()


func get_slot_info(slot_id: int) -> Dictionary:
	if not _is_valid_slot(slot_id):
		return _empty_slot_info(slot_id)

	var save_path: String = _get_slot_path(slot_id)
	if not FileAccess.file_exists(save_path):
		if slot_id == 1 and _has_legacy_quick_slot():
			return {
				"slot_id": 1,
				"is_empty": false,
				"timestamp": "Legacy",
				"chapter_name": "Legacy Quick Save",
				"thumbnail": "",
				"exists": true,
				"is_legacy": true
			}
		return _empty_slot_info(slot_id)

	var data: Dictionary = _read_save_file(save_path)
	if data.is_empty():
		return _empty_slot_info(slot_id)

	return {
		"slot_id": slot_id,
		"is_empty": false,
		"timestamp": str(data.get("timestamp", "")),
		"chapter_name": str(data.get("chapter_name", "")),
		"thumbnail": str(data.get("thumbnail", "")),
		"exists": true
	}


func save_game(slot_id: int) -> bool:
	if not _is_valid_slot(slot_id):
		return false

	if not is_instance_valid(Dialogic):
		push_error("[SaveManager] Dialogic autoload is unavailable.")
		return false

	_ensure_save_dir()

	var save_data: Dictionary = {
		"timestamp": Time.get_datetime_string_from_system(),
		"chapter_name": _get_current_chapter_name(),
		"dialogic_state": _state_to_dict(Dialogic.get_full_state()),
		"dialogic_state_blob": Marshalls.variant_to_base64(Dialogic.get_full_state()),
		"thumbnail": _capture_thumbnail_base64()
	}

	var saved: bool = _write_save_file(_get_slot_path(slot_id), save_data)
	if saved:
		_write_migration_marker()
		save_completed.emit(slot_id)

	return saved


func load_game(slot_id: int) -> bool:
	if not _is_valid_slot(slot_id):
		return false

	if not is_instance_valid(Dialogic):
		push_error("[SaveManager] Dialogic autoload is unavailable.")
		return false

	var save_path: String = _get_slot_path(slot_id)
	if not FileAccess.file_exists(save_path):
		if slot_id == 1 and _has_legacy_quick_slot():
			Dialogic.Save.load("")
			_attempt_migrate_legacy_slot_to_new_format()
			load_completed.emit(slot_id)
			return true
		push_warning("[SaveManager] Save slot %d is empty." % slot_id)
		return false

	var data: Dictionary = _read_save_file(save_path)
	if data.is_empty():
		return false

	var state: DialogicSaveState = _extract_state_from_save(data)
	if state == null:
		push_error("[SaveManager] Invalid state payload in slot %d." % slot_id)
		return false

	Dialogic.load_full_state(state)
	_write_migration_marker()
	load_completed.emit(slot_id)
	return true


func delete_save(slot_id: int) -> bool:
	if not _is_valid_slot(slot_id):
		return false

	var save_path: String = _get_slot_path(slot_id)
	if not FileAccess.file_exists(save_path):
		return true

	var error: int = DirAccess.remove_absolute(save_path)
	if error != OK:
		push_error("[SaveManager] Failed to delete slot %d (error %d)." % [slot_id, error])
		return false

	return true


func get_all_slots() -> Array[Dictionary]:
	var slots: Array[Dictionary] = []
	for slot_id in range(1, MAX_SLOTS + 1):
		slots.append(get_slot_info(slot_id))
	return slots


func _ensure_save_dir() -> void:
	if DirAccess.dir_exists_absolute(SAVE_DIR):
		return

	var error: int = DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	if error != OK:
		push_error("[SaveManager] Failed to create save directory (error %d)." % error)


func _is_valid_slot(slot_id: int) -> bool:
	if slot_id < 1 or slot_id > MAX_SLOTS:
		push_warning("[SaveManager] Invalid slot id: %d" % slot_id)
		return false
	return true


func _get_slot_path(slot_id: int) -> String:
	return SAVE_DIR.path_join("save_%d.json" % slot_id)


func _empty_slot_info(slot_id: int) -> Dictionary:
	return {
		"slot_id": slot_id,
		"is_empty": true,
		"timestamp": "",
		"chapter_name": "",
		"thumbnail": "",
		"exists": false
	}


func _read_save_file(save_path: String) -> Dictionary:
	var file: FileAccess = FileAccess.open(save_path, FileAccess.READ)
	if file == null:
		push_error("[SaveManager] Failed to open save file: %s" % save_path)
		return {}

	var json_text: String = file.get_as_text()
	var parsed_variant: Variant = JSON.parse_string(json_text)
	if not (parsed_variant is Dictionary):
		push_error("[SaveManager] Save file is invalid JSON: %s" % save_path)
		return {}

	return parsed_variant as Dictionary


func _write_save_file(save_path: String, save_data: Dictionary) -> bool:
	var file: FileAccess = FileAccess.open(save_path, FileAccess.WRITE)
	if file == null:
		push_error("[SaveManager] Failed to write save file: %s" % save_path)
		return false

	file.store_string(JSON.stringify(save_data, "\t"))
	return true


func _state_to_dict(state: DialogicSaveState) -> Dictionary:
	if state == null:
		return {}

	return {
		"timeline": state.timeline,
		"event_index": state.event_index,
		"subsystems": state.subsystems
	}


func _dict_to_state(data: Dictionary) -> DialogicSaveState:
	var state: DialogicSaveState = DialogicSaveState.new()
	state.timeline = str(data.get("timeline", ""))
	state.event_index = int(data.get("event_index", -1))

	var raw_subsystems: Variant = data.get("subsystems", {})
	var typed_subsystems: Dictionary[String, Dictionary] = {}
	if raw_subsystems is Dictionary:
		var raw_subsystems_dict: Dictionary = raw_subsystems
		for key in raw_subsystems_dict.keys():
			var subsystem_state: Variant = raw_subsystems_dict.get(key, {})
			if subsystem_state is Dictionary:
				var subsystem_state_dict: Dictionary = subsystem_state
				typed_subsystems[String(key)] = subsystem_state_dict

	state.subsystems = typed_subsystems
	return state


func _extract_state_from_save(data: Dictionary) -> DialogicSaveState:
	var state_blob: String = str(data.get("dialogic_state_blob", ""))
	if not state_blob.is_empty():
		var decoded_variant: Variant = Marshalls.base64_to_variant(state_blob)
		if decoded_variant is DialogicSaveState:
			return decoded_variant as DialogicSaveState

	var raw_state: Variant = data.get("dialogic_state", {})
	if raw_state is Dictionary:
		return _dict_to_state(raw_state as Dictionary)

	return null


func _get_current_chapter_name() -> String:
	if not is_instance_valid(Dialogic):
		return ""

	if Dialogic.current_timeline == null:
		return ""

	if Dialogic.current_timeline.has_method("get_identifier"):
		var identifier: String = str(Dialogic.current_timeline.get_identifier())
		if not identifier.is_empty():
			return identifier

	return str(Dialogic.current_timeline.resource_path)


func _capture_thumbnail_base64() -> String:
	var viewport: Viewport = get_viewport()
	if viewport == null:
		return ""

	var viewport_texture: Texture2D = viewport.get_texture()
	if viewport_texture == null:
		return ""

	var image: Image = viewport_texture.get_image()
	if image == null:
		return ""

	var png_buffer: PackedByteArray = image.save_png_to_buffer()
	if png_buffer.is_empty():
		return ""

	return Marshalls.raw_to_base64(png_buffer)


func _has_legacy_quick_slot() -> bool:
	return is_instance_valid(Dialogic) and Dialogic.Save.has_slot("")


func _attempt_migrate_legacy_slot_to_new_format() -> Dictionary:
	if not _has_legacy_quick_slot():
		return {"migrated": false, "reason": "legacy_not_found"}
	if has_any_slot() and FileAccess.file_exists(_get_slot_path(1)):
		_write_migration_marker()
		return {"migrated": false, "reason": "new_slots_exist"}
	var saved := save_game(1)
	if saved:
		_write_migration_marker()
		return {"migrated": true, "slot": 1}
	return {"migrated": false, "reason": "save_failed"}


func migrate_legacy_slot_if_needed() -> Dictionary:
	if FileAccess.file_exists(MIGRATION_MARKER_PATH):
		return {"migrated": false, "reason": "already_marked"}
	return _attempt_migrate_legacy_slot_to_new_format()


func _write_migration_marker() -> void:
	var file := FileAccess.open(MIGRATION_MARKER_PATH, FileAccess.WRITE)
	if file == null:
		return
	file.store_string(JSON.stringify({
		"timestamp": Time.get_datetime_string_from_system()
	}))
