extends Node

const CHAPTER_TREE_SCENE_PATH := "res://scenes/chapter_tree_select.tscn"
const CHAPTER_SELECT_SCENE_PATH := "res://scenes/chapter_select.tscn"
const LEGACY_TIMELINE_ID := "orient_express"

var chapter_ui: Control


func _ready() -> void:
	if Dialogic and not Dialogic.timeline_ended.is_connected(_on_timeline_ended):
		Dialogic.timeline_ended.connect(_on_timeline_ended)
	if Dialogic and not Dialogic.signal_event.is_connected(_on_dialogic_signal):
		Dialogic.signal_event.connect(_on_dialogic_signal)

	if Dialogic and Dialogic.current_timeline != null:
		return

	await get_tree().process_frame
	_show_chapter_entry()

func _on_timeline_ended() -> void:
	_show_chapter_entry()

func _on_dialogic_signal(argument: String) -> void:
	if argument.begins_with("next_chapter:"):
		var target_chapter = argument.trim_prefix("next_chapter:")
		if target_chapter.begins_with("chapter_"):
			target_chapter = target_chapter.trim_prefix("chapter_")
			
		var progress = get_node_or_null("/root/ChapterProgress")
		if progress:
			progress.unlocked[target_chapter] = true
			progress._save_state()


func _show_chapter_entry() -> void:
	if is_instance_valid(chapter_ui):
		return

	var chapter_scene: PackedScene = load(CHAPTER_TREE_SCENE_PATH)
	if chapter_scene == null:
		push_error("[Main] Failed to load chapter tree scene: %s" % CHAPTER_TREE_SCENE_PATH)
		_show_fallback_chapter_select("Tree scene load failed.")
		return

	chapter_ui = chapter_scene.instantiate()
	if chapter_ui == null:
		push_error("[Main] Failed to instantiate chapter tree scene.")
		_show_fallback_chapter_select("Tree scene instantiate failed.")
		return
	add_child(chapter_ui)


func _show_fallback_chapter_select(reason: String = "") -> void:
	var chapter_scene: PackedScene = load(CHAPTER_SELECT_SCENE_PATH)
	if chapter_scene == null:
		push_error("[Main] Failed to load fallback chapter select scene: %s" % CHAPTER_SELECT_SCENE_PATH)
		_start_legacy_timeline()
		return

	chapter_ui = chapter_scene.instantiate()
	if chapter_ui == null:
		push_error("[Main] Failed to instantiate fallback chapter select scene.")
		_start_legacy_timeline()
		return
	add_child(chapter_ui)
	if not reason.is_empty():
		var status_label: Node = chapter_ui.get_node_or_null("MarginContainer/VBoxContainer/StatusLabel")
		if status_label and status_label is Label:
			status_label.text = "Fallback mode: %s Check console errors for tree scene." % reason


func _start_legacy_timeline() -> void:
	if not Dialogic.timeline_exists(LEGACY_TIMELINE_ID):
		push_error("[Main] Legacy timeline not found: %s. Run import_orient_express.py to generate timeline files." % LEGACY_TIMELINE_ID)
		return
	Dialogic.start(LEGACY_TIMELINE_ID)
