# Changelog

- 2026-02-26: Explore pass for menu error, BGM reliability, and branch-style flow-map connectors.

## 2026-02-26 Recheck Pass (CN + Layout + BGM)
- Rewrote scripts/main_menu.gd and scenes/main_menu.tscn in UTF-8; forced runtime CN labels and stronger BGM fallback.
- Rewrote scripts/chapter_tree_select.gd and scenes/chapter_tree_select.tscn; centered graph based on viewport/graph width and localized runtime labels.
- Hardened scripts/bgm_manager.gd to unmute Master bus and use tone fallback when track playback fails.
