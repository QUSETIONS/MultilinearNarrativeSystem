extends CanvasLayer

signal slot_selected(slot_id: int, mode: String)

const DEFAULT_SLOT_COUNT: int = 8

@export var slot_scene: PackedScene

@onready var title_label: Label = $Overlay/MarginContainer/VBoxContainer/TitleLabel
@onready var slots_container: VBoxContainer = $Overlay/MarginContainer/VBoxContainer/SlotsScroll/SlotsContainer
@onready var back_button: Button = $Overlay/MarginContainer/VBoxContainer/BackButton

var _mode: String = "save"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	back_button.pressed.connect(close)
	hide()


func open(mode: String) -> void:
	if not is_node_ready():
		await ready

	_mode = mode.to_lower()
	title_label.text = "保存" if _mode == "save" else "读取"
	_populate_slots()
	show()
	get_tree().paused = true


func close() -> void:
	get_tree().paused = false
	hide()


func _populate_slots() -> void:
	for child in slots_container.get_children():
		child.queue_free()

	var slots: Array = _get_slots_data()
	for index in range(slots.size()):
		var slot_data: Dictionary = slots[index]
		var slot_id: int = int(slot_data.get("slot_id", index + 1))
		if slot_scene == null:
			continue

		var slot_item: Control = slot_scene.instantiate()
		slots_container.add_child(slot_item)

		var slot_label: Label = slot_item.get_node_or_null("MarginContainer/HBoxContainer/Meta/SlotLabel")
		var timestamp_label: Label = slot_item.get_node_or_null("MarginContainer/HBoxContainer/Meta/TimestampLabel")
		var chapter_label: Label = slot_item.get_node_or_null("MarginContainer/HBoxContainer/Meta/ChapterLabel")
		var action_button: Button = slot_item.get_node_or_null("MarginContainer/HBoxContainer/ActionButton")

		var is_empty: bool = bool(slot_data.get("is_empty", true))

		if slot_label:
			slot_label.text = "存档 %d" % slot_id
		if timestamp_label:
			timestamp_label.text = str(slot_data.get("timestamp", "--"))
		if chapter_label:
			chapter_label.text = "空槽位" if is_empty else str(slot_data.get("chapter_name", "未知章节"))
		if action_button:
			action_button.text = "保存" if _mode == "save" else "读取"
			action_button.disabled = (_mode == "load" and is_empty)
			action_button.pressed.connect(_on_slot_action_pressed.bind(slot_id))


func _on_slot_action_pressed(slot_id: int) -> void:
	slot_selected.emit(slot_id, _mode)


func _get_slots_data() -> Array:
	if is_instance_valid(SaveManager):
		var result: Variant = SaveManager.get_all_slots()
		if result is Array and not result.is_empty():
			return result

	var fallback_slots: Array = []
	for i in range(DEFAULT_SLOT_COUNT):
		fallback_slots.append({
			"slot_id": i + 1,
			"is_empty": true,
			"timestamp": "--",
			"chapter_name": "空槽位"
		})

	return fallback_slots
