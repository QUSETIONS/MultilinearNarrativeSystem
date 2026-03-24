<template>
  <div class="app-container">
    <!-- Header -->
    <header class="premium-header">
      <div class="logo-area">
        <span class="logo-text">TRAIN EDITOR</span>
        <el-tag type="info" size="small" effect="plain" style="border:1px solid var(--border)">V 25.0 AI-POWERED</el-tag>
      </div>

      <!-- View Switcher -->
      <nav class="view-toggle">
        <div 
          v-for="tab in viewTabs" :key="tab.key"
          class="toggle-item" 
          :class="{ active: currentView === tab.key }" 
          @click="switchView(tab.key)"
        >
          <span class="toggle-icon">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
          <span v-if="currentView === tab.key" class="active-bar"></span>
        </div>
      </nav>

      <div class="action-area">
        <!-- Backend Status Indicator -->
        <el-tooltip :content="healthTooltip" placement="bottom" :show-after="200">
          <div class="health-indicator" :class="{ online: backendOnline, offline: !backendOnline }">
            <span class="health-dot"></span>
            <span class="health-text">{{ backendOnline ? '已连接' : '离线' }}</span>
          </div>
        </el-tooltip>

        <el-button-group>
          <el-button size="small" :icon="RefreshLeft" @click="store.undo()" :disabled="store.historyIndex <= 0">撤销</el-button>
          <el-button size="small" :icon="RefreshRight" @click="store.redo()" :disabled="store.historyIndex >= store.history.length - 1">重做</el-button>
        </el-button-group>
        
        <el-button-group>
          <el-button type="primary" size="small" :icon="FolderOpened" @click="onImport">导入 JSON</el-button>
          <el-button type="success" size="small" :icon="Download" :disabled="!store.filename" @click="onExport">导出 JSON</el-button>
        </el-button-group>
        <transition name="fade-slide">
          <span v-if="store.filename" class="filename-badge">📄 {{ store.filename }}</span>
        </transition>
      </div>
    </header>

    <!-- Main Content with View Transition -->
    <div class="page-view">
      <transition :name="viewTransition" mode="out-in">
        <component :is="currentComponent" :key="currentView"
          v-bind="currentProps"
          @jump-to-editor="onJumpToEditor"
          @import-json="onImport"
          @go-assets="switchView('assets')"
          @go-editor="switchView('editor')"
          @open-wizard="openWizard"
        />
      </transition>
    </div>

    <!-- Generation Wizard Dialog -->
    <GenerationWizard ref="wizardRef" />

    <!-- Hidden Input for File -->
    <input ref="fileInputRef" type="file" accept=".json" style="display:none" @change="onFileChange" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, shallowRef } from 'vue'
import { FolderOpened, Download, RefreshLeft, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useEditorStore } from './stores/editor.js'
import { apiService } from './services/api'
import OverviewPage from './components/OverviewPage.vue'
import EditorPage from './components/EditorPage.vue'
import AssetWorkstation from './components/AssetWorkstation.vue'
import NarrativeControl from './components/NarrativeControl.vue'
import GenerationWizard from './components/GenerationWizard.vue'

const store = useEditorStore()
const currentView = ref('overview')
const fileInputRef = ref(null)
const wizardRef = ref(null)
const jumpChapterId = ref(null)
const backendOnline = ref(false)
const healthInfo = ref(null)
let healthTimer = null

const viewTabs = [
  { key: 'overview',  label: '总览',     icon: '📊' },
  { key: 'editor',    label: '节点编辑器', icon: '🧩' },
  { key: 'assets',    label: '素材工作站', icon: '🎨' },
  { key: 'narrative', label: '叙事控制',  icon: '🔮' },
]

const viewTransition = ref('view-fade-slide')

const viewComponents = {
  overview: OverviewPage,
  editor: EditorPage,
  assets: AssetWorkstation,
  narrative: NarrativeControl,
}

const currentComponent = computed(() => viewComponents[currentView.value])
const currentProps = computed(() => {
  if (currentView.value === 'editor') return { 'initial-chapter-id': jumpChapterId.value }
  return {}
})

// Determine slide direction based on tab order
const viewOrder = ['overview', 'editor', 'assets', 'narrative']
function switchView(target) {
  if (target === currentView.value) return
  const fromIdx = viewOrder.indexOf(currentView.value)
  const toIdx = viewOrder.indexOf(target)
  viewTransition.value = toIdx > fromIdx ? 'view-slide-left' : 'view-slide-right'
  currentView.value = target
}

const healthTooltip = computed(() => {
  if (!backendOnline.value) return '后端服务未连接 (localhost:8095)'
  const h = healthInfo.value
  if (!h) return '已连接'
  const parts = [`版本: ${h.version || 'N/A'}`]
  if (h.image_model) parts.push(`生图模型: ${h.image_model}`)
  if (h.llm_available) parts.push('LLM: ✅')
  if (h.image_gen_available) parts.push('生图: ✅')
  return parts.join(' | ')
})

async function checkHealth() {
  try {
    const data = await apiService.checkHealth(AbortSignal.timeout(3000))
    backendOnline.value = true
    healthInfo.value = data
  } catch {
    backendOnline.value = false
    healthInfo.value = null
  }
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 10000)
})

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer)
})

function onImport() { fileInputRef.value?.click() }
function openWizard() { wizardRef.value?.open() }

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      store.importJSON(ev.target.result, file.name)
      ElNotification({
        title: '导入成功',
        message: `已载入项目: ${file.name}`,
        type: 'success',
        duration: 3000,
        position: 'bottom-right'
      })
    } catch (err) {
      ElNotification({
        title: '导入失败',
        message: 'JSON 解析失败: ' + err.message,
        type: 'error',
        duration: 5000,
        position: 'bottom-right'
      })
    }
  }
  reader.readAsText(file, 'utf-8')
  e.target.value = ''
}

function onExport() {
  const text = store.exportJSON()
  const blob = new Blob([text], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = store.filename
  a.click()
  URL.revokeObjectURL(url)
  ElNotification({
    title: '导出完成',
    message: `配置已保存: ${store.filename}`,
    type: 'success',
    duration: 2500,
    position: 'bottom-right'
  })
}

function onJumpToEditor(chapterId) {
  jumpChapterId.value = chapterId
  switchView('editor')
}
</script>

<style>
/* ============================================================
   Phase 33: Premium Transitions & Micro-Animations
   ============================================================ */

/* ---- View Transition: Directional Slide ---- */
.view-slide-left-enter-active,
.view-slide-left-leave-active,
.view-slide-right-enter-active,
.view-slide-right-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.view-slide-left-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.view-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-40px);
}

.view-slide-right-enter-from {
  opacity: 0;
  transform: translateX(-40px);
}
.view-slide-right-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

/* ---- Fade slide (for filename badge etc) ---- */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* ---- Simple Fade ---- */
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ---- Filename badge ---- */
.filename-badge {
  font-size: 11px;
  color: var(--text-muted, #8899aa);
  background: rgba(255,255,255,0.05);
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  letter-spacing: 0.3px;
}

/* ---- View Toggle Enhancement ---- */
.view-toggle {
  display: flex;
  gap: 2px;
  background: rgba(255,255,255,0.04);
  border-radius: 10px;
  padding: 3px;
}

.toggle-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: rgba(255,255,255,0.55);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  overflow: hidden;
}

.toggle-item:hover {
  color: rgba(255,255,255,0.85);
  background: rgba(255,255,255,0.06);
}

.toggle-item:active {
  transform: scale(0.96);
}

.toggle-item.active {
  color: #fff;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.35), rgba(139, 92, 246, 0.25));
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.2);
  font-weight: 600;
}

.toggle-icon {
  font-size: 14px;
  transition: transform 0.2s ease;
}

.toggle-item:hover .toggle-icon {
  transform: scale(1.15);
}

.active-bar {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: linear-gradient(90deg, #818cf8, #a78bfa);
  border-radius: 2px;
  animation: active-bar-enter 0.3s ease forwards;
}

@keyframes active-bar-enter {
  from { width: 0; opacity: 0; }
  to   { width: 20px; opacity: 1; }
}

/* ---- Action Area ---- */
.action-area {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* ---- Button Ripple Effect ---- */
.el-button {
  transition: all 0.2s ease !important;
}
.el-button:active:not(:disabled) {
  transform: scale(0.95) !important;
}

/* ---- Health Indicator ---- */
.health-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  cursor: default;
  transition: all 0.3s ease;
}

.health-indicator.online {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.health-indicator.offline {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.health-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  animation: health-pulse 2s infinite;
}

.online .health-dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

.offline .health-dot {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
  animation: none;
}

@keyframes health-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}
</style>
