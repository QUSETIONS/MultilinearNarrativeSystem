<p align="center">
  <img src="https://img.shields.io/badge/Engine-Godot_4.3+-478cbf?style=for-the-badge&logo=godotengine&logoColor=white" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Frontend-Vue_3-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/AI-DPO_Aligned-FF6F00?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<h1 align="center">🚂 Multilinear Narrative System</h1>
<h3 align="center">多线性叙事系统 · AI 驱动的互动叙事引擎</h3>

---

## 🗺️ 系统总览

本项目包含 **两个生产平台** + **一个游戏运行时**，三者协作完成从创意到成品的全流程：

```
                    ┌─────────────────────────┐
                    │  创作者输入（文字大纲）     │
                    │                         │
                    │  角色：波洛、公主、布克...   │
                    │  场景：车站夜景、餐车、包厢   │
                    │  BGM：紧张、优雅、悬疑      │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│  🧠 素材提取与生成平台     │   │  🎛️ 内容设计与编辑平台      │
│  foundation_platform/    │   │  editor-web/              │
│                         │   │                          │
│  输入: 文字素材说明        │   │  输入: 创作者的叙事设计      │
│  输出: 美术资产 + BGM     │   │  输出: JSON（叙事结构数据）  │
│                         │   │                          │
│  ← 用户反馈(👍/👎)调整 →  │   │  流程图编辑 / 节点设计      │
└────────────┬────────────┘   └────────────┬─────────────┘
              │                             │
              ▼                             ▼
        assets/背景图                  东方快车谋杀案修复版.json
        assets/人物立绘
        assets/bgm
              │                             │
              └──────────────┬──────────────┘
                             ▼
                    ┌─────────────────────┐
                    │  🎮 游戏运行时        │
                    │  Godot 4.3 + Dialogic│
                    │                     │
                    │  读取 JSON + 资产     │
                    │  → 可玩的互动小说      │
                    └─────────────────────┘
```

---

## 🧠 素材提取与生成平台（`foundation_platform/`）

> **AI 驱动的游戏资产工厂。** 创作者只需用文字描述需要什么素材，平台自动生成美术和音频。

### 它做了什么？

| 步骤 | 说明 |
|------|------|
| **1. 接收素材说明** | 创作者用文字描述需要的资产（角色外貌、场景氛围、音乐风格等） |
| **2. 注意力聚焦** | AI 分析文字，提取关键词并分配叙事权重（时代、情绪、角色特征） |
| **3. 提示词精炼** | 将简单描述扩展为高质量 AI Prompt（融入社交关系、递归打磨） |
| **4. AI 生成** | 调用 AI 模型（Mock / Coze / ComfyUI）生成图片或音频 |
| **5. 人类反馈 (DPO)** | 创作者对结果 👍/👎，不满意的原因会被记录并自动影响下次生成 |

### 核心流程

```
 "车站夜景，寒冷刺骨，         Attention          Refiner           Generator
  蒸汽弥漫的1930年代"    →   注意力聚焦     →   提示词精炼     →    AI 生成
  (文字素材说明)             (cold mood:1.25)   (+ art deco,       → station_night.png
                            (1930s:1.1)         cinematic...)
                                                    ↑
                                              DPO 反馈闭环
                                          "太现代" → 自动规避
```

### 特色机制

| 机制 | 说明 |
|------|------|
| **Narrative Attention** | 模仿 Transformer 自注意力，根据情绪/角色/时代为 Prompt 分配权重 |
| **Social Weights** | 角色间社交关系（张力/亲密度）影响生成的视觉语气 |
| **Recursive Refinement** | AI 自我评审多轮迭代，逐步提升 Prompt 质量 |
| **DPO Feedback** | 用户 👍/👎 → 负面反馈注入 anti-pattern → 权重衰减 → 下次自动规避 |

### 目录结构

```
foundation_platform/
├── api/
│   └── api.py                # FastAPI 服务 (端口 8088)
│                              # /status            资产盘点
│                              # /generate           触发生成
│                              # /narrative/config   全局参数
│                              # /narrative/feedback DPO 反馈
└── core/
    ├── extractor.py          # 📦 资产提取器
    ├── attention.py          # 🎯 注意力管理器
    ├── refiner.py            # ✨ 提示词精炼器 + ICL
    ├── relationships.py      # 👥 社交关系管理
    └── generator.py          # 🏭 AI 生成器注册表
```

### 启动

```bash
pip install fastapi uvicorn pydantic
python -m foundation_platform.api.api   # http://localhost:8088
```

---

## 🎛️ 内容设计与编辑平台（`editor-web/`）

> **叙事结构的可视化编辑器。** 创作者在这里设计故事的分支、对话、选项，最终导出 JSON 供游戏引擎使用。

### 它做了什么？

| 功能 | 说明 |
|------|------|
| **流程图编辑** | 多线性分支的可视化拖拽设计 |
| **节点编辑** | 对话、选择、跳转等节点的属性配置 |
| **素材管理** | 资产生产指挥台（盘点/批量生成/实时监控） |
| **叙事控制** | 社交关系矩阵 / 全局注意力参数调节 |
| **DPO 反馈** | 对已生成素材进行 👍/👎，驱动生成平台优化 |
| **JSON 导出** | 输出叙事结构 JSON，供 Godot 游戏引擎消费 |

### 关键组件

```
editor-web/src/components/
├── FlowCanvas.vue           # 🔀 章节流程图（多线性分支可视化）
├── NodeCanvas.vue           # 📝 节点编辑画布
├── EditorPage.vue           # 🎬 叙事编辑器主页
├── AssetWorkstation.vue     # 📊 资产生产指挥中心
├── AssetCard.vue            # 🃏 素材卡片（预览 + 👍/👎）
└── NarrativeControl.vue     # 🕸️ 叙事控制（社交矩阵/参数调节）
```

### 启动

```bash
cd editor-web
npm install
npm run dev   # http://localhost:5173
```

---

## 🎮 游戏运行时（Godot + Dialogic）

> **最终玩家体验的互动视觉小说。** 读取编辑平台导出的 JSON 和生成平台产出的资产，渲染为可玩的游戏。

| 目录 | 内容 |
|------|------|
| `addons/dialogic/` | Dialogic 2 插件 |
| `dialogic/characters/` | 角色定义 (`.dch`) |
| `dialogic/timelines/` | 章节对话树 (`.dtl`) |
| `assets/` | 背景图、人物立绘、BGM |
| `scripts/main.gd` | 游戏主逻辑 |

**启动**：Godot 4.3+ 打开 `project.godot` → F5

---

## 🔁 DPO 反馈闭环

```mermaid
sequenceDiagram
    participant C as 👤 创作者
    participant E as 🎛️ 编辑平台
    participant G as 🧠 生成平台
    participant S as 💾 feedback.jsonl

    C->>E: 描述需要的素材（文字）
    E->>G: 传递素材说明
    G->>G: Attention → Refiner → Generator
    G-->>E: 返回美术/BGM 资产

    C->>E: 对结果 👎 "光影太现代"
    E->>G: POST /narrative/feedback
    G->>S: 记录反馈

    Note over C,S: 下次生成同一资产

    C->>E: 重新生成
    E->>G: POST /generate
    G->>G: 注入 [AVOID: 光影太现代] + 权重衰减
    G-->>E: 改进后的资产
```

---

## 📊 开发阶段

| 阶段 | 名称 | 子系统 | 状态 |
|------|------|--------|------|
| 1 | 基础架构设计 | 🧠 生成平台 | ✅ |
| 2 | 任务系统实现 | 🧠 生成平台 | ✅ |
| 3 | 工作站实时更新 | 🎛️ 编辑平台 | ✅ |
| 4 | 基础优化 v2.0 | 🧠 生成平台 | ✅ |
| 5 | Attention 注意力机制 | 🧠 生成平台 | ✅ |
| 6 | 系统审计 (Scout) | 全局 | ✅ |
| 7 | 叙事结构修复 | 🎮 游戏运行时 | ✅ |
| 8 | 社交关系权重 | 🧠 生成平台 | ✅ |
| 9 | 递归细化机制 | 🧠 生成平台 | ✅ |
| 10 | 观测与控制 | 🎛️ 编辑平台 | ✅ |
| 11 | 叙事控制中心 | 🎛️ 编辑平台 | ✅ |
| **12** | **DPO 人类反馈对齐** | **🧠 + 🎛️** | ✅ |

---

## 🛠 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 游戏引擎 | Godot 4.3 + GDScript | 互动对话 & 视觉小说 |
| 对话插件 | Dialogic 2 | 时间线管理 & 角色系统 |
| AI 后端 | Python + FastAPI | 资产生成管线 |
| AI 逻辑 | Attention + DPO | 叙事感知 Prompt 工程 |
| 前端 | Vue 3 + Element Plus | 编辑平台 & 生产指挥 |
| 数据 | JSON + JSONL | 叙事结构 + 反馈对 |

---

## 📜 License
MIT License. Built with [Dialogic 2](https://github.com/dialogic-godot/dialogic).

<p align="center">
  <sub>Built with ❤️ for interactive storytelling. Powered by AI, guided by human taste.</sub>
</p>
