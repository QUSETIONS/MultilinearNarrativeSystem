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
var return_btn: Button
var history_btn: Button
var history_panel: ScrollContainer
var history_vbox: VBoxContainer
var max_history_entries: int = 50

var evidence_btn: Button
var evidence_panel: ScrollContainer
var evidence_grid: GridContainer
var unlocked_evidences: Array[String] = []

var evidence_db: Dictionary = {
	"handkerchief": {"name": "带有H缩写的纽扣", "desc": "在凶案现场发现的纽扣。"},
	"pipe_cleaner": {"name": "烟斗通条", "desc": "案发现场发现的通条。"},
	"watch": {"name": "破损的怀表", "desc": "指针停留在1点15分的怀表。"},
	"button": {"name": "列车员制服纽扣", "desc": "案发现场找到的铜纽扣。"},
	"knife": {"name": "带血的凶器", "desc": "一把锋利的匕首。"},
	"uniform": {"name": "列车员制服", "desc": "在空包厢行李箱里发现的制服。"},
	"kimono": {"name": "猩红色和服", "desc": "在波洛包厢里被发现的和服。"}
}


func _ready() -> void:
	_apply_localized_labels()
	_disable_legacy_dialog_ui()
	_set_runtime_controls_visible(false)
	if Dialogic and not Dialogic.timeline_ended.is_connected(_on_dialogic_timeline_ended):
		Dialogic.timeline_ended.connect(_on_dialogic_timeline_ended)
	if Dialogic and Dialogic.has_subsystem("Text"):
		if not Dialogic.Text.about_to_show_text.is_connected(_on_dialogic_about_to_show_text):
			Dialogic.Text.about_to_show_text.connect(_on_dialogic_about_to_show_text)
	if Dialogic and not Dialogic.signal_event.is_connected(_on_dialogic_signal_event):
		Dialogic.signal_event.connect(_on_dialogic_signal_event)

	_setup_history_panel()
	_setup_evidence_panel()

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
	if control_panel:
		history_btn = Button.new()
		control_panel.add_child(history_btn)
		history_btn.pressed.connect(_on_history_pressed)
		_setup_premium_btn(history_btn)

		evidence_btn = Button.new()
		control_panel.add_child(evidence_btn)
		evidence_btn.pressed.connect(_on_evidence_pressed)
		_setup_premium_btn(evidence_btn)

		return_btn = Button.new()
		control_panel.add_child(return_btn)
		return_btn.pressed.connect(_on_return_pressed)
		_setup_premium_btn(return_btn)

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
	if history_btn:
		history_btn.text = "\u56de\u770b"
	if evidence_btn:
		evidence_btn.text = "\u7ebf\u7d22"
	if return_btn:
		return_btn.text = "\u8fd4\u56de"



func _on_viewport_size_changed() -> void:
	_apply_responsive_runtime_ui()


func _apply_responsive_runtime_ui() -> void:
	var vp_size := get_viewport_rect().size
	var base_scale := clampf(vp_size.y / 1080.0, 0.9, 1.35)
	var btn_font_size := int(round(18 * base_scale))
	var btn_h := int(round(40 * base_scale))
	var btn_w := int(round(82 * base_scale))
	for btn in [auto_btn, skip_btn, save_btn, load_btn, history_btn, evidence_btn, return_btn]:
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

func _on_return_pressed() -> void:
	if Dialogic:
		Dialogic.end_timeline()
	get_tree().change_scene_to_file("res://main.tscn")

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

func _setup_history_panel() -> void:
	history_panel = ScrollContainer.new()
	ui_layer.add_child(history_panel)
	history_panel.visible = false
	history_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# background block
	var bg = Panel.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.1, 0.1, 0.08, 0.85)
	bg.add_theme_stylebox_override("panel", style)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	history_panel.add_child(bg)
	
	history_vbox = VBoxContainer.new()
	history_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 120)
	margin.add_theme_constant_override("margin_right", 120)
	margin.add_theme_constant_override("margin_top", 60)
	margin.add_theme_constant_override("margin_bottom", 120)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(history_vbox)
	history_panel.add_child(margin)

func _on_history_pressed() -> void:
	if not is_instance_valid(history_panel): return
	history_panel.visible = not history_panel.visible
	if history_panel.visible:
		evidence_panel.visible = false
		# auto scroll to bottom when opened
		await get_tree().process_frame
		history_panel.scroll_vertical = history_panel.get_v_scroll_bar().max_value

func _setup_evidence_panel() -> void:
	evidence_panel = ScrollContainer.new()
	ui_layer.add_child(evidence_panel)
	evidence_panel.visible = false
	evidence_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# background block
	var bg = Panel.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.12, 0.1, 0.08, 0.9)
	bg.add_theme_stylebox_override("panel", style)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	evidence_panel.add_child(bg)
	
	evidence_grid = GridContainer.new()
	evidence_grid.columns = 3
	evidence_grid.add_theme_constant_override("h_separation", 20)
	evidence_grid.add_theme_constant_override("v_separation", 20)
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 60)
	margin.add_theme_constant_override("margin_right", 60)
	margin.add_theme_constant_override("margin_top", 60)
	margin.add_theme_constant_override("margin_bottom", 60)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(evidence_grid)
	evidence_panel.add_child(margin)

func _on_evidence_pressed() -> void:
	if not is_instance_valid(evidence_panel): return
	evidence_panel.visible = not evidence_panel.visible
	if evidence_panel.visible:
		history_panel.visible = false

func _on_dialogic_signal_event(argument: String) -> void:
	if argument.begins_with("add_evidence:"):
		var ev_id = argument.trim_prefix("add_evidence:")
		if not ev_id in unlocked_evidences and ev_id in evidence_db:
			unlocked_evidences.append(ev_id)
			_add_evidence_item_to_ui(ev_id)

func _add_evidence_item_to_ui(ev_id: String) -> void:
	var info = evidence_db[ev_id]
	var card = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.2, 0.18, 0.15, 1.0)
	style.border_width_bottom = 2
	style.border_color = Color(0.8, 0.7, 0.5, 1.0)
	style.content_margin_left = 15
	style.content_margin_top = 15
	style.content_margin_right = 15
	style.content_margin_bottom = 15
	card.add_theme_stylebox_override("panel", style)
	card.custom_minimum_size = Vector2(250, 150)
	
	var vbox = VBoxContainer.new()
	card.add_child(vbox)
	
	var title = Label.new()
	title.text = info["name"]
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", Color(0.9, 0.8, 0.6, 1.0))
	vbox.add_child(title)
	
	var desc = Label.new()
	desc.text = info["desc"]
	desc.add_theme_font_size_override("font_size", 16)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(desc)
	
	evidence_grid.add_child(card)

func _on_dialogic_about_to_show_text(info: Dictionary) -> void:
	if not is_instance_valid(history_vbox): return
	
	var text_str: String = info.get("text", "")
	var character = info.get("character")
	var speaker_name := ""
	var name_color := Color.WHITE
	
	if character and character is DialogicCharacter:
		speaker_name = character.display_name
		name_color = character.color

	var final_bbcode = ""
	if speaker_name != "":
		final_bbcode = "[color=#%s]%s:[/color] %s" % [name_color.to_html(), speaker_name, text_str]
	else:
		final_bbcode = text_str

	var entry = RichTextLabel.new()
	entry.bbcode_enabled = true
	entry.text = final_bbcode
	entry.fit_content = true
	entry.add_theme_font_size_override("normal_font_size", 22)
	
	history_vbox.add_child(entry)
	
	if history_vbox.get_child_count() > max_history_entries:
		history_vbox.get_child(0).queue_free()
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
