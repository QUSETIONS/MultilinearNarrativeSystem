extends Node

var bgm_player: AudioStreamPlayer
var current_track: String = ""
var tween: Tween
var tone_player: AudioStreamPlayer
var tone_playback: AudioStreamGeneratorPlayback
var tone_phase: float = 0.0

func _ready() -> void:
	var master_idx := AudioServer.get_bus_index("Master")
	if master_idx >= 0:
		AudioServer.set_bus_mute(master_idx, false)
		if AudioServer.get_bus_volume_db(master_idx) < -60.0:
			AudioServer.set_bus_volume_db(master_idx, -6.0)
	bgm_player = AudioStreamPlayer.new()
	bgm_player.bus = "Master"
	add_child(bgm_player)
	tone_player = AudioStreamPlayer.new()
	tone_player.bus = "Master"
	add_child(tone_player)
	
	# Initial attempt to find any bgm
	var dir = DirAccess.open("res://assets/bgm")
	if dir:
		var files = dir.get_files()
		for file in files:
			if file.ends_with(".wav") or file.ends_with(".mp3") or file.ends_with(".ogg"):
				play_track("res://assets/bgm/" + file)
				break

func play_track(path: String, fade_time: float = 1.0) -> void:
	if current_track == path and bgm_player.playing:
		return
		
	if tween:
		tween.kill()
	
	var stream = load(path)
	if not stream:
		push_warning("BGMManager: Could not load track " + path)
		_play_tone_fallback()
		return
	if stream is AudioStreamWAV and _looks_silent_wav(stream as AudioStreamWAV):
		push_warning("BGMManager: Track appears silent, using tone fallback: " + path)
		_play_tone_fallback()
		return

	if bgm_player.playing:
		tween = create_tween()
		tween.tween_property(bgm_player, "volume_db", -80, fade_time)
		await tween.finished
		
	bgm_player.stream = stream
	bgm_player.volume_db = -80
	bgm_player.play()
	if not bgm_player.playing:
		_play_tone_fallback()
		return
	if tone_player.playing:
		tone_player.stop()
		tone_playback = null
		set_process(false)
	current_track = path
	
	tween = create_tween()
	tween.tween_property(bgm_player, "volume_db", 0, fade_time)

func stop(fade_time: float = 1.0) -> void:
	if tween:
		tween.kill()
	tween = create_tween()
	tween.tween_property(bgm_player, "volume_db", -80, fade_time)
	await tween.finished
	bgm_player.stop()
	if tone_player.playing:
		tone_player.stop()
	tone_playback = null
	set_process(false)
	current_track = ""


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


func _play_tone_fallback() -> void:
	var generator := AudioStreamGenerator.new()
	generator.mix_rate = 44100.0
	generator.buffer_length = 0.5
	tone_player.stream = generator
	tone_player.volume_db = -10.0
	tone_player.play()
	var playback := tone_player.get_stream_playback()
	if playback is AudioStreamGeneratorPlayback:
		tone_playback = playback as AudioStreamGeneratorPlayback
		tone_phase = 0.0
		set_process(true)


func _process(_delta: float) -> void:
	if tone_playback == null:
		return
	var frames := tone_playback.get_frames_available()
	if frames <= 0:
		return
	var hz := 220.0
	var increment := TAU * hz / 44100.0
	for _i in range(frames):
		var sample := sin(tone_phase) * 0.1
		tone_playback.push_frame(Vector2(sample, sample))
		tone_phase += increment
