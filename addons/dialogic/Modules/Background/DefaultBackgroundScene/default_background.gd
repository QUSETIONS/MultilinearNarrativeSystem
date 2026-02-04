extends DialogicBackground

## The default background scene.
## Extend the DialogicBackground class to create your own background scene.

@onready var image_node: TextureRect = $Image
@onready var color_node: ColorRect = $ColorRect


func _ready() -> void:
	image_node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	image_node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED

	image_node.anchor_right = 1
	image_node.anchor_bottom = 1


func _update_background(argument:String, _time:float) -> void:
	if argument.begins_with('res://'):
		var tex = null
		
		# FORCE LOAD FROM FILE: Always try to load raw image first to avoid "Failed loading resource"
		# errors caused by Godot's import system being out of sync.
		var img_path = ProjectSettings.globalize_path(argument)
		if FileAccess.file_exists(img_path) or FileAccess.file_exists(argument):
			var img = Image.load_from_file(img_path)
			if img:
				tex = ImageTexture.create_from_image(img)
		
		# Only fall back to standard load if image load failed
		if tex == null:
			if ResourceLoader.exists(argument):
				tex = load(argument)
			
		image_node.texture = tex
		color_node.color = Color.TRANSPARENT
	elif argument.begins_with('user://'):
		var ext_image = Image.load_from_file(argument)
		image_node.texture = ImageTexture.create_from_image(ext_image)
		color_node.color = Color.TRANSPARENT
	elif argument.is_valid_html_color():
		image_node.texture = null
		color_node.color = Color(argument, 1)
	else:
		image_node.texture = null
		color_node.color = Color.from_string(argument, Color.TRANSPARENT)
