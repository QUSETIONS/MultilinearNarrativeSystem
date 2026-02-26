extends Control

const SAVE_LOAD_SCREEN_SCENE: PackedScene = preload("res://scenes/save_load_screen.tscn")

@onready var auto_btn: Button = $UI_Layer/ControlPanel/AutoButton
@onready var skip_btn: Button = $UI_Layer/ControlPanel/SkipButton
@onready var save_btn: Button = $UI_Layer/ControlPanel/SaveButton
@onready var load_btn: Button = $UI_Layer/ControlPanel/LoadButton
@onready var ui_layer: CanvasLayer = $UI_Layer
@onready var control_panel: HBoxContainer = $UI_Layer/ControlPanel
@onready var legacy_dialog_box: Control = $DialogBox
@onready var legacy_choice_container: Control = $ChoiceContainer

var is_auto_mode: bool = false
var is_skip_mode: bool = false
var save_load_screen: CanvasLayer


func _ready() -> void:
	_apply_localized_labels()
	_disable_legacy_dialog_ui()
	_set_runtime_controls_visible(false)
	if Dialogic and not Dialogic.timeline_started.is_connected(_on_dialogic_timeline_started):
		Dialogic.timeline_started.connect(_on_dialogic_timeline_started)
	if Dialogic and not Dialogic.timeline_ended.is_connected(_on_dialogic_timeline_ended):
		Dialogic.timeline_ended.connect(_on_dialogic_timeline_ended)
	if auto_btn:
		auto_btn.pressed.connect(_on_auto_button_pressed)
		_setup_premium_btn(auto_btn)
	if skip_btn:
		skip_btn.pressed.connect(_on_skip_button_pressed)
		_setup_premium_btn(skip_btn)
	if save_btn:
		save_btn.pressed.connect(_on_save_pressed)
		_setup_premium_btn(save_btn)
	if load_btn:
		load_btn.pressed.connect(_on_load_pressed)
		_setup_premium_btn(load_btn)
	_ensure_save_load_screen()
	if Dialogic and Dialogic.current_timeline != null:
		_set_runtime_controls_visible(true)
	get_viewport().size_changed.connect(_on_viewport_size_changed)
	_apply_responsive_runtime_ui()


func _apply_localized_labels() -> void:
	if auto_btn:
		auto_btn.text = "\u81ea\u52a8"
	if skip_btn:
		skip_btn.text = "\u5feb\u8fdb"
	if save_btn:
		save_btn.text = "\u4fdd\u5b58"
	if load_btn:
		load_btn.text = "\u8bfb\u53d6"


func _on_viewport_size_changed() -> void:
	_apply_responsive_runtime_ui()


func _apply_responsive_runtime_ui() -> void:
	var vp_size := get_viewport_rect().size
	var base_scale := clampf(vp_size.y / 1080.0, 0.9, 1.35)
	var btn_font_size := int(round(18 * base_scale))
	var btn_h := int(round(40 * base_scale))
	var btn_w := int(round(82 * base_scale))
	for btn in [auto_btn, skip_btn, save_btn, load_btn]:
		if not btn:
			continue
		btn.custom_minimum_size = Vector2(btn_w, btn_h)
		btn.add_theme_font_size_override("font_size", btn_font_size)
	if control_panel:
		control_panel.add_theme_constant_override("separation", int(round(8 * base_scale)))


func _disable_legacy_dialog_ui() -> void:
	# Dialogic now renders the active timeline UI. Keep only control buttons here.
	if legacy_dialog_box:
		legacy_dialog_box.visible = false
	if legacy_choice_container:
		legacy_choice_container.visible = false


func _set_runtime_controls_visible(controls_visible: bool) -> void:
	if ui_layer:
		ui_layer.visible = controls_visible


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
		save_load_screen.call("open", "save")

func _on_load_pressed() -> void:
	_ensure_save_load_screen()
	if is_instance_valid(save_load_screen):
		save_load_screen.call("open", "load")

func _setup_premium_btn(btn: Button) -> void:
	btn.pivot_offset = btn.size / 2
	btn.mouse_entered.connect(func():
		var tween = create_tween()
		tween.tween_property(btn, "scale", Vector2(1.1, 1.1), 0.1).set_trans(Tween.TRANS_SINE)
		tween.parallel().tween_property(btn, "modulate", Color(1.2, 1.2, 1.5, 1.0), 0.1)
	)
	btn.mouse_exited.connect(func():
		var tween = create_tween()
		tween.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.1).set_trans(Tween.TRANS_SINE)
		tween.parallel().tween_property(btn, "modulate", Color.WHITE, 0.1)
		_update_button_states() # Restore state-based color
	)


# Removed legacy SL screen logic


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


func _on_dialogic_timeline_started() -> void:
	_set_runtime_controls_visible(true)


func _on_dialogic_timeline_ended() -> void:
	_set_runtime_controls_visible(false)


func _ensure_save_load_screen() -> void:
	if is_instance_valid(save_load_screen):
		return
	if SAVE_LOAD_SCREEN_SCENE == null:
		return
	save_load_screen = SAVE_LOAD_SCREEN_SCENE.instantiate()
	add_child(save_load_screen)
	if save_load_screen.has_signal("slot_selected"):
		save_load_screen.slot_selected.connect(_on_slot_selected)


func _on_slot_selected(slot_id: int, mode: String) -> void:
	if not is_instance_valid(SaveManager):
		return
	var normalized_mode := mode.to_lower()
	if normalized_mode == "save":
		var ok_save := SaveManager.save_game(slot_id)
		_show_feedback(save_btn, Color.GREEN if ok_save else Color.RED)
		save_load_screen.call("close")
		return
	if normalized_mode == "load":
		var ok_load := SaveManager.load_game(slot_id)
		_show_feedback(load_btn, Color.CYAN if ok_load else Color.RED)
		if ok_load:
			_set_runtime_controls_visible(true)
		save_load_screen.call("close")
