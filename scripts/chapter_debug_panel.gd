extends CanvasLayer
class_name ChapterDebugPanel

## Runtime-only debug panel for chapter entry + variable checks.
## Attach to any scene during testing, then remove/disable for release.

@export var visible_on_start := true
@export var panel_anchor := Vector2(16, 16)

var _root: PanelContainer
var _status: Label
var _vars: Label
var _adapter := ChapterEntryUIAdapter.new()

func _bridge() -> Node:
	return get_node_or_null("/root/ChapterEntryBridge")


func _ready() -> void:
	add_child(_adapter)
	_adapter.start_failed.connect(_on_start_failed)
	_adapter.chapter_started.connect(_on_chapter_started)
	_build_ui()
	_root.visible = visible_on_start
	_refresh_snapshot()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F9:
		_root.visible = not _root.visible
		if _root.visible:
			_refresh_snapshot()


func _build_ui() -> void:
	_root = PanelContainer.new()
	_root.name = "ChapterDebugPanel"
	_root.position = panel_anchor
	_root.size = Vector2(420, 320)
	add_child(_root)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	_root.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	margin.add_child(vbox)

	var title := Label.new()
	title.text = "Chapter Debug Panel (F9 Toggle)"
	title.add_theme_font_size_override("font_size", 16)
	vbox.add_child(title)

	var hbox1 := HBoxContainer.new()
	hbox1.add_theme_constant_override("separation", 6)
	vbox.add_child(hbox1)
	hbox1.add_child(_make_button("Start Poirot (Reset)", _start_poirot_reset))
	hbox1.add_child(_make_button("Start Bouc (Reset)", _start_bouc_reset))

	var hbox2 := HBoxContainer.new()
	hbox2.add_theme_constant_override("separation", 6)
	vbox.add_child(hbox2)
	hbox2.add_child(_make_button("Start Poirot (Keep)", _start_poirot_keep))
	hbox2.add_child(_make_button("Start Bouc (Keep)", _start_bouc_keep))

	var hbox3 := HBoxContainer.new()
	hbox3.add_theme_constant_override("separation", 6)
	vbox.add_child(hbox3)
	hbox3.add_child(_make_button("Reset Vars", _reset_vars))
	hbox3.add_child(_make_button("Refresh", _refresh_snapshot))

	_status = Label.new()
	_status.text = "Ready."
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(_status)

	_vars = Label.new()
	_vars.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_vars.text = ""
	vbox.add_child(_vars)


func _make_button(text: String, callable_action: Callable) -> Button:
	var btn := Button.new()
	btn.text = text
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.pressed.connect(callable_action)
	return btn


func _start_poirot_reset() -> void:
	_start_entry("poirot", true)


func _start_bouc_reset() -> void:
	_start_entry("bouc", true)


func _start_poirot_keep() -> void:
	_start_entry("poirot", false)


func _start_bouc_keep() -> void:
	_start_entry("bouc", false)


func _start_entry(entry_key: String, reset_vars: bool) -> void:
	var ok := _adapter.start_from_entry(entry_key, reset_vars)
	if ok:
		_status.text = "Started entry '%s' (reset=%s)." % [entry_key, str(reset_vars)]
	else:
		_status.text = "Failed to start entry '%s'." % entry_key
	_refresh_snapshot()


func _reset_vars() -> void:
	var bridge := _bridge()
	if not is_instance_valid(bridge):
		_status.text = "ChapterEntryBridge unavailable."
		return
	var ok := bridge.reset_story_variables()
	_status.text = "Reset vars: %s" % str(ok)
	_refresh_snapshot()


func _refresh_snapshot() -> void:
	var lines: Array[String] = []
	var bridge := _bridge()
	if is_instance_valid(bridge):
		lines.append("entries=%d" % bridge.get_entries().size())
	else:
		lines.append("entries=<bridge unavailable>")

	if is_instance_valid(Dialogic) and Dialogic.VAR:
		var storage: Dictionary = Dialogic.VAR.var_storage
		lines.append("var_storage=%s" % JSON.stringify(storage))
	else:
		lines.append("var_storage=<dialogic unavailable>")

	_vars.text = "\n".join(lines)


func _on_start_failed(entry_key: String, reason: String) -> void:
	_status.text = "Start failed [%s]: %s" % [entry_key, reason]


func _on_chapter_started(entry_key: String) -> void:
	_status.text = "Chapter started from entry: %s" % entry_key
