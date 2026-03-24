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
          <el-select v-model="selectedProvider" size="small" style="width: 140px; margin-right: 12px;">
            <el-option v-for="p in providers" :key="p" :label="p.toUpperCase()" :value="p" />
          </el-select>
          <el-switch v-model="useLLM" active-text="AI理解" inactive-text="规则" style="margin-right: 12px;" />
        </div>
        <el-button-group>
          <el-button type="warning" :icon="Document" @click="onExtractFromScript" :loading="extracting">从剧本提取素材</el-button>
          <el-button type="primary" :icon="Refresh" @click="onRefresh">刷新状态</el-button>
          <el-button type="success" :icon="MagicStick" @click="onGenerateAll" :disabled="stats.missing === 0 || generating">生成所有缺失项</el-button>
          <el-button :icon="List" @click="showTaskQueue = true">任务队列</el-button>
        </el-button-group>
      </div>
      <!-- Generation Progress Bar -->
      <transition name="fade">
        <div v-if="generating" class="generation-progress">
          <el-progress :percentage="genProgress" :format="genProgressFormat" :stroke-width="8" />
          <span class="gen-status">{{ genStatusText }}</span>
        </div>
      </transition>
    </div>

    <!-- Phase 24: Extraction Mode Badge -->
    <div v-if="extractionMode" class="extraction-mode-badge">
      <el-tag :type="extractionMode === 'llm' ? 'success' : 'info'" effect="dark" size="small">
        {{ extractionMode === 'llm' ? '🧠 DeepSeek AI 智能提取' : '📝 规则提取 (Regex)' }}
      </el-tag>
    </div>

    <!-- Phase 23: Asset Review List -->
    <AssetReviewList 
      v-if="showReviewList" 
      :candidates="reviewCandidates" 
      :stats="reviewStats"
      @confirm="onReviewConfirm"
    />

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
                                <AssetCard :asset="item" @generate="onGenerate" @generate-variants="onGenerateVariants" @view-monitor="onViewMonitor" @feedback="onFeedback" />
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
                                <AssetCard :asset="item" @generate="onGenerate" @generate-variants="onGenerateVariants" @view-monitor="onViewMonitor" @feedback="onFeedback" />
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

    <!-- Phase 28: Task Queue Drawer -->
    <TaskQueueDrawer v-model="showTaskQueue" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh, MagicStick, PictureFilled, UserFilled, Headset, Document, List } from '@element-plus/icons-vue'
import { API, API_BASE } from '../utils/api.config.js'
import { ElMessage } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'
import { apiService } from '../services/api'
import AssetCard from './AssetCard.vue'
import AssetReviewList from './AssetReviewList.vue'
import TaskQueueDrawer from './TaskQueueDrawer.vue'

const activeTab = ref('背景图')
const auditData = ref(null)
const selectedProvider = ref('siliconflow')
const providers = ref(['siliconflow', 'mock', 'coze'])
const editorStore = useEditorStore()
const extracting = ref(false)
const useLLM = ref(true)
const extractionMode = ref('')
const showTaskQueue = ref(false)
const showReviewList = ref(false)
const reviewCandidates = ref([])
const reviewStats = ref(null)
const generating = ref(false)
const genProgress = ref(0)
const genStatusText = ref('')
const genProgressFormat = (pct) => pct === 100 ? '完成!' : `${pct}%`
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
const ws = ref(null)
const monitorVisible = ref(false)
const monitoringAsset = ref(null)

const bannerStyle = {
  background: 'linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/asset_workstation_hero.png")',
  backgroundSize: 'cover',
  backgroundPosition: 'center'
}

onMounted(async () => {
  await onRefresh()
  connectWebSocket()
})

function connectWebSocket() {
  if (ws.value) return
  
  ws.value = new WebSocket(API.WEBSOCKET)
  
  ws.value.onopen = () => {
    console.log('[WS] Connected to live updates')
  }
  
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (!auditData.value || !auditData.value.details) return
      
      const asset = auditData.value.details.find(a => a.path === data.path)
      if (!asset) return
      
      if (data.event === 'log_update') {
        if (!asset.logs) asset.logs = []
        asset.logs.push(data.log)
        if (asset.logs.length > 5) asset.logs.shift()
      } else if (data.event === 'status_update') {
        asset.task_status = data.status
        if (data.prompt) asset.last_prompt = data.prompt
        if (data.status === 'COMPLETED') {
          asset.status = 'FOUND'
          auditData.value.summary.found++
          auditData.value.summary.missing--
        }
      }
    } catch (e) {
      console.error('[WS] Error parsing message', e)
    }
  }
  
  ws.value.onclose = () => {
    console.log('[WS] Disconnected. Reconnecting in 3s...')
    ws.value = null
    setTimeout(connectWebSocket, 3000)
  }
}

onUnmounted(() => {
  if (ws.value) {
    ws.value.onclose = null // Prevent auto-reconnect
    ws.value.close()
  }
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
    const data = await apiService.getStatus()
    auditData.value = data
    if (data.providers) providers.value = data.providers
  } catch (err) {
    console.error('Service Offline:', err)
  }
}

// Phase 23: 从剧本提取素材
async function onExtractFromScript() {
  extracting.value = true
  try {
    // 从 editorStore 获取章节和角色数据
    const chapters = editorStore.chapters || []
    const characters = editorStore.assets?.characters || []
    
    if (chapters.length === 0) {
      ElMessage.warning('请先导入剧本 JSON 文件')
      extracting.value = false
      return
    }
    
    const data = await apiService.extractFromScript({ chapters, characters, use_llm: useLLM.value })
    
    reviewCandidates.value = data.candidates || []
    reviewStats.value = data.stats || null
    extractionMode.value = data.extraction_mode || 'regex'
    showReviewList.value = true
    
    ElMessage.success(data.message || '提取完成')
  } catch (err) {
    ElMessage.error('无法连接后端服务: ' + err.message)
  } finally {
    extracting.value = false
  }
}

// Phase 23: 用户审阅后确认注册
async function onReviewConfirm(selected) {
  // 转换为 outline 格式发送给 /assets/register
  const lines = []
  const byType = {}
  for (const item of selected) {
    if (!byType[item.type]) byType[item.type] = []
    byType[item.type].push(item)
  }
  
  // 构建文本 outline
  for (const [type, items] of Object.entries(byType)) {
    const category = type === '人物立绘' ? '角色' : type === '背景图' ? '场景' : 'BGM'
    const entries = items.map(i => i.description ? `${i.name}（${i.description}）` : i.name)
    lines.push(`${category}：${entries.join('、')}`)
  }
  
  try {
    const data = await apiService.registerAssets(lines.join('\n'))
    ElMessage.success(data.message || '注册成功')
    showReviewList.value = false
    await onRefresh()
  } catch (err) {
    ElMessage.error('注册失败: ' + err.message)
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
    await apiService.generateAsset({
      asset_path: asset.path,
      description: asset.description,
      asset_type: asset.type,
      provider: selectedProvider.value,
      entropy: asset.entropy,
      seed: asset.seed !== undefined ? asset.seed : -1, // Pass seed
      negative_prompt: asset.negative_prompt || "", // Pass negative_prompt
      relationships: {
        speaker: asset.speaker,
        listener: asset.listener,
        graph: {}
      },
      refinement_passes: asset.refinement_passes
    })
    ElMessage.success(`任务已加入队列 (Override): ${asset.path}`)
    editDialogVisible.value = false
    onRefresh()
  } catch (err) {
    ElMessage.error('无法触发生成任务')
  }
}

async function onGenerateVariants(asset) {
  try {
    const data = await apiService.generateVariants({
      asset_path: asset.path,
      description: asset.description || '',
      asset_type: asset.type || 'auto',
      provider: selectedProvider.value,
      count: 3,
      seed: asset.seed !== undefined ? asset.seed : -1, // Pass seed
      negative_prompt: asset.negative_prompt || "" // Pass negative_prompt
    })
    ElMessage.success(data.message || '变体生成已启动')
    showTaskQueue.value = true  // Auto-open task queue to see progress
  } catch {
    ElMessage.error('变体生成请求失败')
  }
}

async function onGenerateAll() {
  const missing = auditData.value.details.filter(d => d.status === 'MISSING')
  if (missing.length === 0) return
  
  generating.value = true
  genProgress.value = 0
  genStatusText.value = `准备生成 ${missing.length} 个资产...`
  
  for (let i = 0; i < missing.length; i++) {
    const asset = missing[i]
    genStatusText.value = `正在生成 (${i + 1}/${missing.length}): ${asset.path.split('/').pop()}`
    genProgress.value = Math.round(((i) / missing.length) * 100)
    
    try {
      await apiService.generateAsset({
        asset_path: asset.path,
        description: asset.description,
        asset_type: asset.type,
        provider: selectedProvider.value,
        seed: asset.seed !== undefined ? asset.seed : -1, // Pass seed
        negative_prompt: asset.negative_prompt || "" // Pass negative_prompt
      })
    } catch (err) {
      console.error(`Failed to generate ${asset.path}:`, err)
    }
  }
  
  genProgress.value = 100
  genStatusText.value = `全部完成! 共生成 ${missing.length} 个资产`
  ElMessage.success(`批量生成完成: ${missing.length} 个资产`)
  
  // Auto-hide progress bar after 3s
  setTimeout(() => { generating.value = false }, 3000)
  await onRefresh()
}

function onViewMonitor(asset) {
  monitoringAsset.value = asset
  monitorVisible.value = true
}

async function onFeedback(data) {
  const { asset, status, reason } = data
  try {
    await apiService.submitFeedback({
      asset_path: asset.path,
      status: status,
      reason: reason || null,
      prompt: asset.last_prompt || asset.description,
      context: {
        type: asset.type,
        description: asset.description
      }
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
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  margin-top: -30px;
}

.banner-actions > div:first-child {
  display: flex;
  align-items: center;
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

.generation-progress {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.generation-progress .el-progress {
  flex: 1;
}

.gen-status {
  font-size: 12px;
  color: #67c23a;
  white-space: nowrap;
  min-width: 120px;
  text-align: right;
}

.extraction-mode-badge {
  padding: 4px 40px 8px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
