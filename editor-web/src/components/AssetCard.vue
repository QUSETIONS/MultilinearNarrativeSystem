<template>
  <el-card :body-style="{ padding: '0px' }" class="asset-card" shadow="hover">
    <div class="asset-preview" :style="previewStyle">
      <div class="status-overlay">
        <el-tag :type="asset.status === 'FOUND' ? 'success' : 'danger'" size="small" effect="dark">
          {{ asset.status === 'FOUND' ? 'NORMAL' : 'MISSING' }}
        </el-tag>
      </div>
      <div v-if="asset.status === 'MISSING'" class="missing-placeholder">
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
      <div class="asset-actions">
        <el-button 
          v-if="asset.status === 'MISSING'" 
          type="primary" 
          size="small" 
          class="generate-btn"
          @click="$emit('generate', asset)"
        >
          GENERATE NOW
        </el-button>
        <el-button v-else type="info" size="small" plain class="preview-btn">
          PREVIEW
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Picture, Document } from '@element-plus/icons-vue'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  }
})

defineEmits(['generate'])

const fileName = computed(() => {
  const parts = props.asset.path.split('/')
  return parts[parts.length - 1]
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

.missing-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #444;
  font-size: 10px;
  letter-spacing: 1px;
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

.generate-btn {
  width: 100%;
  background: linear-gradient(90deg, #409EFF, #3a8ee6);
  border: none;
}

.preview-btn {
  width: 100%;
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
