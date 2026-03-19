<template>
  <div class="overview-scroll fade-in">
    <!-- Header Hero -->
    <div style="margin-bottom: 20px;">
      <h1 style="font-size: 32px; font-weight: 800; margin-bottom: 8px;">欢迎回来, 编剧</h1>
      <p style="color: var(--text-secondary); font-size: 15px;">
        {{ store.filename ? `当前正在编辑: ${store.filename}` : '开始创作你的第一个故事' }}
      </p>
    </div>

    <!-- Chapter Timeline -->
    <section class="section-card">
      <div class="card-header">
        <h2><el-icon><Collection /></el-icon> 章节流覆盖</h2>
        <el-button type="primary" size="small" @click="store.addChapter">新建章节</el-button>
      </div>
      <div style="padding: 24px; overflow-x: auto;">
        <ChapterFlow @select-chapter="jumpToEditor" />
      </div>
    </section>

    <!-- Asset Gallery -->
    <section class="section-card">
      <div class="card-header">
        <h2><el-icon><Picture /></el-icon> 资源库 (Gallery)</h2>
      </div>
      <div style="padding: 24px;">
        <AssetsPanel />
      </div>
    </section>
  </div>
</template>

<script setup>
import { Collection, Picture } from '@element-plus/icons-vue'
import { useEditorStore } from '../stores/editor.js'
import ChapterFlow from './ChapterFlow.vue'
import AssetsPanel from './AssetsPanel.vue'

const store = useEditorStore()
const emit = defineEmits(['jump-to-editor'])

function jumpToEditor(chapterId) {
  emit('jump-to-editor', chapterId)
}
</script>
