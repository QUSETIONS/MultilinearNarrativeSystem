<template>
  <el-card :body-style="{ padding: '0px' }" class="asset-card" shadow="hover">
    <div class="asset-preview" :style="previewStyle">
      <div class="status-overlay">
        <el-tag :type="statusType" size="small" effect="dark">
          {{ statusText }}
        </el-tag>
      </div>
      <div v-if="asset.task_id === 'PROCESSING'" class="processing-overlay">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <div class="log-stream">
          <p v-for="(log, i) in asset.logs" :key="i" class="log-line">{{ log }}</p>
        </div>
      </div>
      <div v-else-if="asset.status === 'MISSING'" class="missing-placeholder">
        <el-icon :size="40"><Picture /></el-icon>
        <span>AWAITING GENERATION</span>
      </div>
    </div>
    <div class="asset-info">
      <div class="asset-path text-truncate">
        <el-icon><Document /></el-icon>
        <span>{{ fileName }}</span>
      </div>
      <p class="asset-desc">{{ asset.description }}</p>
      
      <!-- Attention Mechanism: Focus Spotlight (Structured) -->
      <div v-if="asset.attention && typeof asset.attention === 'object' && Object.keys(asset.attention).length" class="attention-spotlight structured">
        <template v-for="(tokens, type) in asset.attention" :key="type">
          <el-tag 
            v-for="(token, index) in tokens" 
            :key="type + index" 
            size="small" 
            :class="['attention-tag', type]" 
            effect="dark"
          >
            {{ token }}
          </el-tag>
        </template>
      </div>

      <div v-else-if="asset.attention_flat && asset.attention_flat.length" class="attention-spotlight">
        <el-tag 
          v-for="(token, index) in asset.attention_flat" 
          :key="'flat' + index" 
          size="small" 
          class="attention-tag neutral"
          effect="plain"
        >
          <el-icon><View /></el-icon> {{ token }}
        </el-tag>
      </div>

      <div class="asset-actions">
        <el-button 
          v-if="asset.status === 'MISSING'" 
          type="primary" 
          size="small" 
          class="generate-btn"
          @click="emit('generate', asset)"
        >
          GENERATE NOW
        </el-button>
        <template v-else>
          <el-button type="info" size="small" plain class="preview-btn">
            PREVIEW
          </el-button>
          <el-button-group>
            <el-button size="small" type="success" plain @click="emit('feedback', {asset, status: 'LIKED'})" title="Chosen">👍</el-button>
            <el-button size="small" type="danger" plain @click="promptDislike" title="Rejected">👎</el-button>
          </el-button-group>
        </template>
        <el-button 
          v-if="asset.snapshots && asset.snapshots.length" 
          type="warning" 
          size="small" 
          plain 
          @click="emit('view-monitor', asset)"
        >
          MONITOR
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Picture, Document, Loading } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['generate', 'view-monitor', 'feedback'])

async function promptDislike() {
  try {
    const { value } = await ElMessageBox.prompt('请输入不满意的原因 (例如: 太暗、风格不对)', '提供反馈', {
      confirmButtonText: '提交反馈',
      cancelButtonText: '取消',
      inputErrorMessage: '原因不能为空',
      inputValidator: (val) => { return !!val }
    })
    emit('feedback', { asset: props.asset, status: 'DISLIKED', reason: value })
  } catch (e) {
    // cancelled
  }
}

const fileName = computed(() => {
  const parts = props.asset.path.split('/')
  return parts[parts.length - 1]
})

const statusText = computed(() => {
  if (props.asset.task_id === 'PROCESSING') return 'GENERATING'
  if (props.asset.task_id === 'COMPLETED') return 'JUST FINISHED'
  return props.asset.status === 'FOUND' ? 'NORMAL' : 'MISSING'
})

const statusType = computed(() => {
  if (props.asset.task_id === 'PROCESSING') return 'warning'
  return props.asset.status === 'FOUND' ? 'success' : 'danger'
})

const previewStyle = computed(() => {
  if (props.asset.status === 'FOUND') {
    return {
      background: 'linear-gradient(45deg, #2b2d42, #8d99ae)',
      opacity: 0.8
    }
  }
  return {
    background: '#1a1a1a',
    borderBottom: '1px solid #333'
  }
})
</script>

<style scoped>
.asset-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--bg);
  transition: transform 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.asset-card:hover {
  transform: translateY(-5px);
  border-color: var(--primary);
}

.asset-preview {
  height: 140px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
}

.missing-placeholder, .processing-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #444;
  font-size: 10px;
  letter-spacing: 1px;
}

.processing-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.9);
  color: #00ff00;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.log-stream {
  margin-top: 12px;
  font-family: 'Fira Code', monospace;
  font-size: 8px;
  width: 100%;
  text-align: left;
  opacity: 0.8;
}

.log-line {
  margin: 2px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-info {
  padding: 16px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.asset-path {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: var(--primary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.asset-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 36px;
}

.asset-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
}

.attention-spotlight {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.attention-tag {
  background: rgba(0, 255, 0, 0.05) !important;
  border-color: rgba(0, 255, 0, 0.2) !important;
  color: #00ff00 !important;
  font-size: 10px !important;
  font-family: 'Fira Code', monospace;
  padding: 0 6px;
}

.negative-tag {
  background: rgba(255, 0, 0, 0.05) !important;
  border-color: rgba(255, 0, 0, 0.2) !important;
  color: #ff4d4f !important;
  font-size: 10px !important;
  font-family: 'Fira Code', monospace;
  padding: 0 6px;
}

.generate-btn {
  width: 100%;
  background: linear-gradient(90deg, #409EFF, #3a8ee6);
  border: none;
}

.preview-btn {
  flex-grow: 1;
}
.attention-tag.global { background: #409eff !important; border-color: #409eff !important; }
.attention-tag.mood { background: #b37feb !important; border-color: #b37feb !important; }
.attention-tag.entity { background: #73d13d !important; border-color: #73d13d !important; }
.attention-tag.consistency { background: #ffa940 !important; border-color: #ffa940 !important; }
.attention-tag.neutral { background: #909399 !important; border-color: #909399 !important; }

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
