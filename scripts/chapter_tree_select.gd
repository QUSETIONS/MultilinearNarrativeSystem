extends Control

const NODE_WIDTH = 320.0
const NODE_HEIGHT = 140.0
const LAYER_X_GAP = 430.0
const ROW_Y_GAP = 210.0
const PAD_X = 120.0
const PAD_Y = 90.0

@onready var status_label: Label = $MarginContainer/VBoxContainer/StatusLabel
@onready var refresh_button: Button = $MarginContainer/VBoxContainer/ButtonBar/RefreshButton
@onready var list_button: Button = $MarginContainer/VBoxContainer/ButtonBar/ListButton
@onready var map_scroll: ScrollContainer = $MarginContainer/VBoxContainer/MapScroll
@onready var map_root: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot
@onready var line_layer: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot/LineLayer
@onready var node_layer: Control = $MarginContainer/VBoxContainer/MapScroll/MapRoot/NodeLayer

func _registry() -> Node:
	return get_node_or_null("/root/ChapterRegistry")


func _progress() -> Node:
	return get_node_or_null("/root/ChapterProgress")


func _ready() -> void:
	refresh_button.pressed.connect(_on_refresh_pressed)
	list_button.pressed.connect(_on_list_pressed)
	_rebuild_view()


func _on_refresh_pressed() -> void:
	DialogicResourceUtil.update_directory(".dtl")
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "ChapterRegistry unavailable."
		return
	var ok_registry = registry.rebuild_registry()
	var ok_graph = registry.rebuild_graph()
	if not ok_registry or not ok_graph:
		var reason = str(registry.last_error).strip_edges()
		if reason.is_empty():
			reason = "Failed to refresh chapter graph."
		status_label.text = reason
	_rebuild_view()


func _on_list_pressed() -> void:
	var list_scene: PackedScene = load("res://scenes/chapter_select.tscn")
	if list_scene == null:
		status_label.text = "List scene not found."
		return
	var instance = list_scene.instantiate()
	get_parent().add_child(instance)
	queue_free()


func _rebuild_view() -> void:
	for child in node_layer.get_children():
		child.queue_free()
	line_layer.call("set_graph_edges", [], {})

	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "ChapterRegistry unavailable."
		return
	var graph = registry.get_chapter_graph()
	var graph_nodes: Array = graph.get("nodes", [])
	var edges: Array = graph.get("edges", [])
	if graph_nodes.is_empty():
		status_label.text = "No chapter graph found. Run import_orient_express.py first."
		return

	var entry_chapter_id = str(graph.get("entry_chapter_id", ""))
	var progress := _progress()
	if is_instance_valid(progress):
		progress.ensure_entry_unlocked(entry_chapter_id)

	var nodes_by_id: Dictionary = {}
	for node_variant in graph_nodes:
		if node_variant is Dictionary:
			var node: Dictionary = node_variant
			nodes_by_id[str(node.get("chapter_id", ""))] = node

	var layers = _compute_layers(entry_chapter_id, nodes_by_id, edges)
	var row_count_by_layer: Dictionary = {}
	var max_layer = 0
	for chapter_id in layers.keys():
		var layer = int(layers[chapter_id])
		max_layer = maxi(max_layer, layer)
		if not row_count_by_layer.has(layer):
			row_count_by_layer[layer] = 0
		row_count_by_layer[layer] += 1

	var max_rows = 1
	for layer_key in row_count_by_layer.keys():
		max_rows = maxi(max_rows, int(row_count_by_layer[layer_key]))

	var map_width = PAD_X * 2.0 + float(max_layer) * LAYER_X_GAP + NODE_WIDTH
	var map_height = PAD_Y * 2.0 + float(max_rows - 1) * ROW_Y_GAP + NODE_HEIGHT
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

	var root_center = Vector2.ZERO
	for chapter_id in chapter_ids:
		var node_data: Dictionary = nodes_by_id[chapter_id]
		var layer = int(layers.get(chapter_id, 0))
		var row = int(row_index_by_layer.get(layer, 0))
		row_index_by_layer[layer] = row + 1

		var x = PAD_X + float(layer) * LAYER_X_GAP
		var y = PAD_Y + float(row) * ROW_Y_GAP

		var card = _create_chapter_card(
			chapter_id,
			str(node_data.get("title", chapter_id)),
			int(node_data.get("order", 0))
		)
		card.position = Vector2(x, y)
		node_layer.add_child(card)

		centers[chapter_id] = Vector2(x + NODE_WIDTH * 0.5, y + NODE_HEIGHT * 0.5)
		if chapter_id == entry_chapter_id:
			root_center = centers[chapter_id]

	line_layer.call("set_graph_edges", edges, centers)
	map_scroll.scroll_horizontal = int(maxf(root_center.x - 280.0, 0.0))
	map_scroll.scroll_vertical = int(maxf(root_center.y - 220.0, 0.0))
	status_label.text = "Select an unlocked chapter node to start."


func _create_chapter_card(chapter_id: String, chapter_title: String, chapter_order: int) -> PanelContainer:
	var card = PanelContainer.new()
	card.custom_minimum_size = Vector2(NODE_WIDTH, NODE_HEIGHT)
	size_card(card)

	var box = VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 8)
	card.add_child(box)

	var title_label = Label.new()
	title_label.text = "%d. %s" % [chapter_order, chapter_title]
	title_label.add_theme_font_size_override("font_size", 22)
	box.add_child(title_label)

	var id_label = Label.new()
	id_label.text = chapter_id
	id_label.modulate = Color(0.85, 0.88, 0.95, 0.9)
	box.add_child(id_label)

	var start_button = Button.new()
	start_button.text = "Start Chapter"
	start_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var unlocked = true
	var visited = false
	var progress := _progress()
	if is_instance_valid(progress):
		unlocked = progress.is_unlocked(chapter_id)
		visited = progress.is_visited(chapter_id)
	start_button.disabled = not unlocked
	start_button.pressed.connect(_on_start_chapter_pressed.bind(chapter_id))
	box.add_child(start_button)

	var state_label = Label.new()
	if visited:
		state_label.text = "Visited"
		card.modulate = Color(0.56, 0.93, 0.67, 1.0)
	elif unlocked:
		state_label.text = "Unlocked"
		card.modulate = Color(0.56, 0.74, 1.0, 1.0)
	else:
		state_label.text = "Locked"
		card.modulate = Color(0.55, 0.55, 0.55, 1.0)
	box.add_child(state_label)

	return card


func size_card(card: PanelContainer) -> void:
	card.size = Vector2(NODE_WIDTH, NODE_HEIGHT)


func _on_start_chapter_pressed(chapter_id: String) -> void:
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "ChapterRegistry unavailable."
		return
	var ok = registry.start_chapter(chapter_id)
	if not ok:
		status_label.text = "Failed to start chapter: %s" % chapter_id
		return
	queue_free()


func _compute_layers(entry_id: String, nodes_by_id: Dictionary, edges: Array) -> Dictionary:
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

	var root = entry_id
	if root.is_empty() or not nodes_by_id.has(root):
		for chapter_id in nodes_by_id.keys():
			if int(incoming.get(chapter_id, 0)) == 0:
				root = chapter_id
				break
		if root.is_empty():
			root = str(nodes_by_id.keys()[0])

	var layers: Dictionary = {}
	var queue: Array = [root]
	layers[root] = 0

	while not queue.is_empty():
		var current = str(queue.pop_front())
		var next_layer = int(layers[current]) + 1
		for child_variant in adjacency.get(current, []):
			var child = str(child_variant)
			if not layers.has(child):
				layers[child] = next_layer
				queue.append(child)

	for chapter_id in nodes_by_id.keys():
		if not layers.has(chapter_id):
			layers[chapter_id] = 0

	return layers
