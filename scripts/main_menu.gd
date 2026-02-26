extends Control

const MAIN_RUNTIME_SCENE := "res://main.tscn"
const SAVE_LOAD_SCREEN_SCENE: PackedScene = preload("res://scenes/save_load_screen.tscn")

const INK_BG := Color(0.12, 0.1, 0.09, 0.92)
const GOLD := Color(0.89, 0.73, 0.46, 1.0)
const GOLD_SOFT := Color(0.65, 0.53, 0.34, 0.9)
const TEXT_MAIN := Color(0.97, 0.92, 0.83, 1.0)
const TEXT_SUB := Color(0.82, 0.77, 0.67, 0.95)
const DEFAULT_VOLUME_LINEAR := 0.72

@onready var start_btn: Button = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/ButtonsWrap/StartButton
@onready var load_btn: Button = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/ButtonsWrap/LoadButton
@onready var quit_btn: Button = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/ButtonsWrap/QuitButton
@onready var hint_label: Label = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/HintLabel
@onready var mute_btn: Button = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/AudioRow/MuteButton
@onready var volume_slider: HSlider = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/AudioRow/VolumeSlider
@onready var volume_value_label: Label = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/AudioRow/VolumeValueLabel
@onready var overline_label: Label = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/Overline
@onready var subtitle_label: Label = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/Subtitle
@onready var title_label: Label = $CenterWrap/HeroPanel/HeroMargin/HeroVBox/Title
@onready var hero_panel: PanelContainer = $CenterWrap/HeroPanel
@onready var bg: TextureRect = $Background

var _save_load_screen: CanvasLayer
var _buttons: Array[Button] = []
var _fallback_bgm_player: AudioStreamPlayer
var _tone_player: AudioStreamPlayer
var _tone_playback: AudioStreamGeneratorPlayback
var _tone_phase: float = 0.0
var _audio_bus_idx: int = -1
var _is_muted: bool = false
var _last_volume_linear: float = DEFAULT_VOLUME_LINEAR

func _ready() -> void:
	_buttons = [start_btn, load_btn, quit_btn]
	_apply_background()
	_apply_localized_texts()
	_apply_theme()
	_connect_events()
	_ensure_save_load_screen()
	_refresh_load_button_state()
	_init_audio_controls()
	_play_intro()
	_play_menu_bgm()

func _apply_localized_texts() -> void:
	overline_label.text = "沉浸式推理体验"
	title_label.text = "东方快车谋杀案"
	subtitle_label.text = "在雪夜列车中追索真相"
	start_btn.text = "开始游戏"
	load_btn.text = "读取进度"
	quit_btn.text = "退出游戏"

func _apply_background() -> void:
	if bg == null:
		return
	var candidates: Array[String] = [
		"res://assets/backgrounds/main_menu_bg.png",
		"res://assets/backgrounds/station_night.png",
		"res://assets/backgrounds/train_compartment_night.png",
	]
	for path in candidates:
		if not ResourceLoader.exists(path):
			continue
		var tex: Texture2D = load(path) as Texture2D
		if tex != null:
			bg.texture = tex
			return
	push_warning("[MainMenu] No valid background texture found in fallback list.")

func _apply_theme() -> void:
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = INK_BG
	panel_style.border_color = GOLD_SOFT
	panel_style.border_width_top = 1
	panel_style.border_width_bottom = 2
	panel_style.border_width_left = 1
	panel_style.border_width_right = 1
	panel_style.corner_radius_top_left = 14
	panel_style.corner_radius_top_right = 14
	panel_style.corner_radius_bottom_left = 14
	panel_style.corner_radius_bottom_right = 14
	panel_style.shadow_color = Color(0.02, 0.01, 0.0, 0.55)
	panel_style.shadow_size = 14
	hero_panel.add_theme_stylebox_override("panel", panel_style)
	title_label.add_theme_color_override("font_color", TEXT_MAIN)
	title_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.65))
	title_label.add_theme_constant_override("shadow_offset_x", 2)
	title_label.add_theme_constant_override("shadow_offset_y", 2)
	overline_label.add_theme_color_override("font_color", GOLD)
	subtitle_label.add_theme_color_override("font_color", TEXT_SUB)
	hint_label.add_theme_color_override("font_color", Color(0.86, 0.8, 0.7, 0.86))
	volume_value_label.add_theme_color_override("font_color", TEXT_SUB)
	for btn in _buttons:
		_style_button(btn)
	_style_audio_button(mute_btn)

func _style_audio_button(btn: Button) -> void:
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.16, 0.13, 0.1, 0.95)
	normal.border_color = GOLD_SOFT
	normal.border_width_top = 1
	normal.border_width_bottom = 1
	normal.border_width_left = 1
	normal.border_width_right = 1
	normal.corner_radius_top_left = 8
	normal.corner_radius_top_right = 8
	normal.corner_radius_bottom_left = 8
	normal.corner_radius_bottom_right = 8
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(0.24, 0.18, 0.12, 1.0)
	hover.border_color = GOLD
	btn.add_theme_stylebox_override("normal", normal)
	btn.add_theme_stylebox_override("hover", hover)
	btn.add_theme_stylebox_override("pressed", hover)
	btn.add_theme_color_override("font_color", TEXT_MAIN)

func _style_button(btn: Button) -> void:
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.19, 0.15, 0.12, 0.96)
	normal.border_color = GOLD_SOFT
	normal.border_width_top = 1
	normal.border_width_bottom = 1
	normal.border_width_left = 1
	normal.border_width_right = 1
	normal.corner_radius_top_left = 10
	normal.corner_radius_top_right = 10
	normal.corner_radius_bottom_left = 10
	normal.corner_radius_bottom_right = 10
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(0.28, 0.21, 0.14, 1.0)
	hover.border_color = GOLD
	hover.shadow_color = Color(0.75, 0.58, 0.28, 0.26)
	hover.shadow_size = 8
	var disabled := normal.duplicate() as StyleBoxFlat
	disabled.bg_color = Color(0.12, 0.11, 0.1, 0.88)
	disabled.border_color = Color(0.3, 0.28, 0.24, 0.5)
	btn.add_theme_stylebox_override("normal", normal)
	btn.add_theme_stylebox_override("hover", hover)
	btn.add_theme_stylebox_override("pressed", hover)
	btn.add_theme_stylebox_override("disabled", disabled)
	btn.add_theme_color_override("font_color", TEXT_MAIN)
	btn.add_theme_color_override("font_disabled_color", Color(0.58, 0.56, 0.53, 0.86))

func _connect_events() -> void:
	start_btn.pressed.connect(_on_start_pressed)
	load_btn.pressed.connect(_on_load_pressed)
	quit_btn.pressed.connect(_on_quit_pressed)
	mute_btn.pressed.connect(_on_mute_pressed)
	volume_slider.value_changed.connect(_on_volume_slider_changed)
	for btn in _buttons:
		btn.pivot_offset = btn.size * 0.5
		btn.mouse_entered.connect(_on_button_entered.bind(btn))
		btn.mouse_exited.connect(_on_button_exited.bind(btn))

func _on_button_entered(btn: Button) -> void:
	if btn.disabled:
		return
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(btn, "scale", Vector2(1.03, 1.03), 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(btn, "modulate", Color(1.07, 1.05, 1.0, 1.0), 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

func _on_button_exited(btn: Button) -> void:
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(btn, "scale", Vector2.ONE, 0.2).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(btn, "modulate", Color.WHITE, 0.2).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

func _play_intro() -> void:
	hero_panel.modulate.a = 0.0
	hero_panel.scale = Vector2(0.96, 0.96)
	var panel_tween := create_tween()
	panel_tween.set_parallel(true)
	panel_tween.tween_property(hero_panel, "modulate:a", 1.0, 0.36).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	panel_tween.tween_property(hero_panel, "scale", Vector2.ONE, 0.36).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	var index := 0
	for btn in _buttons:
		btn.modulate.a = 0.0
		btn.scale = Vector2(0.98, 0.98)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(btn, "modulate:a", 1.0, 0.24).set_delay(0.18 + float(index) * 0.05).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tween.tween_property(btn, "scale", Vector2.ONE, 0.24).set_delay(0.18 + float(index) * 0.05).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		index += 1

func _play_menu_bgm() -> void:
	var bgm_path := "res://assets/bgm/main_theme.wav"
	var preloaded_stream := load(bgm_path)
	if preloaded_stream is AudioStreamWAV and _looks_silent_wav(preloaded_stream as AudioStreamWAV):
		push_warning("[MainMenu] main_theme.wav appears silent. Switching to generator tone fallback.")
		_play_generator_tone()
		return
	if BGMManager and BGMManager.has_method("play_track"):
		BGMManager.play_track(bgm_path)
		await get_tree().create_timer(0.18).timeout
		if BGMManager.get("bgm_player") and BGMManager.bgm_player.playing:
			_apply_volume_to_players()
			return
	if not is_instance_valid(_fallback_bgm_player):
		_fallback_bgm_player = AudioStreamPlayer.new()
		_fallback_bgm_player.bus = "Master"
		_fallback_bgm_player.volume_db = -4.0
		add_child(_fallback_bgm_player)
	var stream := preloaded_stream
	if stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream = wav
	if stream is AudioStreamOggVorbis:
		var ogg := stream as AudioStreamOggVorbis
		ogg.loop = true
		stream = ogg
	if stream == null:
		push_warning("[MainMenu] Failed to load BGM stream. Switching to generator tone fallback.")
		_play_generator_tone()
		return
	_fallback_bgm_player.stream = stream
	_fallback_bgm_player.play()
	if not _fallback_bgm_player.playing:
		_play_generator_tone()
	_apply_volume_to_players()

func _init_audio_controls() -> void:
	_audio_bus_idx = AudioServer.get_bus_index("Master")
	if _audio_bus_idx < 0:
		_audio_bus_idx = 0
	var db_value := AudioServer.get_bus_volume_db(_audio_bus_idx)
	if is_inf(db_value) or db_value < -60.0:
		_last_volume_linear = DEFAULT_VOLUME_LINEAR
	else:
		_last_volume_linear = db_to_linear(db_value)
	_last_volume_linear = clampf(_last_volume_linear, 0.0, 1.0)
	if _last_volume_linear < 0.05:
		_last_volume_linear = DEFAULT_VOLUME_LINEAR
	_is_muted = false
	AudioServer.set_bus_mute(_audio_bus_idx, _is_muted)
	AudioServer.set_bus_volume_db(_audio_bus_idx, linear_to_db(max(_last_volume_linear, 0.0001)))
	volume_slider.value = _last_volume_linear * 100.0
	_update_audio_ui()
	_apply_volume_to_players()

func _on_volume_slider_changed(value: float) -> void:
	_last_volume_linear = clampf(value / 100.0, 0.0, 1.0)
	if _last_volume_linear > 0.0 and _is_muted:
		_is_muted = false
	AudioServer.set_bus_mute(_audio_bus_idx, _is_muted)
	if not _is_muted:
		AudioServer.set_bus_volume_db(_audio_bus_idx, linear_to_db(max(_last_volume_linear, 0.0001)))
	else:
		AudioServer.set_bus_volume_db(_audio_bus_idx, -80.0)
	_apply_volume_to_players()
	_update_audio_ui()

func _on_mute_pressed() -> void:
	_is_muted = not _is_muted
	AudioServer.set_bus_mute(_audio_bus_idx, _is_muted)
	if _is_muted:
		AudioServer.set_bus_volume_db(_audio_bus_idx, -80.0)
	else:
		AudioServer.set_bus_volume_db(_audio_bus_idx, linear_to_db(max(_last_volume_linear, 0.0001)))
	_apply_volume_to_players()
	_update_audio_ui()

func _update_audio_ui() -> void:
	var percent := int(round(_last_volume_linear * 100.0))
	volume_value_label.text = "%d%%" % percent
	mute_btn.text = "静音：开" if _is_muted else "静音：关"

func _apply_volume_to_players() -> void:
	if is_instance_valid(_fallback_bgm_player):
		_fallback_bgm_player.volume_db = -80.0 if _is_muted else linear_to_db(max(_last_volume_linear, 0.0001))
	if is_instance_valid(_tone_player):
		_tone_player.volume_db = -80.0 if _is_muted else linear_to_db(max(_last_volume_linear * 0.55, 0.0001))

func _looks_silent_wav(wav: AudioStreamWAV) -> bool:
	var bytes := wav.data
	if bytes.is_empty():
		return true
	var non_zero := 0
	var step := maxi(1, int(bytes.size() / 4096.0))
	for i in range(0, bytes.size(), step):
		if bytes[i] != 0:
			non_zero += 1
			if non_zero > 8:
				return false
	return true

func _play_generator_tone() -> void:
	if not is_instance_valid(_tone_player):
		_tone_player = AudioStreamPlayer.new()
		_tone_player.bus = "Master"
		add_child(_tone_player)
	var generator := AudioStreamGenerator.new()
	generator.mix_rate = 44100.0
	generator.buffer_length = 0.5
	_tone_player.stream = generator
	_tone_player.play()
	var playback := _tone_player.get_stream_playback()
	if playback is AudioStreamGeneratorPlayback:
		_tone_playback = playback as AudioStreamGeneratorPlayback
		_tone_phase = 0.0
		set_process(true)
	_apply_volume_to_players()

func _process(_delta: float) -> void:
	if _tone_playback == null:
		return
	var frames_available := _tone_playback.get_frames_available()
	if frames_available <= 0:
		return
	var base_hz := 220.0
	var increment := TAU * base_hz / 44100.0
	for _i in range(frames_available):
		var sample := sin(_tone_phase) * 0.12
		_tone_playback.push_frame(Vector2(sample, sample))
		_tone_phase += increment

func _on_start_pressed() -> void:
	var err := get_tree().change_scene_to_file(MAIN_RUNTIME_SCENE)
	if err != OK:
		push_error("Failed to load runtime scene: ", err)

func _on_load_pressed() -> void:
	_ensure_save_load_screen()
	if is_instance_valid(_save_load_screen):
		_save_load_screen.call("open", "load")

func _on_quit_pressed() -> void:
	get_tree().quit()

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
	if mode.to_lower() != "load":
		return
	if not is_instance_valid(SaveManager):
		return
	if SaveManager.load_game(slot_id):
		var err := get_tree().change_scene_to_file(MAIN_RUNTIME_SCENE)
		if err != OK:
			push_error("Failed to enter runtime scene after loading slot: ", err)
		return
	_refresh_load_button_state()

func _refresh_load_button_state() -> void:
	if not is_instance_valid(SaveManager):
		load_btn.disabled = true
		hint_label.text = "提示：存档系统不可用。"
		return
	var has_save := SaveManager.has_any_slot()
	load_btn.disabled = not has_save
	if has_save:
		hint_label.text = "提示：可从最近进度继续调查。"
	else:
		hint_label.text = "提示：当前未检测到存档，请先开始游戏。"
