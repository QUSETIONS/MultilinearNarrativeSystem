<template>
  <div class="asset-workstation">
    <!-- Premium Dashboard Header -->
    <div class="dashboard-banner" :style="bannerStyle">
      <div class="banner-content">
        <div class="title-area">
          <h1 class="glitch-text">资产生产指挥中心</h1>
          <p class="subtitle">AI 驱动的生产管线 v1.0</p>
        </div>
        <div class="dashboard-stats">
          <div class="stat-item">
            <span class="stat-label">完成度</span>
            <div class="progress-container">
              <el-progress 
                type="circle" 
                :percentage="completionRate" 
                :stroke-width="12" 
                :width="80"
                color="#409eff"
              />
            </div>
          </div>
          <div class="stat-info">
            <div class="info-row">
              <span class="label">资产总计</span>
              <span class="value">{{ stats.total_defined }}</span>
            </div>
            <div class="info-row">
              <span class="label">已上线</span>
              <span class="value green">{{ stats.found }}</span>
            </div>
            <div class="info-row">
              <span class="label">缺失</span>
              <span class="value red">{{ stats.missing }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="banner-actions">
        <div class="model-select-wrapper">
          <span class="label">基座模型:</span>
          <el-select v-model="selectedProvider" size="small" style="width: 120px; margin-right: 12px;">
            <el-option v-for="p in providers" :key="p" :label="p.toUpperCase()" :value="p" />
          </el-select>
        </div>
        <el-button-group>
          <el-button type="primary" :icon="Refresh" @click="onRefresh">刷新状态</el-button>
          <el-button type="success" :icon="MagicStick" @click="onGenerateAll" :disabled="stats.missing === 0">生成所有缺失项</el-button>
        </el-button-group>
      </div>
    </div>

    <!-- Main Workspace -->
    <div class="workspace-tabs">
      <el-tabs v-model="activeTab">
        <el-tab-pane name="背景图">
          <template #label>
            <span class="tab-label"><el-icon><PictureFilled /></el-icon> 场景背景</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('背景图')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" @view-monitor="onViewMonitor" @feedback="onFeedback" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane name="人物立绘">
          <template #label>
            <span class="tab-label"><el-icon><UserFilled /></el-icon> 人物立绘</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('人物立绘')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" @view-monitor="onViewMonitor" @feedback="onFeedback" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane name="bgm">
          <template #label>
            <span class="tab-label"><el-icon><Headset /></el-icon> 音频轨道</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('bgm')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" @view-monitor="onViewMonitor" @feedback="onFeedback" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- AISettings Dialog -->
    <el-dialog v-model="editDialogVisible" title="生产提示词精修 (Override)" width="600px" custom-class="dark-dialog">
      <el-form label-position="top">
        <el-form-item label="目标资产路径">
          <el-input v-model="editingAsset.path" disabled />
        </el-form-item>
        <el-form-item label="创意提示词 (基础描述)">
          <el-input v-model="editingAsset.description" type="textarea" :rows="4" placeholder="描述视觉或音频特征..." />
        </el-form-item>
        <el-form-item label="叙事熵 (创意自由度)">
          <el-slider v-model="editingAsset.entropy" :min="0" :max="1" :step="0.1" show-input />
          <div class="slider-hint">低: 严格遵循剧本 | 高: 允许 AI 自由装饰</div>
        </el-form-item>
        
        <el-divider content-position="left">高级叙事逻辑</el-divider>
        
        <el-form-item label="社交关系上下文 (人物张力)">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-input v-model="editingAsset.speaker" placeholder="发言者 (如: 波洛)" size="small" />
            </el-col>
            <el-col :span="12">
              <el-input v-model="editingAsset.listener" placeholder="倾听者 (如: 布克)" size="small" />
            </el-col>
          </el-row>
          <div class="slider-hint">定义影响生成语气和氛围的'社交权重'。</div>
        </el-form-item>

        <el-form-item label="递归细化 (多轮 AI 评议打磨)">
          <el-radio-group v-model="editingAsset.refinement_passes" size="small">
            <el-radio-button :label="1">关闭</el-radio-button>
            <el-radio-button :label="2">快速 (2轮)</el-radio-button>
            <el-radio-button :label="3">深度 (3轮)</el-radio-button>
          </el-radio-group>
          <div class="slider-hint">通过连续的 AI 自省评议来提升最终产物质量。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmGenerate">开始生产任务 (Override)</el-button>
      </template>
    </el-dialog>

    <!-- Generation Monitor Drawer -->
    <el-drawer v-model="monitorVisible" title="叙事生产监控 (Observability)" size="450px" custom-class="dark-drawer">
      <div v-if="monitoringAsset" class="monitor-content">
        <el-divider content-position="left">关注点细分 (Attention Breakdown)</el-divider>
        <div class="attention-details">
          <div v-for="(tokens, type) in monitoringAsset.attention" :key="type" class="attention-row">
            <span class="type-header">{{ type.toUpperCase() }}</span>
            <div class="token-list">
              <el-tag v-for="token in tokens" :key="token" size="small" :class="type" effect="dark">{{ token }}</el-tag>
            </div>
          </div>
        </div>

        <el-divider content-position="left">递归打磨轨迹 (Recursive Timeline)</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="snap in monitoringAsset.snapshots"
            :key="snap.pass"
            :timestamp="'Pass ' + snap.pass"
            :type="snap.pass === 0 ? 'info' : 'success'"
          >
            <h4 class="critique-title">{{ snap.critique }}</h4>
            <div class="snapshot-prompt">{{ snap.prompt }}</div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh, MagicStick, PictureFilled, UserFilled, Headset } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AssetCard from './AssetCard.vue'

const activeTab = ref('背景图')
const auditData = ref(null)
const selectedProvider = ref('mock')
const providers = ref(['mock', 'coze'])
const editDialogVisible = ref(false)
const editingAsset = ref({ 
  path: '', 
  description: '', 
  type: '', 
  entropy: 0.5,
  speaker: 'Poirot',
  listener: 'Narrator',
  refinement_passes: 1
})
const pollTimer = ref(null)
const monitorVisible = ref(false)
const monitoringAsset = ref(null)

const bannerStyle = {
  background: 'linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/asset_workstation_hero.png")',
  backgroundSize: 'cover',
  backgroundPosition: 'center'
}

onMounted(async () => {
  await onRefresh()
  // Start polling
  pollTimer.value = setInterval(onRefresh, 3000)
})

onUnmounted(() => {
  if (pollTimer.value) clearInterval(pollTimer.value)
})

const stats = computed(() => {
  if (auditData.value) return auditData.value.summary
  return { total_defined: 0, found: 0, missing: 0 }
})

const completionRate = computed(() => {
  if (!stats.value.total_defined) return 0
  return Math.round((stats.value.found / stats.value.total_defined) * 100)
})

async function onRefresh() {
  try {
    const res = await fetch('http://localhost:8088/status')
    const data = await res.json()
    auditData.value = data
    if (data.providers) providers.value = data.providers
  } catch (err) {
    console.error('Service Offline:', err)
  }
}

function getAssetsByType(type) {
  if (!auditData.value) return []
  return auditData.value.details.filter(d => d.type === type)
}

function onGenerate(asset) {
  editingAsset.value = { 
    ...asset, 
    entropy: asset.entropy || 0.5,
    speaker: asset.speaker || 'Poirot',
    listener: asset.listener || 'Narrator',
    refinement_passes: asset.refinement_passes || 1
  }
  editDialogVisible.value = true
}

async function confirmGenerate() {
  const asset = editingAsset.value
  try {
    await fetch('http://localhost:8088/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset_path: asset.path,
        description: asset.description,
        asset_type: asset.type,
        provider: selectedProvider.value,
        entropy: asset.entropy,
        relationships: {
          speaker: asset.speaker,
          listener: asset.listener,
          graph: {} // In a real app, this would come from a global state
        },
        refinement_passes: asset.refinement_passes
      })
    })
    ElMessage.success(`任务已加入队列 (Override): ${asset.path}`)
    editDialogVisible.value = false
    onRefresh()
  } catch (err) {
    ElMessage.error('无法触发生成任务')
  }
}

async function onGenerateAll() {
  const missing = auditData.value.details.filter(d => d.status === 'MISSING')
  ElMessage.info(`正在开始批量生成 ${missing.length} 个资产...`)
  for (const asset of missing) {
    // For batch, we use the default descriptions
    await fetch('http://localhost:8088/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset_path: asset.path,
        description: asset.description,
        asset_type: asset.type,
        provider: selectedProvider.value
      })
    })
  }
}

function onViewMonitor(asset) {
  monitoringAsset.value = asset
  monitorVisible.value = true
}

async function onFeedback(data) {
  const { asset, status, reason } = data
  try {
    await fetch('http://localhost:8088/narrative/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset_path: asset.path,
        status: status,
        reason: reason || null,
        prompt: asset.last_prompt || asset.description,
        context: {
          type: asset.type,
          description: asset.description
        }
      })
    })
    ElMessage.success(status === 'LIKED' ? '已记录好评' : '反馈已提交，将优化下次生成')
    
    if (status === 'DISLIKED') {
      onGenerate(asset)
    }
  } catch (err) {
    ElMessage.error('无法提交反馈')
  }
}
</script>

<style scoped>
.asset-workstation {
  height: calc(100vh - 80px);
  overflow-y: auto;
  background: #0a0a0c;
  color: #fff;
  padding: 0;
}

.dashboard-banner {
  padding: 60px 40px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid #333;
}

.glitch-text {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 4px;
  margin: 0;
  background: linear-gradient(90deg, #fff, #409eff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #888;
  letter-spacing: 2px;
  font-size: 12px;
  margin-top: 8px;
}

.dashboard-stats {
  display: flex;
  gap: 40px;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 20px 40px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 150px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  letter-spacing: 1px;
}

.info-row .label { color: #666; }
.info-row .value { font-weight: 600; }
.info-row .green { color: #67C23A; }
.info-row .red { color: #F56C6C; }

.banner-actions {
  padding: 0 40px 20px;
  display: flex;
  justify-content: flex-end;
  margin-top: -30px;
}

.workspace-tabs {
  padding: 20px 40px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  letter-spacing: 1px;
}

.slider-hint {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.asset-grid {
  padding: 20px 0;
}

:deep(.el-tabs__item) {
  color: #666;
  font-weight: 400;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background-color: #409eff;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: #222;
}

.attention-row {
  margin-bottom: 16px;
}
.type-header {
  font-size: 10px;
  color: #888;
  display: block;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.token-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.critique-title {
  font-size: 14px;
  color: var(--primary);
  margin-bottom: 8px;
}
.snapshot-prompt {
  font-size: 12px;
  color: #aaa;
  background: rgba(0,0,0,0.3);
  padding: 8px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  line-height: 1.5;
}
</style>
