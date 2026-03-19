<template>
  <div style="position:relative;width:100%;height:100%">
    <!-- Toolbar inside canvas -->
    <div class="canvas-toolbar">
      <el-select
        v-model="currentChapterId"
        placeholder="选择章节"
        size="small"
        style="width:180px"
        @change="loadChapter"
      >
        <el-option
          v-for="ch in store.chapters"
          :key="ch.id"
          :label="ch.title || ch.id"
          :value="ch.id"
        />
      </el-select>
      <el-button size="small" :icon="MagicStick" @click="autoLayout" title="自动排版">
        自动排版
      </el-button>
      <el-button size="small" :icon="Plus" type="primary" @click="addDialogueNode">
        加对话节点
      </el-button>
      <el-button size="small" :icon="CirclePlus" type="warning" @click="addChoiceNode">
        加选项节点
      </el-button>
    </div>

    <!-- Empty state -->
    <div v-if="!currentChapterId" class="canvas-empty">
      <el-empty description="请从左侧选择章节，或导入 JSON 文件开始编辑" />
    </div>

    <!-- Vue Flow Canvas -->
    <VueFlow
      v-else
      :nodes="flowNodes"
      :edges="flowEdges"
      :node-types="nodeTypes"
      :default-viewport="{ zoom: 0.85, x: 40, y: 40 }"
      fit-view-on-init
      :connect-on-click="false"
      @nodes-change="onNodesChange"
      @edges-change="onEdgesChange"
      @connect="onConnect"
      @node-click="onNodeClick"
      style="width:100%;height:100%;background:#0d1b2a"
    >
      <Background pattern-color="#1a2d48" :gap="20" />
      <Controls />
      <MiniMap node-color="#e94560" />
    </VueFlow>
  </div>
</template>

<script setup>
import { ref, computed, watch, markRaw } from 'vue'
import { VueFlow, useVueFlow, applyNodeChanges, applyEdgeChanges } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { MagicStick, Plus, CirclePlus } from '@element-plus/icons-vue'
import { useEditorStore } from '../stores/editor.js'
import { useSelectionStore } from '../stores/selection.js'
import { layoutNodes } from '../utils/layout.js'
import DialogueNode from './nodes/DialogueNode.vue'
import ChoiceNode from './nodes/ChoiceNode.vue'

const store = useEditorStore()
const sel = useSelectionStore()

const currentChapterId = ref(null)
const flowNodes = ref([])
const flowEdges = ref([])

// Register custom node types
const nodeTypes = {
  dialogue: markRaw(DialogueNode),
  choice: markRaw(ChoiceNode),
  branch: markRaw(ChoiceNode),  // branch uses same visual as choice
  segment: markRaw(DialogueNode),
  chapter: markRaw(DialogueNode),
}

// ---- Load chapter into canvas ----
function loadChapter(chapterId) {
  const ch = store.chapters.find(c => c.id === chapterId)
  if (!ch) return

  const nodes = ch.nodes.map((n, i) => ({
    id: n.id,
    type: n.type === 'choice' || n.type === 'branch' ? n.type : 'dialogue',
    position: { x: n._x ?? i * 320, y: n._y ?? 0 },
    data: { ...n }
  }))

  const edges = []
  for (const n of ch.nodes) {
    if (n.next) {
      edges.push({ id: `e-${n.id}-${n.next}`, source: n.id, target: n.next, animated: false })
    }
    if (n.choices) {
      n.choices.forEach((c, i) => {
        if (c.next) {
          edges.push({
            id: `e-${n.id}-choice${i}-${c.next}`,
            source: n.id,
            sourceHandle: `choice-${i}`,
            target: c.next,
            label: c.text?.slice(0, 15),
            style: { stroke: '#f4a261' }
          })
        }
      })
    }
    if (n.conditions) {
      n.conditions.forEach((c, i) => {
        if (c.next) {
          edges.push({
            id: `e-${n.id}-cond${i}-${c.next}`,
            source: n.id,
            target: c.next,
            label: `${c.variable}==${c.value}`,
            style: { stroke: '#90e0ef' }
          })
        }
      })
    }
    if (n.default) {
      edges.push({ id: `e-${n.id}-default-${n.default}`, source: n.id, target: n.default, label: 'default', style: { stroke: '#aaa' } })
    }
  }

  flowNodes.value = nodes
  flowEdges.value = edges
}

// Reload when chapters change externally
watch(() => store.chapters, () => {
  if (currentChapterId.value) loadChapter(currentChapterId.value)
}, { deep: true })

// ---- Auto-layout ----
function autoLayout() {
  flowNodes.value = layoutNodes(flowNodes.value, flowEdges.value, 'LR')
  persistNodePositions()
}

// ---- Sync positions back to store ----
function persistNodePositions() {
  const ch = store.chapters.find(c => c.id === currentChapterId.value)
  if (!ch) return
  for (const fn of flowNodes.value) {
    const n = ch.nodes.find(n => n.id === fn.id)
    if (n) {
      n._x = fn.position.x
      n._y = fn.position.y
    }
  }
}

// ---- Vue Flow Event Handlers ----
function onNodesChange(changes) {
  flowNodes.value = applyNodeChanges(changes, flowNodes.value)
  persistNodePositions()
}

function onEdgesChange(changes) {
  flowEdges.value = applyEdgeChanges(changes, flowEdges.value)
}

function onConnect(params) {
  // A user drew a new edge; update the store's `next`
  const ch = store.chapters.find(c => c.id === currentChapterId.value)
  if (!ch) return
  const srcNode = ch.nodes.find(n => n.id === params.source)
  if (!srcNode) return

  if (params.sourceHandle && params.sourceHandle.startsWith('choice-')) {
    const idx = parseInt(params.sourceHandle.split('-')[1])
    if (srcNode.choices[idx]) srcNode.choices[idx].next = params.target
  } else {
    srcNode.next = params.target
  }

  // Add visual edge
  flowEdges.value.push({
    id: `e-${params.source}-${params.target}-${Date.now()}`,
    source: params.source,
    sourceHandle: params.sourceHandle,
    target: params.target,
    animated: false
  })
}

function onNodeClick({ node }) {
  sel.selectNode(node.id)
  sel.selectedChapterId = currentChapterId.value
}

// ---- Add nodes ----
function addDialogueNode() {
  if (!currentChapterId.value) return
  const id = store.addNode(currentChapterId.value, 'dialogue')
  flowNodes.value.push({
    id, type: 'dialogue', position: { x: 200, y: 200 },
    data: { id, type: 'dialogue', text: '', speaker: '', next: null }
  })
}

function addChoiceNode() {
  if (!currentChapterId.value) return
  const id = store.addNode(currentChapterId.value, 'choice')
  flowNodes.value.push({
    id, type: 'choice', position: { x: 300, y: 300 },
    data: { id, type: 'choice', choices: [] }
  })
}
</script>

<style scoped>
.canvas-toolbar {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
  display: flex;
  gap: 8px;
  align-items: center;
  background: rgba(22, 33, 62, 0.9);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #0f3460;
  backdrop-filter: blur(4px);
}
.canvas-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
