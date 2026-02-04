## 主场景脚本 - 启动 Dialogic 时间线
extends Node

func _ready() -> void:
	# Wait for systems to initialize to prevent race conditions with PortraitContainers
	await get_tree().process_frame
	
	# 启动演示时间线
	# 使用 Dialogic.start() 会自动加载默认样式
	# 参数是时间线资源路径
	Dialogic.start("res://dialogic/timelines/orient_express.dtl")
	
	# 监听时间线结束事件
	Dialogic.timeline_ended.connect(_on_timeline_ended)


func _on_timeline_ended() -> void:
	print("[Main] 时间线结束")
	# 可以在此处添加返回标题画面等逻辑
	# get_tree().change_scene_to_file("res://scenes/title.tscn")
