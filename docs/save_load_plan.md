# Save/Load System Implementation Plan

将"快速存读档"升级为带有多槽位的独立存档界面。计划分为两个**互不干扰**的部分。

---

## Part 1: UI 界面层 (Agent A)

**目标**: 创建存档/读档界面场景，包含可视化的槽位列表。

### 1.1 创建存档界面场景

- **[NEW]** `res://scenes/save_load_screen.tscn`
  - Root: `CanvasLayer` (layer=10，覆盖游戏但在UI按钮之下)
  - `PanelContainer` (全屏半透明背景)
  - `VBoxContainer`:
    - `Label` (标题："存档" 或 "读档")
    - `GridContainer` 或 `VBoxContainer` (槽位容器，5-8个槽位)
    - `Button` (返回按钮)

### 1.2 创建单个槽位组件

- **[NEW]** `res://scenes/save_slot.tscn`
  - `PanelContainer`:
    - `HBoxContainer`:
      - `TextureRect` (缩略图，可选)
      - `VBoxContainer`:
        - `Label` (槽位号："存档 1")
        - `Label` (时间戳："2026-02-06 17:30")
        - `Label` (章节名："第二章：开往伊斯坦布尔")
      - `Button` (操作按钮：存档/读档/删除)

### 1.3 修改现有按钮逻辑

- **[MODIFY]** `res://scripts/vn_controller.gd`
  - `_on_save_pressed()`: 改为打开存档界面 (Mode: Save)
  - `_on_load_pressed()`: 改为打开存档界面 (Mode: Load)

### 1.4 界面脚本 (UI逻辑，不涉及存档数据)

- **[NEW]** `res://scripts/save_load_screen.gd`
  - `func open(mode: String)`: 打开界面，设置模式 ("save"/"load")
  - `func close()`: 关闭界面，恢复游戏
  - `func _populate_slots()`: 遍历槽位，加载显示数据 (调用 Part 2 的 API)
  - 信号: `slot_selected(slot_id, mode)` -> 发送给 Part 2 处理

---

## Part 2: 数据逻辑层 (Agent B)

**目标**: 实现存档数据管理、文件读写、与 Dialogic 状态交互。

### 2.1 创建存档管理器 (Autoload)

- **[NEW]** `res://scripts/save_manager.gd`
  - 常量: `MAX_SLOTS = 8`, `SAVE_DIR = "user://saves/"`
  - `func get_slot_info(slot_id: int) -> Dictionary`: 返回槽位元数据 (时间戳、章节名、是否为空)
  - `func save_game(slot_id: int)`: 保存当前游戏状态到指定槽位
  - `func load_game(slot_id: int)`: 从槽位恢复游戏状态
  - `func delete_save(slot_id: int)`: 删除存档
  - `func get_all_slots() -> Array[Dictionary]`: 返回所有槽位信息供 UI 显示

### 2.2 存档数据结构

```gdscript
# 每个存档文件 (e.g., save_1.json):
{
    "timestamp": "2026-02-06T17:30:00",
    "chapter_name": "第二章：开往伊斯坦布尔",
    "dialogic_state": { ... },  # Dialogic.Save.get_full_state()
    "thumbnail": "base64_encoded_image"  # 可选
}
```

### 2.3 与 Dialogic 集成

- 使用 `Dialogic.Save.get_full_state()` 获取完整状态
- 使用 `Dialogic.Save.load_full_state(state)` 恢复状态
- 保存/恢复后触发信号通知 UI

### 2.4 注册 Autoload

- **[MODIFY]** `project.godot`
  - 添加 `SaveManager` 到 autoload 列表

---

## 接口约定 (两 Agent 共用)

| Part 1 调用 | Part 2 提供 |
|------------|-------------|
| `SaveManager.get_all_slots()` | 返回 `Array[Dictionary]` |
| `SaveManager.save_game(slot_id)` | 执行存档 |
| `SaveManager.load_game(slot_id)` | 执行读档 |
| `SaveManager.delete_save(slot_id)` | 删除存档 |

**信号 (Part 2 发出, Part 1 监听)**:

- `save_completed(slot_id)`
- `load_completed(slot_id)`

---

## Verification Plan

### Part 1 测试

- 点击 Save/Load 按钮，界面正确弹出
- 槽位正确显示占用/空闲状态
- 返回按钮关闭界面

### Part 2 测试

- 调用 `SaveManager.save_game(1)` 后，`user://saves/save_1.json` 存在
- 调用 `SaveManager.load_game(1)` 后，Dialogic 状态正确恢复
- 空槽位返回正确的元数据
