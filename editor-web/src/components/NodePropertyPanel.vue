<template>
  <div class="prop-panel">
    <!-- No selection -->
    <div v-if="!selectedNode" class="prop-empty">
      <el-empty description="点击画布中的节点以编辑属性" :image-size="60" />
    </div>

    <!-- Node editor -->
    <template v-else>
      <div class="prop-title">
        <el-tag :type="tagType" size="small">{{ selectedNode.type }}</el-tag>
        <span style="font-size:12px;color:#888;margin-left:6px">{{ selectedNode.id }}</span>
        <el-button
          size="small"
          type="danger"
          :icon="Delete"
          style="margin-left:auto"
          @click="deleteSelected"
        />
      </div>

      <el-form label-position="top" size="small">
        <!-- Speaker -->
        <el-form-item label="说话人 (speaker)">
          <el-select v-model="selectedNode.speaker" placeholder="选择角色或 narrator" clearable style="width:100%">
            <el-option label="narrator" value="narrator" />
            <el-option
              v-for="c in store.assets.characters"
              :key="c.id"
              :label="c.name || c.id"
              :value="c.id"
            />
          </el-select>
        </el-form-item>

        <!-- Text -->
        <el-form-item label="对话文本">
          <el-input
            v-model="selectedNode.text"
            type="textarea"
            :rows="4"
            placeholder="输入对话内容…"
          />
        </el-form-item>

        <!-- Background -->
        <el-form-item label="背景 (bg)">
          <el-select v-model="selectedNode.bg" placeholder="选背景（可留空）" clearable style="width:100%">
            <el-option
              v-for="b in store.assets.backgrounds"
              :key="b.path"
              :label="b.name || b.path"
              :value="b.path"
            />
          </el-select>
        </el-form-item>

        <!-- Music -->
        <el-form-item label="音乐 (music)">
          <el-select v-model="selectedNode.music" placeholder="选背景音乐（可留空）" clearable style="width:100%">
            <el-option
              v-for="(desc, key) in store.assets.bgm"
              :key="key"
              :label="desc || key"
              :value="key"
            />
          </el-select>
        </el-form-item>

        <!-- Next (for dialogue) -->
        <el-form-item v-if="selectedNode.type !== 'choice' && selectedNode.type !== 'branch'" label="下一节点 (next)">
          <el-input v-model="selectedNode.next" placeholder="目标 node_id 或留空" />
        </el-form-item>

        <!-- Choices (for choice node) -->
        <template v-if="selectedNode.type === 'choice' || selectedNode.type === 'branch'">
          <el-form-item label="选项列表">
            <div style="width:100%;display:flex;flex-direction:column;gap:8px">
              <div
                v-for="(c, i) in selectedNode.choices"
                :key="i"
                style="background:#0d1b2a;border-radius:6px;padding:8px"
              >
                <el-input v-model="c.text" placeholder="选项文字" size="small" style="margin-bottom:4px"/>
                <div style="display:flex;gap:4px">
                  <el-input v-model="c.next" placeholder="跳转 node_id" size="small" style="flex:1"/>
                  <el-button size="small" :icon="Delete" @click="selectedNode.choices.splice(i,1)" />
                </div>
              </div>
              <el-button size="small" :icon="Plus" @click="selectedNode.choices.push({text:'',next:null})">
                添加选项
              </el-button>
            </div>
          </el-form-item>
        </template>

        <!-- Conditions (for branch) -->
        <template v-if="selectedNode.type === 'branch'">
          <el-form-item label="条件列表">
            <div style="width:100%;display:flex;flex-direction:column;gap:8px">
              <div v-for="(c, i) in selectedNode.conditions" :key="i"
                style="background:#0d1b2a;border-radius:6px;padding:8px">
                <el-input v-model="c.variable" placeholder="变量名" size="small" style="margin-bottom:4px"/>
                <div style="display:flex;gap:4px;margin-bottom:4px">
                  <el-input v-model="c.value" placeholder="值" size="small" style="flex:1"/>
                  <el-input v-model="c.next" placeholder="跳转 node_id" size="small" style="flex:1"/>
                  <el-button size="small" :icon="Delete" @click="selectedNode.conditions.splice(i,1)" />
                </div>
              </div>
              <el-input v-model="selectedNode.default" placeholder="默认跳转 default node_id" size="small"/>
              <el-button size="small" :icon="Plus" @click="selectedNode.conditions.push({variable:'',value:'',next:null})">
                添加条件
              </el-button>
            </div>
          </el-form-item>
        </template>

        <!-- node ID (last so people don't accidentally change it first) -->
        <el-form-item label="Node ID">
          <el-input v-model="selectedNode.id" disabled size="small" />
        </el-form-item>
      </el-form>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'
import { useSelectionStore } from '../stores/selection.js'

const store = useEditorStore()
const sel = useSelectionStore()

const selectedNode = computed(() => {
  if (!sel.selectedNodeId || !sel.selectedChapterId) return null
  const ch = store.chapters.find(c => c.id === sel.selectedChapterId)
  if (!ch) return null
  return ch.nodes.find(n => n.id === sel.selectedNodeId) || null
})

const tagType = computed(() => {
  const t = selectedNode.value?.type
  if (t === 'choice') return 'warning'
  if (t === 'branch') return 'danger'
  return 'info'
})

async function deleteSelected() {
  if (!selectedNode.value) return
  try {
    await ElMessageBox.confirm(`确认删除节点 ${selectedNode.value.id}？`, '警告', { type: 'warning' })
    store.deleteNode(sel.selectedChapterId, sel.selectedNodeId)
    sel.clearNode()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.prop-panel { display: flex; flex-direction: column; gap: 12px; }
.prop-empty { padding-top: 60px; }
.prop-title {
  display: flex;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid #0f3460;
  margin-bottom: 4px;
}
:deep(.el-form-item__label) { color: #aaa !important; font-size: 12px; }
:deep(.el-input__inner, .el-textarea__inner) {
  background: #0d1b2a !important;
  border-color: #0f3460 !important;
  color: #e0e0e0 !important;
}
</style>
