<template>
  <section class="section-block" id="section-nodes">
    <div class="section-header">
      <span class="section-title">🔗 节点流程图 (Nodes)</span>
      <template v-if="chapterId">
        <el-button size="small" type="primary" :icon="Plus" @click="addNode('dialogue')">加对话节点</el-button>
        <el-button size="small" type="warning" :icon="Switch" @click="addNode('choice')">加选项节点</el-button>
        <el-button size="small" :icon="MagicStick" @click="autoLayout">自动排版</el-button>
        <el-tag size="small" type="info" style="margin-left:auto">{{ currentChapter?.title }}</el-tag>
      </template>
    </div>

    <!-- No chapter selected -->
    <div v-if="!chapterId" class="node-placeholder">
      <el-empty description="点击上方章节卡片以编辑节点" />
    </div>

    <!-- Canvas + Property Panel side by side -->
    <div v-else style="display:flex; flex:1; overflow:hidden;">
      <!-- Vue Flow -->
      <div style="flex:1;overflow:hidden;position:relative;" @contextmenu.prevent="onContextMenu">
        <VueFlow
          :nodes="flowNodes"
          :edges="flowEdges"
          :node-types="nodeTypes"
          :default-viewport="{ zoom: 0.9, x: 40, y: 40 }"
          fit-view-on-init
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @connect="onConnect"
          @node-click="onNodeClick"
          @pane-click="onPaneClick"
          @connect-end="onConnectEnd"
          style="width:100%;height:100%;background:#0d1117"
        >
          <Background pattern-color="#1a2d48" :gap="24" />
          <!-- <Controls /> -->
          <MiniMap node-color="#6366f1" style="background:#111827; border: 1px solid var(--border);" />

          <!-- Context Menu -->
          <div v-if="menuVisible" class="canvas-context-menu" :style="{ left: menuPos.x + 'px', top: menuPos.y + 'px' }">
             <div class="menu-header">新建节点</div>
             <div class="menu-item" @click="addNodeAtPos('dialogue')">
               <el-icon><ChatDotRound /></el-icon> 对话节点 (Dialogue)
             </div>
             <div class="menu-item" @click="addNodeAtPos('choice')">
               <el-icon><Opportunity /></el-icon> 分歧选择 (Choice)
             </div>
             <div class="menu-item" @click="addNodeAtPos('branch')">
               <el-icon><Filter /></el-icon> 条件判定 (Branch)
             </div>
          </div>
        </VueFlow>
      </div>

      <!-- Right Property Panel -->
      <transition name="slide-right">
        <NodePropPanel
          v-if="selectedNode"
          :node="selectedNode"
          @delete="onDeleteNode"
          @close="selectedNode = null"
          style="width:340px; border-left:1px solid var(--border);"
        />
      </transition>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, markRaw, nextTick } from 'vue'
import { VueFlow, useVueFlow, applyNodeChanges, applyEdgeChanges } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'
import { Plus, Switch, MagicStick, ChatDotRound, Opportunity, Filter } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'
import { layoutNodes } from '../utils/layout.js'
import DialogueNode from './nodes/DialogueNode.vue'
import ChoiceNode from './nodes/ChoiceNode.vue'
import NodePropPanel from './NodePropPanel.vue'

const props = defineProps({ chapterId: String })
const store = useEditorStore()
const { project } = useVueFlow()

const flowNodes = ref([])
const flowEdges = ref([])
const selectedNode = ref(null)

// Context Menu State
const menuVisible = ref(false)
const menuPos = ref({ x: 0, y: 0 })
const menuFlowPos = ref({ x: 0, y: 0 })
const pendingConnection = ref(null) // for drag-to-connect

const nodeTypes = {
  dialogue: markRaw(DialogueNode),
  segment: markRaw(DialogueNode),
  chapter: markRaw(DialogueNode),
  choice: markRaw(ChoiceNode),
  branch: markRaw(ChoiceNode),
}

const currentChapter = computed(() => store.chapters.find(c => c.id === props.chapterId))

// ---- Load chapter ----
watch(() => props.chapterId, (id) => {
  if (id) loadChapter(id)
  selectedNode.value = null
  menuVisible.value = false
}, { immediate: true })

function loadChapter(chapterId) {
  const ch = store.chapters.find(c => c.id === chapterId)
  if (!ch) return

  flowNodes.value = ch.nodes.map((n, i) => ({
    id: n.id,
    type: ['choice','branch'].includes(n.type) ? n.type : 'dialogue',
    position: { x: n._x ?? i * 320, y: n._y ?? 100 },
    data: n
  }))

  flowEdges.value = buildEdges(ch.nodes)
}

function buildEdges(nodes) {
  const edges = []
  for (const n of nodes) {
    if (n.next) {
      edges.push({ id: `e-${n.id}-next`, source: n.id, target: String(n.next), animated: false, style: { stroke: 'rgba(99, 102, 241, 0.5)', strokeWidth: 2 } })
    }
    if (n.choices) {
      n.choices.forEach((c, i) => {
        if (c.next) edges.push({
          id: `e-${n.id}-c${i}-${c.next}`, source: n.id,
          sourceHandle: `choice-${i}`, target: String(c.next),
          label: c.text?.slice(0,12), style: { stroke: 'rgba(245, 158, 11, 0.5)' }
        })
      })
    }
    if (n.conditions) {
      n.conditions.forEach((c, i) => {
        if (c.next) edges.push({
          id: `e-${n.id}-cond${i}`, source: n.id, target: String(c.next),
          label: `${c.variable}==${c.value}`, style: { stroke: '#10b981', strokeDasharray: '5,3' }
        })
      })
    }
    if (n.default) {
      edges.push({ id: `e-${n.id}-def`, source: n.id, target: String(n.default), label: 'default', style: { stroke: '#4b5563' } })
    }
  }
  return edges
}

// ---- Context Menu & Drag-to-Connect ----
const lastConnectStart = ref(null)

function onContextMenu(event) {
  menuVisible.value = true
  menuPos.value = { x: event.clientX, y: event.clientY }
  menuFlowPos.value = project({ x: event.clientX, y: event.clientY })
}

function onConnectStart(params) {
  lastConnectStart.value = params
}

function onConnectEnd(event) {
  // If connection dropped on pane (not on a target handle)
  if (!event.target.classList.contains('vue-flow__handle')) {
    onContextMenu(event)
  } else {
    lastConnectStart.value = null
  }
}

function addNodeAtPos(type) {
  const ch = currentChapter.value; if (!ch) return
  const id = store.addNode(ch.id, type)
  const newNode = {
    id, type: ['choice','branch'].includes(type) ? type : 'dialogue',
    position: menuFlowPos.value,
    data: ch.nodes.find(n => n.id === id)
  }
  flowNodes.value.push(newNode)
  menuVisible.value = false

  // If we came here from a drag-connection, link it!
  if (lastConnectStart.value) {
    const { nodeId, handleId, type: handleType } = lastConnectStart.value
    if (handleType === 'source') {
      onConnect({ source: nodeId, sourceHandle: handleId, target: id })
    }
    lastConnectStart.value = null
  }
  
  ElMessage.success(`已创建并自动连接节点: ${id}`)
}

function onNodesChange(changes) {
  flowNodes.value = applyNodeChanges(changes, flowNodes.value)
  // Persist positions without triggering saveState for every single pixel move (maybe only on drag-end in a production app)
  const ch = currentChapter.value
  if (!ch) return
  for (const fn of flowNodes.value) {
    const n = ch.nodes.find(n => n.id === fn.id)
    if (n && fn.position) { n._x = fn.position.x; n._y = fn.position.y }
  }
}

function onEdgesChange(changes) {
  flowEdges.value = applyEdgeChanges(changes, flowEdges.value)
}

function onConnect(params) {
  const ch = currentChapter.value; if (!ch) return
  const srcNode = ch.nodes.find(n => n.id === params.source)
  if (!srcNode) return

  // Store logic
  if (params.sourceHandle?.startsWith('choice-')) {
    const idx = parseInt(params.sourceHandle.split('-')[1])
    if (srcNode.choices[idx]) srcNode.choices[idx].next = params.target
  } else {
    srcNode.next = params.target
  }
  store.saveState()

  // UI Flow logic
  flowEdges.value.push({
    id: `e-${params.source}-${params.target}-${Date.now()}`,
    source: params.source, sourceHandle: params.sourceHandle, target: params.target,
    animated: false, style: { stroke: 'rgba(99, 102, 241, 0.7)', strokeWidth: 2 }
  })
}

function onNodeClick({ node }) {
  const ch = currentChapter.value; if (!ch) return
  selectedNode.value = ch.nodes.find(n => n.id === node.id) || null
}

function onPaneClick() {
  selectedNode.value = null
  menuVisible.value = false
}

// ---- CRUD (Top buttons fallback) ----
function addNode(type) {
  menuFlowPos.value = { x: 100 + (flowNodes.value.length % 4) * 300, y: 150 }
  addNodeAtPos(type)
}

function onDeleteNode() {
  const ch = currentChapter.value; if (!ch || !selectedNode.value) return
  const id = selectedNode.value.id
  store.deleteNode(ch.id, id)
  flowNodes.value = flowNodes.value.filter(n => n.id !== id)
  flowEdges.value = flowEdges.value.filter(e => e.source !== id && e.target !== id)
  selectedNode.value = null
}

function autoLayout() {
  flowNodes.value = layoutNodes(flowNodes.value, flowEdges.value, 'LR')
  const ch = currentChapter.value; if (!ch) return
  for (const fn of flowNodes.value) {
    const n = ch.nodes.find(n => n.id === fn.id)
    if (n) { n._x = fn.position.x; n._y = fn.position.y }
  }
  store.saveState()
}
</script>

<style scoped>
.section-block {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.2s ease, opacity 0.2s; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(20px); opacity: 0; }
</style>
