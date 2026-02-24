# External UI Patch Template

This is a minimal patch template for teams that already built their own chapter UI.

## 1) Attach adapter to your UI scene script

```gdscript
extends Control

@onready var adapter := ChapterEntryUIAdapter.new()
@onready var list_container: VBoxContainer = %EntryList

func _ready() -> void:
	add_child(adapter)
	adapter.entries_loaded.connect(_on_entries_loaded)
	adapter.start_failed.connect(_on_start_failed)
	adapter.load_entries()

func _on_entries_loaded(entries: Array[Dictionary]) -> void:
	for child in list_container.get_children():
		child.queue_free()
	for entry in entries:
		var btn := Button.new()
		btn.text = "%s. %s" % [int(entry.get("order", 0)), str(entry.get("title", entry.get("entry_key", "")))]
		var key := str(entry.get("entry_key", ""))
		btn.pressed.connect(func() -> void:
			adapter.start_from_entry(key, true) # true=new run, false=keep current vars
		)
		list_container.add_child(btn)

func _on_start_failed(entry_key: String, reason: String) -> void:
	push_warning("Start failed: %s (%s)" % [entry_key, reason])
```

## 2) Start chapter by entry key

- `ChapterEntryBridge.start_entry("poirot")`
- `ChapterEntryBridge.start_entry("bouc")`

## 3) Optional variable reset before showing chapter list

```gdscript
ChapterEntryBridge.reset_story_variables()
```

## 4) Required artifacts

- `dialogic/timelines/chapter_entries.json`
- `dialogic/timelines/variable_defaults.json`
- `dialogic/timelines/chapter_*.dtl`

Generate and validate:

```powershell
python import_orient_express.py --input "东方快车谋杀案(6).json" --strict
python scripts/validate_chapter_outputs.py --input "东方快车谋杀案(6).json"
```
