<template>
  <div
    class="premium-node dialogue"
    :class="{ selected, highlight: data.id === selection.selectedNodeId }"
    @click.stop="onSelect"
  >
    <!-- Entry Point Handle -->
    <Handle type="target" :position="Position.Left" :style="{ background: 'var(--accent)' }" />
    
    <!-- Node Header -->
    <div class="node-top-bar" :style="{ borderLeft: `4px solid ${typeColor}` }">
      <div class="speaker-avatar" :style="{ background: avatarColor }">
        {{ (data.speaker || 'n').slice(0, 1).toUpperCase() }}
      </div>
      <div style="flex: 1; min-width: 0;">
        <div class="speaker-name">{{ data.speaker || 'narrator' }}</div>
        <div class="node-id-badge">ID: {{ data.id }}</div>
      </div>
      <el-tag size="mini" type="info" effect="dark" style="border:none; opacity: 0.6;">{{ data.type }}</el-tag>
    </div>

    <!-- Node Body -->
    <div class="node-content">
      <div class="text-excerpt">
        {{ data.text || '(空台词...)' }}
      </div>
    </div>

    <!-- Node Footer -->
    <div class="node-footer" v-if="data.bg || data.music">
      <span v-if="data.bg" title="背景切换"><el-icon><Picture /></el-icon> {{ shortPath(data.bg) }}</span>
      <span v-if="data.music" title="音乐切换"><el-icon><Headset /></el-icon> {{ shortPath(data.music) }}</span>
    </div>

    <!-- Exit Point Handle -->
    <Handle type="source" :position="Position.Right" :style="{ background: 'var(--accent)' }" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Position, Handle } from '@vue-flow/core'
import { Picture, Headset } from '@element-plus/icons-vue'
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

function shortPath(p) {
  if (!p) return ''
  const parts = p.split('/')
  return parts[parts.length - 1]
}

const typeColor = computed(() => {
  if (props.data.type === 'segment') return '#10b981'
  if (props.data.type === 'chapter') return '#f59e0b'
  return '#3b82f6'
})

const avatarColor = computed(() => {
  const s = props.data.speaker || 'narrator'
  if (s === 'narrator') return '#4b5563'
  // Simple hash for color
  let hash = 0
  for (let i = 0; i < s.length; i++) hash = s.charCodeAt(i) + ((hash << 5) - hash)
  const c = (hash & 0x00FFFFFF).toString(16).toUpperCase()
  return '#' + '00000'.substring(0, 6 - c.length) + c
})
</script>

<style scoped>
.premium-node.dialogue {
  border-left-width: 0 !important; /* using colored bar in header instead or keep it simple */
}

.speaker-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: white;
  border: 1px solid rgba(255,255,255,0.2);
  flex-shrink: 0;
}

.speaker-name { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.node-id-badge { font-size: 10px; color: var(--text-muted); }

.text-excerpt {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-footer span { display: flex; align-items: center; gap: 4px; }
</style>
