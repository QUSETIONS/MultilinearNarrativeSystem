## VN Controller - 视觉小说 UI 控制脚本
## 提供 Auto-Advance, Auto-Skip, QuickSave, QuickLoad 入口
extends Control

# 引用 UI 按钮
@onready var auto_btn: Button = $UI_Layer/ControlPanel/AutoButton
@onready var skip_btn: Button = $UI_Layer/ControlPanel/SkipButton
@onready var save_btn: Button = $UI_Layer/ControlPanel/SaveButton
@onready var load_btn: Button = $UI_Layer/ControlPanel/LoadButton

# 状态指示
var is_auto_mode: bool = false
var is_skip_mode: bool = false

func _ready() -> void:
	# 连接按钮信号
	if auto_btn:
		auto_btn.pressed.connect(_on_auto_button_pressed)
	if skip_btn:
		skip_btn.pressed.connect(_on_skip_button_pressed)
	if save_btn:
		save_btn.pressed.connect(_on_quick_save_pressed)
	if load_btn:
		load_btn.pressed.connect(_on_quick_load_pressed)


## 切换自动推进模式
func _on_auto_button_pressed() -> void:
	is_auto_mode = !is_auto_mode
	# DialogicAutoAdvance doesn't have 'enabled', use 'enabled_forced' for toggle.
	Dialogic.Inputs.auto_advance.enabled_forced = is_auto_mode
	_update_button_states()
	print("[VN] Auto-Advance: ", is_auto_mode)


## 切换自动跳过模式
func _on_skip_button_pressed() -> void:
	is_skip_mode = !is_skip_mode
	Dialogic.Inputs.auto_skip.enabled = is_skip_mode
	# 禁用"遇到未读文本时停止"以允许快进所有内容
	Dialogic.Inputs.auto_skip.disable_on_unread_text = false
	_update_button_states()
	print("[VN] Auto-Skip: ", is_skip_mode)


## 快速存档入口
func _on_quick_save_pressed() -> void:
	print("[VN] QuickSave triggered")
	Dialogic.Save.save("quick_save")
	_show_feedback(save_btn, Color.GREEN)

## 快速读档入口
func _on_quick_load_pressed() -> void:
	print("[VN] QuickLoad triggered")
	if Dialogic.Save.has_slot("quick_save"):
		Dialogic.Save.load("quick_save")
		_show_feedback(load_btn, Color.GREEN)
	else:
		print("[VN] No quick save found")
		_show_feedback(load_btn, Color.RED)

func _show_feedback(btn: Button, color: Color) -> void:
	var original_modulate = btn.modulate
	btn.modulate = color
	await get_tree().create_timer(0.5).timeout
	if is_instance_valid(btn):
		btn.modulate = original_modulate


## 更新按钮视觉状态
func _update_button_states() -> void:
	if auto_btn:
		auto_btn.modulate = Color.GREEN if is_auto_mode else Color.WHITE
	if skip_btn:
		skip_btn.modulate = Color.YELLOW if is_skip_mode else Color.WHITE


## 响应 Dialogic 时间线结束
func _on_timeline_ended() -> void:
	print("[VN] Timeline ended")
	# 可在此处添加返回标题画面等逻辑
