<template>
  <el-drawer 
    v-model="visible" 
    title="生成任务队列" 
    direction="rtl" 
    size="420px"
    :destroy-on-close="false"
    class="task-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <h3>📦 生成任务队列</h3>
        <div class="header-stats">
          <el-tag size="small" type="info">{{ tasks.length }} 任务</el-tag>
          <el-button size="small" :icon="Refresh" circle @click="fetchTasks" :loading="loading" />
        </div>
      </div>
    </template>

    <div class="task-list" v-loading="loading">
      <div v-if="tasks.length === 0" class="empty-queue">
        <el-icon :size="48" style="color: #555;"><Box /></el-icon>
        <p>暂无生成任务</p>
        <p class="hint">在素材工作站中点击"生成"来添加任务</p>
      </div>

      <div 
        v-for="task in tasks" 
        :key="task.path" 
        class="task-item"
        :class="statusClass(task.status)"
      >
        <div class="task-header">
          <div class="task-status-badge" :class="statusClass(task.status)">
            <span class="status-dot"></span>
            {{ statusLabel(task.status) }}
          </div>
          <el-tag size="small" effect="plain" style="font-size: 10px;">{{ task.provider }}</el-tag>
        </div>

        <div class="task-path">{{ task.path.split('/').pop() }}</div>
        <div class="task-path-full"><code>{{ task.path }}</code></div>

        <!-- Prompt preview -->
        <div v-if="task.prompt" class="task-prompt">
          {{ task.prompt.substring(0, 80) }}{{ task.prompt.length > 80 ? '...' : '' }}
        </div>

        <!-- Latest logs -->
        <div v-if="task.logs.length > 0" class="task-logs">
          <div v-for="(log, i) in task.logs" :key="i" class="log-line">
            <el-icon style="color: #666;"><InfoFilled /></el-icon>
            {{ log }}
          </div>
        </div>

        <!-- Actions -->
        <div class="task-actions" v-if="task.status === 'FAILED'">
          <el-button size="small" type="warning" @click="retryTask(task)">
            <el-icon><RefreshRight /></el-icon> 重试
          </el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Refresh, Box, InfoFilled, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { API_BASE, API } from '../utils/api.config.js'
import { apiService } from '../services/api'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const tasks = ref([])
const loading = ref(false)

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v) fetchTasks()
})

watch(visible, (v) => emit('update:modelValue', v))

async function fetchTasks() {
  loading.value = true
  try {
    const data = await apiService.getTasks()
    tasks.value = data.tasks || []
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

function statusClass(status) {
  return {
    'status-processing': status === 'PROCESSING' || status === 'IN_PROGRESS',
    'status-completed': status === 'COMPLETED',
    'status-failed': status === 'FAILED',
    'status-queued': status === 'QUEUED'
  }
}

function statusLabel(status) {
  const labels = {
    'PROCESSING': '生成中',
    'IN_PROGRESS': '生成中',
    'COMPLETED': '已完成',
    'FAILED': '失败',
    'QUEUED': '排队中'
  }
  return labels[status] || status
}

async function retryTask(task) {
  try {
    await apiService.generateAsset({
      asset_path: task.path,
      description: task.prompt || '',
      asset_type: 'auto',
      provider: task.provider
    })
    ElMessage.success(`已重新加入队列: ${task.path.split('/').pop()}`)
    setTimeout(fetchTasks, 1000)
  } catch {
    ElMessage.error('重试失败')
  }
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.empty-queue {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

.empty-queue p {
  margin: 8px 0 0;
  font-size: 14px;
}

.empty-queue .hint {
  font-size: 12px;
  color: #555;
}

.task-item {
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.2s;
}

.task-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.task-item.status-processing {
  border-left: 3px solid #3b82f6;
}

.task-item.status-completed {
  border-left: 3px solid #10b981;
}

.task-item.status-failed {
  border-left: 3px solid #ef4444;
}

.task-item.status-queued {
  border-left: 3px solid #6b7280;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-processing .status-dot {
  background: #3b82f6;
  animation: pulse 1.5s infinite;
}

.status-completed .status-dot { background: #10b981; }
.status-failed .status-dot { background: #ef4444; }
.status-queued .status-dot { background: #6b7280; }

.task-path {
  font-weight: 600;
  font-size: 14px;
  color: #e0e0e0;
}

.task-path-full {
  margin-top: 2px;
}

.task-path-full code {
  font-size: 10px;
  color: #666;
}

.task-prompt {
  margin-top: 8px;
  font-size: 11px;
  color: #888;
  line-height: 1.4;
  font-style: italic;
}

.task-logs {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-line {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 10px;
  color: #777;
  line-height: 1.3;
}

.task-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
