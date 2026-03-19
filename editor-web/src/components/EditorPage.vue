<template>
  <div class="editor-layout fade-in">
    <!-- Sidebar -->
    <aside class="editor-sidebar">
      <div style="padding: 16px; border-bottom: 1px solid var(--border);">
        <h3 style="font-size: 14px; font-weight: 700; color: var(--gold); display: flex; align-items: center; gap: 8px;">
          <el-icon><Fold /></el-icon> 章节目录
        </h3>
      </div>
      
      <el-scrollbar>
        <div style="padding: 8px;">
          <div 
            v-for="ch in store.chapters" 
            :key="ch.id"
            class="chapter-nav-item"
            :class="{ active: activeChapterId === ch.id }"
            @click="activeChapterId = ch.id"
          >
            <el-icon><Document /></el-icon>
            <span class="nav-text">{{ ch.title || '未命名章节' }}</span>
          </div>
        </div>
      </el-scrollbar>

      <div style="padding: 16px; border-top: 1px solid var(--border); background: rgba(0,0,0,0.1);">
         <el-button type="primary" size="small" style="width:100%" @click="store.addChapter">
           <el-icon><Plus /></el-icon> 新增章节
         </el-button>
      </div>
    </aside>

    <!-- Canvas -->
    <main class="editor-canvas-area" :class="{ fullscreen: isFullscreen }">
      <NodeCanvas :chapter-id="activeChapterId" />
      
      <!-- Canvas Tip Bar -->
      <div class="canvas-tip-bar">
        <el-icon><InfoFilled /></el-icon>
        <span>💡 拖动节点右侧点以拉出连线 · 双击空白处添加节点 · 使用 Ctrl + 滚轮缩放</span>
        <div style="margin-left: auto;">
           <el-button link size="small" :icon="isFullscreen ? FullScreen : FullScreen" @click="toggleFullscreen">
             {{ isFullscreen ? '退出全屏' : '全屏编辑器' }}
           </el-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Fold, Document, Plus, InfoFilled, FullScreen } from '@element-plus/icons-vue'
import { useEditorStore } from '../stores/editor.js'
import NodeCanvas from './NodeCanvas.vue'

const props = defineProps({ initialChapterId: String })
const store = useEditorStore()
const activeChapterId = ref(props.initialChapterId)
const isFullscreen = ref(false)

onMounted(() => {
  if (!activeChapterId.value && store.chapters.length) {
    activeChapterId.value = store.chapters[0].id
  }
})

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}
</script>

<style scoped>
.chapter-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
  color: var(--text-secondary);
}
.chapter-nav-item:hover { background: var(--border); color: var(--text-primary); }
.chapter-nav-item.active { background: var(--accent-gradient); color: white; }
.nav-text { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.canvas-tip-bar {
  position: absolute;
  bottom: 16px; left: 16px; right: 16px;
  height: 40px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: 12px;
  color: var(--text-secondary);
  gap: 8px;
  z-index: 10;
}

.editor-canvas-area.fullscreen {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 2000;
}
</style>
