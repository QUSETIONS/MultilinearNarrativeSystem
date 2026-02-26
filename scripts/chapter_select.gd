extends Control

@onready var chapter_list: VBoxContainer = $MarginContainer/VBoxContainer/ScrollContainer/ChapterList
@onready var status_label: Label = $MarginContainer/VBoxContainer/StatusLabel
@onready var refresh_button: Button = $MarginContainer/VBoxContainer/RefreshButton

func _registry() -> Node:
	return get_node_or_null("/root/ChapterRegistry")


func _ready() -> void:
	refresh_button.pressed.connect(_on_refresh_pressed)
	_populate_chapter_list()


func _populate_chapter_list() -> void:
	for child in chapter_list.get_children():
		child.queue_free()

	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "章节注册器不可用。"
		refresh_button.visible = false
		return

	var chapters: Array[Dictionary] = registry.get_chapter_list()
	if chapters.is_empty():
		var reason := str(registry.last_error).strip_edges()
		if reason.is_empty():
			reason = "未找到章节。"
		status_label.text = "%s 请点击刷新，或先运行 import_orient_express.py。" % reason
		refresh_button.visible = true
		return

	status_label.text = "请选择一个章节开始"
	refresh_button.visible = true
	for chapter in chapters:
		var chapter_id := str(chapter.get("id", ""))
		var title := str(chapter.get("title", chapter_id))
		var order := int(chapter.get("order", 0))

		var button := Button.new()
		button.text = "%d. %s" % [order, title]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.custom_minimum_size = Vector2(0, 44)
		button.pressed.connect(_on_chapter_pressed.bind(chapter_id))
		chapter_list.add_child(button)


func _on_chapter_pressed(chapter_id: String) -> void:
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "章节注册器不可用。"
		return
	if not registry.chapters.has(chapter_id):
		status_label.text = "未找到章节：%s" % chapter_id
		return

	var started: bool = bool(registry.start_chapter(chapter_id))
	if not started:
		status_label.text = "启动章节失败：%s" % chapter_id
		return

	queue_free()


func _on_refresh_pressed() -> void:
	var registry := _registry()
	if not is_instance_valid(registry):
		status_label.text = "章节注册器不可用。"
		return

	DialogicResourceUtil.update_directory(".dtl")
	var ok: bool = bool(registry.rebuild_registry())
	_populate_chapter_list()
	if not ok:
		var reason := str(registry.last_error).strip_edges()
		if reason.is_empty():
			reason = "未找到章节。"
		status_label.text = "刷新完成，但失败：%s" % reason
