<template>
  <div class="review-list-container">
    <!-- Header -->
    <div class="review-header">
      <div class="header-left">
        <h2 class="review-title">
          <el-icon><List /></el-icon>
          素材审阅清单
        </h2>
        <el-tag :type="selectedCount === candidates.length ? 'success' : 'warning'" effect="dark" size="small">
          {{ selectedCount }} / {{ candidates.length }} 已勾选
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="toggleAll(true)">全选</el-button>
        <el-button size="small" @click="toggleAll(false)">全不选</el-button>
        <el-button size="small" @click="toggleByType('人物立绘')">
          <el-icon><UserFilled /></el-icon> 选角色
        </el-button>
        <el-button size="small" @click="toggleByType('背景图')">
          <el-icon><PictureFilled /></el-icon> 选场景
        </el-button>
        <el-button type="primary" size="small" :icon="Check" :disabled="selectedCount === 0" @click="onConfirm">
          确认并注册 ({{ selectedCount }})
        </el-button>
      </div>
    </div>

    <!-- Stats Banner -->
    <div class="stats-bar" v-if="stats">
      <div class="stat-chip"><el-icon><UserFilled /></el-icon> 角色 {{ stats.characters }}</div>
      <div class="stat-chip"><el-icon><PictureFilled /></el-icon> 场景 {{ stats.backgrounds }}</div>
      <div class="stat-chip"><el-icon><Headset /></el-icon> BGM {{ stats.bgm }}</div>
    </div>

    <!-- Grouped Candidate List -->
    <template v-for="(group, groupType) in groupedCandidates" :key="groupType">
      <div class="group-header" v-if="group.length > 0">
        <el-icon v-if="groupType === '人物立绘'"><UserFilled /></el-icon>
        <el-icon v-else-if="groupType === '背景图'"><PictureFilled /></el-icon>
        <el-icon v-else><Headset /></el-icon>
        <span>{{ groupType }}</span>
        <el-tag size="small" effect="plain">{{ group.length }}</el-tag>
      </div>
      <div class="candidate-list">
        <div 
          v-for="(item, idx) in group" 
          :key="idx" 
          class="candidate-row"
          :class="{ 'is-selected': item.selected, 'type-portrait': item.type === '人物立绘', 'type-bg': item.type === '背景图', 'type-bgm': item.type === 'BGM' }"
        >
          <el-checkbox v-model="item.selected" class="candidate-check" />
          
          <div class="candidate-type">
            <el-icon v-if="item.type === '人物立绘'"><UserFilled /></el-icon>
            <el-icon v-else-if="item.type === '背景图'"><PictureFilled /></el-icon>
            <el-icon v-else><Headset /></el-icon>
          </div>

          <div class="candidate-info">
            <div class="candidate-name">{{ item.name }}</div>
            <div class="desc-row">
              <el-input 
                v-model="item.description" 
                size="small" 
                class="candidate-desc-input"
                placeholder="编辑素材描述..."
              />
              <el-tooltip content="用 AI 润色描述（DeepSeek）" placement="top">
                <el-button 
                  size="small" 
                  :icon="MagicStick" 
                  circle 
                  :loading="item._polishing"
                  @click="polishDesc(item)"
                  class="polish-btn"
                />
              </el-tooltip>
            </div>
          </div>
          
          <div class="candidate-path">
            <code>{{ item.path }}</code>
          </div>
        </div>
      </div>
    </template>

    <!-- Empty State -->
    <div v-if="candidates.length === 0" class="empty-state">
      <el-icon :size="48" style="color: #555;"><Warning /></el-icon>
      <p>暂无候选素材。请先导入剧本或点击"从剧本提取"。</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check, List, UserFilled, PictureFilled, Headset, Warning, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { API_BASE } from '../utils/api.config.js'

const props = defineProps({
  candidates: { type: Array, default: () => [] },
  stats: { type: Object, default: null }
})

const emit = defineEmits(['confirm'])

const selectedCount = computed(() => {
  return props.candidates.filter(c => c.selected).length
})

const groupedCandidates = computed(() => {
  const groups = { '人物立绘': [], '背景图': [], 'BGM': [] }
  for (const c of props.candidates) {
    const key = c.type || 'BGM'
    if (!groups[key]) groups[key] = []
    groups[key].push(c)
  }
  return groups
})

function toggleAll(val) {
  props.candidates.forEach(c => { c.selected = val })
}

function toggleByType(type) {
  props.candidates.forEach(c => {
    if (c.type === type) c.selected = true
  })
}

async function polishDesc(item) {
  if (!item.description || item.description.trim().length < 2) {
    ElMessage.warning('描述太短，无法润色')
    return
  }
  
  item._polishing = true
  try {
    // Call a lightweight LLM endpoint to enhance the description
    const res = await fetch(`${API_BASE}/enhance-desc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset_type: item.type,
        description: item.description
      })
    })
    const data = await res.json()
    if (data.enhanced) {
      item.description = data.enhanced
      ElMessage.success('描述已 AI 润色')
    }
  } catch {
    ElMessage.info('AI 润色服务暂不可用，请手动修改')
  } finally {
    item._polishing = false
  }
}

function onConfirm() {
  const selected = props.candidates.filter(c => c.selected)
  emit('confirm', selected)
}
</script>

<style scoped>
.review-list-container {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 24px;
  margin: 20px 0;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.review-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e0e0e0;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 12px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

/* Group Headers */
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 8px;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 360px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.candidate-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.2s ease;
}

.candidate-row:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
}

.candidate-row.is-selected {
  border-left: 3px solid #409eff;
}

.candidate-row.type-portrait.is-selected { border-left-color: #e6a23c; }
.candidate-row.type-bg.is-selected { border-left-color: #67c23a; }
.candidate-row.type-bgm.is-selected { border-left-color: #909399; }

.candidate-type {
  font-size: 18px;
  color: #666;
  width: 32px;
  text-align: center;
  flex-shrink: 0;
}

.candidate-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.candidate-name {
  font-weight: 600;
  font-size: 14px;
  color: #ddd;
}

.desc-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.polish-btn {
  flex-shrink: 0;
  border-color: rgba(168, 85, 247, 0.3) !important;
  color: #a855f7 !important;
}

.polish-btn:hover {
  background: rgba(168, 85, 247, 0.15) !important;
}

.candidate-desc-input :deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

.candidate-desc-input :deep(.el-input__inner) {
  color: #aaa;
  font-size: 12px;
}

.candidate-path {
  flex-shrink: 0;
}

.candidate-path code {
  font-size: 10px;
  color: #555;
  letter-spacing: 0.5px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #555;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
