<template>
  <div class="asset-workstation">
    <!-- Premium Dashboard Header -->
    <div class="dashboard-banner" :style="bannerStyle">
      <div class="banner-content">
        <div class="title-area">
          <h1 class="glitch-text">ASSET COMMAND CENTER</h1>
          <p class="subtitle">AI-Driven Production Pipeline v1.0</p>
        </div>
        <div class="dashboard-stats">
          <div class="stat-item">
            <span class="stat-label">COMPLETION</span>
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
              <span class="label">TOTAL ASSETS</span>
              <span class="value">{{ stats.total_defined }}</span>
            </div>
            <div class="info-row">
              <span class="label">LIVE ON DISK</span>
              <span class="value green">{{ stats.found }}</span>
            </div>
            <div class="info-row">
              <span class="label">MISSING</span>
              <span class="value red">{{ stats.missing }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="banner-actions">
        <el-button-group>
          <el-button type="primary" :icon="Refresh" @click="onRefresh">REFRESH AUDIT</el-button>
          <el-button type="success" :icon="MagicStick" @click="onGenerateAll" :disabled="stats.missing === 0">GENERATE ALL</el-button>
        </el-button-group>
      </div>
    </div>

    <!-- Main Workspace -->
    <div class="workspace-tabs">
      <el-tabs v-model="activeTab">
        <el-tab-pane name="背景图">
          <template #label>
            <span class="tab-label"><el-icon><PictureFilled /></el-icon> BACKGROUNDS</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('背景图')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane name="人物立绘">
          <template #label>
            <span class="tab-label"><el-icon><UserFilled /></el-icon> PORTRAITS</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('人物立绘')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane name="bgm">
          <template #label>
            <span class="tab-label"><el-icon><Headset /></el-icon> AUDIO TRACKS</span>
          </template>
          <div class="asset-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in getAssetsByType('bgm')" :key="item.path">
                <AssetCard :asset="item" @generate="onGenerate" />
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, MagicStick, PictureFilled, UserFilled, Headset } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AssetCard from './AssetCard.vue'

const activeTab = ref('背景图')
const auditData = ref(null)

const bannerStyle = {
  background: 'linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/asset_workstation_hero.png")',
  backgroundSize: 'cover',
  backgroundPosition: 'center'
}

onMounted(async () => {
  await onRefresh()
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
    const res = await fetch('/audit_results.json?t=' + Date.now())
    auditData.value = await res.json()
  } catch (err) {
    console.error('Failed to load audit results:', err)
  }
}

function getAssetsByType(type) {
  if (!auditData.value) return []
  return auditData.value.details.filter(d => d.type === type)
}

function onGenerate(asset) {
  ElMessage.success(`Triggered AI Generation for: ${asset.path}`)
}

function onGenerateAll() {
  ElMessage.info('Initializing bulk generation pipeline...')
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
</style>
