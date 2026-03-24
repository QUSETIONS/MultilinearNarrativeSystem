<template>
  <div class="narrative-control-container">
    <div class="header">
      <h2>叙事控制中心 (Narrative Control)</h2>
      <div style="display: flex; gap: 8px;">
        <el-button :icon="Check" type="primary" @click="saveConfig">保存全局配置</el-button>
      </div>
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

      <!-- Social Force Graph + Matrix -->
      <el-col :span="16">
        <el-card class="dark-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Share /></el-icon> 角色关系网络</span>
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="graph">力导向图</el-radio-button>
                <el-radio-button value="matrix">矩阵</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <!-- Force Graph View -->
          <div v-show="viewMode === 'graph'" class="force-graph-container" ref="graphContainer">
            <svg ref="svgEl" :width="graphWidth" :height="graphHeight">
              <!-- Links -->
              <line v-for="link in graphLinks" :key="link.id"
                :x1="link.source.x" :y1="link.source.y"
                :x2="link.target.x" :y2="link.target.y"
                :stroke="linkColor(link.trust)"
                :stroke-width="Math.max(1, Math.abs(link.trust) * 4)"
                stroke-opacity="0.6"
                @click="openLinkEditor(link.sourceName, link.targetName)"
                class="graph-link"
              />
              <!-- Link labels -->
              <text v-for="link in graphLinks" :key="'t'+link.id"
                :x="(link.source.x + link.target.x) / 2"
                :y="(link.source.y + link.target.y) / 2 - 6"
                fill="#888" font-size="10" text-anchor="middle"
              >
                T:{{ link.trust.toFixed(1) }}
              </text>

              <!-- Nodes -->
              <g v-for="node in graphNodes" :key="node.id"
                :transform="`translate(${node.x}, ${node.y})`"
                class="graph-node"
                @mousedown="startDrag(node, $event)"
              >
                <circle r="24" :fill="nodeColor(node.id)" stroke="rgba(255,255,255,0.3)" stroke-width="2" />
                <text dy="4" text-anchor="middle" fill="white" font-size="11" font-weight="bold">
                  {{ node.label.substring(0, 4) }}
                </text>
                <text dy="38" text-anchor="middle" fill="#aaa" font-size="10">
                  {{ node.label }}
                </text>
              </g>
            </svg>
          </div>

          <!-- Matrix View (original) -->
          <div v-show="viewMode === 'matrix'" class="matrix-wrapper">
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
    <el-dialog v-model="editorVisible" title="关系链路微调" width="440px" custom-class="dark-dialog">
      <div v-if="activeLink" class="link-info">
        <h3 style="margin-bottom: 16px;">{{ activeLink.source }} → {{ activeLink.target }}</h3>
        <el-form label-width="80px">
          <el-form-item label="信任度">
            <el-slider v-model="activeLink.trust" :min="-1" :max="1" :step="0.1" show-input />
            <div class="hint-text">影响角色间互动的色调和光影。正值 = 暖色调/亲近, 负值 = 冷色调/对立</div>
          </el-form-item>
          <el-form-item label="紧张感">
            <el-slider v-model="activeLink.tension" :min="0" :max="1" :step="0.1" show-input />
            <div class="hint-text">高紧张 → 更强对比度、更暗的氛围</div>
          </el-form-item>
          <el-form-item label="阶级感">
            <el-slider v-model="activeLink.hierarchy" :min="0" :max="1" :step="0.1" show-input />
            <div class="hint-text">影响角色立绘的姿态和构图</div>
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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Compass, Share, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { API } from '../utils/api.config.js'

const config = ref({
  global_context: { era: '', theme: '', negative_prompt: '' },
  social_graph: {}
})

const charList = ref(['Poirot', 'Countess', 'Bouc', 'Princess', 'MacQueen'])
const editorVisible = ref(false)
const activeLink = ref(null)
const viewMode = ref('graph')
const graphContainer = ref(null)
const svgEl = ref(null)
const graphWidth = ref(600)
const graphHeight = ref(380)

// Force graph state
const graphNodes = ref([])
const graphLinks = ref([])
let animFrame = null
let dragging = null

const nodeColors = ['#6366f1', '#f59e0b', '#10b981', '#ec4899', '#3b82f6', '#8b5cf6', '#ef4444']

function nodeColor(idx) {
  return nodeColors[idx % nodeColors.length]
}

function linkColor(trust) {
  if (trust > 0.3) return '#10b981'
  if (trust < -0.3) return '#ef4444'
  return '#6b7280'
}

function initGraph() {
  const cx = graphWidth.value / 2
  const cy = graphHeight.value / 2
  const radius = Math.min(cx, cy) * 0.6

  // Place nodes in a circle
  graphNodes.value = charList.value.map((name, i) => {
    const angle = (2 * Math.PI * i) / charList.value.length - Math.PI / 2
    return {
      id: i,
      label: name,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
      vx: 0, vy: 0
    }
  })

  // Build links from social_graph
  updateGraphLinks()
}

function updateGraphLinks() {
  const links = []
  const nodeMap = {}
  graphNodes.value.forEach(n => { nodeMap[n.label] = n })

  for (let i = 0; i < charList.value.length; i++) {
    for (let j = i + 1; j < charList.value.length; j++) {
      const s = charList.value[i]
      const t = charList.value[j]
      const trust = getTrust(s, t) || 0
      links.push({
        id: `${s}-${t}`,
        source: nodeMap[s],
        target: nodeMap[t],
        sourceName: s,
        targetName: t,
        trust: trust
      })
    }
  }
  graphLinks.value = links
}

// Simple force simulation step
function simulate() {
  const nodes = graphNodes.value
  const links = graphLinks.value
  const cx = graphWidth.value / 2
  const cy = graphHeight.value / 2

  // Repulsion
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[j].x - nodes[i].x
      const dy = nodes[j].y - nodes[i].y
      const dist = Math.max(30, Math.sqrt(dx * dx + dy * dy))
      const force = 800 / (dist * dist)
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      nodes[i].vx -= fx; nodes[i].vy -= fy
      nodes[j].vx += fx; nodes[j].vy += fy
    }
  }

  // Attraction (links)
  for (const link of links) {
    const dx = link.target.x - link.source.x
    const dy = link.target.y - link.source.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    const desired = 120
    const force = (dist - desired) * 0.005
    const fx = (dx / dist) * force
    const fy = (dy / dist) * force
    link.source.vx += fx; link.source.vy += fy
    link.target.vx -= fx; link.target.vy -= fy
  }

  // Center gravity
  for (const node of nodes) {
    node.vx += (cx - node.x) * 0.002
    node.vy += (cy - node.y) * 0.002
  }

  // Apply velocity with damping
  for (const node of nodes) {
    if (dragging && dragging.id === node.id) continue
    node.vx *= 0.85; node.vy *= 0.85
    node.x += node.vx; node.y += node.vy
    // Bounds
    node.x = Math.max(30, Math.min(graphWidth.value - 30, node.x))
    node.y = Math.max(30, Math.min(graphHeight.value - 30, node.y))
  }

  animFrame = requestAnimationFrame(simulate)
}

function startDrag(node, event) {
  dragging = node
  const onMove = (e) => {
    const rect = svgEl.value.getBoundingClientRect()
    node.x = e.clientX - rect.left
    node.y = e.clientY - rect.top
    node.vx = 0; node.vy = 0
  }
  const onUp = () => {
    dragging = null
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

// Data functions
async function fetchConfig() {
  try {
    config.value = await apiService.getNarrativeConfig()
    nextTick(initGraph)
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
  updateGraphLinks()
  ElMessage.success('局部关系已缓存 (需点保存应用至引擎)')
}

async function saveConfig() {
  try {
    await apiService.updateNarrativeConfig({
      theme: config.value.global_context.theme,
      era: config.value.global_context.era,
      social_graph: config.value.social_graph
    })
    ElMessage.success('全局叙事配置已同步至引擎')
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  fetchConfig()
  nextTick(() => {
    if (graphContainer.value) {
      graphWidth.value = graphContainer.value.clientWidth || 600
    }
    initGraph()
    simulate()
  })
})

watch(viewMode, (v) => {
  if (v === 'graph') {
    nextTick(() => {
      if (!animFrame) simulate()
    })
  } else {
    if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }
  }
})
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Force Graph */
.force-graph-container {
  width: 100%;
  height: 380px;
  overflow: hidden;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
  cursor: default;
}

.force-graph-container svg {
  display: block;
}

.graph-node {
  cursor: grab;
}

.graph-node:active {
  cursor: grabbing;
}

.graph-node circle {
  transition: r 0.2s;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.graph-node:hover circle {
  r: 28;
  stroke: rgba(255,255,255,0.6);
}

.graph-link {
  cursor: pointer;
  transition: stroke-width 0.2s;
}

.graph-link:hover {
  stroke-width: 6 !important;
  stroke-opacity: 1 !important;
}

/* Matrix */
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

.link-info h3 {
  color: var(--text-primary);
}

.hint-text {
  font-size: 11px;
  color: #777;
  margin-top: 4px;
  line-height: 1.3;
}
</style>
