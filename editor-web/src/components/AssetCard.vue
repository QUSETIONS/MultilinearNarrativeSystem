<template>
  <el-card :body-style="{ padding: '0px' }" class="asset-card" shadow="hover">
    <div class="asset-preview" :style="previewStyle">
      <!-- Real Image Preview (Phase 25) -->
      <img 
        v-if="asset.status === 'FOUND' && isImageAsset" 
        :src="imageUrl" 
        class="preview-image"
        @error="imgError = true"
        loading="lazy"
      />
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
        <span>等待生成</span>
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
          <el-icon style="margin-right:4px"><MagicStick /></el-icon> 立即生成
        </el-button>
        <el-button 
          v-if="asset.status === 'MISSING'" 
          type="warning" 
          size="small" 
          plain
          @click="emit('generate-variants', asset)"
        >
          🎨 生成3变体
        </el-button>
        <template v-else>
          <el-button type="info" size="small" plain class="preview-btn" @click="onFullPreview">
            <el-icon style="margin-right:4px"><ZoomIn /></el-icon> 预览
          </el-button>
          <el-button-group>
            <el-button size="small" type="success" plain @click="emit('feedback', {asset, status: 'LIKED'})" title="采用">👍</el-button>
            <el-button size="small" type="danger" plain @click="promptDislike" title="拒绝">👎</el-button>
          </el-button-group>
        </template>
        <el-button 
          v-if="asset.snapshots && asset.snapshots.length" 
          type="warning" 
          size="small" 
          plain 
          @click="emit('view-monitor', asset)"
        >
          监控
        </el-button>
      </div>
    </div>

    <!-- Full Preview Dialog -->
    <el-dialog v-model="previewDialogVisible" :title="fileName" width="680px" custom-class="dark-dialog" append-to-body>
      <div class="full-preview-container">
        <img v-if="imageUrl && !imgError" :src="imageUrl" class="full-preview-img" />
        <div v-else class="no-preview">暂无预览</div>
      </div>
      <div class="preview-meta">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="路径">{{ asset.path }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ asset.description }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Picture, Document, Loading, MagicStick, ZoomIn } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { API_BASE } from '../utils/api.config.js'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['generate', 'view-monitor', 'feedback'])
const imgError = ref(false)
const previewDialogVisible = ref(false)

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

function onFullPreview() {
  previewDialogVisible.value = true
}

const fileName = computed(() => {
  const parts = props.asset.path.split('/')
  return parts[parts.length - 1]
})

const isImageAsset = computed(() => {
  const p = props.asset.path.toLowerCase()
  return p.endsWith('.png') || p.endsWith('.jpg') || p.endsWith('.jpeg') || p.endsWith('.webp')
})

const imageUrl = computed(() => {
  if (!isImageAsset.value || imgError.value) return ''
  // Serve from backend static files or local path
  return `${API_BASE}/static/${props.asset.path}`
})

const statusText = computed(() => {
  if (props.asset.task_id === 'PROCESSING') return '生成中...'
  if (props.asset.task_id === 'COMPLETED') return '刚完成'
  return props.asset.status === 'FOUND' ? '已就绪' : '待生成'
})

const statusType = computed(() => {
  if (props.asset.task_id === 'PROCESSING') return 'warning'
  return props.asset.status === 'FOUND' ? 'success' : 'danger'
})

const previewStyle = computed(() => {
  if (props.asset.status === 'FOUND' && isImageAsset.value && !imgError.value) {
    return { background: '#0a0a0a' }
  }
  if (props.asset.status === 'FOUND') {
    return {
      background: 'linear-gradient(135deg, #1a1a3e, #2d2d5e)',
      opacity: 0.9
    }
  }
  return {
    background: 'linear-gradient(135deg, #0f0f0f, #1a1a1a)',
    borderBottom: '1px solid rgba(255,255,255,0.06)'
  }
})
</script>

<style scoped>
.asset-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--bg-card);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.asset-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: 0 12px 24px rgba(99, 102, 241, 0.15);
}

.asset-preview {
  height: 180px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.asset-card:hover .preview-image {
  transform: scale(1.05);
}

.status-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 3;
}

.missing-placeholder, .processing-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #555;
  font-size: 11px;
  letter-spacing: 1px;
}

.processing-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.92);
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
  padding: 14px 16px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.asset-path {
  font-family: 'Fira Code', monospace;
  font-size: 11px;
  color: var(--accent);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0.8;
}

.asset-desc {
  font-size: 13px;
  color: var(--text-secondary, #9ca3af);
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.asset-actions {
  margin-top: auto;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.attention-spotlight {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.attention-tag {
  background: rgba(0, 255, 0, 0.05) !important;
  border-color: rgba(0, 255, 0, 0.2) !important;
  color: #00ff00 !important;
  font-size: 10px !important;
  font-family: 'Fira Code', monospace;
  padding: 0 6px;
}

.generate-btn {
  width: 100%;
  background: var(--accent-gradient, linear-gradient(135deg, #6366f1, #a855f7)) !important;
  border: none !important;
  font-weight: 600;
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

/* Full Preview Dialog */
.full-preview-container {
  display: flex;
  justify-content: center;
  background: #0a0a0a;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.full-preview-img {
  max-width: 100%;
  max-height: 480px;
  object-fit: contain;
}

.no-preview {
  padding: 60px;
  color: #555;
  font-size: 14px;
}

.preview-meta {
  margin-top: 8px;
}
</style>
