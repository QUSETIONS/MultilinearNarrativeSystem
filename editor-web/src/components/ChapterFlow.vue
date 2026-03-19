<template>
  <div class="chapter-flow-container">
    <div v-if="!store.chapters.length" class="empty-state-mini">
      暂无章节，请先导入剧情文件或点击“新建章节”
    </div>
    <div v-else class="chapter-track">
      <template v-for="(ch, idx) in store.chapters" :key="ch.id">
        <div 
          class="chapter-premium-card" 
          :class="{ active: activeId === ch.id }"
          @click="selectChapter(ch.id)"
        >
          <div class="ch-number">CHAPTER 0{{ idx + 1 }}</div>
          <el-input 
            v-model="ch.title" 
            placeholder="章节标题..." 
            class="ch-name-input" 
            @click.stop 
          />
          <div class="ch-stats">
            <span><el-icon><CopyDocument /></el-icon> {{ ch.nodes.length }} 节点</span>
            <span v-if="ch.nodes.length > 0" class="ch-id-badge">#{{ ch.id }}</span>
          </div>
          
          <div class="card-actions">
            <el-button size="small" type="primary" :icon="Right" round @click.stop="selectChapter(ch.id)">编辑节点</el-button>
            <el-button size="small" link type="danger" :icon="Delete" @click.stop="confirmDelete(ch.id)" />
          </div>
        </div>
        <div v-if="idx < store.chapters.length - 1" class="flow-arrow">
          <el-icon><ArrowRightBold /></el-icon>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CopyDocument, Right, Delete, ArrowRightBold } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'

const store = useEditorStore()
const emit = defineEmits(['select-chapter'])
const activeId = ref(null)

function selectChapter(id) {
  activeId.value = id
  emit('select-chapter', id)
}

function confirmDelete(id) {
  ElMessageBox.confirm('确认删除此章节与其关联的所有剧情节点吗？此操作不可撤销。', '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    buttonSize: 'small'
  }).then(() => {
    store.deleteChapter(id)
    ElMessage.success('章节已删除')
  }).catch(() => {})
}
</script>

<style scoped>
.chapter-track {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: max-content;
}

.chapter-premium-card {
  width: 220px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.chapter-premium-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--accent);
  transform: translateY(-4px);
  box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.5);
}

.chapter-premium-card.active {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.1);
  box-shadow: 0 0 0 1px var(--accent);
}

.ch-number {
  font-size: 10px; font-weight: 800; color: var(--accent);
  letter-spacing: 1px; margin-bottom: 8px;
}

.ch-name-input :deep(.el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.ch-name-input :deep(.el-input__inner) {
  font-size: 16px !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
}

.ch-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 11px;
  color: var(--text-muted);
}

.card-actions {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  opacity: 0.4;
  transition: opacity 0.2s;
}
.chapter-premium-card:hover .card-actions { opacity: 1; }

.flow-arrow {
  color: var(--border);
  flex-shrink: 0;
  padding: 0 4px;
}

.empty-state-mini {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
  border: 1px dashed var(--border);
  border-radius: 12px;
  font-size: 14px;
}
</style>
