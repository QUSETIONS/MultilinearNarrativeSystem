<template>
  <div class="narrative-control-container">
    <div class="header">
      <h2>叙事控制中心 (Narrative Control)</h2>
      <el-button type="primary" :icon="Check" @click="saveConfig">保存全局配置</el-button>
    </div>

    <el-row :gutter="20">
      <!-- Attention Settings -->
      <el-col :span="8">
        <el-card class="dark-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Compass /></el-icon> 全局关注点 (Attention)</span>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item label="时代背景 (Era)">
              <el-input v-model="config.global_context.era" placeholder="例如: 1930s" />
            </el-form-item>
            <el-form-item label="叙事主题 (Theme)">
              <el-input v-model="config.global_context.theme" placeholder="例如: 1930s Detective Mystery" />
            </el-form-item>
            <el-form-item label="全局负向提示词 (Negative)">
              <el-input v-model="config.global_context.negative_prompt" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Social Matrix -->
      <el-col :span="16">
        <el-card class="dark-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Share /></el-icon> 社交关系矩阵 (Social Matrix)</span>
            </div>
          </template>
          <div class="matrix-wrapper">
            <el-table :data="charList" border style="width: 100%" class="matrix-table">
              <el-table-column label="角色 / 目标角色" width="150" fixed>
                <template #default="scope">
                  <span class="char-name">{{ scope.row }}</span>
                </template>
              </el-table-column>
              <el-table-column v-for="target in charList" :key="target" :label="target">
                <template #default="scope">
                  <div v-if="scope.row !== target" class="cell-editor" @click="openLinkEditor(scope.row, target)">
                    <div class="stat-pill" :class="getRelationClass(scope.row, target)">
                      T: {{ getTrust(scope.row, target) }}
                    </div>
                  </div>
                  <div v-else class="cell-self">---</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Relation Editor Dialog -->
    <el-dialog v-model="editorVisible" title="关系链路微调" width="400px" custom-class="dark-dialog">
      <div v-if="activeLink" class="link-info">
        <h3>{{ activeLink.source }} -> {{ activeLink.target }}</h3>
        <el-form label-width="80px">
          <el-form-item label="信任度">
            <el-slider v-model="activeLink.trust" :min="-1" :max="1" :step="0.1" show-input />
          </el-form-item>
          <el-form-item label="紧张感">
            <el-slider v-model="activeLink.tension" :min="0" :max="1" :step="0.1" show-input />
          </el-form-item>
          <el-form-item label="阶级感">
            <el-slider v-model="activeLink.hierarchy" :min="0" :max="1" :step="0.1" show-input />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" @click="applyLinkChanges">更新关系</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Compass, Share, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const config = ref({
  global_context: { era: '', theme: '', negative_prompt: '' },
  social_graph: {}
})

const charList = ref(['Poirot', 'Countess', 'Bouc', 'Princess', 'MacQueen'])
const editorVisible = ref(false)
const activeLink = ref(null)

async function fetchConfig() {
  try {
    const res = await fetch('http://localhost:8088/narrative/config')
    config.value = await res.json()
  } catch (err) {
    ElMessage.error('无法连接至叙事引擎')
  }
}

function getTrust(source, target) {
  return config.value.social_graph?.[source]?.[target]?.trust ?? 0
}

function getRelationClass(source, target) {
  const t = getTrust(source, target)
  if (t < -0.3) return 'hostile'
  if (t > 0.3) return 'trusted'
  return 'neutral'
}

function openLinkEditor(source, target) {
  const rel = config.value.social_graph?.[source]?.[target] || { trust: 0, tension: 0.5, hierarchy: 0.5 }
  activeLink.value = { source, target, ...rel }
  editorVisible.value = true
}

function applyLinkChanges() {
  if (!config.value.social_graph[activeLink.value.source]) {
    config.value.social_graph[activeLink.value.source] = {}
  }
  config.value.social_graph[activeLink.value.source][activeLink.value.target] = {
    trust: activeLink.value.trust,
    tension: activeLink.value.tension,
    hierarchy: activeLink.value.hierarchy
  }
  editorVisible.value = false
  ElMessage.success('局部关系已缓存 (需点保存应用至引擎)')
}

async function saveConfig() {
  try {
    await fetch('http://localhost:8088/narrative/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        theme: config.value.global_context.theme,
        era: config.value.global_context.era,
        social_graph: config.value.social_graph
      })
    })
    ElMessage.success('全局叙事配置已同步至引擎')
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchConfig)
</script>

<style scoped>
.narrative-control-container {
  padding: 24px;
  background: var(--bg-dark);
  min-height: 100vh;
  color: var(--text-base);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dark-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  margin-bottom: 20px;
}

.matrix-wrapper {
  overflow-x: auto;
}

.cell-editor {
  cursor: pointer;
  padding: 8px;
  transition: all 0.2s;
}

.cell-editor:hover {
  background: rgba(255, 255, 255, 0.05);
}

.stat-pill {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  text-align: center;
}

.trusted { background: rgba(103, 194, 58, 0.2); color: #67c23a; border: 1px solid #67c23a; }
.hostile { background: rgba(245, 108, 108, 0.2); color: #f56c6c; border: 1px solid #f56c6c; }
.neutral { background: rgba(144, 147, 153, 0.2); color: #909399; border: 1px solid #909399; }

.char-name {
  font-weight: bold;
  color: var(--primary-light);
}

.matrix-table :deep(.el-table__row) {
  background: transparent !important;
}
</style>
