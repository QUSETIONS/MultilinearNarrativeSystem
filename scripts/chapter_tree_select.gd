extends Control

const NODE_WIDTH := 320.0
const NODE_HEIGHT := 160.0
const LAYER_Y_GAP := 280.0
const ROW_X_GAP := 400.0
const PAD_X := 150.0
const PAD_Y := 100.0
const MAIN_MENU_SCENE := "res://scenes/main_menu.tscn"
const MAIN_RUNTIME_SCENE := "res://main.tscn"
const SAVE_LOAD_SCREEN_SCENE: PackedScene = preload("res://scenes/save_load_screen.tscn")

const GOLD := Color(0.86, 0.71, 0.45, 1.0)
const GOLD_SOFT := Color(0.66, 0.54, 0.34, 0.85)
const INK := Color(0.18, 0.15, 0.12, 0.96)
const ACCENT_BLUE := Color(0.38, 0.56, 0.72, 0.9)

@onready var title_label: Label = $MarginContainer/VBoxContainer/TitleLabel
@onready var status_label: Label = $MarginContainer/VBoxContainer/StatusLabel
@onready var refresh_button: Button = $MarginContainer/VBoxContainer/ButtonBar/RefreshButton
@onready var list_button: Button = $MarginContainer/VBoxContainer/ButtonBar/ListButton
@onready var save_button: Button = $MarginContainer/VBoxContainer/ButtonBar/SaveButton
@onready var load_button: Button = $MarginContainer/VBoxContainer/ButtonBar/LoadButton
@onready var back_button: Button = $MarginContainer/VBoxContainer/ButtonBar/BackButton
@onready var map_scroll: ScrollContainer = $MarginContainer/VBoxContainer/MapScroll
@onready var map_root: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot
@onready var line_layer: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot/LineLayer
@onready var node_layer: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot/NodeLayer
@onready var left_ornament: Label = $LeftOrnament
@onready var right_ornament: Label = $RightOrnament

var _save_load_screen: CanvasLayer
var _bgm_fallback_player: AudioStreamPlayer
var _bgm_tone_player: AudioStreamPlayer
var _bgm_tone_playback: AudioStreamGeneratorPlayback
var _bgm_tone_phase: float = 0.0

func _registry() -> Node:
	return get_node_or_null("/root/ChapterRegistry")


func _progress() -> Node:
	return get_node_or_null("/root/ChapterProgress")


func _ready() -> void:
	_apply_localized_texts()
	_apply_flow_theme()
	_apply_ornaments()
	refresh_button.pressed.connect(_on_refresh_pressed)
	list_button.pressed.connect(_on_list_pressed)
	save_button.pressed.connect(_on_save_pressed)
	load_button.pressed.connect(_on_load_pressed)
	back_button.pressed.connect(_on_back_pressed)
	_ensure_save_load_screen()
	_ensure_bgm_started()
	await get_tree().process_frame
	_rebuild_view()


func _process(_delta: float) -> void:
	if _bgm_tone_playback == null:
		return
	var frames := _bgm_tone_playback.get_frames_available()
	if frames <= 0:
		return
	var hz := 196.0
	var increment := TAU * hz / 44100.0
	for _i in range(frames):
		var sample := sin(_bgm_tone_phase) * 0.08
		_bgm_tone_playback.push_frame(Vector2(sample, sample))
		_bgm_tone_phase += increment


func _apply_localized_texts() -> void:
	title_label.text = "\u4e1c\u65b9\u5feb\u8f66 \u7ae0\u8282\u6d41\u7a0b\u56fe"
	status_label.text = "\u6b63\u5728\u52a0\u8f7d\u7ae0\u8282\u6d41\u7a0b\u56fe..."
	refresh_button.text = "\u5237\u65b0\u6d41\u7a0b\u56fe"
	list_button.text = "\u6253\u5f00\u5217\u8868\u6a21\u5f0f"
	save_button.text = "\u4fdd\u5b58"
	load_button.text = "\u8bfb\u53d6"
	back_button.text = "\u8fd4\u56de\u4e3b\u83dc\u5355"


func _apply_ornaments() -> void:
	left_ornament.text = "\u2736\n\u2572\n\u2727\n\u254e\n\u2731\n\u2572\n\u2726\n\u254e\n\u2737"
	right_ornament.text = "\u2737\n\u254e\n\u2726\n\u2571\n\u2731\n\u254e\n\u2727\n\u2571\n\u2736"
	for node in [left_ornament, right_ornament]:
		node.add_theme_font_size_override("font_size", 24)
		node.add_theme_color_override("font_color", Color(0.88, 0.73, 0.46, 0.36))
		node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		node.vertical_alignment = VERTICAL_ALIGNMENT_CENTER


func _on_refresh_pressed() -> void:
	DialogicResourceUtil.update_directory(".dtl")
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "\u7ae0\u8282\u6ce8\u518c\u5668\u4e0d\u53ef\u7528\u3002"
		return
	var ok_registry = registry.rebuild_registry()
	var ok_graph = registry.rebuild_graph()
	if not ok_registry or not ok_graph:
		var reason = str(registry.last_error).strip_edges()
		if reason.is_empty():
			reason = "\u5237\u65b0\u7ae0\u8282\u6d41\u7a0b\u56fe\u5931\u8d25\u3002"
		status_label.text = reason
	_rebuild_view()


func _on_list_pressed() -> void:
	var list_scene: PackedScene = load("res://scenes/chapter_select.tscn")
	if list_scene == null:
		status_label.text = "\u5217\u8868\u573a\u666f\u4e0d\u5b58\u5728\u3002"
		return
	var instance = list_scene.instantiate()
	get_parent().add_child(instance)
	queue_free()


func _on_save_pressed() -> void:
	_open_save_load("save")


func _on_load_pressed() -> void:
	_open_save_load("load")


func _on_back_pressed() -> void:
	get_tree().change_scene_to_file(MAIN_MENU_SCENE)


func _open_save_load(mode: String) -> void:
	_ensure_save_load_screen()
	if is_instance_valid(_save_load_screen):
		_save_load_screen.call("open", mode)


func _ensure_save_load_screen() -> void:
	if is_instance_valid(_save_load_screen):
		return
	if SAVE_LOAD_SCREEN_SCENE == null:
		return
	_save_load_screen = SAVE_LOAD_SCREEN_SCENE.instantiate()
	add_child(_save_load_screen)
	if _save_load_screen.has_signal("slot_selected"):
		_save_load_screen.slot_selected.connect(_on_slot_selected)


func _on_slot_selected(slot_id: int, mode: String) -> void:
	if not is_instance_valid(SaveManager):
		return
	var normalized_mode := mode.to_lower()
	if normalized_mode == "save":
		var ok_save: bool = bool(SaveManager.save_game(slot_id))
		status_label.text = "\u5df2\u4fdd\u5b58\u5230\u69fd\u4f4d %d\u3002" % slot_id if ok_save else "\u4fdd\u5b58\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5\u3002"
		_save_load_screen.call("close")
		return
	if normalized_mode == "load":
		var ok_load: bool = bool(SaveManager.load_game(slot_id))
		status_label.text = "\u8bfb\u53d6\u6210\u529f\uff0c\u6b63\u5728\u6062\u590d\u5267\u60c5\u3002" if ok_load else "\u8bfb\u53d6\u5931\u8d25\uff0c\u69fd\u4f4d\u53ef\u80fd\u4e3a\u7a7a\u3002"
		if ok_load:
			get_tree().change_scene_to_file(MAIN_RUNTIME_SCENE)
		_save_load_screen.call("close")


func _rebuild_view() -> void:
	for child in node_layer.get_children():
		child.queue_free()
	line_layer.call("set_graph_edges", [], {})

	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "\u7ae0\u8282\u6ce8\u518c\u5668\u4e0d\u53ef\u7528\u3002"
		return

	var graph = registry.get_chapter_graph()
	var graph_nodes: Array = graph.get("nodes", [])
	var base_edges: Array = graph.get("edges", [])
	if graph_nodes.is_empty():
		status_label.text = "\u672a\u627e\u5230\u7ae0\u8282\u6d41\u7a0b\u56fe\uff0c\u8bf7\u5148\u8fd0\u884c\u5bfc\u5165\u811a\u672c\u3002"
		return

	var entry_points: Array = graph.get("entry_points", [])
	if entry_points.is_empty() and graph.has("entry_chapter_id"):
		entry_points.append(str(graph.get("entry_chapter_id")))

	var progress := _progress()
	if is_instance_valid(progress):
		progress.ensure_entries_unlocked(entry_points)

	var nodes_by_id: Dictionary = {}
	for node_variant in graph_nodes:
		if node_variant is Dictionary:
			var node: Dictionary = node_variant
			nodes_by_id[str(node.get("chapter_id", ""))] = node

	var edges_for_view := _build_display_edges(base_edges, nodes_by_id)
	var layers = _compute_layers(entry_points, nodes_by_id, edges_for_view)

	var row_count_by_layer: Dictionary = {}
	var max_layer := 0
	for chapter_id in layers.keys():
		var layer = int(layers[chapter_id])
		max_layer = maxi(max_layer, layer)
		if not row_count_by_layer.has(layer):
			row_count_by_layer[layer] = 0
		row_count_by_layer[layer] += 1

	var max_rows := 1
	for layer_key in row_count_by_layer.keys():
		max_rows = maxi(max_rows, int(row_count_by_layer[layer_key]))

	var graph_width := PAD_X * 2.0 + float(max_rows - 1) * ROW_X_GAP + NODE_WIDTH
	var viewport_width := maxf(map_scroll.size.x, 960.0)
	var map_width := maxf(graph_width, viewport_width)
	var map_height := PAD_Y * 2.0 + float(max_layer) * LAYER_Y_GAP + NODE_HEIGHT
	map_root.custom_minimum_size = Vector2(map_width, map_height)
	line_layer.custom_minimum_size = map_root.custom_minimum_size
	node_layer.custom_minimum_size = map_root.custom_minimum_size

	var row_index_by_layer: Dictionary = {}
	var centers: Dictionary = {}
	var chapter_ids: Array[String] = []
	for chapter_id_variant in nodes_by_id.keys():
		chapter_ids.append(str(chapter_id_variant))
	chapter_ids.sort_custom(func(a: String, b: String) -> bool:
		var la = int(layers.get(a, 0))
		var lb = int(layers.get(b, 0))
		if la != lb:
			return la < lb
		var oa = int((nodes_by_id.get(a, {}) as Dictionary).get("order", 0))
		var ob = int((nodes_by_id.get(b, {}) as Dictionary).get("order", 0))
		if oa != ob:
			return oa < ob
		return a < b
	)

	var root_center := Vector2.ZERO
	var global_x_offset := maxf((map_width - graph_width) * 0.5, 0.0)
	for chapter_id in chapter_ids:
		var node_data: Dictionary = nodes_by_id[chapter_id]
		var layer = int(layers.get(chapter_id, 0))
		var row = int(row_index_by_layer.get(layer, 0))
		row_index_by_layer[layer] = row + 1
		var layer_count := int(row_count_by_layer.get(layer, 1))
		var center_offset := float(max_rows - layer_count) * ROW_X_GAP * 0.5
		var x := PAD_X + global_x_offset + center_offset + float(row) * ROW_X_GAP
		var y := PAD_Y + float(layer) * LAYER_Y_GAP

		var card = _create_chapter_card(chapter_id, str(node_data.get("title", chapter_id)), int(node_data.get("order", 0)))
		card.position = Vector2(x, y)
		node_layer.add_child(card)

		centers[chapter_id] = Vector2(x + NODE_WIDTH * 0.5, y + NODE_HEIGHT * 0.5)
		if entry_points.has(chapter_id) and root_center == Vector2.ZERO:
			root_center = centers[chapter_id]

	line_layer.call("set_graph_edges", edges_for_view, centers)
	map_scroll.scroll_horizontal = int(maxf(root_center.x - viewport_width * 0.5, 0.0))
	map_scroll.scroll_vertical = int(maxf(root_center.y - 220.0, 0.0))
	status_label.text = "\u8bf7\u9009\u62e9\u5df2\u89e3\u9501\u7ae0\u8282\u5f00\u59cb\uff0c\u6216\u968f\u65f6\u4fdd\u5b58/\u8bfb\u53d6\u3002"
	_animate_cards_in()


func _build_display_edges(base_edges: Array, nodes_by_id: Dictionary) -> Array:
	var output: Array = base_edges.duplicate(true)
	if not nodes_by_id.has("b1"):
		return output
	for target in ["n1", "chapter2_with_bouc", "chapter2_without_bouc"]:
		if nodes_by_id.has(target) and not _edge_exists(output, "b1", target):
			output.append({
				"from_chapter_id": "b1",
				"to_chapter_id": target,
				"choice_text": "display-link"
			})
	return output


func _edge_exists(edges: Array, from_id: String, to_id: String) -> bool:
	for edge_variant in edges:
		if not (edge_variant is Dictionary):
			continue
		var edge: Dictionary = edge_variant
		if str(edge.get("from_chapter_id", "")) == from_id and str(edge.get("to_chapter_id", "")) == to_id:
			return true
	return false


func _create_chapter_card(chapter_id: String, chapter_title: String, chapter_order: int) -> PanelContainer:
	var card = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = INK
	style.border_color = GOLD_SOFT
	style.border_width_bottom = 2
	style.border_width_top = 2
	style.border_width_left = 6
	style.border_width_right = 2
	style.corner_radius_bottom_left = 10
	style.corner_radius_bottom_right = 10
	style.corner_radius_top_left = 10
	style.corner_radius_top_right = 10
	style.shadow_color = Color(0, 0, 0, 0.45)
	style.shadow_size = 8
	style.content_margin_left = 16
	style.content_margin_top = 16
	style.content_margin_right = 16
	style.content_margin_bottom = 16
	card.add_theme_stylebox_override("panel", style)
	card.custom_minimum_size = Vector2(NODE_WIDTH, NODE_HEIGHT)
	card.size = Vector2(NODE_WIDTH, NODE_HEIGHT)

	var box = VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 10)
	card.add_child(box)

	var title = Label.new()
	title.text = "%d. %s" % [chapter_order, chapter_title]
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", Color(0.97, 0.92, 0.83, 1.0))
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(title)

	var id_label = Label.new()
	id_label.text = chapter_id
	id_label.add_theme_font_size_override("font_size", 12)
	id_label.add_theme_color_override("font_color", Color(0.78, 0.71, 0.58, 0.9))
	box.add_child(id_label)

	var start_button = Button.new()
	var btn_style = StyleBoxFlat.new()
	btn_style.bg_color = Color(0.23, 0.19, 0.13, 1.0)
	btn_style.border_color = GOLD_SOFT
	btn_style.border_width_bottom = 1
	btn_style.border_width_top = 1
	btn_style.border_width_left = 1
	btn_style.border_width_right = 1
	btn_style.corner_radius_bottom_left = 4
	btn_style.corner_radius_bottom_right = 4
	btn_style.corner_radius_top_left = 4
	btn_style.corner_radius_top_right = 4
	start_button.add_theme_stylebox_override("normal", btn_style)
	start_button.text = "\u5f00\u59cb\u7ae0\u8282"
	start_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	start_button.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var unlocked := true
	var visited := false
	var progress := _progress()
	if is_instance_valid(progress):
		unlocked = progress.is_unlocked(chapter_id)
		visited = progress.is_visited(chapter_id)
	start_button.disabled = not unlocked
	start_button.pressed.connect(_on_start_chapter_pressed.bind(chapter_id))
	box.add_child(start_button)

	var state_label = Label.new()
	state_label.add_theme_font_size_override("font_size", 14)
	if visited:
		state_label.text = "\u5df2\u4f53\u9a8c"
		state_label.add_theme_color_override("font_color", Color(0.72, 0.95, 0.78, 1.0))
		style.border_color = Color(0.45, 0.76, 0.56, 0.85)
	elif unlocked:
		state_label.text = "\u5df2\u89e3\u9501"
		state_label.add_theme_color_override("font_color", Color(0.74, 0.84, 0.98, 1.0))
		style.border_color = ACCENT_BLUE
	else:
		state_label.text = "\u672a\u89e3\u9501"
		state_label.add_theme_color_override("font_color", Color(0.6, 0.57, 0.5, 1.0))
		style.border_color = Color(0.28, 0.24, 0.2, 0.85)
	box.add_child(state_label)

	return card


func _on_start_chapter_pressed(chapter_id: String) -> void:
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "\u7ae0\u8282\u6ce8\u518c\u5668\u4e0d\u53ef\u7528\u3002"
		return
	var ok: bool = bool(registry.start_chapter(chapter_id))
	if not ok:
		status_label.text = "\u542f\u52a8\u7ae0\u8282\u5931\u8d25\uff1a%s" % chapter_id
		return
	queue_free()


func _ensure_bgm_started() -> void:
	var bgm_path := "res://assets/bgm/main_theme.wav"
	if BGMManager and BGMManager.has_method("play_track"):
		BGMManager.play_track(bgm_path)
		await get_tree().create_timer(0.18).timeout
		if BGMManager.get("bgm_player") and BGMManager.bgm_player.playing:
			return
	if not is_instance_valid(_bgm_fallback_player):
		_bgm_fallback_player = AudioStreamPlayer.new()
		_bgm_fallback_player.bus = "Master"
		_bgm_fallback_player.volume_db = -6.0
		add_child(_bgm_fallback_player)
	var stream := load(bgm_path)
	if stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream = wav
	if stream is AudioStreamOggVorbis:
		var ogg := stream as AudioStreamOggVorbis
		ogg.loop = true
		stream = ogg
	if stream != null:
		_bgm_fallback_player.stream = stream
		_bgm_fallback_player.play()
		if _bgm_fallback_player.playing:
			return
	_play_bgm_tone_fallback()


func _play_bgm_tone_fallback() -> void:
	if not is_instance_valid(_bgm_tone_player):
		_bgm_tone_player = AudioStreamPlayer.new()
		_bgm_tone_player.bus = "Master"
		_bgm_tone_player.volume_db = -11.0
		add_child(_bgm_tone_player)
	var generator := AudioStreamGenerator.new()
	generator.mix_rate = 44100.0
	generator.buffer_length = 0.5
	_bgm_tone_player.stream = generator
	_bgm_tone_player.play()
	var playback := _bgm_tone_player.get_stream_playback()
	if playback is AudioStreamGeneratorPlayback:
		_bgm_tone_playback = playback as AudioStreamGeneratorPlayback
		_bgm_tone_phase = 0.0
		set_process(true)


func _apply_flow_theme() -> void:
	title_label.add_theme_color_override("font_color", Color(0.95, 0.87, 0.73, 1.0))
	title_label.add_theme_font_size_override("font_size", 40)
	status_label.add_theme_color_override("font_color", Color(0.86, 0.8, 0.67, 0.9))
	for btn in [refresh_button, list_button, save_button, load_button, back_button]:
		_style_command_button(btn)
	if line_layer and line_layer.has_method("set_line_theme"):
		line_layer.call("set_line_theme", GOLD, 3.0, 0.26)


func _style_command_button(btn: Button) -> void:
	if not btn:
		return
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.2, 0.16, 0.12, 0.96)
	normal.border_color = GOLD_SOFT
	normal.border_width_bottom = 1
	normal.border_width_top = 1
	normal.border_width_left = 1
	normal.border_width_right = 1
	normal.corner_radius_top_left = 8
	normal.corner_radius_top_right = 8
	normal.corner_radius_bottom_left = 8
	normal.corner_radius_bottom_right = 8
	var hover := normal.duplicate()
	hover.bg_color = Color(0.26, 0.2, 0.14, 1.0)
	btn.add_theme_stylebox_override("normal", normal)
	btn.add_theme_stylebox_override("hover", hover)
	btn.add_theme_stylebox_override("pressed", hover)
	btn.add_theme_color_override("font_color", Color(0.95, 0.9, 0.8))


func _animate_cards_in() -> void:
	var i := 0
	for child in node_layer.get_children():
		if not (child is Control):
			continue
		var card := child as Control
		card.modulate.a = 0.0
		card.scale = Vector2(0.94, 0.94)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(card, "modulate:a", 1.0, 0.28).set_delay(float(i) * 0.04).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tween.tween_property(card, "scale", Vector2.ONE, 0.28).set_delay(float(i) * 0.04).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		i += 1


func _compute_layers(entry_points: Array, nodes_by_id: Dictionary, edges: Array) -> Dictionary:
	var incoming: Dictionary = {}
	var adjacency: Dictionary = {}
	for chapter_id in nodes_by_id.keys():
		incoming[chapter_id] = 0
		adjacency[chapter_id] = []

	for edge_variant in edges:
		if not (edge_variant is Dictionary):
			continue
		var edge: Dictionary = edge_variant
		var from_id = str(edge.get("from_chapter_id", ""))
		var to_id = str(edge.get("to_chapter_id", ""))
		if not nodes_by_id.has(from_id) or not nodes_by_id.has(to_id):
			continue
		var out: Array = adjacency.get(from_id, [])
		if not out.has(to_id):
			out.append(to_id)
			adjacency[from_id] = out
			incoming[to_id] = int(incoming.get(to_id, 0)) + 1

	var roots: Array[String] = []
	for ep in entry_points:
		var root = str(ep)
		if not root.is_empty() and nodes_by_id.has(root):
			roots.append(root)

	if roots.is_empty():
		for chapter_id in nodes_by_id.keys():
			if int(incoming.get(chapter_id, 0)) == 0:
				roots.append(str(chapter_id))
		if roots.is_empty() and nodes_by_id.size() > 0:
			roots.append(str(nodes_by_id.keys()[0]))

	var layers: Dictionary = {}
	var queue: Array[String] = []
	for root in roots:
		layers[root] = 0
		queue.append(root)

	while not queue.is_empty():
		var current = queue.pop_front()
		var next_layer = int(layers[current]) + 1
		for child_variant in adjacency.get(current, []):
			var child = str(child_variant)
			if not layers.has(child) or next_layer > int(layers[child]):
				layers[child] = next_layer
				if not queue.has(child):
					queue.append(child)

	for chapter_id in nodes_by_id.keys():
		if not layers.has(chapter_id):
			layers[chapter_id] = 0

	return layers
