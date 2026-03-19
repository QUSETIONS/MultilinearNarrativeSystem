<template>
  <div class="app-container">
    <!-- Header -->
    <header class="premium-header">
      <div class="logo-area">
        <span class="logo-text">TRAIN EDITOR</span>
        <el-tag type="info" size="small" effect="plain" style="border:1px solid var(--border)">V 4.0 PREMIUM</el-tag>
      </div>

      <!-- View Switcher -->
      <div class="view-toggle">
        <div 
          class="toggle-item" 
          :class="{ active: currentView === 'overview' }" 
          @click="currentView = 'overview'"
        >
          总览
        </div>
        <div 
          class="toggle-item" 
          :class="{ active: currentView === 'editor' }" 
          @click="currentView = 'editor'"
        >
          节点编辑器
        </div>
        <div 
          class="toggle-item" 
          :class="{ active: currentView === 'assets' }" 
          @click="currentView = 'assets'"
        >
          素材工作站
        </div>
      </div>

      <div class="action-area" style="display: flex; gap: 12px; align-items: center;">
        <el-button-group>
          <el-button size="small" :icon="RefreshLeft" @click="store.undo()" :disabled="store.historyIndex <= 0">撤销</el-button>
          <el-button size="small" :icon="RefreshRight" @click="store.redo()" :disabled="store.historyIndex >= store.history.length - 1">重做</el-button>
        </el-button-group>
        
        <el-button-group>
          <el-button type="primary" size="small" :icon="FolderOpened" @click="onImport">导入 JSON</el-button>
          <el-button type="success" size="small" :icon="Download" :disabled="!store.filename" @click="onExport">导出 JSON</el-button>
        </el-button-group>
        <transition name="fade">
          <span v-if="store.filename" style="font-size: 12px; color: var(--text-muted);">{{ store.filename }}</span>
        </transition>
      </div>
    </header>

    <!-- Main Content -->
    <div class="page-view">
      <OverviewPage 
        v-if="currentView === 'overview'" 
        @jump-to-editor="onJumpToEditor" 
      />
      <EditorPage 
        v-if="currentView === 'editor'" 
        :initial-chapter-id="jumpChapterId" 
      />
      <AssetWorkstation 
        v-if="currentView === 'assets'" 
      />
    </div>

    <!-- Hidden Input for File -->
    <input ref="fileInputRef" type="file" accept=".json" style="display:none" @change="onFileChange" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FolderOpened, Download, RefreshLeft, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useEditorStore } from './stores/editor.js'
import OverviewPage from './components/OverviewPage.vue'
import EditorPage from './components/EditorPage.vue'
import AssetWorkstation from './components/AssetWorkstation.vue'

const store = useEditorStore()
const currentView = ref('overview')
const fileInputRef = ref(null)
const jumpChapterId = ref(null)

function onImport() { fileInputRef.value?.click() }

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      store.importJSON(ev.target.result, file.name)
      ElMessage({
        message: `成功载入: ${file.name}`,
        type: 'success',
        duration: 2000
      })
    } catch (err) {
      ElMessage.error('JSON 解析失败: ' + err.message)
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
  ElMessage.success('配置已保存至本地')
}

function onJumpToEditor(chapterId) {
  jumpChapterId.value = chapterId
  currentView.value = 'editor'
}
</script>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity 0.5s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
