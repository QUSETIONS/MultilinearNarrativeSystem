<template>
  <div
    class="premium-node choice"
    :class="{ selected, highlight: data.id === selection.selectedNodeId }"
    @click.stop="onSelect"
  >
    <!-- Entry Point Handle -->
    <Handle type="target" :position="Position.Left" :style="{ background: 'var(--warning)' }" />
    
    <!-- Node Header -->
    <div class="node-top-bar" :style="{ borderLeft: `4px solid var(--warning)` }">
      <el-icon :size="20" style="color: var(--warning)"><Opportunity /></el-icon>
      <div style="flex: 1; min-width: 0;">
        <div class="speaker-name">分歧选择</div>
        <div class="node-id-badge">ID: {{ data.id }}</div>
      </div>
    </div>

    <!-- Node Body -->
    <div class="node-content">
      <div v-if="!data.choices?.length" style="color: var(--text-muted); font-size: 12px; font-style: italic;">
        无选项，请添加...
      </div>
      <div v-for="(c, i) in data.choices" :key="i" class="choice-row">
        <span class="choice-num">{{ i + 1 }}</span>
        <span class="choice-text">{{ c.text || '未定义文本' }}</span>
        
        <!-- Individual Source Handle for each choice -->
        <Handle
          type="source"
          :id="`choice-${i}`"
          :position="Position.Right"
          :style="{ top: `${4 + i * 28}px`, background: 'var(--warning)' }"
          class="choice-handle"
        />
      </div>
    </div>

    <!-- Additional Handles for Conditions / Branch -->
    <template v-if="data.conditions?.length">
      <div class="node-footer" style="flex-direction: column; gap: 4px; padding-top: 4px; border-top: 1px solid var(--border);">
        <div v-for="(cond, ci) in data.conditions" :key="'cond'+ci" style="font-size: 10px; color: var(--success); display: flex; align-items: center; gap: 4px;">
           <el-icon><Filter /></el-icon> {{ cond.variable }} == {{ cond.value }}
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Position, Handle } from '@vue-flow/core'
import { Opportunity, Filter } from '@element-plus/icons-vue'
import { useSelectionStore } from '../../stores/selection.js'

const props = defineProps({
  data: Object,
  selected: Boolean,
  id: String
})

const selection = useSelectionStore()

function onSelect() {
  selection.selectNode(props.id)
}
</script>

<style scoped>
.choice-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  position: relative;
  min-height: 24px;
}
.choice-num {
  font-size: 11px; font-weight: 800; color: var(--warning);
  background: rgba(245, 158, 11, 0.1);
  width: 18px; height: 18px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
}
.choice-text { font-size: 12px; color: var(--text-primary); flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.choice-handle {
  right: -12px !important;
  width: 10px !important; height: 10px !important;
  border: 2px solid var(--bg-surface) !important;
}

.speaker-name { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.node-id-badge { font-size: 10px; color: var(--text-muted); }
</style>
