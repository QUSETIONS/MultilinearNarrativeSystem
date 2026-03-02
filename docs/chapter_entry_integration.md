# Chapter Entry Integration (Parser-Only)

This project exposes parser-generated chapter entry contracts for external chapter UIs.

## Generated files

- `dialogic/timelines/chapter_entries.json`
- `dialogic/timelines/variable_defaults.json`
- `dialogic/timelines/chapter_*.dtl`

## Registry APIs

Use `ChapterRegistry` autoload:

- `get_entry_list() -> Array[Dictionary]`
- `start_entry(entry_key: String, label_name: String = "") -> bool`
- `start_chapter(chapter_id: String, label_name: String = "", reset_variables: bool = true) -> bool`
- `reset_variables_to_defaults() -> bool`

`start_entry/start_chapter` can refresh/apply defaults before start (`reset_variables=true` by default).

## Bridge script for external UI

`scripts/chapter_entry_bridge.gd` provides a thin adapter:

```gdscript
var bridge := ChapterEntryBridge.new()
var entries := bridge.get_entries() # entry_key/chapter_id/title/order...
bridge.start_entry("poirot")
```

It is also registered as an autoload singleton:

```gdscript
var entries = ChapterEntryBridge.get_entries()
ChapterEntryBridge.start_entry("poirot", "", true) # reset defaults
ChapterEntryBridge.start_entry("poirot", "", false) # keep current variables
```

For UI projects, use `scripts/chapter_entry_ui_adapter.gd` to avoid coupling UI code with registry internals.
See `docs/external_ui_patch_template.md` for a copy-paste patch template.

## Recommended startup flow

1. Run parser:
```powershell
python import_orient_express.py --input "东方快车谋杀案(6).json" --strict
```
2. Validate artifacts:
```powershell
python scripts/validate_chapter_outputs.py --input "东方快车谋杀案(6).json"
```
3. External UI reads `get_entries()` and calls `start_entry(...)`.

## Godot quick verification panel

For local QA, attach `scripts/chapter_debug_panel.gd` to any active scene as a child node.
At runtime:

- Press `F9` to show/hide panel.
- Test entry starts:
  - `Start Poirot (Reset)`
  - `Start Bouc (Reset)`
  - `Start Poirot (Keep)`
  - `Start Bouc (Keep)`
- Use `Reset Vars` and `Refresh` to inspect current `Dialogic.VAR.var_storage`.
