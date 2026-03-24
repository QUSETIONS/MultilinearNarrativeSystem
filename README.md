<p align="center">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Frontend-Vue_3-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/AI-NAR_Pipeline-FF6F00?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<h1 align="center">🎨 Narrative Asset Factory</h1>
<h3 align="center">叙事资产工厂 · AI 驱动的游戏素材提取与生成平台</h3>

---

## 💡 这是什么？

一个 **AI 驱动的游戏资产生产平台**，专为视觉小说 / 互动叙事游戏设计。

创作者只需 **导入剧本 JSON** 或 **输入纯文字大纲**，平台自动：

1. 🧠 **智能提取** — DeepSeek AI 从全剧本中识别角色、场景、道具、CG、BGM、音效
2. ✨ **叙事精炼** — NAR 注意力机制为每个素材生成高质量 AI 绘画提示词
3. 🎨 **批量生成** — 调用 SiliconFlow (FLUX/Kolors) 等模型批量生产美术资产
4. 📦 **一键导出** — 打包为 Godot 引擎可直接使用的 ZIP 资源包

```
剧本 JSON / 纯文字大纲
        │
        ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ 🧠 AI 提取   │ ──▶ │ ✨ NAR 精炼  │ ──▶ │ 🎨 AI 生成  │
  │  DeepSeek    │     │  注意力+DPO  │     │  FLUX/Kolors│
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
                              ┌────────────────────┤
                              ▼                    ▼
                        assets/             godot_assets.zip
                   (立绘/背景/BGM)        (Godot 引擎资源包)
```

---

## 🏗️ 项目结构

```
.
├── foundation_platform/          ← 后端：FastAPI 资产生成服务
│   ├── api/
│   │   ├── api.py                #  应用入口 (uvicorn, port 8095)
│   │   ├── models.py             #  Pydantic 数据模型
│   │   ├── state.py              #  全局状态 (内存注册表)
│   │   ├── routes/
│   │   │   ├── assets.py         #  素材注册 & 剧本提取
│   │   │   ├── generation.py     #  生成任务调度 & 状态查询
│   │   │   ├── narrative.py      #  叙事配置 & DPO 反馈
│   │   │   ├── export.py         #  Godot ZIP 导出
│   │   │   ├── health.py         #  健康检查
│   │   │   └── ws.py             #  WebSocket 实时推送
│   │   └── services/
│   │       ├── generation_service.py  #  核心生成管线 (并发控制)
│   │       ├── db_service.py          #  SQLite 持久化
│   │       └── websocket.py           #  连接管理器
│   ├── core/
│   │   ├── nar.py                #  🧩 NAR 引擎 (Softmax 深度注意力)
│   │   ├── extractor.py          #  📦 文字大纲解析器
│   │   ├── attention.py          #  🎯 叙事注意力管理器
│   │   ├── refiner.py            #  ✨ 提示词精炼器
│   │   ├── critic.py             #  🔍 叙事一致性审计
│   │   ├── memory.py             #  💾 共享叙事记忆缓冲区
│   │   ├── relationships.py      #  👥 角色社交关系图
│   │   ├── generator.py          #  🏭 模型注册表 (Mock/SiliconFlow)
│   │   └── llm_service.py        #  🤖 DeepSeek LLM 服务
│   └── config/
│       └── models.json           #  API 密钥配置
│
├── editor-web/                   ← 前端：Vue 3 + Element Plus
│   └── src/
│       ├── App.vue               #  主框架 (4 Tab 页面)
│       ├── components/
│       │   ├── AssetWorkstation.vue    #  📊 资产生产指挥中心
│       │   ├── NarrativeControl.vue    #  🕸️ 叙事控制 (力导向图)
│       │   ├── ScriptEditor.vue       #  ✏️ 剧本编辑器
│       │   ├── OverviewPage.vue       #  📋 项目总览
│       │   ├── GenerationWizard.vue   #  🧙 单资产生成向导
│       │   └── TaskQueueDrawer.vue    #  📦 任务队列
│       ├── stores/                    #  Pinia 状态管理
│       └── services/api.js            #  后端 API 封装
│
└── assets/                       ← 生成产物
    ├── portraits/                #  人物立绘
    ├── backgrounds/              #  背景图
    ├── items/                    #  道具图
    ├── cgs/                      #  剧情 CG
    ├── bgm/                      #  背景音乐
    └── sfx/                      #  音效
```

---

## 🚀 快速启动

**🔥 一键启动（推荐）：**
- **Windows**: 直接双击项目根目录下的 `start.bat`
- **Mac/Linux**: 在终端执行 `./start.sh`
即可同时启动并自动连接所有的前后端服务！

---

### 手动分步启动方式（如需调试）：

### 1. 后端

```bash
cd foundation_platform
pip install fastapi uvicorn pydantic requests numpy
python -m foundation_platform.api.api
# ✅ http://localhost:8095
```

### 2. 前端

```bash
cd editor-web
npm install
npm run dev
# ✅ http://localhost:5173
```

### 3. 配置 AI 模型（可选）

编辑 `foundation_platform/config/models.json`：

```json
{
  "deepseek": {
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat"
  },
  "siliconflow": {
    "api_key": "sk-xxx",
    "base_url": "https://api.siliconflow.cn/v1",
    "model": "Kwai-Kolors/Kolors"
  }
}
```

> 未配置 API Key 时，系统自动回退到 Mock 生成器（生成占位文件）。

---

## ⚙️ 核心机制

### NAR — Narrative Attention Residuals

参考 Kimi Team 2026 论文 [Attention Residuals](https://arxiv.org/abs/2603.15031)，用 **softmax 深度注意力** 替代固定权重残差：

| 层级 | 机制 | 作用 |
|------|------|------|
| **Pipeline NAR** | 跨阶段信息检索 | 精炼器自动回溯全局配置和提取阶段上下文 |
| **Recursive NAR** | 跨轮次信息强化 | 多轮精炼防止信息因"深度"增加而稀释 |
| **Temporal NAR** | 跨会话反馈召回 | 从 DPO 历史中检索最相关的 👍/👎 反馈 |

### DPO 人类反馈对齐

用户对生成结果 👍/👎 → 反馈注入 NAR 栈 → 权重衰减 → 下次自动规避。

### 模态路由

| 素材类型 | 路由 | 生成器 |
|---------|------|--------|
| 人物立绘 / 背景图 / 道具图 / 剧情CG | 图像管线 | SiliconFlow (FLUX/Kolors) |
| BGM / 音效 | 占位生成 | Placeholder (预留 Audio-LLM 接口) |

---

## 🛠 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | API 服务 + WebSocket 实时推送 |
| AI 文本 | DeepSeek API | 剧本理解 + 提示词增强 |
| AI 绘画 | SiliconFlow (FLUX/Kolors) | 高质量图像生成 |
| 核心逻辑 | NAR + Attention + DPO | 叙事感知 Prompt 工程 |
| 前端 | Vue 3 + Element Plus + Pinia | 可视化生产指挥台 |
| 持久化 | SQLite | 资产注册表 + 生成历史 |

---

## 📜 License

MIT License.

<p align="center">
  <sub>Built with ❤️ for interactive storytelling. Powered by AI, guided by human taste.</sub>
</p>
