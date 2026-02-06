extends Control

const SAVE_LOAD_SCREEN_SCENE: PackedScene = preload("res://scenes/save_load_screen.tscn")

@onready var auto_btn: Button = $UI_Layer/ControlPanel/AutoButton
@onready var skip_btn: Button = $UI_Layer/ControlPanel/SkipButton
@onready var save_btn: Button = $UI_Layer/ControlPanel/SaveButton
@onready var load_btn: Button = $UI_Layer/ControlPanel/LoadButton

var is_auto_mode: bool = false
var is_skip_mode: bool = false
var save_load_screen: CanvasLayer


func _ready() -> void:
	if auto_btn:
		auto_btn.pressed.connect(_on_auto_button_pressed)
	if skip_btn:
		skip_btn.pressed.connect(_on_skip_button_pressed)
	if save_btn:
		save_btn.pressed.connect(_on_save_pressed)
	if load_btn:
		load_btn.pressed.connect(_on_load_pressed)


func _on_auto_button_pressed() -> void:
	is_auto_mode = !is_auto_mode
	Dialogic.Inputs.auto_advance.enabled_forced = is_auto_mode
	_update_button_states()


func _on_skip_button_pressed() -> void:
	is_skip_mode = !is_skip_mode
	Dialogic.Inputs.auto_skip.enabled = is_skip_mode
	Dialogic.Inputs.auto_skip.disable_on_unread_text = false
	_update_button_states()


func _on_save_pressed() -> void:
	_ensure_save_load_screen()
	if is_instance_valid(save_load_screen):
		save_load_screen.call_deferred("open", "save")


func _on_load_pressed() -> void:
	_ensure_save_load_screen()
	if is_instance_valid(save_load_screen):
		save_load_screen.call_deferred("open", "load")


func _ensure_save_load_screen() -> void:
	if is_instance_valid(save_load_screen):
		if not save_load_screen.is_inside_tree():
			get_tree().root.call_deferred("add_child", save_load_screen)
		return

	save_load_screen = SAVE_LOAD_SCREEN_SCENE.instantiate()
	get_tree().root.call_deferred("add_child", save_load_screen)
	save_load_screen.slot_selected.connect(_on_slot_selected)


func _on_slot_selected(slot_id: int, mode: String) -> void:
	if mode == "save":
		SaveManager.save_game(slot_id)
		_show_feedback(save_btn, Color.GREEN)
	elif mode == "load":
		var loaded: bool = SaveManager.load_game(slot_id)
		_show_feedback(load_btn, Color.GREEN if loaded else Color.RED)

	if is_instance_valid(save_load_screen):
		save_load_screen.close()


func _show_feedback(btn: Button, color: Color) -> void:
	if not is_instance_valid(btn):
		return
	var original_modulate: Color = btn.modulate
	btn.modulate = color
	await get_tree().create_timer(0.5).timeout
	if is_instance_valid(btn):
		btn.modulate = original_modulate


func _update_button_states() -> void:
	if auto_btn:
		auto_btn.modulate = Color.GREEN if is_auto_mode else Color.WHITE
	if skip_btn:
		skip_btn.modulate = Color.YELLOW if is_skip_mode else Color.WHITE


func _on_timeline_ended() -> void:
	pass
